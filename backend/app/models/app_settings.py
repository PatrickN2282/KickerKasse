from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func
from .base import BaseModel


class AppSettings(BaseModel):
    __tablename__ = "app_settings"

    app_name = Column(String(120), nullable=False, default="KickerKasse")
    background_color = Column(String(7), nullable=False, default="#d7dce2")
    banner_color = Column(String(7), nullable=False, default="#131820")
    highlight_color = Column(String(7), nullable=False, default="#5c8f3a")
    kasse_area_background_color = Column(String(7), nullable=False, default="#ffffff")
    logo_path = Column(String(255), nullable=True)
    kasse_products_background_path = Column(String(255), nullable=True)
    kasse_layout = Column(String(50), nullable=True)
    session_timer_enabled = Column(Boolean, nullable=False, default=False)
    session_timer_minutes = Column(Integer, nullable=False, default=15)
    kasse_direct_login_enabled = Column(Boolean, nullable=False, default=True)
    deckel_enabled = Column(Boolean, nullable=False, default=True)
    guest_list_enabled = Column(Boolean, nullable=False, default=True)
    kasse_products_background_scale = Column(Integer, nullable=False, default=100)
    kasse_products_background_opacity = Column(Integer, nullable=False, default=100)
    kasse_products_background_enabled = Column(Boolean, nullable=False, default=True)

    business_name = Column(String(160), nullable=True)
    business_street = Column(String(160), nullable=True)
    business_zip = Column(String(20), nullable=True)
    business_city = Column(String(120), nullable=True)
    business_phone = Column(String(50), nullable=True)
    business_email = Column(String(160), nullable=True)
    business_tax_number = Column(String(80), nullable=True)
    business_registration_number = Column(String(120), nullable=True)

    email_enabled = Column(Boolean, nullable=False, default=False)
    email_sender = Column(String(160), nullable=True)
    email_recipient_zbon = Column(String(160), nullable=True)
    email_recipient_stock = Column(String(160), nullable=True)
    email_recipient_backup = Column(String(160), nullable=True)
    email_subject_suffix = Column(String(120), nullable=True)
    email_subject_zbon_info = Column(String(120), nullable=True)
    email_subject_stock_info = Column(String(120), nullable=True)
    email_subject_backup_info = Column(String(120), nullable=True)
    email_critical_stock_enabled = Column(Boolean, nullable=False, default=False)
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, nullable=False, default=587)
    smtp_username = Column(String(255), nullable=True)
    smtp_password = Column(String(255), nullable=True)
    smtp_use_tls = Column(Boolean, nullable=False, default=True)
    send_zbon_on_create_enabled = Column(Boolean, nullable=False, default=False)
    scheduled_zbon_enabled = Column(Boolean, nullable=False, default=False)
    scheduled_zbon_time = Column(String(5), nullable=False, default="23:59")
    scheduled_zbon_report_type = Column(String(32), nullable=False, default="full-zbon")
    scheduled_stock_warning_time = Column(String(5), nullable=False, default="09:00")
    scheduled_database_backup_enabled = Column(Boolean, nullable=False, default=False)
    scheduled_database_backup_time = Column(String(5), nullable=False, default="03:00")
    zbon_last_run_at = Column(DateTime, nullable=True)
    zbon_last_run_status = Column(String(16), nullable=True)
    zbon_last_run_message = Column(Text, nullable=True)
    zbon_last_business_date = Column(String(10), nullable=True)
    stock_last_run_at = Column(DateTime, nullable=True)
    stock_last_run_status = Column(String(16), nullable=True)
    stock_last_run_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<AppSettings {self.id}>"
