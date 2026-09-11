from sqlalchemy import Column, String, Integer, DateTime
from .base import Base


class AuthRateLimit(Base):
    __tablename__ = "auth_rate_limits"
    key = Column(String(64), primary_key=True)
    window_started_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, nullable=False)
