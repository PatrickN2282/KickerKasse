from datetime import datetime
from pydantic import BaseModel, Field


class AppSettingsBase(BaseModel):
    background_color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    banner_color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    highlight_color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")


class AppSettingsUpdate(AppSettingsBase):
    pass


class AppSettingsResponse(AppSettingsBase):
    id: int
    logo_url: str
    favicon_url: str
    apple_touch_icon_url: str
    manifest_url: str
    asset_version: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PublicAppSettingsResponse(AppSettingsBase):
    logo_url: str
    favicon_url: str
    apple_touch_icon_url: str
    manifest_url: str
    asset_version: str
    app_name: str
