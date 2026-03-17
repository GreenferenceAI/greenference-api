from __future__ import annotations

from fastapi import HTTPException, status

from greenference_persistence import CredentialStore, get_metrics_store
from greenference_validator.application.services import service


credential_store = CredentialStore(
    engine=service.repository.engine,
    session_factory=service.repository.session_factory,
)
metrics = get_metrics_store("greenference-validator")


def require_admin_api_key(authorization: str | None, x_api_key: str | None) -> None:
    if not isinstance(x_api_key, str):
        x_api_key = None
    if not isinstance(authorization, str):
        authorization = None
    secret = x_api_key
    if secret is None and authorization and authorization.lower().startswith("bearer "):
        secret = authorization[7:].strip()
    if not secret:
        metrics.increment("auth.failure.missing_admin_key")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing admin api key")
    api_key = credential_store.get_api_key_by_secret(secret)
    if api_key is None:
        metrics.increment("auth.failure.invalid_admin_key")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid admin api key")
    if not api_key.admin:
        metrics.increment("auth.failure.non_admin_key")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin api key required")
    metrics.increment("auth.success.admin")


def require_miner_header(expected_hotkey: str, x_miner_hotkey: str | None) -> None:
    if not isinstance(x_miner_hotkey, str):
        x_miner_hotkey = None
    if not x_miner_hotkey:
        metrics.increment("auth.failure.missing_miner_header")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing miner hotkey header")
    if x_miner_hotkey != expected_hotkey:
        metrics.increment("auth.failure.miner_hotkey_mismatch")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="miner hotkey mismatch")
    metrics.increment("auth.success.miner")
