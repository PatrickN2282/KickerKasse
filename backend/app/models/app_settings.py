from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from .base import BaseModel


class AppSettings(BaseModel):
    __tablename__ = "app_settings"

    app_name = Column(String(120), nullable=False, default="KGB - KickerKasse")
    background_color = Column(String(7), nullable=False, default="#d7dce2")
    banner_color = Column(String(7), nullable=False, default="#131820")
    highlight_color = Column(String(7), nullable=False, default="#5c8f3a")
    logo_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<AppSettings {self.id}>"
