"""Concurrent password reset / recharge and durable limits on disposable databases."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.core.db_migration import run_migrations
from app.core.security import get_password_hasher
from app.models import User, UserRole, Member, Product, PasswordResetToken, Transaction, BalanceLog, AuditLog
from app.services.password_reset_service import PasswordResetService, _hash_token
from app.services.member_service import MemberService
from app.services.auth_rate_limit_service import AuthRateLimitService
from app.api.transaction import create_sale
from app.schemas.transaction import TransactionCreate


def seed(engine):
    assert run_migrations(engine)
    with Session(engine) as db:
        actor = User(username="stage56", password_hash=get_password_hasher().hash_password("Old-Test56!"), role=UserRole.TOP_ADMIN)
        person = Member(member_number=1, name="Mara Test", first_name="Mara", last_name="Test", balance_cents=1000)
        product = Product(name="Wasser", price_cents=200, stock_quantity=10)
        db.add_all([actor, person, product])
        db.commit()
        return actor.id, person.id, product.id


@pytest.mark.parametrize("same_link", [True, False])
def test_concurrent_reset_changes_password_once_and_revokes_all_links(pg_engine, same_link):
    actor_id, _, _ = seed(pg_engine)
    with Session(pg_engine) as db:
        db.add_all([PasswordResetToken(user_id=actor_id, token_hash=_hash_token(raw),
                                      expires_at=datetime.utcnow() + timedelta(minutes=10)) for raw in ["link-one", "link-two"]])
        db.commit()
    barrier = Barrier(2)
    def reset(raw):
        with Session(pg_engine) as db:
            barrier.wait(timeout=10)
            try:
                PasswordResetService(db).confirm_reset(raw, "New-Test56!")
                return True
            except ValueError:
                return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reset, ["link-one", "link-one" if same_link else "link-two"]))
    assert sorted(results) == [False, True]
    with Session(pg_engine) as db:
        assert db.get(User, actor_id).session_version == 2
        assert db.query(AuditLog).filter_by(action="PASSWORD_RESET_COMPLETED").count() == 1
        assert all(t.used_at for t in db.query(PasswordResetToken).all())


def test_concurrent_recharges_and_real_sale_preserve_every_movement(pg_engine):
    actor_id, member_id, product_id = seed(pg_engine)
    barrier = Barrier(3)
    def run(operation):
        with Session(pg_engine, autoflush=False) as db:
            # Deliberately pre-load the old balance in each identity map.
            assert db.get(Member, member_id).balance_cents == 1000
            barrier.wait(timeout=10)
            if operation == "sale":
                request = Request({"type": "http", "method": "POST", "path": "/api/transactions/sale", "headers": [],
                                   "session": {"user_id": actor_id, "session_version": 1}})
                payload = TransactionCreate(user_id=actor_id, payment_method="BALANCE", member_id=member_id,
                                            items=[{"product_id": product_id, "quantity": 1, "unit_price_cents": 200}])
                asyncio.run(create_sale(payload, request, db))
            else:
                MemberService(db).recharge_balance(member_id, 500, executed_by_user_id=actor_id, executed_by_username="stage56")
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(run, ["sale", "recharge", "recharge"]))
    with Session(pg_engine) as db:
        assert db.get(Member, member_id).balance_cents == 1800
        assert db.get(Product, product_id).stock_quantity == 9
        assert db.query(Transaction).count() == 3
        logs = db.query(BalanceLog).all()
        assert len(logs) == 3 and all(log.transaction_id for log in logs)
        assert sum(log.change_cents for log in logs) == 800
        assert db.query(AuditLog).filter_by(action="RECHARGED").count() == 2


def test_limit_is_atomic_across_independent_sessions(pg_engine):
    assert run_migrations(pg_engine)
    barrier = Barrier(8)
    def consume(_):
        with Session(pg_engine) as db:
            barrier.wait(timeout=10)
            return AuthRateLimitService(db).consume("login-test", "same-account", 5, 60)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(consume, range(8)))
    assert results.count(0) == 5
    with Session(pg_engine) as db:
        assert AuthRateLimitService(db).consume("login-test", "same-account", 5, 60) > 0


@pytest.mark.parametrize("mail_fails", [False, True])
def test_reset_request_records_long_audit_action_and_keeps_mail_failures_generic(pg_engine, monkeypatch, mail_fails):
    actor_id, _, _ = seed(pg_engine)
    calls = []
    def send(*args):
        calls.append(args)
        if mail_fails:
            raise RuntimeError("Test mail provider unavailable")
    monkeypatch.setattr("app.services.password_reset_service.EmailService.send_password_reset_email", send)
    with Session(pg_engine) as db:
        db.get(User, actor_id).email = "stage56@example.invalid"
        db.commit()
        service = PasswordResetService(db)
        service.request_reset("stage56@example.invalid", reset_url_base="http://test/password-reset/", requested_ip="test")
        service.request_reset("stage56@example.invalid", reset_url_base="http://test/password-reset/", requested_ip="test")
        assert len(calls) == 1
        assert db.query(PasswordResetToken).count() == 1
        assert db.query(AuditLog).filter_by(action="PASSWORD_RESET_REQUESTED").count() == 1


def test_upgrade_adds_session_version_and_limits_without_changing_accounts(pg_engine):
    actor_id, _, _ = seed(pg_engine)
    with pg_engine.begin() as conn:
        conn.execute(text("DELETE FROM schema_migrations WHERE version='1.6.7'"))
        conn.execute(text("ALTER TABLE users DROP COLUMN session_version"))
        conn.execute(text("DROP TABLE auth_rate_limits"))
        conn.execute(text("ALTER TABLE audit_logs ALTER COLUMN action TYPE VARCHAR(20)"))
    assert run_migrations(pg_engine)
    assert run_migrations(pg_engine)
    with Session(pg_engine) as db:
        actor = db.get(User, actor_id)
        assert actor.session_version == 1 and actor.role == UserRole.TOP_ADMIN
    action = next(c for c in inspect(pg_engine).get_columns("audit_logs") if c["name"] == "action")
    assert action["type"].length == 64
