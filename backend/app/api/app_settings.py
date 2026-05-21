from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core import get_db
from app.core.auth import require_roles
from app.models import UserRole
from app.schemas import AppSettingsResponse, AppSettingsUpdate, PublicAppSettingsResponse
from app.services.app_settings_service import AppSettingsService

router = APIRouter(prefix="/api/app-settings", tags=["App Settings"])
TOP_ADMIN_ONLY_SETTINGS_FIELDS = (
    "kasse_layout",
    "session_timer_enabled",
    "session_timer_minutes",
)


@router.get("/public", response_model=PublicAppSettingsResponse)
@router.get("/public/", response_model=PublicAppSettingsResponse)
async def get_public_app_settings(db: Session = Depends(get_db)):
    service = AppSettingsService(db)
    return service.to_public_payload()


@router.get("/", response_model=AppSettingsResponse)
@router.get("", response_model=AppSettingsResponse)
async def get_app_settings(
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.ADMIN)
    service = AppSettingsService(db)
    return service.to_private_payload()


@router.put("/", response_model=AppSettingsResponse)
@router.put("", response_model=AppSettingsResponse)
async def update_app_settings(
    payload: AppSettingsUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = require_roles(request, db, UserRole.ADMIN)
    service = AppSettingsService(db)
    payload_data = payload.model_dump(exclude_unset=True)

    current_settings = service.get_or_create_settings()
    current_payload = service.to_private_payload(current_settings)
    is_restricted_change = any(
        field_name in payload_data and payload_data[field_name] != current_payload[field_name]
        for field_name in TOP_ADMIN_ONLY_SETTINGS_FIELDS
    )
    if is_restricted_change and not current_user.is_top_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur der Top-Admin darf Kassenlayout und Session-Timer ändern",
        )

    try:
        settings = service.update_settings(performed_by_username=current_user.username, **payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return service.to_private_payload(settings)


@router.post("/logo", response_model=AppSettingsResponse)
@router.post("/logo/", response_model=AppSettingsResponse)
async def upload_app_logo(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.ADMIN)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image upload required")

    service = AppSettingsService(db)
    settings = await service.update_logo(file)
    return service.to_private_payload(settings)


@router.get("/logo")
@router.get("/logo/")
async def get_logo_file(db: Session = Depends(get_db)):
    file_path = AppSettingsService(db).get_logo_file_path()
    return FileResponse(file_path, media_type="image/png")


@router.get("/favicon.png")
@router.get("/favicon.png/")
async def get_favicon_file(db: Session = Depends(get_db)):
    file_path = AppSettingsService(db).get_icon_file_path("favicon.png")
    return FileResponse(file_path, media_type="image/png")


@router.get("/favicon.ico")
@router.get("/favicon.ico/")
async def get_favicon_ico_file(db: Session = Depends(get_db)):
    file_path = AppSettingsService(db).get_icon_file_path("favicon.ico")
    return FileResponse(file_path, media_type="image/x-icon")


@router.get("/favicon-16x16.png")
@router.get("/favicon-16x16.png/")
async def get_favicon_16_file(db: Session = Depends(get_db)):
    file_path = AppSettingsService(db).get_icon_file_path("favicon-16x16.png")
    return FileResponse(file_path, media_type="image/png")


@router.get("/favicon-32x32.png")
@router.get("/favicon-32x32.png/")
async def get_favicon_32_file(db: Session = Depends(get_db)):
    file_path = AppSettingsService(db).get_icon_file_path("favicon-32x32.png")
    return FileResponse(file_path, media_type="image/png")


@router.get("/apple-touch-icon.png")
@router.get("/apple-touch-icon.png/")
async def get_apple_touch_icon_file(db: Session = Depends(get_db)):
    file_path = AppSettingsService(db).get_icon_file_path("apple-touch-icon.png")
    return FileResponse(file_path, media_type="image/png")


@router.get("/icon-192.png")
@router.get("/icon-192.png/")
async def get_icon_192_file(db: Session = Depends(get_db)):
    file_path = AppSettingsService(db).get_icon_file_path("icon-192.png")
    return FileResponse(file_path, media_type="image/png")


@router.get("/icon-512.png")
@router.get("/icon-512.png/")
async def get_icon_512_file(db: Session = Depends(get_db)):
    file_path = AppSettingsService(db).get_icon_file_path("icon-512.png")
    return FileResponse(file_path, media_type="image/png")


@router.get("/manifest.webmanifest")
@router.get("/manifest.webmanifest/")
async def get_manifest(db: Session = Depends(get_db)):
    service = AppSettingsService(db)
    payload = service.to_public_payload()
    manifest = {
        "name": payload["app_name"],
        "short_name": payload["app_name"],
        "description": "Webbasierte Kassensoftware für Vereine",
        "id": "/",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "display_override": ["standalone", "minimal-ui", "browser"],
        "background_color": payload["background_color"],
        "theme_color": payload["banner_color"],
        "orientation": "any",
        "icons": [
            {
                "src": f"/api/app-settings/favicon.png?v={payload['asset_version']}",
                "sizes": "64x64",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": f"/api/app-settings/apple-touch-icon.png?v={payload['asset_version']}",
                "sizes": "180x180",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": f"{payload['icon_192_url']}?v={payload['asset_version']}",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": f"{payload['icon_512_url']}?v={payload['asset_version']}",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": f"{payload['icon_192_url']}?v={payload['asset_version']}",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "maskable",
            },
            {
                "src": f"{payload['icon_512_url']}?v={payload['asset_version']}",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable",
            },
        ],
    }
    return JSONResponse(content=manifest, media_type="application/manifest+json")
