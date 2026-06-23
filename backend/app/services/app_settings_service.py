from pathlib import Path
import re

from sqlalchemy.orm import Session

from app.models import AppSettings
from app.services.file_service import APP_SETTINGS_DIR, get_full_path, save_app_logo, save_kasse_products_background


HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
DEFAULT_APP_NAME = "KGB - KickerKasse Test"
DEFAULT_BACKGROUND_COLOR = "#d7dce2"
DEFAULT_BANNER_COLOR = "#131820"
DEFAULT_HIGHLIGHT_COLOR = "#5c8f3a"
DEFAULT_KASSE_AREA_BACKGROUND_COLOR = "#ffffff"
DEFAULT_LOGO_RELATIVE_PATH = "app_settings/logo.png"
DEFAULT_SESSION_TIMER_ENABLED = False
DEFAULT_SESSION_TIMER_MINUTES = 15
DEFAULT_DECKEL_ENABLED = True
DEFAULT_KASSE_PRODUCTS_BACKGROUND_SCALE = 100
DEFAULT_KASSE_PRODUCTS_BACKGROUND_OPACITY = 100
DEFAULT_KASSE_PRODUCTS_BACKGROUND_ENABLED = True
DEFAULT_EMAIL_ENABLED = False
DEFAULT_EMAIL_SENDER = "noreply@kassensystem.local"
DEFAULT_EMAIL_RECIPIENT_ZBON = ""
DEFAULT_EMAIL_SUBJECT_SUFFIX = ""
DEFAULT_EMAIL_CRITICAL_STOCK_ENABLED = False
DEFAULT_SMTP_HOST = ""
DEFAULT_SMTP_PORT = 587
DEFAULT_SMTP_USERNAME = ""
DEFAULT_SMTP_PASSWORD = ""
DEFAULT_SMTP_USE_TLS = True
DEFAULT_SEND_ZBON_ON_CREATE_ENABLED = False
DEFAULT_SCHEDULED_ZBON_ENABLED = False
DEFAULT_SCHEDULED_ZBON_TIME = "23:59"
DEFAULT_SCHEDULED_ZBON_REPORT_TYPE = "full-zbon"
DEFAULT_SCHEDULED_DATABASE_BACKUP_ENABLED = False
DEFAULT_SCHEDULED_DATABASE_BACKUP_TIME = "03:00"
SCHEDULED_REPORT_TYPES = {"full-zbon", "short-zbon", "daily-report"}
SENSITIVE_SETTINGS_FIELDS = {"smtp_password"}


class AppSettingsService:
    def __init__(self, db: Session):
        self.db = db
        self.assets_dir = Path(__file__).parent.parent / "assets"

    @staticmethod
    def _normalize_optional_string(value):
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    @staticmethod
    def _mask_sensitive(field_name: str, value):
        if field_name == "smtp_password":
            return "***" if value else ""
        return value

    def get_or_create_settings(self) -> AppSettings:
        settings = self.db.query(AppSettings).order_by(AppSettings.id.asc()).first()
        if settings:
            return settings

        settings = AppSettings(
            app_name=DEFAULT_APP_NAME,
            background_color=DEFAULT_BACKGROUND_COLOR,
            banner_color=DEFAULT_BANNER_COLOR,
            highlight_color=DEFAULT_HIGHLIGHT_COLOR,
            kasse_area_background_color=DEFAULT_KASSE_AREA_BACKGROUND_COLOR,
            logo_path=None,
            session_timer_enabled=DEFAULT_SESSION_TIMER_ENABLED,
            session_timer_minutes=DEFAULT_SESSION_TIMER_MINUTES,
            deckel_enabled=DEFAULT_DECKEL_ENABLED,
            kasse_products_background_path=None,
            kasse_products_background_scale=DEFAULT_KASSE_PRODUCTS_BACKGROUND_SCALE,
            kasse_products_background_opacity=DEFAULT_KASSE_PRODUCTS_BACKGROUND_OPACITY,
            kasse_products_background_enabled=DEFAULT_KASSE_PRODUCTS_BACKGROUND_ENABLED,
            email_enabled=DEFAULT_EMAIL_ENABLED,
            email_sender=DEFAULT_EMAIL_SENDER,
            email_recipient_zbon=DEFAULT_EMAIL_RECIPIENT_ZBON,
            email_subject_suffix=DEFAULT_EMAIL_SUBJECT_SUFFIX,
            email_critical_stock_enabled=DEFAULT_EMAIL_CRITICAL_STOCK_ENABLED,
            smtp_host=DEFAULT_SMTP_HOST,
            smtp_port=DEFAULT_SMTP_PORT,
            smtp_username=DEFAULT_SMTP_USERNAME,
            smtp_password=DEFAULT_SMTP_PASSWORD,
            smtp_use_tls=DEFAULT_SMTP_USE_TLS,
            send_zbon_on_create_enabled=DEFAULT_SEND_ZBON_ON_CREATE_ENABLED,
            scheduled_zbon_enabled=DEFAULT_SCHEDULED_ZBON_ENABLED,
            scheduled_zbon_time=DEFAULT_SCHEDULED_ZBON_TIME,
            scheduled_zbon_report_type=DEFAULT_SCHEDULED_ZBON_REPORT_TYPE,
            scheduled_database_backup_enabled=DEFAULT_SCHEDULED_DATABASE_BACKUP_ENABLED,
            scheduled_database_backup_time=DEFAULT_SCHEDULED_DATABASE_BACKUP_TIME,
        )
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        return settings

    def _asset_version(self, settings: AppSettings) -> str:
        return str(int(settings.updated_at.timestamp())) if settings.updated_at else "1"

    def to_public_payload(self, settings: AppSettings | None = None) -> dict:
        settings = settings or self.get_or_create_settings()
        return {
            "app_name": settings.app_name or DEFAULT_APP_NAME,
            "background_color": settings.background_color,
            "banner_color": settings.banner_color,
            "highlight_color": settings.highlight_color,
            "kasse_area_background_color": settings.kasse_area_background_color or DEFAULT_KASSE_AREA_BACKGROUND_COLOR,
            "logo_url": "/api/app-settings/logo",
            "kasse_products_background_url": "/api/app-settings/kasse-products-background" if settings.kasse_products_background_path else "",
            "favicon_ico_url": "/api/app-settings/favicon.ico",
            "favicon_16_url": "/api/app-settings/favicon-16x16.png",
            "favicon_32_url": "/api/app-settings/favicon-32x32.png",
            "favicon_url": "/api/app-settings/favicon.png",
            "apple_touch_icon_url": "/api/app-settings/apple-touch-icon.png",
            "icon_192_url": "/api/app-settings/icon-192.png",
            "icon_512_url": "/api/app-settings/icon-512.png",
            "manifest_url": "/api/app-settings/manifest.webmanifest",
            "asset_version": self._asset_version(settings),
            "kasse_layout": settings.kasse_layout,
            "session_timer_enabled": settings.session_timer_enabled,
            "session_timer_minutes": settings.session_timer_minutes or DEFAULT_SESSION_TIMER_MINUTES,
            "deckel_enabled": settings.deckel_enabled,
            "kasse_products_background_scale": settings.kasse_products_background_scale or DEFAULT_KASSE_PRODUCTS_BACKGROUND_SCALE,
            "kasse_products_background_opacity": settings.kasse_products_background_opacity if settings.kasse_products_background_opacity is not None else DEFAULT_KASSE_PRODUCTS_BACKGROUND_OPACITY,
            "kasse_products_background_enabled": settings.kasse_products_background_enabled if settings.kasse_products_background_enabled is not None else DEFAULT_KASSE_PRODUCTS_BACKGROUND_ENABLED,
            "send_zbon_on_create_enabled": settings.send_zbon_on_create_enabled if settings.send_zbon_on_create_enabled is not None else DEFAULT_SEND_ZBON_ON_CREATE_ENABLED,
        }

    def to_private_payload(self, settings: AppSettings | None = None, include_sensitive: bool = True) -> dict:
        settings = settings or self.get_or_create_settings()
        payload = self.to_public_payload(settings)
        payload.update({
            "id": settings.id,
            "created_at": settings.created_at,
            "updated_at": settings.updated_at,
            "business_name": settings.business_name,
            "business_street": settings.business_street,
            "business_zip": settings.business_zip,
            "business_city": settings.business_city,
            "business_phone": settings.business_phone,
            "business_email": settings.business_email,
            "business_tax_number": settings.business_tax_number,
            "business_registration_number": settings.business_registration_number,
            "email_enabled": settings.email_enabled if settings.email_enabled is not None else DEFAULT_EMAIL_ENABLED,
            "email_sender": settings.email_sender or DEFAULT_EMAIL_SENDER,
            "email_recipient_zbon": settings.email_recipient_zbon or DEFAULT_EMAIL_RECIPIENT_ZBON,
            "email_subject_suffix": settings.email_subject_suffix or DEFAULT_EMAIL_SUBJECT_SUFFIX,
            "email_critical_stock_enabled": settings.email_critical_stock_enabled if settings.email_critical_stock_enabled is not None else DEFAULT_EMAIL_CRITICAL_STOCK_ENABLED,
            "smtp_host": settings.smtp_host or DEFAULT_SMTP_HOST,
            "smtp_port": settings.smtp_port or DEFAULT_SMTP_PORT,
            "smtp_username": settings.smtp_username or DEFAULT_SMTP_USERNAME,
            "smtp_password": settings.smtp_password or DEFAULT_SMTP_PASSWORD,
            "smtp_use_tls": settings.smtp_use_tls if settings.smtp_use_tls is not None else DEFAULT_SMTP_USE_TLS,
            "send_zbon_on_create_enabled": settings.send_zbon_on_create_enabled if settings.send_zbon_on_create_enabled is not None else DEFAULT_SEND_ZBON_ON_CREATE_ENABLED,
            "scheduled_zbon_enabled": settings.scheduled_zbon_enabled if settings.scheduled_zbon_enabled is not None else DEFAULT_SCHEDULED_ZBON_ENABLED,
            "scheduled_zbon_time": settings.scheduled_zbon_time or DEFAULT_SCHEDULED_ZBON_TIME,
            "scheduled_zbon_report_type": settings.scheduled_zbon_report_type or DEFAULT_SCHEDULED_ZBON_REPORT_TYPE,
            "scheduled_database_backup_enabled": settings.scheduled_database_backup_enabled if settings.scheduled_database_backup_enabled is not None else DEFAULT_SCHEDULED_DATABASE_BACKUP_ENABLED,
            "scheduled_database_backup_time": settings.scheduled_database_backup_time or DEFAULT_SCHEDULED_DATABASE_BACKUP_TIME,
        })
        if not include_sensitive:
            payload["smtp_password"] = ""
        return payload

    def get_email_settings(self, settings: AppSettings | None = None) -> dict:
        settings = settings or self.get_or_create_settings()
        return {
            "email_enabled": settings.email_enabled if settings.email_enabled is not None else DEFAULT_EMAIL_ENABLED,
            "email_sender": settings.email_sender or DEFAULT_EMAIL_SENDER,
            "email_recipient_zbon": settings.email_recipient_zbon or DEFAULT_EMAIL_RECIPIENT_ZBON,
            "email_subject_suffix": settings.email_subject_suffix or DEFAULT_EMAIL_SUBJECT_SUFFIX,
            "email_critical_stock_enabled": settings.email_critical_stock_enabled if settings.email_critical_stock_enabled is not None else DEFAULT_EMAIL_CRITICAL_STOCK_ENABLED,
            "smtp_host": settings.smtp_host or DEFAULT_SMTP_HOST,
            "smtp_port": settings.smtp_port or DEFAULT_SMTP_PORT,
            "smtp_username": settings.smtp_username or DEFAULT_SMTP_USERNAME,
            "smtp_password": settings.smtp_password or DEFAULT_SMTP_PASSWORD,
            "smtp_use_tls": settings.smtp_use_tls if settings.smtp_use_tls is not None else DEFAULT_SMTP_USE_TLS,
            "send_zbon_on_create_enabled": settings.send_zbon_on_create_enabled if settings.send_zbon_on_create_enabled is not None else DEFAULT_SEND_ZBON_ON_CREATE_ENABLED,
            "scheduled_zbon_enabled": settings.scheduled_zbon_enabled if settings.scheduled_zbon_enabled is not None else DEFAULT_SCHEDULED_ZBON_ENABLED,
            "scheduled_zbon_time": settings.scheduled_zbon_time or DEFAULT_SCHEDULED_ZBON_TIME,
            "scheduled_zbon_report_type": settings.scheduled_zbon_report_type or DEFAULT_SCHEDULED_ZBON_REPORT_TYPE,
            "scheduled_database_backup_enabled": settings.scheduled_database_backup_enabled if settings.scheduled_database_backup_enabled is not None else DEFAULT_SCHEDULED_DATABASE_BACKUP_ENABLED,
            "scheduled_database_backup_time": settings.scheduled_database_backup_time or DEFAULT_SCHEDULED_DATABASE_BACKUP_TIME,
        }

    def get_business_info(self, settings: AppSettings | None = None) -> dict:
        settings = settings or self.get_or_create_settings()
        return {
            "name": settings.business_name or settings.app_name or DEFAULT_APP_NAME,
            "street": settings.business_street or "",
            "zip": settings.business_zip or "",
            "city": settings.business_city or "",
            "phone": settings.business_phone or "",
            "email": settings.business_email or "",
            "tax_number": settings.business_tax_number or "",
            "registration_number": settings.business_registration_number or "",
        }

    def update_settings(self, performed_by_username: str | None = None, **kwargs) -> AppSettings:
        settings = self.get_or_create_settings()
        tracked_fields = [
            "app_name",
            "background_color",
            "banner_color",
            "highlight_color",
            "kasse_area_background_color",
            "kasse_layout",
            "session_timer_enabled",
            "session_timer_minutes",
            "deckel_enabled",
            "kasse_products_background_scale",
            "kasse_products_background_opacity",
            "kasse_products_background_enabled",
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
        ]
        old_snapshot = {
            field_name: self._mask_sensitive(field_name, getattr(settings, field_name, None))
            for field_name in tracked_fields
        }

        if "app_name" in kwargs and kwargs["app_name"] is not None:
            app_name = kwargs["app_name"].strip()
            if not app_name:
                raise ValueError("App name must not be empty")
            settings.app_name = app_name

        for field in ("background_color", "banner_color", "highlight_color", "kasse_area_background_color"):
            if field in kwargs and kwargs[field] is not None:
                value = str(kwargs[field]).upper()
                if not HEX_COLOR_RE.match(value):
                    raise ValueError(f"Invalid color value for {field}")
                setattr(settings, field, value)

        if "kasse_layout" in kwargs:
            settings.kasse_layout = kwargs["kasse_layout"]

        if "session_timer_enabled" in kwargs and kwargs["session_timer_enabled"] is not None:
            settings.session_timer_enabled = bool(kwargs["session_timer_enabled"])

        if "session_timer_minutes" in kwargs and kwargs["session_timer_minutes"] is not None:
            minutes = int(kwargs["session_timer_minutes"])
            if minutes < 1:
                raise ValueError("Session timer minutes must be at least 1")
            settings.session_timer_minutes = minutes

        if "deckel_enabled" in kwargs and kwargs["deckel_enabled"] is not None:
            settings.deckel_enabled = bool(kwargs["deckel_enabled"])

        if "kasse_products_background_scale" in kwargs and kwargs["kasse_products_background_scale"] is not None:
            scale = int(kwargs["kasse_products_background_scale"])
            if scale < 10 or scale > 300:
                raise ValueError("Kasse products background scale must be between 10 and 300")
            settings.kasse_products_background_scale = scale

        if "kasse_products_background_opacity" in kwargs and kwargs["kasse_products_background_opacity"] is not None:
            opacity = int(kwargs["kasse_products_background_opacity"])
            if opacity < 0 or opacity > 100:
                raise ValueError("Kasse products background opacity must be between 0 and 100")
            settings.kasse_products_background_opacity = opacity

        if "kasse_products_background_enabled" in kwargs and kwargs["kasse_products_background_enabled"] is not None:
            settings.kasse_products_background_enabled = bool(kwargs["kasse_products_background_enabled"])

        for field in (
            "business_name",
            "business_street",
            "business_zip",
            "business_city",
            "business_phone",
            "business_email",
            "business_tax_number",
            "business_registration_number",
            "email_sender",
            "email_recipient_zbon",
            "email_subject_suffix",
            "smtp_host",
            "smtp_username",
            "smtp_password",
        ):
            if field in kwargs:
                setattr(settings, field, self._normalize_optional_string(kwargs[field]))

        if "email_enabled" in kwargs and kwargs["email_enabled"] is not None:
            settings.email_enabled = bool(kwargs["email_enabled"])

        if "email_critical_stock_enabled" in kwargs and kwargs["email_critical_stock_enabled"] is not None:
            settings.email_critical_stock_enabled = bool(kwargs["email_critical_stock_enabled"])

        if "smtp_port" in kwargs and kwargs["smtp_port"] is not None:
            port = int(kwargs["smtp_port"])
            if port < 1 or port > 65535:
                raise ValueError("SMTP port must be between 1 and 65535")
            settings.smtp_port = port

        if "smtp_use_tls" in kwargs and kwargs["smtp_use_tls"] is not None:
            settings.smtp_use_tls = bool(kwargs["smtp_use_tls"])

        if "send_zbon_on_create_enabled" in kwargs and kwargs["send_zbon_on_create_enabled"] is not None:
            settings.send_zbon_on_create_enabled = bool(kwargs["send_zbon_on_create_enabled"])

        if "scheduled_zbon_enabled" in kwargs and kwargs["scheduled_zbon_enabled"] is not None:
            settings.scheduled_zbon_enabled = bool(kwargs["scheduled_zbon_enabled"])

        if "scheduled_zbon_time" in kwargs and kwargs["scheduled_zbon_time"] is not None:
            scheduled_time = str(kwargs["scheduled_zbon_time"]).strip()
            if not TIME_RE.match(scheduled_time):
                raise ValueError("Scheduled Z-Bon time must use HH:MM format")
            settings.scheduled_zbon_time = scheduled_time

        if "scheduled_zbon_report_type" in kwargs and kwargs["scheduled_zbon_report_type"] is not None:
            # Keep backwards compatibility but enforce a single consolidated report format.
            settings.scheduled_zbon_report_type = DEFAULT_SCHEDULED_ZBON_REPORT_TYPE

        if "scheduled_database_backup_enabled" in kwargs and kwargs["scheduled_database_backup_enabled"] is not None:
            settings.scheduled_database_backup_enabled = bool(kwargs["scheduled_database_backup_enabled"])

        if "scheduled_database_backup_time" in kwargs and kwargs["scheduled_database_backup_time"] is not None:
            backup_time = str(kwargs["scheduled_database_backup_time"]).strip()
            if not TIME_RE.match(backup_time):
                raise ValueError("Scheduled database backup time must use HH:MM format")
            settings.scheduled_database_backup_time = backup_time

        self.db.commit()
        self.db.refresh(settings)

        try:
            from app.services.audit_log_service import AuditLogService

            new_snapshot = {
                field_name: self._mask_sensitive(field_name, getattr(settings, field_name, None))
                for field_name in tracked_fields
            }
            changed = {k: v for k, v in new_snapshot.items() if old_snapshot.get(k) != v}
            if changed:
                AuditLogService(self.db).log(
                    entity_type="settings",
                    action="UPDATED",
                    user_username=performed_by_username,
                    entity_id=settings.id,
                    entity_name="AppSettings",
                    old_value={k: old_snapshot[k] for k in changed},
                    new_value=changed,
                )
                self.db.commit()
        except Exception:
            pass

        return settings

    async def update_logo(self, file) -> AppSettings:
        settings = self.get_or_create_settings()
        settings.logo_path = await save_app_logo(file)
        self.db.commit()
        self.db.refresh(settings)
        return settings

    async def update_kasse_products_background(self, file) -> AppSettings:
        settings = self.get_or_create_settings()
        settings.kasse_products_background_path = await save_kasse_products_background(file)
        self.db.commit()
        self.db.refresh(settings)
        return settings

    def get_logo_file_path(self) -> Path:
        settings = self.get_or_create_settings()
        logo_path = get_full_path(settings.logo_path) if settings.logo_path else None
        if logo_path and logo_path.exists():
            return logo_path
        return self.assets_dir / "logo.png"

    def get_icon_file_path(self, filename: str) -> Path:
        uploaded_icon = APP_SETTINGS_DIR / filename
        if uploaded_icon.exists():
            return uploaded_icon
        return self.assets_dir / filename

    def get_kasse_products_background_file_path(self) -> Path | None:
        settings = self.get_or_create_settings()
        background_path = get_full_path(settings.kasse_products_background_path) if settings.kasse_products_background_path else None
        if background_path and background_path.exists():
            return background_path
        return None
