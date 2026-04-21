from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core import get_db
from app.core.auth import require_password_confirmation, require_top_admin
from app.services.data_maintenance_service import DataMaintenanceService

router = APIRouter(prefix="/api/admin/data-maintenance", tags=["Admin - Data Maintenance"])


class HardResetRequest(BaseModel):
    auth_password: str = Field(..., min_length=1)
    confirmation_text: str = Field(..., min_length=1)


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
