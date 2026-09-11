"""Signed-cookie, rollback and abuse-limit regressions for audit 04/15/17/18."""
import asyncio
import json
from datetime import datetime, timedelta

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from starlette.middleware.sessions import SessionMiddleware
from app.api import auth, product, member, category, guest_list, voucher, user, transaction, app_settings
from app.core import get_db
from app.core.auth import require_password_confirmation
from app.core.security import get_password_hasher
from app.models import User, UserRole, Member, BalanceLog, Transaction, AuditLog, PasswordResetToken
from app.models.auth_rate_limit import AuthRateLimit
from app.repositories import UserRepository, TransactionRepository, BalanceLogRepository
from app.services.audit_log_service import AuditLogService
from app.services.member_service import MemberService
from app.services.password_reset_service import PasswordResetService, _hash_token
from app.services.email_service import EmailService

PASSWORD = "Isolated-Login56!"


@pytest.fixture(scope="module")
def password_hash():
    return get_password_hasher().hash_password(PASSWORD)


@pytest.fixture()
def records(db_session, password_hash):
    actor = User(username="stage56", email="stage56@example.test", password_hash=password_hash, role=UserRole.TOP_ADMIN, is_active=True)
    person = Member(member_number=1, name="Mara Test", first_name="Mara", last_name="Test", balance_cents=1000)
    db_session.add_all([actor, person])
    db_session.commit()
    return actor, person


@pytest.fixture()
def api(db_session):
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="only-for-isolated-tests")
    for router in (auth.router, product.router, member.router, category.router, guest_list.router,
                   voucher.admin_router, voucher.kasse_router, user.router, transaction.router, app_settings.router):
        app.include_router(router)
    async def isolated_db():
        yield db_session
    app.dependency_overrides[get_db] = isolated_db
    cookies = httpx.Cookies()
    def send(method, path, payload=None):
        async def run():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
                                         base_url="http://test", cookies=cookies) as client:
                response = await client.request(method, path, json=payload)
                cookies.update(client.cookies)
                return response
        return asyncio.run(run())
    send.cookies = cookies
    return send


def login(api):
    response = api("POST", "/api/auth/login", {"username": "stage56", "password": PASSWORD})
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("path", [
    "/api/auth/me", "/api/auth/usernames", "/api/products", "/api/products/1",
    "/api/products/1/image", "/api/products/1/original-image", "/api/categories",
    "/api/members/selection", "/api/members/1/photo", "/api/members/1/original-photo",
    "/api/guest-list/guests", "/api/admin/vouchers", "/api/transactions/next-receipt-number",
])
def test_disabled_signed_session_cannot_read_protected_routes(db_session, records, api, path):
    actor, _ = records
    login(api)
    UserRepository(db_session).update(actor.id, is_active=False)
    response = api("GET", path)
    assert response.status_code == 401, (path, response.text)


@pytest.mark.parametrize("change", [{"password": "Changed-Password56!"}, {"role": "MANAGER"}, {"is_active": False}])
def test_security_changes_revoke_old_cookie_even_after_reactivation(db_session, records, api, change):
    actor, _ = records
    login(api)
    original_version = actor.session_version
    UserRepository(db_session).update(actor.id, **change)
    assert actor.session_version > original_version
    if not actor.is_active:
        UserRepository(db_session).update(actor.id, is_active=True)
    assert api("GET", "/api/auth/me").status_code == 401


def test_profile_change_keeps_session_and_roles_come_from_database(db_session, records, api):
    actor, _ = records
    login(api)
    UserRepository(db_session).update(actor.id, email="new@example.test")
    response = api("GET", "/api/auth/me")
    assert response.status_code == 200 and response.json()["email"] == "new@example.test"


def test_legacy_cookie_without_version_is_rejected(records, api):
    import base64
    from itsdangerous import TimestampSigner
    value = base64.b64encode(json.dumps({"user_id": records[0].id, "role": "TOP_ADMIN"}).encode())
    api.cookies.set("session", TimestampSigner("only-for-isolated-tests").sign(value).decode())
    assert api("GET", "/api/auth/me").status_code == 401


def test_login_limit_expires_without_extending_window(db_session, records, api):
    for _ in range(5):
        assert api("POST", "/api/auth/login", {"username": "stage56", "password": "wrong"}).status_code == 401
    before = {r.key: r.window_started_at for r in db_session.query(AuthRateLimit).all()}
    response = api("POST", "/api/auth/login", {"username": "stage56", "password": PASSWORD})
    assert response.status_code == 429 and int(response.headers["retry-after"]) <= 60
    db_session.expire_all()
    assert {r.key: r.window_started_at for r in db_session.query(AuthRateLimit).all()} == before
    db_session.query(AuthRateLimit).update({AuthRateLimit.window_started_at: datetime.utcnow() - timedelta(seconds=61)})
    db_session.commit()
    login(api)


def test_source_limit_also_blocks_rotating_unknown_usernames(db_session, api):
    for i in range(30):
        assert api("POST", "/api/auth/login", {"username": f"unknown-{i}", "password": "wrong"}).status_code == 401
    assert api("POST", "/api/auth/login", {"username": "another", "password": "wrong"}).status_code == 429


def test_reset_request_responses_are_generic_and_mail_is_throttled(db_session, records, api, monkeypatch):
    sent = []
    monkeypatch.setattr(EmailService, "send_password_reset_email", lambda *args: sent.append(args))
    responses = [api("POST", "/api/auth/password-reset/request", {"email": address}) for address in
                 ["stage56@example.test", "unknown@example.test", "stage56@example.test", "STAGE56@example.test"]]
    assert all(r.status_code == 200 and r.json() == responses[0].json() for r in responses)
    assert len(sent) == 1 and db_session.query(PasswordResetToken).count() == 1


def tokens(db, actor):
    records = [PasswordResetToken(user_id=actor.id, token_hash=_hash_token(raw),
                                 expires_at=datetime.utcnow() + timedelta(minutes=10)) for raw in ["link-one", "link-two"]]
    db.add_all(records)
    db.commit()
    return records


def test_reset_revokes_other_links_and_old_signed_session(db_session, records, api):
    actor, _ = records
    login(api)
    tokens(db_session, actor)
    PasswordResetService(db_session).confirm_reset("link-one", "New-Password56!")
    assert api("GET", "/api/auth/me").status_code == 401
    assert all(t.used_at for t in db_session.query(PasswordResetToken).all())
    with pytest.raises(ValueError, match="verwendet"):
        PasswordResetService(db_session).confirm_reset("link-two", "Another-Password56!")


@pytest.mark.parametrize("failure", ["password", "audit", "commit"])
def test_reset_failure_rolls_back_password_token_and_session_version(db_session, records, monkeypatch, failure):
    actor, _ = records
    links = tokens(db_session, actor)
    original = actor.password_hash, actor.session_version
    def fail(*args, **kwargs):
        raise RuntimeError("injected failure")
    target, method = {"password": (UserRepository, "update"), "audit": (AuditLogService, "log"), "commit": (db_session, "commit")}[failure]
    with monkeypatch.context() as patch:
        patch.setattr(target, method, fail)
        with pytest.raises(RuntimeError):
            PasswordResetService(db_session).confirm_reset("link-one", "New-Password56!")
    db_session.expire_all()
    assert (actor.password_hash, actor.session_version) == original
    assert all(link.used_at is None for link in links)
    assert db_session.query(AuditLog).count() == 0


@pytest.mark.parametrize("failure", ["transaction", "balance_log", "audit", "commit"])
def test_recharge_failure_preserves_all_original_state(db_session, records, monkeypatch, failure):
    actor, person = records
    def fail(*args, **kwargs):
        raise RuntimeError("injected failure")
    target, method = {"transaction": (TransactionRepository, "create"), "balance_log": (BalanceLogRepository, "create"),
                      "audit": (AuditLogService, "log"), "commit": (db_session, "commit")}[failure]
    with monkeypatch.context() as patch:
        patch.setattr(target, method, fail)
        with pytest.raises(RuntimeError):
            MemberService(db_session).recharge_balance(person.id, 500, executed_by_user_id=actor.id, executed_by_username=actor.username)
    db_session.expire_all()
    assert person.balance_cents == 1000
    for model in (Transaction, BalanceLog, AuditLog):
        assert db_session.query(model).count() == 0


def test_recharge_links_cash_and_balance_history_and_keeps_404(db_session, records, api):
    actor, person = records
    login(api)
    response = api("POST", f"/api/members/{person.id}/recharge", {"amount_cents": 500, "auth_password": PASSWORD})
    assert response.status_code == 200, response.text
    assert response.json()["balance_cents"] == 1500 and response.json()["drawer_targets"] == ["main"]
    movement, log = db_session.query(Transaction).one(), db_session.query(BalanceLog).one()
    assert log.transaction_id == movement.id
    assert movement.total_amount_cents == log.change_cents == 500
    assert json.loads(db_session.query(AuditLog).one().new_value)["transaction_id"] == movement.id
    assert api("POST", "/api/members/9999/recharge", {"amount_cents": 500, "auth_password": PASSWORD}).status_code == 404


def test_valid_password_confirmations_are_not_limited_like_failed_attempts(db_session, records):
    actor, _ = records
    for _ in range(7):
        require_password_confirmation(actor, PASSWORD, db_session)
    for _ in range(5):
        with pytest.raises(HTTPException) as exc:
            require_password_confirmation(actor, "wrong", db_session)
        assert exc.value.status_code == 403
    with pytest.raises(HTTPException) as exc:
        require_password_confirmation(actor, "wrong", db_session)
    assert exc.value.status_code == 429
