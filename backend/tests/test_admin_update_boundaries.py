"""Regression coverage for audit tasks 01/02 using real routers and an isolated DB."""

import asyncio
import json
from unittest.mock import Mock

import httpx
import pytest
from fastapi import FastAPI

from app.api import app_settings, member as member_api
from app.core import get_db
from app.core.security import get_password_hasher
from app.models import (
    AuditLog, BalanceLog, Member, MemberBalanceCorrectionLog, Transaction,
    User, UserRole,
)
from app.services.app_settings_service import AppSettingsService
from app.services.member_service import MemberService
from app.schemas import AppSettingsUpdate, MemberUpdate


@pytest.fixture()
def api_request(db_session, monkeypatch):
    # Exercise HTTP validation/authorization without production startup or a real login.
    app = FastAPI()
    app.include_router(app_settings.router)
    app.include_router(member_api.router)
    session = {}

    @app.middleware("http")
    async def test_session(request, call_next):
        request.scope["session"] = session
        return await call_next(request)

    async def isolated_db():
        yield db_session

    app.dependency_overrides[get_db] = isolated_db
    scheduler_reload = Mock()
    monkeypatch.setattr(app_settings.SchedulerService, "reload_scheduler", scheduler_reload)

    def send(user, method, path, payload):
        session.clear()
        if user is not None:
            session["user_id"] = user.id
            session["session_version"] = user.session_version

        async def run():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.request(method, path, json=payload)

        return asyncio.run(run())

    send.scheduler_reload = scheduler_reload
    return send


def make_user(db, role):
    user = User(username="boundary-test", password_hash="unused", role=role, is_active=True)
    db.add(user)
    db.commit()
    return user


@pytest.fixture()
def member(db_session):
    record = Member(member_number=1, name="Mara Mitglied", first_name="Mara",
                    last_name="Mitglied", balance_cents=1000, notes="original")
    db_session.add(record)
    db_session.commit()
    return record


def assert_no_bookings(db):
    for model in (AuditLog, BalanceLog, MemberBalanceCorrectionLog, Transaction):
        assert db.query(model).count() == 0


@pytest.mark.parametrize("field", ["email_recipient_backup", "email_recipient_stock"])
@pytest.mark.parametrize("value", ["changed@example.test", None])
@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.MANAGER, UserRole.VERKAUF])
def test_restricted_recipient_update_rejects_entire_request(db_session, api_request, field, value, role):
    user = make_user(db_session, role)
    settings = AppSettingsService(db_session).get_or_create_settings()
    setattr(settings, field, "original@example.test")
    db_session.commit()
    old_name = settings.app_name

    response = api_request(user, "PUT", "/api/app-settings", {field: value, "app_name": "Changed"})

    assert response.status_code == 403
    db_session.refresh(settings)
    assert getattr(settings, field) == "original@example.test"
    assert settings.app_name == old_name
    assert db_session.query(AuditLog).count() == 0
    api_request.scheduler_reload.assert_not_called()


@pytest.mark.parametrize("value", ["changed@example.test", None])
def test_top_admin_can_change_recipients_with_audit(db_session, api_request, value):
    user = make_user(db_session, UserRole.TOP_ADMIN)
    settings = AppSettingsService(db_session).get_or_create_settings()
    fields = ("email_recipient_backup", "email_recipient_stock")
    for field in fields:
        setattr(settings, field, "original@example.test")
    db_session.commit()

    response = api_request(user, "PUT", "/api/app-settings/", dict.fromkeys(fields, value))

    assert response.status_code == 200, response.text
    db_session.refresh(settings)
    audit = db_session.query(AuditLog).one()
    assert audit.user_username == user.username
    for field in fields:
        assert getattr(settings, field) == value
        assert json.loads(audit.old_value)[field] == "original@example.test"
        assert json.loads(audit.new_value)[field] == value
    api_request.scheduler_reload.assert_called_once()


def test_admin_can_still_change_design(db_session, api_request):
    user = make_user(db_session, UserRole.ADMIN)
    response = api_request(user, "PUT", "/api/app-settings", {"app_name": "Vereinskasse", "banner_color": "#123456"})
    assert response.status_code == 200, response.text
    assert response.json()["app_name"] == "Vereinskasse"
    assert response.json()["banner_color"] == "#123456"


@pytest.mark.parametrize("field", sorted(set(AppSettingsUpdate.model_fields) - {
    "app_name", "background_color", "banner_color", "highlight_color",
    "kasse_area_background_color", "deckel_enabled", "guest_list_enabled",
    "kasse_products_background_scale", "kasse_products_background_opacity",
    "kasse_products_background_enabled",
}))
def test_admin_cannot_submit_any_advanced_setting(db_session, api_request, field):
    user = make_user(db_session, UserRole.ADMIN)
    settings = AppSettingsService(db_session).get_or_create_settings()
    old_name = settings.app_name
    # Explicit null must not bypass role checks, even if the service would ignore it.
    response = api_request(user, "PUT", "/api/app-settings", {field: None, "app_name": "Changed"})
    assert response.status_code == 403, response.text
    db_session.refresh(settings)
    assert settings.app_name == old_name
    assert db_session.query(AuditLog).count() == 0
    api_request.scheduler_reload.assert_not_called()


def test_balance_is_not_advertised_as_a_member_profile_field():
    assert "balance_cents" not in MemberUpdate.model_json_schema()["properties"]


@pytest.mark.parametrize("role", [UserRole.MANAGER, UserRole.ADMIN, UserRole.TOP_ADMIN])
@pytest.mark.parametrize("balance", [9999, -1, 0, 1000, None])
def test_generic_member_update_rejects_balance_even_when_mixed(db_session, api_request, member, role, balance):
    user = make_user(db_session, role)
    response = api_request(user, "PUT", f"/api/members/{member.id}", {"notes": "changed", "balance_cents": balance})
    assert response.status_code == 422, response.text
    assert "Aufladung" in response.text
    db_session.refresh(member)
    assert member.balance_cents == 1000
    assert member.notes == "original"
    assert_no_bookings(db_session)


@pytest.mark.parametrize("balance", [9999, -1, None])
def test_member_service_also_rejects_generic_balance_update(db_session, member, balance):
    with pytest.raises(ValueError, match="Aufladung"):
        MemberService(db_session).update_member(member.id, balance_cents=balance, notes="changed")
    db_session.refresh(member)
    assert member.balance_cents == 1000
    assert member.notes == "original"
    assert_no_bookings(db_session)


@pytest.mark.parametrize("role", [UserRole.MANAGER, UserRole.ADMIN, UserRole.TOP_ADMIN])
def test_generic_member_details_remain_editable(db_session, api_request, member, role):
    user = make_user(db_session, role)
    response = api_request(user, "PUT", f"/api/members/{member.id}/", {"notes": "changed"})
    assert response.status_code == 200, response.text
    db_session.refresh(member)
    assert member.notes == "changed"
    assert member.balance_cents == 1000
    assert db_session.query(AuditLog).one().action == "UPDATED"
    assert db_session.query(BalanceLog).count() == 0
    assert db_session.query(MemberBalanceCorrectionLog).count() == 0
    assert db_session.query(Transaction).count() == 0


@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.TOP_ADMIN])
def test_authorized_balance_correction_remains_logged(db_session, api_request, member, role):
    user = make_user(db_session, role)
    response = api_request(user, "POST", f"/api/members/{member.id}/balance-correction",
                           {"new_balance_cents": 500, "reason": "Testkorrektur"})
    assert response.status_code == 200, response.text
    db_session.refresh(member)
    assert member.balance_cents == 500
    correction = db_session.query(MemberBalanceCorrectionLog).one()
    assert (correction.old_balance_cents, correction.new_balance_cents, correction.change_cents) == (1000, 500, -500)
    assert correction.executed_by_username == user.username
    assert correction.reason == "Testkorrektur"
    assert db_session.query(AuditLog).one().action == "BALANCE_CORRECTION"
    assert db_session.query(Transaction).count() == 0


def test_manager_cannot_use_balance_correction(db_session, api_request, member):
    user = make_user(db_session, UserRole.MANAGER)
    response = api_request(user, "POST", f"/api/members/{member.id}/balance-correction", {"new_balance_cents": 500})
    assert response.status_code == 403
    db_session.refresh(member)
    assert member.balance_cents == 1000
    assert_no_bookings(db_session)


def test_manager_recharge_still_requires_password_and_records_cash(db_session, api_request, member):
    user = make_user(db_session, UserRole.MANAGER)
    user.password_hash = get_password_hasher().hash_password("test-password")
    db_session.commit()
    path = f"/api/members/{member.id}/recharge"
    response = api_request(user, "POST", path, {"amount_cents": 500, "auth_password": "wrong"})
    assert response.status_code == 403
    assert_no_bookings(db_session)
    response = api_request(user, "POST", path, {"amount_cents": 500, "auth_password": "test-password"})
    assert response.status_code == 200, response.text
    db_session.refresh(member)
    assert member.balance_cents == 1500
    assert db_session.query(BalanceLog).one().new_balance_cents == 1500
    transaction = db_session.query(Transaction).one()
    assert transaction.total_amount_cents == 500
    assert transaction.type.value == "RECHARGE"
    assert transaction.payment_method.value == "CASH"
    assert db_session.query(MemberBalanceCorrectionLog).count() == 0
