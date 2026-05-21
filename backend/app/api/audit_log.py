from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core import get_db
from app.core.auth import require_roles
from app.models import UserRole
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/api/admin/audit-log", tags=["Audit Log"])


def _serialize_entry(entry) -> dict:
    return {
        "id": entry.id,
        "created_at": entry.created_at,
        "user_username": entry.user_username,
        "entity_type": entry.entity_type,
        "entity_id": entry.entity_id,
        "entity_name": entry.entity_name,
        "action": entry.action,
        "old_value": entry.old_value,
        "new_value": entry.new_value,
    }


@router.get("")
@router.get("/")
async def get_audit_log(
    request: Request,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    """Return audit log entries (admin only), newest first."""
    require_roles(request, db, UserRole.ADMIN)
    entries = AuditLogService(db).get_all(skip=skip, limit=limit)
    return [_serialize_entry(e) for e in entries]
