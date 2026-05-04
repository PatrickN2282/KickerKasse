from datetime import datetime
from pydantic import BaseModel, Field


class AppSettingsBase(BaseModel):
    app_name: str = Field(..., min_length=1, max_length=120)
    background_color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    banner_color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    highlight_color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    kasse_layout: str | None = None
    session_timer_enabled: bool = False
    session_timer_minutes: int = Field(default=15, ge=1, le=1440)


class AppSettingsUpdate(AppSettingsBase):
    pass


class AppSettingsResponse(AppSettingsBase):
    id: int
    logo_url: str
    favicon_ico_url: str
    favicon_16_url: str
    favicon_32_url: str
    favicon_url: str
    apple_touch_icon_url: str
    icon_192_url: str
    icon_512_url: str
    manifest_url: str
    asset_version: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PublicAppSettingsResponse(AppSettingsBase):
    logo_url: str
    favicon_ico_url: str
    favicon_16_url: str
    favicon_32_url: str
    favicon_url: str
    apple_touch_icon_url: str
    icon_192_url: str
    icon_512_url: str
    manifest_url: str
    asset_version: str
