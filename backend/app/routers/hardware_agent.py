import shutil
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core import get_db
from app.core.auth import require_password_confirmation, require_roles
from app.models import UserRole
from app.services.hardware_agent_service import HardwareAgentService

router = APIRouter(prefix="/api/hardware-agent", tags=["Hardware Agent"])


class ServiceActionRequest(BaseModel):
    action: str = Field(..., min_length=1)


class DrawerOpenRequest(BaseModel):
    auth_password: str = Field(..., min_length=1)


@router.get("/status")
@router.get("/status/")
async def get_hardware_status(
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.ADMIN)
    return HardwareAgentService.get_status()


@router.get("/download-installer")
@router.get("/download-installer/")
async def download_installer(
    request: Request,
    db: Session = Depends(get_db),
):
    """Liefert das Kickerkasse Hardware Agent Installationspaket als ZIP-Download."""
    require_roles(request, db, UserRole.ADMIN)

    # Installer-Dateien liegen unter backend/services/
    base = Path(__file__).resolve().parents[2] / "services"
    files = {
        "agent.py":                    base / "agent.py",
        "install_agent_service.py":    base / "install_agent_service.py",
        "kickerkasse_bootstrapper.py": base / "kickerkasse_bootstrapper.py",
        "README.txt":                  base / "README.txt",
    }

    missing = [name for name, path in files.items() if not path.exists()]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Installer-Dateien fehlen auf dem Server: {', '.join(missing)}"
        )

    tmp_dir = tempfile.mkdtemp()
    zip_path = Path(tmp_dir) / "kickerkasse-agent-installer.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, path in files.items():
            zf.write(path, name)

    return FileResponse(
        path=str(zip_path),
        filename="kickerkasse-agent-installer.zip",
        media_type="application/zip",
    )


@router.post("/service-action")
@router.post("/service-action/")
async def execute_service_action(
    payload: ServiceActionRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.TOP_ADMIN)
    success, detail = HardwareAgentService.manage_service(payload.action)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail or "Service-Aktion fehlgeschlagen",
        )
    return {"status": "ok", "detail": detail}


@router.post("/install")
@router.post("/install/")
async def install_hardware_agent(
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.TOP_ADMIN)
    success, detail = HardwareAgentService.run_install_script()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail or "Installation fehlgeschlagen",
        )
    return {"status": "ok", "detail": detail}


@router.post("/open-drawer")
@router.post("/open-drawer/")
async def open_cash_drawer(
    payload: DrawerOpenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = require_roles(request, db, UserRole.ADMIN)
    require_password_confirmation(current_user, payload.auth_password)

    success, detail = HardwareAgentService.trigger_drawer_open()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail or "Kassenschublade konnte nicht geöffnet werden",
        )
    return {"status": "ok", "detail": detail}
