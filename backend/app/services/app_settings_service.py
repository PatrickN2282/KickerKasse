from pathlib import Path
import re

from sqlalchemy.orm import Session

from app.models import AppSettings
from app.services.file_service import APP_SETTINGS_DIR, get_full_path, save_app_logo, save_kasse_products_background


HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
DEFAULT_APP_NAME = "KGB - KickerKasse"
DEFAULT_BACKGROUND_COLOR = "#d7dce2"
DEFAULT_BANNER_COLOR = "#131820"
DEFAULT_HIGHLIGHT_COLOR = "#5c8f3a"
DEFAULT_LOGO_RELATIVE_PATH = "app_settings/logo.png"
DEFAULT_SESSION_TIMER_ENABLED = False
DEFAULT_SESSION_TIMER_MINUTES = 15
DEFAULT_DECKEL_ENABLED = True
DEFAULT_KASSE_PRODUCTS_BACKGROUND_SCALE = 100
DEFAULT_KASSE_PRODUCTS_BACKGROUND_OPACITY = 100
DEFAULT_KASSE_PRODUCTS_BACKGROUND_ENABLED = True


class AppSettingsService:
    def __init__(self, db: Session):
        self.db = db
        self.assets_dir = Path(__file__).parent.parent / "assets"

    def get_or_create_settings(self) -> AppSettings:
        settings = self.db.query(AppSettings).order_by(AppSettings.id.asc()).first()
        if settings:
            return settings

        settings = AppSettings(
            app_name=DEFAULT_APP_NAME,
            background_color=DEFAULT_BACKGROUND_COLOR,
            banner_color=DEFAULT_BANNER_COLOR,
            highlight_color=DEFAULT_HIGHLIGHT_COLOR,
            logo_path=None,
            session_timer_enabled=DEFAULT_SESSION_TIMER_ENABLED,
            session_timer_minutes=DEFAULT_SESSION_TIMER_MINUTES,
            deckel_enabled=DEFAULT_DECKEL_ENABLED,
            kasse_products_background_path=None,
            kasse_products_background_scale=DEFAULT_KASSE_PRODUCTS_BACKGROUND_SCALE,
            kasse_products_background_opacity=DEFAULT_KASSE_PRODUCTS_BACKGROUND_OPACITY,
            kasse_products_background_enabled=DEFAULT_KASSE_PRODUCTS_BACKGROUND_ENABLED,
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
        }

    def to_private_payload(self, settings: AppSettings | None = None) -> dict:
        settings = settings or self.get_or_create_settings()
        payload = self.to_public_payload(settings)
        payload.update({
            "id": settings.id,
            "created_at": settings.created_at,
            "updated_at": settings.updated_at,
        })
        return payload

    def update_settings(self, performed_by_username: str | None = None, **kwargs) -> AppSettings:
        settings = self.get_or_create_settings()
        old_snapshot = {
            "app_name": settings.app_name,
            "background_color": settings.background_color,
            "banner_color": settings.banner_color,
            "highlight_color": settings.highlight_color,
            "kasse_layout": settings.kasse_layout,
            "session_timer_enabled": settings.session_timer_enabled,
            "session_timer_minutes": settings.session_timer_minutes,
            "deckel_enabled": settings.deckel_enabled,
            "kasse_products_background_scale": settings.kasse_products_background_scale or DEFAULT_KASSE_PRODUCTS_BACKGROUND_SCALE,
            "kasse_products_background_opacity": settings.kasse_products_background_opacity if settings.kasse_products_background_opacity is not None else DEFAULT_KASSE_PRODUCTS_BACKGROUND_OPACITY,
            "kasse_products_background_enabled": settings.kasse_products_background_enabled if settings.kasse_products_background_enabled is not None else DEFAULT_KASSE_PRODUCTS_BACKGROUND_ENABLED,
        }

        if "app_name" in kwargs and kwargs["app_name"] is not None:
            app_name = kwargs["app_name"].strip()
            if not app_name:
                raise ValueError("App name must not be empty")
            settings.app_name = app_name

        for field in ("background_color", "banner_color", "highlight_color"):
            if field in kwargs and kwargs[field] is not None:
                value = kwargs[field].upper()
                if not HEX_COLOR_RE.match(value):
                    raise ValueError(f"Invalid color value for {field}")
                setattr(settings, field, value)

        if "kasse_layout" in kwargs:
            settings.kasse_layout = kwargs["kasse_layout"]

        if "session_timer_enabled" in kwargs:
            settings.session_timer_enabled = bool(kwargs["session_timer_enabled"])

        if "session_timer_minutes" in kwargs and kwargs["session_timer_minutes"] is not None:
            minutes = int(kwargs["session_timer_minutes"])
            if minutes < 1:
                raise ValueError("Session timer minutes must be at least 1")
            settings.session_timer_minutes = minutes

        if "deckel_enabled" in kwargs:
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

        if "kasse_products_background_enabled" in kwargs:
            settings.kasse_products_background_enabled = bool(kwargs["kasse_products_background_enabled"])

        self.db.commit()
        self.db.refresh(settings)

        # Write audit log entry (non-fatal)
        try:
            from app.services.audit_log_service import AuditLogService
            new_snapshot = {k: getattr(settings, k, None) for k in old_snapshot}
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
