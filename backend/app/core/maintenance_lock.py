"""Cross-worker maintenance gate; requests fail promptly instead of queueing writes."""
from contextlib import contextmanager
from sqlalchemy import text
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse

MAINTENANCE_LOCK_ID = 716812
BACKUP_PATHS = {"/api/admin/import-export/export","/api/admin/import-export/import","/api/admin/data-maintenance/database-backup/export",
                "/api/admin/data-maintenance/database-backup/restore"}


@contextmanager
def maintenance_gate(engine, *, exclusive=False, key=MAINTENANCE_LOCK_ID):
    if engine.dialect.name != "postgresql":
        raise HTTPException(503, "Sicherung und Wartung benötigen PostgreSQL.")
    with engine.connect() as connection:
        suffix = "" if exclusive else "_shared"
        locked = connection.execute(text(f"SELECT pg_try_advisory_lock{suffix}(:key)"),
                                    {"key": key}).scalar()
        connection.rollback()
        if not locked:
            raise HTTPException(503, "Datenpflege oder andere Zugriffe laufen. Bitte kurz warten und erneut versuchen.")
        try:
            yield
        finally:
            connection.execute(text(f"SELECT pg_advisory_unlock{suffix}(:key)"),
                               {"key": key})
            connection.commit()


class MaintenanceMiddleware:
    def __init__(self, app, engine):
        self.app, self.engine = app, engine

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "").rstrip("/")
        if scope["type"] != "http" or not path.startswith("/api/") or path in BACKUP_PATHS:
            return await self.app(scope, receive, send)
        gate = maintenance_gate(self.engine)
        try:
            await run_in_threadpool(gate.__enter__)
        except HTTPException as exc:
            return await JSONResponse({"detail": exc.detail}, status_code=exc.status_code,
                                      headers={"Retry-After": "5"})(scope, receive, send)
        try:
            from app.services.backup_media import recovery_pending
            if recovery_pending():
                return await JSONResponse({"detail": "Wiederherstellung unterbrochen. Server-Neustart erforderlich."},
                                          status_code=503)(scope, receive, send)
            await self.app(scope, receive, send)
        finally:
            await run_in_threadpool(gate.__exit__, None, None, None)
