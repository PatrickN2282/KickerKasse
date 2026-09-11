"""Etappe 19 regression checks; prepared for the combined final run, not executed yet."""
from app.models import Product
from app.services.app_settings_service import AppSettingsService
from app.services.email_service import EmailService
from app.services.scheduler_service import SchedulerService
import app.services.scheduler_service as scheduler_module


def test_stock_warning_runs_without_zbon_schedule_and_persists_result(db_session, monkeypatch):
    settings = AppSettingsService(db_session).get_or_create_settings()
    settings.email_enabled = True
    settings.email_critical_stock_enabled = True
    settings.scheduled_zbon_enabled = False
    settings.email_recipient_stock = "lager@example.invalid"
    product = Product(
        name="Knapp",
        price_cents=100,
        stock_quantity=1,
        minimum_stock_quantity=3,
        notify_on_low_stock=True,
        is_unlimited_stock=False,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    sent = []
    monkeypatch.setattr(scheduler_module, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(
        EmailService,
        "send_critical_stock_email",
        lambda recipient, payload: sent.append((recipient, payload)) or True,
    )

    SchedulerService._send_critical_stock()

    current = AppSettingsService(db_session).get_or_create_settings()
    assert sent[0][0] == "lager@example.invalid"
    assert sent[0][1][0]["name"] == "Knapp"
    assert current.stock_last_run_status == "SUCCESS"
    assert current.stock_last_run_at is not None


def test_stock_check_without_critical_products_records_skipped(db_session, monkeypatch):
    settings = AppSettingsService(db_session).get_or_create_settings()
    settings.email_enabled = True
    settings.email_critical_stock_enabled = True
    settings.email_recipient_stock = "lager@example.invalid"
    db_session.commit()
    monkeypatch.setattr(scheduler_module, "SessionLocal", lambda: db_session)

    SchedulerService._send_critical_stock()

    assert AppSettingsService(db_session).get_or_create_settings().stock_last_run_status == "SKIPPED"
