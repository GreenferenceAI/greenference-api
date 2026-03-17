from fastapi import APIRouter, Header, HTTPException

from greenference_persistence import get_metrics_store
from greenference_protocol import CapacityUpdate, DeploymentStatusUpdate, Heartbeat, MinerRegistration
from greenference_control_plane.application.services import service
from greenference_control_plane.transport.security import require_admin_api_key, require_miner_header

router = APIRouter()
metrics = get_metrics_store("greenference-control-plane")


@router.post("/miner/v1/register", response_model=MinerRegistration)
def register_miner(
    payload: MinerRegistration,
    x_miner_hotkey: str | None = Header(default=None, alias="X-Miner-Hotkey"),
) -> MinerRegistration:
    require_miner_header(payload.hotkey, x_miner_hotkey, allow_unregistered=True)
    return service.register_miner(payload)


@router.post("/miner/v1/heartbeat", response_model=Heartbeat)
def heartbeat(
    payload: Heartbeat,
    x_miner_hotkey: str | None = Header(default=None, alias="X-Miner-Hotkey"),
) -> Heartbeat:
    require_miner_header(payload.hotkey, x_miner_hotkey)
    return service.record_heartbeat(payload)


@router.post("/miner/v1/capacity", response_model=CapacityUpdate)
def capacity(
    payload: CapacityUpdate,
    x_miner_hotkey: str | None = Header(default=None, alias="X-Miner-Hotkey"),
) -> CapacityUpdate:
    require_miner_header(payload.hotkey, x_miner_hotkey)
    return service.update_capacity(payload)


@router.get("/miner/v1/leases/{hotkey}")
def list_leases(
    hotkey: str,
    x_miner_hotkey: str | None = Header(default=None, alias="X-Miner-Hotkey"),
) -> list[dict]:
    require_miner_header(hotkey, x_miner_hotkey)
    return [lease.model_dump(mode="json") for lease in service.list_leases(hotkey)]


@router.post("/miner/v1/deployments/{deployment_id}/status")
def deployment_status(
    deployment_id: str,
    payload: DeploymentStatusUpdate,
    x_miner_hotkey: str | None = Header(default=None, alias="X-Miner-Hotkey"),
) -> dict:
    if payload.deployment_id != deployment_id:
        raise HTTPException(status_code=400, detail="deployment id mismatch")
    deployment = service.repository.get_deployment(deployment_id)
    if deployment is None or deployment.hotkey is None:
        raise HTTPException(status_code=404, detail="deployment not found")
    require_miner_header(deployment.hotkey, x_miner_hotkey)
    saved = service.update_deployment_status(payload)
    return saved.model_dump(mode="json")


@router.get("/platform/v1/usage")
def usage_summary(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict[str, dict[str, float]]:
    require_admin_api_key(authorization, x_api_key)
    return service.usage_summary()


@router.post("/platform/v1/events/process")
def process_events(
    limit: int = 10,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict[str, list]:
    require_admin_api_key(authorization, x_api_key)
    return service.process_pending_events(limit=limit)


@router.get("/platform/v1/debug/workflows")
def debug_workflows(
    subject: str | None = None,
    event_status: str | None = None,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> list[dict]:
    require_admin_api_key(authorization, x_api_key)
    subjects = [subject] if subject else None
    statuses = [event_status] if event_status else None
    return [event.model_dump(mode="json") for event in service.workflow_repository.list_events(subjects, statuses)]


@router.get("/platform/v1/debug/deployments")
def debug_deployments(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> list[dict]:
    require_admin_api_key(authorization, x_api_key)
    return [deployment.model_dump(mode="json") for deployment in service.list_deployments()]


@router.get("/platform/v1/debug/leases")
def debug_leases(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> list[dict]:
    require_admin_api_key(authorization, x_api_key)
    return [lease.model_dump(mode="json") for lease in service.repository.list_assignments()]


@router.get("/platform/v1/debug/deployment-events")
def debug_deployment_events(
    deployment_id: str | None = None,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> list[dict]:
    require_admin_api_key(authorization, x_api_key)
    return service.repository.list_deployment_events(deployment_id=deployment_id)


@router.get("/platform/v1/metrics")
def platform_metrics(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    require_admin_api_key(authorization, x_api_key)
    metrics.set_gauge(
        "leases.active",
        float(len(service.repository.list_assignments(statuses=["assigned", "activating", "active"]))),
    )
    metrics.set_gauge(
        "deployments.total",
        float(len(service.repository.list_deployments())),
    )
    return metrics.snapshot()
