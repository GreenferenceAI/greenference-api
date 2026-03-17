import pytest
from fastapi import HTTPException

from greenference_builder.application.services import BuilderService
from greenference_builder.infrastructure.repository import BuilderRepository
from greenference_control_plane.application.services import ControlPlaneService
from greenference_control_plane.infrastructure.repository import ControlPlaneRepository
from greenference_control_plane.transport import routes as control_plane_routes
from greenference_control_plane.transport import security as control_plane_security
from greenference_gateway.application.services import GatewayService
from greenference_gateway.infrastructure.repository import GatewayRepository
from greenference_gateway.transport import routes as gateway_routes
from greenference_gateway.transport import security as gateway_security
from greenference_persistence import CredentialStore, FixedWindowRateLimiter, WorkflowEventRepository
from greenference_protocol import (
    APIKeyCreateRequest,
    BuildRequest,
    CapacityUpdate,
    DeploymentCreateRequest,
    Heartbeat,
    MinerRegistration,
    NodeCapability,
    ProbeResult,
    UserRegistrationRequest,
    WorkloadCreateRequest,
    WorkloadSpec,
)
from greenference_validator.application.services import ValidatorService
from greenference_validator.infrastructure.repository import ValidatorRepository
from greenference_validator.transport import routes as validator_routes
from greenference_validator.transport import security as validator_security


def _seed_keys(repository: GatewayRepository) -> tuple[str, str]:
    gateway = GatewayService(repository=repository)
    user = gateway.register_user(UserRegistrationRequest(username="alice", email="alice@example.com"))
    user_key = gateway.create_api_key(APIKeyCreateRequest(name="user", user_id=user.user_id))
    admin_key = gateway.create_api_key(APIKeyCreateRequest(name="admin", user_id=user.user_id, admin=True))
    return user_key.secret, admin_key.secret


def test_gateway_routes_require_api_key_and_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    shared_db = "sqlite+pysqlite:///:memory:"
    gateway_repository = GatewayRepository(database_url=shared_db, bootstrap=True)
    builder_repository = BuilderRepository(database_url=shared_db, bootstrap=True)
    control_repository = ControlPlaneRepository(database_url=shared_db, bootstrap=True)
    workflow_repository = WorkflowEventRepository(database_url=shared_db, bootstrap=True)

    gateway_service = GatewayService(
        repository=gateway_repository,
        builder=BuilderService(builder_repository, workflow_repository=workflow_repository),
        control_plane=ControlPlaneService(control_repository, workflow_repository=workflow_repository),
    )
    user_secret, admin_secret = _seed_keys(gateway_repository)

    monkeypatch.setattr(gateway_routes, "service", gateway_service)
    monkeypatch.setattr(
        gateway_security,
        "credential_store",
        CredentialStore(engine=gateway_repository.engine, session_factory=gateway_repository.session_factory),
    )
    monkeypatch.setattr(gateway_security, "rate_limiter", FixedWindowRateLimiter())

    with pytest.raises(HTTPException) as missing:
        gateway_routes.build_image(BuildRequest(image="greenference/echo:latest", context_uri="s3://ctx.zip"))
    assert missing.value.status_code == 401

    build = gateway_routes.build_image(
        BuildRequest(image="greenference/echo:latest", context_uri="s3://ctx.zip"),
        authorization=f"Bearer {user_secret}",
    )
    assert build["status"] == "accepted"

    for _ in range(60):
        payload = gateway_routes.embeddings(
            {"input": "hello", "model": "test-embedding"},
            authorization=f"Bearer {admin_secret}",
        )
        assert payload["object"] == "list"

    with pytest.raises(HTTPException) as limited:
        gateway_routes.embeddings(
            {"input": "hello", "model": "test-embedding"},
            authorization=f"Bearer {admin_secret}",
        )
    assert limited.value.status_code == 429


def test_control_plane_routes_require_miner_header_and_expose_debug_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shared_db = "sqlite+pysqlite:///:memory:"
    control_repository = ControlPlaneRepository(database_url=shared_db, bootstrap=True)
    workflow_repository = WorkflowEventRepository(database_url=shared_db, bootstrap=True)
    gateway_repository = GatewayRepository(database_url=shared_db, bootstrap=True)
    service = ControlPlaneService(control_repository, workflow_repository=workflow_repository)
    _, admin_secret = _seed_keys(gateway_repository)

    monkeypatch.setattr(control_plane_routes, "service", service)
    monkeypatch.setattr(control_plane_security, "service", service)
    monkeypatch.setattr(
        control_plane_security,
        "credential_store",
        CredentialStore(engine=gateway_repository.engine, session_factory=gateway_repository.session_factory),
    )

    registration = MinerRegistration(
        hotkey="miner-a",
        payout_address="5Fminer",
        api_base_url="http://miner-a.local",
        validator_url="http://validator.local",
    )

    with pytest.raises(HTTPException) as mismatch:
        control_plane_routes.register_miner(registration, x_miner_hotkey="miner-b")
    assert mismatch.value.status_code == 403

    control_plane_routes.register_miner(registration, x_miner_hotkey="miner-a")
    control_plane_routes.heartbeat(Heartbeat(hotkey="miner-a", healthy=True), x_miner_hotkey="miner-a")
    control_plane_routes.capacity(
        CapacityUpdate(
            hotkey="miner-a",
            nodes=[
                NodeCapability(
                    hotkey="miner-a",
                    node_id="node-a",
                    gpu_model="a100",
                    gpu_count=1,
                    available_gpus=1,
                    vram_gb_per_gpu=80,
                    cpu_cores=32,
                    memory_gb=128,
                )
            ],
        ),
        x_miner_hotkey="miner-a",
    )
    service.upsert_workload(
        WorkloadSpec(
            **WorkloadCreateRequest(
                name="echo-model",
                image="greenference/echo:latest",
                requirements={"gpu_count": 1},
            ).model_dump()
        )
    )
    workload = service.find_workload_by_name("echo-model")
    assert workload is not None
    deployment = service.create_deployment(DeploymentCreateRequest(workload_id=workload.workload_id))
    service.process_pending_events()

    workflows = control_plane_routes.debug_workflows(authorization=f"Bearer {admin_secret}")
    leases = control_plane_routes.debug_leases(authorization=f"Bearer {admin_secret}")
    metrics = control_plane_routes.platform_metrics(authorization=f"Bearer {admin_secret}")

    assert deployment.deployment_id in {event["payload"]["deployment_id"] for event in workflows if "deployment_id" in event["payload"]}
    assert len(leases) == 1
    assert metrics["gauges"]["deployments.total"] >= 1.0


def test_validator_routes_require_headers_and_expose_probe_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shared_db = "sqlite+pysqlite:///:memory:"
    validator_repository = ValidatorRepository(database_url=shared_db, bootstrap=True)
    gateway_repository = GatewayRepository(database_url=shared_db, bootstrap=True)
    workflow_repository = WorkflowEventRepository(database_url=shared_db, bootstrap=True)
    service = ValidatorService(validator_repository, workflow_repository=workflow_repository)
    _, admin_secret = _seed_keys(gateway_repository)

    monkeypatch.setattr(validator_routes, "service", service)
    monkeypatch.setattr(
        validator_security,
        "credential_store",
        CredentialStore(engine=gateway_repository.engine, session_factory=gateway_repository.session_factory),
    )

    capability = NodeCapability(
        hotkey="miner-a",
        node_id="node-a",
        gpu_model="a100",
        gpu_count=1,
        available_gpus=1,
        vram_gb_per_gpu=80,
        cpu_cores=32,
        memory_gb=128,
    )
    with pytest.raises(HTTPException) as missing:
        validator_routes.register_capability(capability)
    assert missing.value.status_code == 401

    validator_routes.register_capability(capability, x_miner_hotkey="miner-a")
    challenge = validator_routes.create_probe("miner-a", "node-a", authorization=f"Bearer {admin_secret}")
    scorecard = validator_routes.submit_probe_result(
        ProbeResult(
            challenge_id=challenge["challenge_id"],
            hotkey="miner-a",
            node_id="node-a",
            latency_ms=100.0,
            throughput=180.0,
            benchmark_signature="sig-1",
        ),
        x_miner_hotkey="miner-a",
    )
    results = validator_routes.debug_results(authorization=f"Bearer {admin_secret}")
    metrics = validator_routes.validator_metrics(authorization=f"Bearer {admin_secret}")

    assert scorecard["final_score"] > 0
    assert len(results) == 1
    assert metrics["gauges"]["probe.results.total"] == 1.0
