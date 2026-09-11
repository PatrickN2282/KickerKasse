from starlette.concurrency import run_in_threadpool
import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core import get_db
from app.core.auth import require_roles
from app.models import UserRole
from app.services.audit_log_service import AuditLogService
from app.services import ImportExportService

router = APIRouter(prefix="/api/admin/import-export", tags=["Admin - Import/Export"])


async def read_transfer(file):
    if file is None:
        return None
    from app.services.import_export_service import MAX_TRANSFER_BYTES
    data = await file.read(MAX_TRANSFER_BYTES + 1)
    if len(data) > MAX_TRANSFER_BYTES:
        raise HTTPException(413, "Datei überschreitet 128 MiB")
    return data


class ExportRequest(BaseModel):
    sections: list[str]
    include_media: bool = False


def _parse_sections(raw_sections: str | None) -> list[str] | None:
    if not raw_sections:
        return None
    try:
        parsed = json.loads(raw_sections)
    except json.JSONDecodeError as exc:
        raise ValueError("Bereichsauswahl ist ungültig") from exc
    if not isinstance(parsed, list):
        raise ValueError("Bereichsauswahl muss eine Liste sein")
    return [str(item) for item in parsed]


def _parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "ja", "y", "on"}


@router.post("/export")
@router.post("/export/")
async def export_data(
    payload: ExportRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.ADMIN)

    service = ImportExportService(db)
    content, media_type, filename = await run_in_threadpool(service.export_sections, payload.sections, payload.include_media)
    AuditLogService(db).log_optional(
        entity_type="import_export",
        action="EXPORTED",
        user_username=request.session.get("username"),
        new_value={"sections": payload.sections, "include_media": payload.include_media},
    )
    db.commit()
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post("/analyze")
@router.post("/analyze/")
async def analyze_import(
    request: Request,
    data_file: UploadFile = File(...),
    media_file: UploadFile | None = File(default=None),
    source_mode: str = Form(default="foreign"),
    selected_sections: str | None = Form(default=None),
    replace_sections: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.ADMIN)

    service = ImportExportService(db)
    try:
        sections = _parse_sections(selected_sections)
        replacing = _parse_sections(replace_sections)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    analysis = service.analyze_import(
        data_file.filename or "import.csv",
        await read_transfer(data_file),
        media_file.filename if media_file else None,
        await read_transfer(media_file),
        source_mode=source_mode, sections=sections, replace_sections=replacing,
    )
    AuditLogService(db).log_optional(
        entity_type="import_export",
        action="ANALYZED",
        user_username=request.session.get("username"),
        new_value={"data_file": data_file.filename, "media_file": media_file.filename if media_file else None},
    )
    db.commit()
    return analysis


@router.post("/import")
@router.post("/import/")
async def import_data(
    request: Request,
    data_file: UploadFile = File(...),
    media_file: UploadFile | None = File(default=None),
    selected_sections: str | None = Form(default=None),
    replace_sections: str | None = Form(default=None),
    import_media: bool = Form(default=False),
    source_mode: str = Form(default="foreign"),
    acknowledge_initial_values: bool = Form(default=False),
    db: Session = Depends(get_db),
):
    """Apply a fresh conflict check, data, media and audit as one operation."""
    actor = require_roles(request, db, UserRole.TOP_ADMIN).username
    try:
        sections = _parse_sections(selected_sections)
        replacing = _parse_sections(replace_sections)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return await run_in_threadpool(ImportExportService(db).import_sections,
        data_file.filename or "import.csv", await read_transfer(data_file), sections,
        replace_sections=replacing, import_media=import_media,
        media_file_name=media_file.filename if media_file else None,
        media_content=await read_transfer(media_file), source_mode=source_mode,
        acknowledge_initial_values=acknowledge_initial_values, actor_username=actor)
