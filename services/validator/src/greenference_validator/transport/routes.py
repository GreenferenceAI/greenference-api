from fastapi import APIRouter, Header, HTTPException

from greenference_persistence import get_metrics_store
from greenference_protocol import NodeCapability, ProbeResult
from greenference_validator.application.services import (
    InvalidProbeResultError,
    UnknownCapabilityError,
    UnknownProbeChallengeError,
    service,
)
from greenference_validator.transport.security import require_admin_api_key, require_miner_header

router = APIRouter()
metrics = get_metrics_store("greenference-validator")


@router.post("/validator/v1/capabilities", response_model=NodeCapability)
def register_capability(
    payload: NodeCapability,
    x_miner_hotkey: str | None = Header(default=None, alias="X-Miner-Hotkey"),
) -> NodeCapability:
    require_miner_header(payload.hotkey, x_miner_hotkey)
    return service.register_capability(payload)


@router.post("/validator/v1/probes/{hotkey}/{node_id}")
def create_probe(
    hotkey: str,
    node_id: str,
    kind: str = "latency",
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    require_admin_api_key(authorization, x_api_key)
    try:
        return service.create_probe(hotkey=hotkey, node_id=node_id, kind=kind).model_dump(mode="json")
    except UnknownCapabilityError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidProbeResultError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/validator/v1/probes/results")
def submit_probe_result(
    payload: ProbeResult,
    x_miner_hotkey: str | None = Header(default=None, alias="X-Miner-Hotkey"),
) -> dict:
    require_miner_header(payload.hotkey, x_miner_hotkey)
    try:
        return service.submit_probe_result(payload).model_dump(mode="json")
    except UnknownProbeChallengeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UnknownCapabilityError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidProbeResultError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/validator/v1/scores")
def list_scores(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict[str, dict]:
    require_admin_api_key(authorization, x_api_key)
    return {
        hotkey: scorecard.model_dump(mode="json")
        for hotkey, scorecard in service.repository.list_scorecards().items()
    }


@router.post("/validator/v1/weights")
def publish_weights(
    netuid: int = 64,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    require_admin_api_key(authorization, x_api_key)
    return service.publish_weight_snapshot(netuid=netuid).model_dump(mode="json")


@router.get("/validator/v1/debug/results")
def debug_results(
    hotkey: str | None = None,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> list[dict]:
    require_admin_api_key(authorization, x_api_key)
    return [result.model_dump(mode="json") for result in service.repository.list_results(hotkey)]


@router.get("/validator/v1/metrics")
def validator_metrics(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    require_admin_api_key(authorization, x_api_key)
    metrics.set_gauge("probe.results.total", float(len(service.repository.list_results())))
    metrics.set_gauge("scorecards.total", float(len(service.repository.list_scorecards())))
    return metrics.snapshot()
