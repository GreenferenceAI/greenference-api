from __future__ import annotations

from collections import deque
from typing import Any

from sqlalchemy import select

from greenference_persistence import create_db_engine, create_session_factory, init_database, session_scope
from greenference_persistence.db import needs_bootstrap
from greenference_persistence.orm import APIKeyORM, UserORM
from greenference_protocol import APIKeyRecord, UserRecord


class GatewayRepository:
    def __init__(self, database_url: str | None = None, bootstrap: bool | None = None) -> None:
        self.engine = create_db_engine(database_url)
        self.session_factory = create_session_factory(self.engine)
        self.routing_decisions: deque[dict[str, Any]] = deque(maxlen=200)
        if needs_bootstrap(str(self.engine.url), bootstrap):
            init_database(self.engine)

    def save_user(self, user: UserRecord) -> UserRecord:
        with session_scope(self.session_factory) as session:
            row = session.get(UserORM, user.user_id) or UserORM(user_id=user.user_id)
            row.username = user.username
            row.email = user.email
            row.created_at = user.created_at
            session.add(row)
        return user

    def get_user(self, user_id: str) -> UserRecord | None:
        with session_scope(self.session_factory) as session:
            row = session.get(UserORM, user_id)
            return self._to_user(row) if row else None

    def save_api_key(self, api_key: APIKeyRecord) -> APIKeyRecord:
        with session_scope(self.session_factory) as session:
            row = session.get(APIKeyORM, api_key.key_id) or APIKeyORM(key_id=api_key.key_id)
            row.user_id = api_key.user_id
            row.name = api_key.name
            row.admin = api_key.admin
            row.scopes = api_key.scopes
            row.secret = api_key.secret
            row.created_at = api_key.created_at
            session.add(row)
        return api_key

    def list_api_keys(self, user_id: str | None = None) -> list[APIKeyRecord]:
        with session_scope(self.session_factory) as session:
            stmt = select(APIKeyORM)
            if user_id:
                stmt = stmt.where(APIKeyORM.user_id == user_id)
            rows = session.scalars(stmt).all()
            return [self._to_api_key(row) for row in rows]

    def record_routing_decision(self, decision: dict[str, Any]) -> None:
        self.routing_decisions.appendleft(decision)

    def list_routing_decisions(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(self.routing_decisions)[:limit]

    @staticmethod
    def _to_user(row: UserORM) -> UserRecord:
        return UserRecord(user_id=row.user_id, username=row.username, email=row.email, created_at=row.created_at)

    @staticmethod
    def _to_api_key(row: APIKeyORM) -> APIKeyRecord:
        return APIKeyRecord(
            key_id=row.key_id,
            user_id=row.user_id,
            name=row.name,
            admin=row.admin,
            scopes=row.scopes,
            secret=row.secret,
            created_at=row.created_at,
        )
