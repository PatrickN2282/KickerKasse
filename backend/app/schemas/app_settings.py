from datetime import datetime
from pydantic import BaseModel, Field

# Hard limit to one day so accidental oversized values cannot keep sessions alive indefinitely.
MAX_SESSION_TIMER_MINUTES = 1440
SCHEDULED_REPORT_TYPES = ("full-zbon", "short-zbon", "daily-report")


class AppSettingsBase(BaseModel):
    app_name: str = Field(..., min_length=1, max_length=120)
    background_color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    banner_color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    highlight_color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    kasse_area_background_color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    kasse_layout: str | None = None
    session_timer_enabled: bool = False
    session_timer_minutes: int = Field(default=15, ge=1, le=MAX_SESSION_TIMER_MINUTES)
    deckel_enabled: bool = True
    kasse_products_background_scale: int = Field(default=100, ge=10, le=300)
    kasse_products_background_opacity: int = Field(default=100, ge=0, le=100)
    kasse_products_background_enabled: bool = True

    business_name: str | None = Field(default=None, max_length=160)
    business_street: str | None = Field(default=None, max_length=160)
    business_zip: str | None = Field(default=None, max_length=20)
    business_city: str | None = Field(default=None, max_length=120)
    business_phone: str | None = Field(default=None, max_length=50)
    business_email: str | None = Field(default=None, max_length=160)
    business_tax_number: str | None = Field(default=None, max_length=80)
    business_registration_number: str | None = Field(default=None, max_length=120)

    email_enabled: bool = False
    email_sender: str | None = Field(default=None, max_length=160)
    email_recipient_zbon: str | None = Field(default=None, max_length=160)
    email_subject_suffix: str | None = Field(default=None, max_length=120)
    email_critical_stock_enabled: bool = False
    smtp_host: str | None = Field(default=None, max_length=255)
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = Field(default=None, max_length=255)
    smtp_password: str | None = Field(default=None, max_length=255)
    smtp_use_tls: bool = True
    send_zbon_on_create_enabled: bool = False
    scheduled_zbon_enabled: bool = False
    scheduled_zbon_time: str = Field(default="23:59", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    scheduled_zbon_report_type: str = Field(default="full-zbon", pattern=r"^(full-zbon|short-zbon|daily-report)$")
    scheduled_database_backup_enabled: bool = False
    scheduled_database_backup_time: str = Field(default="03:00", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


class AppSettingsUpdate(BaseModel):
    app_name: str | None = Field(default=None, min_length=1, max_length=120)
    background_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    banner_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    highlight_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    kasse_area_background_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    kasse_layout: str | None = None
    session_timer_enabled: bool | None = None
    session_timer_minutes: int | None = Field(default=None, ge=1, le=MAX_SESSION_TIMER_MINUTES)
    deckel_enabled: bool | None = None
    kasse_products_background_scale: int | None = Field(default=None, ge=10, le=300)
    kasse_products_background_opacity: int | None = Field(default=None, ge=0, le=100)
    kasse_products_background_enabled: bool | None = None

    business_name: str | None = Field(default=None, max_length=160)
    business_street: str | None = Field(default=None, max_length=160)
    business_zip: str | None = Field(default=None, max_length=20)
    business_city: str | None = Field(default=None, max_length=120)
    business_phone: str | None = Field(default=None, max_length=50)
    business_email: str | None = Field(default=None, max_length=160)
    business_tax_number: str | None = Field(default=None, max_length=80)
    business_registration_number: str | None = Field(default=None, max_length=120)

    email_enabled: bool | None = None
    email_sender: str | None = Field(default=None, max_length=160)
    email_recipient_zbon: str | None = Field(default=None, max_length=160)
    email_subject_suffix: str | None = Field(default=None, max_length=120)
    email_critical_stock_enabled: bool | None = None
    smtp_host: str | None = Field(default=None, max_length=255)
    smtp_port: int | None = Field(default=None, ge=1, le=65535)
    smtp_username: str | None = Field(default=None, max_length=255)
    smtp_password: str | None = Field(default=None, max_length=255)
    smtp_use_tls: bool | None = None
    send_zbon_on_create_enabled: bool | None = None
    scheduled_zbon_enabled: bool | None = None
    scheduled_zbon_time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    scheduled_zbon_report_type: str | None = Field(default=None, pattern=r"^(full-zbon|short-zbon|daily-report)$")
    scheduled_database_backup_enabled: bool | None = None
    scheduled_database_backup_time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


class AppSettingsResponse(AppSettingsBase):
    id: int
    logo_url: str
    kasse_products_background_url: str
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


class PublicAppSettingsResponse(BaseModel):
    app_name: str
    background_color: str
    banner_color: str
    highlight_color: str
    kasse_area_background_color: str
    logo_url: str
    kasse_products_background_url: str
    favicon_ico_url: str
    favicon_16_url: str
    favicon_32_url: str
    favicon_url: str
    apple_touch_icon_url: str
    icon_192_url: str
    icon_512_url: str
    manifest_url: str
    asset_version: str
    kasse_layout: str | None = None
    session_timer_enabled: bool = False
    session_timer_minutes: int = 15
    deckel_enabled: bool = True
    kasse_products_background_scale: int = 100
    kasse_products_background_opacity: int = 100
    kasse_products_background_enabled: bool = True
    send_zbon_on_create_enabled: bool = False
