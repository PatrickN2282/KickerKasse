from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core import get_db
from app.core.auth import require_authenticated_user, require_password_confirmation, require_roles, require_top_admin
from app.core.security import get_password_hasher
from app.models.user import UserRole
from app.repositories import UserRepository
from app.services.database_backup_service import DatabaseBackupService
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
    require_password_confirmation(current_user, payload.auth_password)

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
    content, filename = DatabaseBackupService(db).create_backup_zip()
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
    require_authenticated_user(request, db)

    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    current_user = UserRepository(db).get_by_id(user_id)
    if not current_user or not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    if current_user.role == UserRole.TOP_ADMIN:
        require_password_confirmation(current_user, auth_password)
    else:
        top_admin = UserRepository(db).get_top_admin()
        if not top_admin or not top_admin.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        if not get_password_hasher().verify_password(auth_password, top_admin.password_hash):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

    result = DatabaseBackupService(db).restore_from_backup_zip(
        backup_file.filename or "backup.zip",
        await backup_file.read(),
    )
    return result
