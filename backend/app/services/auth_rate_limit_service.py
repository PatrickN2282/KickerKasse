"""Shared fixed-window limits; blocked attempts never extend the window."""
import hashlib
import hmac
import math
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import case, delete
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.auth_rate_limit import AuthRateLimit


class AuthRateLimitService:
    def __init__(self, db):
        self.engine = db.get_bind()

    @staticmethod
    def _key(scope, identity):
        return hmac.new(settings.SECRET_KEY.encode(), f"{scope}:{identity}".encode(), hashlib.sha256).hexdigest()

    def check(self, scope, identity, limit, seconds):
        with Session(self.engine) as db:
            entry = db.get(AuthRateLimit, self._key(scope, identity))
            if entry and entry.attempts >= limit:
                retry = math.ceil((entry.window_started_at + timedelta(seconds=seconds) - datetime.utcnow()).total_seconds())
                if retry > 0:
                    self._reject(retry)

    def consume(self, scope, identity, limit, seconds):
        key = self._key(scope, identity)
        now = datetime.utcnow()
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        insert = pg_insert if self.engine.dialect.name == "postgresql" else sqlite_insert
        table = AuthRateLimit.__table__
        expired = table.c.window_started_at <= now - timedelta(seconds=seconds)
        statement = insert(table).values(key=key, window_started_at=now, attempts=1)
        statement = statement.on_conflict_do_update(index_elements=[table.c.key], set_={
            "window_started_at": case((expired, now), else_=table.c.window_started_at),
            "attempts": case((expired, 1), (table.c.attempts <= limit, table.c.attempts + 1), else_=table.c.attempts),
        }).returning(table.c.attempts, table.c.window_started_at)
        # A rejected request must not roll back its counter with the business transaction.
        with Session(self.engine) as db:
            db.execute(delete(table).where(table.c.window_started_at < now - timedelta(days=1)))
            attempts, started = db.execute(statement).one()
            db.commit()
        return 0 if attempts <= limit else max(1, math.ceil((started + timedelta(seconds=seconds) - now).total_seconds()))

    def enforce(self, scope, identity, limit, seconds):
        retry = self.consume(scope, identity, limit, seconds)
        if retry:
            self._reject(retry)

    @staticmethod
    def _reject(retry):
        raise HTTPException(status_code=429, detail=f"Zu viele Versuche. Bitte in {retry} Sekunden erneut versuchen.",
                            headers={"Retry-After": str(retry)})
