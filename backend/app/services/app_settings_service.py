from pathlib import Path
import re

from sqlalchemy.orm import Session

from app.models import AppSettings
from app.services.file_service import APP_SETTINGS_DIR, get_full_path, save_app_logo


HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
DEFAULT_APP_NAME = "KGB - KickerKasse"
DEFAULT_BACKGROUND_COLOR = "#d7dce2"
DEFAULT_BANNER_COLOR = "#131820"
DEFAULT_HIGHLIGHT_COLOR = "#5c8f3a"
DEFAULT_LOGO_RELATIVE_PATH = "app_settings/logo.png"


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
            "favicon_url": "/api/app-settings/favicon.png",
            "apple_touch_icon_url": "/api/app-settings/apple-touch-icon.png",
            "manifest_url": "/api/app-settings/manifest.webmanifest",
            "asset_version": self._asset_version(settings),
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

    def update_settings(self, **kwargs) -> AppSettings:
        settings = self.get_or_create_settings()
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

        self.db.commit()
        self.db.refresh(settings)
        return settings

    async def update_logo(self, file) -> AppSettings:
        settings = self.get_or_create_settings()
        settings.logo_path = await save_app_logo(file)
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
