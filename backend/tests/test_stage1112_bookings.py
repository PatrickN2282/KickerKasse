"""Closure ordering, count validation and atomic HTTP replay on isolated databases."""
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import httpx
import pytest
from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import sessionmaker
from app.models import Base, Transaction, CashEntry, CashEntryType, BookingOperation, ZBonHistory, Member
from app.core.database import get_db
from app.core.financial_booking import next_receipt_number
from app.api import transaction as api
from app.api import deckel as deckel_api
from app.api import member as member_api
from app.services.zbon_service import ZBonService
from app.repositories import CashEntryRepository
from app.utils.cash_count import cash_count_cents
from .test_stage789_bookings import seed, sale


@pytest.mark.parametrize("count,total", [({"coins": {"0.03": 1}}, None),
    ({"coins": {"1": -1}}, None), ({"notes": {"5": 1.5}}, None),
    ({"notes": {"5": True}}, None), ({"coins": {"1": 1, "1.00": 1}}, None),
    ({"notes": {"5": 2}}, 9), (None, float("nan")), (None, float("inf")),
    (None, -1), (None, 1.001)])
def test_invalid_cash_counts_rejected(count, total):
    with pytest.raises(ValueError): cash_count_cents(count, total)


def test_cash_counts_are_exact():
    assert cash_count_cents({"coins": {"0.01": 3, "0.10": 3}, "notes": {"5": 2}}, 10.33) == 1033


def test_late_timestamp_is_assigned_to_exactly_one_closure(db_session):
    user, product = seed(db_session)
    first = ZBonService(db_session).create_zbon(created_by_name=user.username)
    result = sale(db_session, user, product)
    transaction = db_session.get(Transaction, result["id"])
    transaction.created_at = datetime.fromisoformat(first["period_end"]) - timedelta(hours=1)
    db_session.commit()
    second = ZBonService(db_session).create_zbon(created_by_name=user.username)
    third = ZBonService(db_session).create_zbon(created_by_name=user.username)
    assert second["summary"]["transaction_count"] == 1
    assert third["summary"]["transaction_count"] == 0
    db_session.expire_all()
    assert transaction.zbon_history_id == second["history_id"]


def test_receipt_counter_spans_cash_and_sale_and_peek_does_not_allocate(db_session):
    user, product = seed(db_session)
    first = CashEntryRepository(db_session).create(CashEntryType.DEPOSIT, 100, "Test", user.id)
    peek = next_receipt_number(db_session, allocate=False)
    assert next_receipt_number(db_session, allocate=False) == peek
    result = sale(db_session, user, product)
    assert result["receipt_number"] == first.receipt_number + 1 == peek


def make_app(db):
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="isolated-stage1112")
    app.dependency_overrides[get_db] = lambda: db
    app.include_router(api.router)
    app.include_router(deckel_api.router)
    app.include_router(member_api.router)
    @app.get("/test-session/{user_id}")
    async def login(user_id: int, request: Request):
        request.session.update(user_id=user_id, session_version=1)
        return {}
    return app


@pytest.mark.parametrize("kind", ["sale", "deckel"])
def test_http_replay_after_lost_response_and_fingerprint_conflict(db_session, kind):
    user, product = seed(db_session)
    app = make_app(db_session)
    key = str(uuid.uuid4())
    body = {"items": [{"product_id": product.id, "quantity": 1, "unit_price_cents": 500}]}
    if kind == "sale":
        path = "/api/transactions/sale"
        body.update(user_id=user.id, payment_method="CASH", cash_received_cents=500)
    else:
        path = "/api/deckel"
        body["name"] = "Replay Test"
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            await client.get(f"/test-session/{user.id}")
            original = await client.post(path, json=body, headers={"Idempotency-Key": key})
            assert original.status_code == 201, original.text
            # Treat the first response as lost; both status lookup and resend recover it.
            status = await client.get(f"/api/transactions/operations/{key}")
            assert status.json()["response"] == original.json()
            replay = await client.post(path + "/", json=body, headers={"Idempotency-Key": key})
            assert replay.json() == original.json()
            assert replay.headers["Idempotency-Replayed"] == "true"
            body["items"][0]["quantity"] = 2
            conflict = await client.post(path, json=body, headers={"Idempotency-Key": key})
            assert conflict.status_code == 409
    asyncio.run(run())
    assert db_session.query(BookingOperation).count() == 1
    assert db_session.query(Transaction).count() == (1 if kind == "sale" else 0)
    assert product.stock_quantity == (19 if kind == "sale" else 20)


def test_result_storage_failure_rolls_back_sale(db_session, monkeypatch):
    user, product = seed(db_session)
    original = db_session.add
    def fail_result(value):
        if isinstance(value, BookingOperation): raise RuntimeError("simulated journal failure")
        return original(value)
    monkeypatch.setattr(db_session, "add", fail_result)
    async def run():
        app = make_app(db_session)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test") as client:
            await client.get(f"/test-session/{user.id}")
            response = await client.post("/api/transactions/sale", headers={"Idempotency-Key": str(uuid.uuid4())},
                json={"user_id": user.id, "payment_method": "CASH", "cash_received_cents": 500,
                      "items": [{"product_id": product.id, "quantity": 1, "unit_price_cents": 500}]})
            assert response.status_code == 500
    asyncio.run(run())
    db_session.expire_all()
    assert db_session.query(Transaction).count() == 0
    assert product.stock_quantity == 20


def test_parallel_receipts_and_closures(pg_engine):
    Base.metadata.create_all(pg_engine)
    factory = sessionmaker(bind=pg_engine, expire_on_commit=False)
    with factory() as db:
        user, _ = seed(db)
        uid = user.id
        # Initialize settings before workers to isolate the closure/booking protocol.
        from app.services.app_settings_service import AppSettingsService
        AppSettingsService(db).get_or_create_settings()
    def worker(index):
        with factory() as db:
            if index % 3 == 0:
                return ZBonService(db).create_zbon(created_by_name="Test")["history_id"]
            return CashEntryRepository(db).create(CashEntryType.DEPOSIT, 100, "Test", uid).receipt_number
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(worker, range(18)))
    with factory() as db:
        ZBonService(db).create_zbon(created_by_name="Final")
        entries = db.query(CashEntry).all()
        assert len({entry.receipt_number for entry in entries}) == 12
        assert all(entry.zbon_history_id is not None for entry in entries)
        closures = db.query(ZBonHistory).all()
        assert len({z.sequence_number for z in closures}) == 7
        assert sum(z.cash_deposits_cents for z in closures) == 1200


def test_recharge_replay_is_owned_by_original_user(db_session, monkeypatch):
    from app.models import User, UserRole, BalanceLog
    user, _ = seed(db_session)
    person = Member(member_number=1, name="Mara Test", first_name="Mara", last_name="Test", balance_cents=0)
    other = User(username="Other", password_hash="unused", role=UserRole.TOP_ADMIN)
    db_session.add_all([person, other]); db_session.commit()
    monkeypatch.setattr(member_api, "require_password_confirmation", lambda *args: None)
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=make_app(db_session)), base_url="http://test") as client:
            key = str(uuid.uuid4())
            await client.get(f"/test-session/{user.id}")
            path = f"/api/members/{person.id}/recharge"
            body = {"amount_cents": 500, "auth_password": "not-stored"}
            original = await client.post(path, json=body, headers={"Idempotency-Key": key})
            assert original.status_code == 200, original.text
            body["auth_password"] = "new-confirmation"
            replay = await client.post(path, json=body, headers={"Idempotency-Key": key})
            assert replay.json() == original.json()
            await client.get(f"/test-session/{other.id}")
            assert (await client.get(f"/api/transactions/operations/{key}")).status_code == 404
            assert (await client.post(path, json=body, headers={"Idempotency-Key": key})).status_code == 409
    asyncio.run(run())
    assert person.balance_cents == 500
    assert db_session.query(Transaction).count() == db_session.query(BalanceLog).count() == 1
    assert "not-stored" not in db_session.query(BookingOperation).one().response_json


def test_zbon_resolves_names_validates_difference_and_replays(db_session, monkeypatch):
    user, _ = seed(db_session)
    person = Member(member_number=1, name="Mara Test", first_name="Mara", last_name="Test", balance_cents=0)
    db_session.add(person); db_session.commit()
    monkeypatch.setattr(api, "require_password_confirmation", lambda *args: None)
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=make_app(db_session)), base_url="http://test") as client:
            await client.get(f"/test-session/{user.id}")
            body = {"created_by_id": f"user-{user.id}", "cash_counted_by_member_id": person.id,
                    "cash_count_total": 0.03, "cash_count": {"coins": {"0.01": 3}}, "auth_password": "test"}
            invalid = await client.post("/api/transactions/zbon/create", json={**body, "created_by_id": "user-99999"})
            assert invalid.status_code == 400
            missing_reason = await client.post("/api/transactions/zbon/create", json=body)
            assert missing_reason.status_code == 400
            body["difference_reason"] = "Testabweichung"
            key = str(uuid.uuid4())
            original = await client.post("/api/transactions/zbon/create", json=body, headers={"Idempotency-Key": key})
            assert original.status_code == 200, original.text
            assert original.json()["created_by_name"] == user.username
            assert original.json()["cash_counted_by_name"] == person.name
            assert original.json()["summary"]["cash_counted_cents"] == 3
            replay = await client.post("/api/transactions/zbon/create", json=body, headers={"Idempotency-Key": key})
            assert replay.json() == original.json()
    asyncio.run(run())
    assert db_session.query(ZBonHistory).count() == 1


def test_parallel_http_same_key_has_one_result(pg_engine, monkeypatch):
    from app.core import booking_route
    Base.metadata.create_all(pg_engine)
    factory = sessionmaker(bind=pg_engine, autoflush=False)
    monkeypatch.setattr(booking_route, "SessionLocal", factory)
    with factory() as db:
        user, product = seed(db)
        uid, pid = user.id, product.id
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="isolated-parallel-replay")
    app.include_router(api.router)
    @app.get("/test-session")
    async def login(request: Request):
        request.session.update(user_id=uid, session_version=1)
        return {}
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            await client.get("/test-session")
            key = str(uuid.uuid4())
            body = {"user_id": uid, "payment_method": "CASH", "cash_received_cents": 500,
                    "items": [{"product_id": pid, "quantity": 1, "unit_price_cents": 500}]}
            replies = await asyncio.gather(*[client.post("/api/transactions/sale", json=body,
                headers={"Idempotency-Key": key}) for _ in range(4)])
            assert all(response.status_code == 201 for response in replies)
            assert len({response.json()["id"] for response in replies}) == 1
    asyncio.run(run())
    with factory() as db:
        assert db.query(Transaction).count() == db.query(BookingOperation).count() == 1


def test_closure_upgrade_preserves_legacy_receipts_and_archive(pg_engine):
    from sqlalchemy import text
    from app.core.closure_migration import migrate_closures
    Base.metadata.create_all(pg_engine)
    with sessionmaker(bind=pg_engine)() as db:
        user, product = seed(db)
        result = sale(db, user, product)
        report = ZBonService(db).create_zbon(created_by_name="Historical")
        receipt = result["receipt_number"]
        report_id = report["history_id"]
        original_html = report["report_content"]
    with pg_engine.begin() as conn:
        conn.execute(text("ALTER TABLE transactions DROP COLUMN zbon_history_id"))
        conn.execute(text("ALTER TABLE cash_entries DROP COLUMN zbon_history_id"))
    migrate_closures(pg_engine)
    migrate_closures(pg_engine)
    with sessionmaker(bind=pg_engine)() as db:
        transaction = db.query(Transaction).one()
        assert transaction.receipt_number == receipt
        assert transaction.zbon_history_id == report_id
        assert db.get(ZBonHistory, report_id).report_content == original_html
        assert next_receipt_number(db, allocate=False) == receipt + 1
