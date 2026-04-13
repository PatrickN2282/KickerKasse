import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://kassensystem:kassensystem@localhost:5432/kassensystem"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Session
    SESSION_COOKIE_NAME: str = "kasse_session"
    SESSION_COOKIE_MAX_AGE: int = 24 * 60 * 60  # 24 Stunden
    
    # Email Configuration
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "noreply@kassensystem.local")
    EMAIL_RECIPIENT_ZBON: str = os.getenv("EMAIL_RECIPIENT_ZBON", "admin@kassensystem.local")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    
    # Automated Z-Bon Email
    SCHEDULED_ZBON_ENABLED: bool = os.getenv("SCHEDULED_ZBON_ENABLED", "false").lower() == "true"
    SCHEDULED_ZBON_TIME: str = os.getenv("SCHEDULED_ZBON_TIME", "23:59")  # HH:MM format

    SCHEDULED_ZBON_REPORT_TYPE: str = os.getenv("SCHEDULED_ZBON_REPORT_TYPE", "zbon")  # 'zbon' or 'daily-report'

settings = Settings()
