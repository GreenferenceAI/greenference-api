from greenference_gateway.application.services import GatewayService
from greenference_gateway.infrastructure.repository import GatewayRepository
from greenference_control_plane.application.services import ControlPlaneService
from greenference_control_plane.infrastructure.repository import ControlPlaneRepository
from greenference_builder.application.services import BuilderService
from greenference_builder.infrastructure.repository import BuilderRepository
from greenference_protocol import (
    APIKeyCreateRequest,
    BuildRequest,
    UserProfileUpdateRequest,
    UserRegistrationRequest,
    UserSecretCreateRequest,
    WorkloadCreateRequest,
    WorkloadShareCreateRequest,
)


def test_gateway_registers_user_and_persists_api_key():
    gateway = GatewayService(
        repository=GatewayRepository(database_url="sqlite+pysqlite:///:memory:", bootstrap=True)
    )
    user = gateway.register_user(UserRegistrationRequest(username="alice", email="alice@example.com"))
    api_key = gateway.create_api_key(APIKeyCreateRequest(name="default", user_id=user.user_id))

    assert user.user_id
    assert api_key.user_id == user.user_id
    assert api_key.secret.startswith("gk_")


def test_gateway_persists_product_foundation_entities():
    shared_db = "sqlite+pysqlite:///:memory:"
    gateway = GatewayService(repository=GatewayRepository(database_url=shared_db, bootstrap=True))
    gateway.control_plane = ControlPlaneService(ControlPlaneRepository(database_url=shared_db, bootstrap=True))

    owner = gateway.register_user(UserRegistrationRequest(username="owner", email="owner@example.com"))
    peer = gateway.register_user(UserRegistrationRequest(username="peer", email="peer@example.com"))

    updated = gateway.update_user_profile(
        owner.user_id,
        UserProfileUpdateRequest(display_name="Owner Name", bio="gpu builder", metadata={"team": "alpha"}),
    )
    assert updated.display_name == "Owner Name"
    assert updated.metadata["team"] == "alpha"

    secret = gateway.create_secret(owner.user_id, UserSecretCreateRequest(name="HF_TOKEN", value="token-123"))
    assert [item.name for item in gateway.list_secrets(owner.user_id)] == ["HF_TOKEN"]
    deleted = gateway.delete_secret(secret.secret_id, user_id=owner.user_id)
    assert deleted.secret_id == secret.secret_id

    workload = gateway.create_workload(
        WorkloadCreateRequest(
            name="private-model",
            image="greenference/private:latest",
            requirements={"gpu_count": 1},
            public=False,
        ),
        owner.user_id,
    )
    assert gateway.list_workloads(user_id=peer.user_id) == []

    share = gateway.share_workload(
        workload.workload_id,
        WorkloadShareCreateRequest(shared_with_user_id=peer.user_id),
        actor_user_id=owner.user_id,
    )
    assert share.shared_with_user_id == peer.user_id

    peer_visible = gateway.list_workloads(user_id=peer.user_id)
    assert [item.workload_id for item in peer_visible] == [workload.workload_id]

    deployment = gateway.create_deployment(
        {"workload_id": workload.workload_id, "requested_instances": 1},
        user_id=peer.user_id,
    )
    assert deployment.owner_user_id == peer.user_id
    assert [item.deployment_id for item in gateway.list_deployments(user_id=peer.user_id)] == [deployment.deployment_id]


def test_gateway_build_visibility_and_workload_metadata():
    shared_db = "sqlite+pysqlite:///:memory:"
    gateway = GatewayService(repository=GatewayRepository(database_url=shared_db, bootstrap=True))
    gateway.control_plane = ControlPlaneService(ControlPlaneRepository(database_url=shared_db, bootstrap=True))
    gateway.builder = BuilderService(BuilderRepository(database_url=shared_db, bootstrap=True))

    owner = gateway.register_user(UserRegistrationRequest(username="builder", email="builder@example.com"))
    peer = gateway.register_user(UserRegistrationRequest(username="viewer", email="viewer@example.com"))

    private_build = gateway.start_build(
        BuildRequest(
            image="greenference/private:latest",
            context_uri="s3://greenference/private.zip",
            display_name="Private Image",
            readme="# private",
            tags=["llm", "gpu"],
            public=False,
        ),
        owner_user_id=owner.user_id,
    )
    public_build = gateway.start_build(
        BuildRequest(
            image="greenference/public:latest",
            context_uri="s3://greenference/public.zip",
            display_name="Public Image",
            public=True,
        ),
        owner_user_id=owner.user_id,
    )

    owner_images = gateway.list_builds(user_id=owner.user_id)
    peer_images = gateway.list_builds(user_id=peer.user_id)
    assert {item.build_id for item in owner_images} == {private_build.build_id, public_build.build_id}
    assert {item.build_id for item in peer_images} == {public_build.build_id}
    assert gateway.get_build(private_build.build_id, user_id=peer.user_id) is None
    assert gateway.get_build(private_build.build_id, user_id=owner.user_id) is not None

    workload = gateway.create_workload(
        WorkloadCreateRequest(
            name="metadata-model",
            image=public_build.image,
            display_name="Metadata Model",
            readme="runtime docs",
            logo_uri="https://example.com/logo.png",
            tags=["chat", "public"],
            requirements={"gpu_count": 1},
            public=True,
        ),
        owner.user_id,
    )
    assert workload.display_name == "Metadata Model"
    assert workload.logo_uri == "https://example.com/logo.png"
    saved = gateway.control_plane.repository.get_workload(workload.workload_id)
    assert saved is not None
    assert saved.tags == ["chat", "public"]
