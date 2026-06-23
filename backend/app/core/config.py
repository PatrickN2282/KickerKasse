import os
from dotenv import load_dotenv
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

load_dotenv()

DEFAULT_TIMEZONE = "Europe/Berlin"


def resolve_timezone_name(timezone_name: str | None) -> str:
    candidate = (timezone_name or "").strip() or DEFAULT_TIMEZONE
    try:
        ZoneInfo(candidate)
        return candidate
    except ZoneInfoNotFoundError:
        return DEFAULT_TIMEZONE


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://"
        "kassensystem:kassensystem@localhost:5432/kassensystem"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    SESSION_COOKIE_NAME: str = "kasse_session"
    SESSION_COOKIE_MAX_AGE: int = 24 * 60 * 60
    APP_TIMEZONE: str = resolve_timezone_name(os.getenv("APP_TIMEZONE", os.getenv("TZ", DEFAULT_TIMEZONE)))


settings = Settings()
