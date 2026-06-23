from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core import get_db
from app.core.auth import require_roles
from app.models import UserRole
from app.schemas import AppSettingsResponse, AppSettingsUpdate, PublicAppSettingsResponse
from app.services.app_settings_service import AppSettingsService
from app.services.email_service import EmailService
from app.services.scheduler_service import SchedulerService

router = APIRouter(prefix="/api/app-settings", tags=["App Settings"])
TOP_ADMIN_ONLY_SETTINGS_FIELDS = {
    "kasse_layout",
    "session_timer_enabled",
    "session_timer_minutes",
    "business_name",
    "business_street",
    "business_zip",
    "business_city",
    "business_phone",
    "business_email",
    "business_tax_number",
    "business_registration_number",
    "email_enabled",
    "email_sender",
    "email_recipient_zbon",
    "email_subject_suffix",
    "email_critical_stock_enabled",
    "smtp_host",
    "smtp_port",
    "smtp_username",
    "smtp_password",
    "smtp_use_tls",
    "send_zbon_on_create_enabled",
    "scheduled_zbon_enabled",
    "scheduled_zbon_time",
    "scheduled_zbon_report_type",
    "scheduled_database_backup_enabled",
    "scheduled_database_backup_time",
}


class EmailConnectionTestRequest(BaseModel):
    email_sender: str | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True


class EmailSendTestRequest(EmailConnectionTestRequest):
    recipient: str | None = None


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
    current_user = require_roles(request, db, UserRole.ADMIN)
    service = AppSettingsService(db)
    return service.to_private_payload(include_sensitive=current_user.is_top_admin)


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

    is_restricted_change = any(field_name in TOP_ADMIN_ONLY_SETTINGS_FIELDS for field_name in payload_data)
    if is_restricted_change and not current_user.is_top_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur der Top-Admin darf diese erweiterten Einstellungen ändern",
        )

    try:
        settings = service.update_settings(performed_by_username=current_user.username, **payload_data)
        SchedulerService.reload_scheduler()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return service.to_private_payload(settings, include_sensitive=current_user.is_top_admin)


@router.post("/email/test-connection")
@router.post("/email/test-connection/")
async def test_email_connection(
    payload: EmailConnectionTestRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.TOP_ADMIN)

    success, detail = EmailService.test_smtp_connection({
        "email_sender": payload.email_sender,
        "smtp_host": payload.smtp_host,
        "smtp_port": payload.smtp_port,
        "smtp_username": payload.smtp_username,
        "smtp_password": payload.smtp_password,
        "smtp_use_tls": payload.smtp_use_tls,
    })

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    return {
        "status": "ok",
        "detail": detail,
    }


@router.post("/email/send-test")
@router.post("/email/send-test/")
async def send_test_email(
    payload: EmailSendTestRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.TOP_ADMIN)

    recipient = (payload.recipient or "").strip()
    if not recipient:
        recipient = (AppSettingsService(db).get_email_settings().get("email_recipient_zbon") or "").strip()

    if not recipient:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kein Test-Empfaenger angegeben")

    config = {
        "email_sender": payload.email_sender,
        "smtp_host": payload.smtp_host,
        "smtp_port": payload.smtp_port,
        "smtp_username": payload.smtp_username,
        "smtp_password": payload.smtp_password,
        "smtp_use_tls": payload.smtp_use_tls,
    }

    success, detail = EmailService.test_smtp_connection(config)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    body = "Dies ist eine Test-E-Mail aus der Kickerkasse SMTP-Diagnose."
    html_body = """
<html>
  <body>
    <p>Dies ist eine <strong>Test-E-Mail</strong> aus der Kickerkasse SMTP-Diagnose.</p>
    <p>Wenn diese Nachricht ankommt, funktionieren SMTP-Verbindung, Authentifizierung und Versand.</p>
  </body>
</html>
"""

    # Send without persisting settings by doing a direct SMTP send with the provided config.
    sent = False
    try:
        sender = (config.get("email_sender") or "").strip()
        if not sender:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Absender fehlt")

        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Kickerkasse SMTP-Testmail"
        msg["From"] = sender
        msg["To"] = recipient
        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with EmailService._open_smtp_client(config) as server:
            server.ehlo()
            if EmailService._uses_starttls(config):
                server.starttls()
                server.ehlo()

            username = (config.get("smtp_username") or "").strip()
            password = config.get("smtp_password") or ""
            if username and password:
                server.login(username, password)

            server.send_message(msg)
            sent = True
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Testmail konnte nicht gesendet werden: {str(exc)}") from exc

    if not sent:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Testmail konnte nicht gesendet werden")

    return {
        "status": "ok",
        "detail": f"Testmail wurde an {recipient} gesendet",
    }


@router.post("/logo", response_model=AppSettingsResponse)
@router.post("/logo/", response_model=AppSettingsResponse)
async def upload_app_logo(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    current_user = require_roles(request, db, UserRole.ADMIN)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image upload required")

    service = AppSettingsService(db)
    settings = await service.update_logo(file)
    return service.to_private_payload(settings, include_sensitive=current_user.is_top_admin)


@router.post("/kasse-products-background", response_model=AppSettingsResponse)
@router.post("/kasse-products-background/", response_model=AppSettingsResponse)
async def upload_kasse_products_background(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    current_user = require_roles(request, db, UserRole.ADMIN)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image upload required")

    service = AppSettingsService(db)
    settings = await service.update_kasse_products_background(file)
    return service.to_private_payload(settings, include_sensitive=current_user.is_top_admin)


@router.get("/kasse-products-background")
@router.get("/kasse-products-background/")
async def get_kasse_products_background_file(db: Session = Depends(get_db)):
    file_path = AppSettingsService(db).get_kasse_products_background_file_path()
    if not file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No background image configured")
    return FileResponse(file_path, media_type="image/png")


@router.get("/donation-banner")
@router.get("/donation-banner/")
async def get_donation_banner_file(db: Session = Depends(get_db)):
    file_path = AppSettingsService(db).assets_dir / "donation.png"
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation banner not found")
    return FileResponse(file_path, media_type="image/png")


@router.get("/donation-qr")
@router.get("/donation-qr/")
async def get_donation_qr_file(db: Session = Depends(get_db)):
    file_path = AppSettingsService(db).assets_dir / "qr-code.png"
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation QR code not found")
    return FileResponse(file_path, media_type="image/png")


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
