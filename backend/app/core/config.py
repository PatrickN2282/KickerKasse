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


settings = Settings()
