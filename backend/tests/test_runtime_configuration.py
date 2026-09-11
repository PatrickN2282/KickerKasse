import runpy
from pathlib import Path

import dotenv
import pytest
from sqlalchemy.engine import make_url


def configured(monkeypatch, **values):
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)
    for key in ("DATABASE_URL", "DATABASE_USER", "DATABASE_PASSWORD", "DATABASE_HOST", "DATABASE_PORT", "DATABASE_NAME", "SECRET_KEY", "PRODUCTION", "COOKIE_SECURE"):
        monkeypatch.delenv(key, raising=False)
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    return runpy.run_path(str(Path(__file__).parents[1] / "app/core/config.py"))["settings"]


def test_default_local_connection_matches_documented_compose_port(monkeypatch):
    settings = configured(monkeypatch)
    url = make_url(settings.DATABASE_URL)
    assert (url.drivername, url.host, url.port, url.database) == ("postgresql+psycopg2", "127.0.0.1", 5434, "kassensystem-test")


def test_split_credentials_preserve_reserved_characters(monkeypatch):
    password = "only-test:@/#?%+"
    settings = configured(monkeypatch, DATABASE_USER="custom-user", DATABASE_PASSWORD=password, DATABASE_NAME="custom-db")
    url = make_url(settings.DATABASE_URL)
    assert url.username == "custom-user" and url.password == password and url.database == "custom-db"


@pytest.mark.parametrize("driver", ["postgresql", "postgres", "postgresql+psycopg", "postgresql+psycopg2"])
def test_explicit_urls_use_installed_driver_and_take_precedence(monkeypatch, driver):
    settings = configured(monkeypatch, DATABASE_URL=f"{driver}://test:only-test@localhost:9876/explicit", DATABASE_NAME="ignored")
    url = make_url(settings.DATABASE_URL)
    assert url.drivername == "postgresql+psycopg2" and url.database == "explicit" and url.port == 9876


@pytest.mark.parametrize("values", [
    {"SECRET_KEY": "change_me", "COOKIE_SECURE": "true"},
    {"SECRET_KEY": "your-secret-key-change-in-production", "COOKIE_SECURE": "true"},
    {"SECRET_KEY": "short", "COOKIE_SECURE": "true"},
    {"SECRET_KEY": "a" * 64, "COOKIE_SECURE": "false"},
])
def test_invalid_production_configuration_stops_startup(monkeypatch, values):
    with pytest.raises(RuntimeError):
        configured(monkeypatch, PRODUCTION="true", **values).validate_runtime_configuration()


def test_valid_production_configuration(monkeypatch):
    configured(monkeypatch, PRODUCTION="true", SECRET_KEY="test-only-" * 8, COOKIE_SECURE="true").validate_runtime_configuration()
