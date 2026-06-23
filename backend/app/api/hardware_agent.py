import io
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core import get_db
from app.core.auth import require_password_confirmation, require_roles
from app.models import UserRole
from app.services.hardware_agent_service import HardwareAgentService

router = APIRouter(prefix="/api/hardware-agent", tags=["Hardware Agent"])
BACKEND_ROOT_DIR = Path(__file__).resolve().parents[2]
INSTALLER_BASE_DIR = BACKEND_ROOT_DIR / "services"
INSTALLER_README_PATH = BACKEND_ROOT_DIR / "app" / "services" / "README_installer.txt"
INSTALLER_FILES = {
    "agent.py": INSTALLER_BASE_DIR / "agent.py",
    "install_agent_service.py": INSTALLER_BASE_DIR / "install_agent_service.py",
    "kickerkasse_bootstrapper.py": INSTALLER_BASE_DIR / "kickerkasse_bootstrapper.py",
    "setup_wizard.py": INSTALLER_BASE_DIR / "setup_wizard.py",
    "Kickerkasse-Install.desktop": INSTALLER_BASE_DIR / "Kickerkasse-Install.desktop",
    "README.txt": INSTALLER_README_PATH,
}


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
    require_roles(request, db, UserRole.ADMIN)
    missing = [name for name, path in INSTALLER_FILES.items() if not path.exists()]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Installer-Dateien fehlen auf dem Server: {', '.join(missing)}",
        )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, path in INSTALLER_FILES.items():
            zf.write(path, name)
    buffer.seek(0)

    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="kickerkasse-agent-installer.zip"'},
    )


@router.get("/download-installer-file/{filename}")
@router.get("/download-installer-file/{filename}/")
async def download_installer_file(
    filename: str,
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.ADMIN)
    file_path = INSTALLER_FILES.get(filename)
    if file_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Datei nicht verfügbar",
        )
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Datei fehlt auf dem Server: {filename}",
        )
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
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
