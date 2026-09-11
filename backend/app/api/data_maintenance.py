from starlette.concurrency import run_in_threadpool
import hashlib

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core import get_db
from app.core.auth import require_password_confirmation, require_roles, require_top_admin
from app.models.user import UserRole
from app.services.audit_log_service import AuditLogService
from app.services.database_backup_service import DatabaseBackupService, MAX_ARCHIVE_BYTES
from app.services.data_maintenance_service import DataMaintenanceService

router = APIRouter(prefix="/api/admin/data-maintenance", tags=["Admin - Data Maintenance"])


class HardResetRequest(BaseModel):
    auth_password: str = Field(..., min_length=1)
    confirmation_text: str = Field(..., min_length=1)


@router.get("/stats")
@router.get("/stats/")
async def get_stats(
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.TOP_ADMIN)
    return DataMaintenanceService(db).get_stats()


@router.post("/hard-reset")
@router.post("/hard-reset/")
async def hard_reset(
    payload: HardResetRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = require_top_admin(request, db)
    require_password_confirmation(current_user, payload.auth_password, db)

    if payload.confirmation_text.strip().upper() != "RESET":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bitte zur Bestätigung exakt RESET eingeben",
        )

    return DataMaintenanceService(db).hard_reset()


@router.post("/database-backup/export")
@router.post("/database-backup/export/")
async def export_database_backup(
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.TOP_ADMIN)
    content, filename = await run_in_threadpool(DatabaseBackupService(db).create_backup_zip)
    return Response(
        content=content,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/database-backup/restore")
@router.post("/database-backup/restore/")
async def restore_database_backup(
    request: Request,
    auth_password: str = Form(...),
    backup_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    current_user = require_top_admin(request, db)
    require_password_confirmation(current_user, auth_password, db)
    actor_username = current_user.username
    backup_name = backup_file.filename or "backup.zip"
    backup_content = await backup_file.read(MAX_ARCHIVE_BYTES + 1)
    if len(backup_content) > MAX_ARCHIVE_BYTES:
        raise HTTPException(413, "Backup-ZIP darf höchstens 256 MiB groß sein")
    backup_sha256 = hashlib.sha256(backup_content).hexdigest()
    try:
        result = await run_in_threadpool(DatabaseBackupService(db).restore_from_backup_zip,
            backup_name, backup_content, actor_username=actor_username)
    except Exception:
        db.rollback()
        AuditLogService(db).log_optional(
            entity_type="database_backup", action="RESTORE_FAILED",
            user_username=actor_username, entity_name=backup_name,
            new_value={"sha256": backup_sha256})
        raise
    request.session.clear()
    from app.services.scheduler_service import SchedulerService
    try:
        SchedulerService.reload_scheduler()
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Scheduler reload after restore failed")
    return result
