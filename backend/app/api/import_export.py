import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core import get_db
from app.core.auth import require_roles
from app.models import UserRole
from app.services import ImportExportService

router = APIRouter(prefix="/api/admin/import-export", tags=["Admin - Import/Export"])


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
    content, media_type, filename = service.export_sections(payload.sections, payload.include_media)
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
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.ADMIN)

    service = ImportExportService(db)
    analysis = service.analyze_import(
        data_file.filename or "import.csv",
        await data_file.read(),
        media_file.filename if media_file else None,
        await media_file.read() if media_file else None,
    )
    return analysis


@router.post("/import")
@router.post("/import/")
async def import_data(
    request: Request,
    data_file: UploadFile = File(...),
    media_file: UploadFile | None = File(default=None),
    selected_sections: str | None = Form(default=None),
    replace_sections: str | None = Form(default=None),
    import_media: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    """
    Import data from a CSV or ZIP file.

    ⚠️ Hinweis: Der Import ist ausschließlich für frische oder leere Datenbanken vorgesehen.
    Auf einer bestehenden Datenbank mit Transaktionen kann der Import zu Inkonsistenzen führen.
    """
    require_roles(request, db, UserRole.ADMIN)

    try:
        sections = _parse_sections(selected_sections)
        replace = _parse_sections(replace_sections)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    service = ImportExportService(db)
    result = service.import_sections(
        data_file.filename or "import.csv",
        await data_file.read(),
        sections,
        replace_sections=replace,
        import_media=_parse_bool(import_media),
        media_file_name=media_file.filename if media_file else None,
        media_content=await media_file.read() if media_file else None,
    )
    return result
