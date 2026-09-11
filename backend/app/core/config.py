import os
from dotenv import load_dotenv
from sqlalchemy.engine import URL, make_url
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
load_dotenv()

DEFAULT_TIMEZONE = "Europe/Berlin"
INSECURE_SECRET_KEYS = {"", "change_me", "your-secret-key-change-in-production"}


def resolve_timezone_name(timezone_name: str | None) -> str:
    candidate = (timezone_name or "").strip() or DEFAULT_TIMEZONE
    try:
        ZoneInfo(candidate)
        return candidate
    except ZoneInfoNotFoundError:
        return DEFAULT_TIMEZONE


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL") or URL.create(
        "postgresql+psycopg2",
        username=os.getenv("DATABASE_USER", "kassensystem-test"),
        password=os.getenv("DATABASE_PASSWORD", "kassensystem-test"),
        host=os.getenv("DATABASE_HOST", "127.0.0.1"),
        port=int(os.getenv("DATABASE_PORT", "5434")),
        database=os.getenv("DATABASE_NAME", "kassensystem-test"),
    ).render_as_string(hide_password=False)
    # Keep existing PostgreSQL URLs compatible with the installed driver.
    if make_url(DATABASE_URL).drivername in {"postgresql", "postgres", "postgresql+psycopg"}:
        DATABASE_URL = make_url(DATABASE_URL).set(drivername="postgresql+psycopg2").render_as_string(hide_password=False)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    PRODUCTION: bool = os.getenv("PRODUCTION", "").strip().lower() in {"1", "true", "yes", "on"}
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "").strip().lower() in {"1", "true", "yes", "on"}
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    SESSION_COOKIE_NAME: str = "kasse_session"
    SESSION_COOKIE_MAX_AGE: int = 24 * 60 * 60
    APP_TIMEZONE: str = resolve_timezone_name(os.getenv("APP_TIMEZONE", os.getenv("TZ", DEFAULT_TIMEZONE)))

    def validate_runtime_configuration(self) -> None:
        if not self.PRODUCTION:
            return
        if self.SECRET_KEY.strip() in INSECURE_SECRET_KEYS or len(self.SECRET_KEY) < 32:
            raise RuntimeError("SECRET_KEY must be at least 32 characters and must not use a placeholder in production")
        if not self.COOKIE_SECURE:
            raise RuntimeError("COOKIE_SECURE must be enabled in production")


settings = Settings()
