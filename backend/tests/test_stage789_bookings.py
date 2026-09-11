"""Rollback and association checks on SQLite and real PostgreSQL."""
import asyncio
from datetime import datetime

import pytest
import httpx
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.core.db_migration import run_migrations
from app.models import User, UserRole, Product, Transaction, Deckel, Voucher, GuestListEntry, ClubAccountEntry, AuditLog
from app.models.transaction import VoucherRedemption
from app.api.transaction import create_sale
from app.api.deckel import DeckelCreatePayload
from app.schemas.transaction import TransactionCreate
from app.services.deckel_service import DeckelService
from app.services.voucher_service import VoucherService
from app.services.material_account_service import MaterialAccountService
from app.services.audit_log_service import AuditLogService
from app.repositories import ProductRepository, TransactionRepository
from app.core import get_db
from app.api import transaction as transaction_api, guest_list as guest_api, deckel as deckel_api


@pytest.fixture(params=["sqlite", "postgres"])
def booking_db(request):
    if request.param == "sqlite":
        yield request.getfixturevalue("db_session")
    else:
        engine = request.getfixturevalue("pg_engine")
        assert run_migrations(engine)
        with Session(engine, autoflush=False) as db:
            yield db


def seed(db, **product_fields):
    user = User(username="booking-test", role=UserRole.TOP_ADMIN, password_hash="test-unused")
    product = Product(name="Testartikel", price_cents=500, stock_quantity=20, **product_fields)
    db.add_all([user, product]); db.commit()
    return user, product


def sale(db, user, product, **kwargs):
    items = kwargs.pop("items", [{"product_id": product.id, "quantity": 1, "unit_price_cents": 500}])
    kwargs.setdefault("cash_received_cents", 2000)
    payload = TransactionCreate(user_id=user.id, payment_method="CASH", items=items, **kwargs)
    request = Request({"type": "http", "method": "POST", "path": "/api/transactions/sale", "headers": [],
                       "session": {"user_id": user.id, "session_version": user.session_version}})
    return asyncio.run(create_sale(payload, request, db))


def fail(*args, **kwargs):
    raise RuntimeError("simulated booking failure")


@pytest.mark.parametrize("failure", ["transaction", "stock", "material", "audit", "commit"])
def test_deckel_failure_rolls_back_every_step(booking_db, monkeypatch, failure):
    db = booking_db
    user, product = seed(db)
    deckel = DeckelService(db).create_deckel("Testtisch", user.id, [{"product_id": product.id, "quantity": 2, "unit_price_cents": 500}])
    deckel_id, product_id = deckel.id, product.id
    with monkeypatch.context() as patch:
        if failure == "transaction": patch.setattr(TransactionRepository, "create", fail)
        if failure == "stock": patch.setattr(ProductRepository, "deduct_stock", lambda *a, **k: False)
        if failure == "material": patch.setattr(MaterialAccountService, "record_sale_transaction", fail)
        if failure == "audit": patch.setattr(AuditLogService, "log", fail)
        if failure == "commit": patch.setattr(db, "commit", fail)
        with pytest.raises((ValueError, RuntimeError)):
            DeckelService(db).settle(deckel_id, user, 1000)
    assert db.get(Deckel, deckel_id) is not None
    assert db.get(Product, product_id).stock_quantity == 20
    assert db.query(Transaction).count() == 0
    assert db.query(AuditLog).count() == 0


def test_deckel_settlement_keeps_saved_variable_price_and_only_pays_once(booking_db):
    db = booking_db
    user, product = seed(db, is_variable_price=True)
    deckel = DeckelService(db).create_deckel("Testtisch", user.id, [{"product_id": product.id, "quantity": 2, "unit_price_cents": 725}])
    deckel_id = deckel.id
    product.price_cents = 900; db.commit()
    transaction = DeckelService(db).settle(deckel_id, user, 2000, 50)
    assert transaction.total_amount_cents == 1450 and transaction.change_given_cents == 500
    assert product.stock_quantity == 18 and transaction.performed_by_username == user.username
    with pytest.raises(LookupError): DeckelService(db).settle(deckel_id, user, 2000)
    assert db.query(Transaction).count() == 1


@pytest.mark.parametrize("special", ["guest", "prepaid"])
def test_deckel_rejects_unsupported_products(booking_db, special):
    db = booking_db
    user, product = seed(db, **({"requires_guest_list": True} if special == "guest" else {"description": "VERZEHRKARTE:500"}))
    with pytest.raises(ValueError):
        DeckelService(db).create_deckel("Test", user.id, [{"product_id": product.id, "quantity": 1, "unit_price_cents": 500}])
    assert db.query(Deckel).count() == 0


@pytest.mark.parametrize("field", ["member_id", "guests", "voucher_redemptions"])
def test_deckel_rejects_unrepresented_context(field):
    with pytest.raises(ValidationError):
        DeckelCreatePayload.model_validate({"name": "Test", "items": [], field: 1})


@pytest.mark.parametrize("kind", ["gift", "prepaid"])
@pytest.mark.parametrize("failure", ["creation", "audit", "commit"])
def test_voucher_creation_is_atomic(booking_db, monkeypatch, kind, failure):
    db = booking_db
    user, _ = seed(db)
    service = VoucherService(db)
    with monkeypatch.context() as patch:
        if failure == "creation":
            original = service.repository.create
            calls = []
            def create(**kwargs):
                result = original(**kwargs)
                calls.append(result.id)
                if kind == "gift" or len(calls) == 2: fail()
                return result
            patch.setattr(service.repository, "create", create)
        if failure == "audit": patch.setattr(AuditLogService, "log", fail)
        if failure == "commit": patch.setattr(db, "commit", fail)
        with pytest.raises(RuntimeError):
            if kind == "gift": service.create_gift_voucher(500, "PROMOTION", user.id)
            else: service.create_prepaid_vouchers(500, user.id, quantity=3)
    assert db.query(Voucher).count() == 0
    assert db.query(Transaction).count() == 0
    assert db.query(ClubAccountEntry).count() == 0
    assert db.query(AuditLog).count() == 0
    assert db.query(Product).count() == 1


def test_multiple_vouchers_record_exact_partial_amounts(booking_db):
    db = booking_db
    user, product = seed(db)
    service = VoucherService(db)
    vouchers = [service.create_gift_voucher(200, "PROMOTION", user.id) for _ in range(3)]
    result = sale(db, user, product, voucher_redemptions=[{"voucher_number": v.voucher_code} for v in vouchers])
    assert len(result["voucher_code"]) > 20 and result["total_amount_cents"] == 0
    assert [db.get(Voucher, v.id).remaining_value_cents for v in vouchers] == [0, 0, 100]
    rows = db.query(VoucherRedemption).order_by(VoucherRedemption.id).all()
    assert [r.amount_cents for r in rows] == [200, 200, 100]
    assert all(r.transaction_id == result["id"] for r in rows)


def test_duplicate_voucher_alias_is_rejected_without_redemption(booking_db):
    db = booking_db
    user, product = seed(db)
    voucher = VoucherService(db).create_gift_voucher(200, "PROMOTION", user.id)
    with pytest.raises(HTTPException):
        sale(db, user, product, voucher_redemptions=[{"voucher_number": voucher.voucher_code}, {"voucher_number": str(voucher.voucher_number)}])
    assert db.query(VoucherRedemption).count() == 0
    assert db.get(Voucher, voucher.id).remaining_value_cents == 200


def test_variable_guest_lines_keep_prices_names_and_exact_sale_positions(booking_db):
    db = booking_db
    user, product = seed(db, requires_guest_list=True, is_variable_price=True)
    result = sale(db, user, product, items=[
        {"product_id": product.id, "quantity": 1, "unit_price_cents": amount,
         "guests": [{"guest_first_name": name, "guest_last_name": "Test"}]} for amount, name in [(125, "Mara"), (275, "Kim")]])
    assert result["total_amount_cents"] == 400
    entries = db.query(GuestListEntry).order_by(GuestListEntry.id).all()
    assert [e.guest_first_name for e in entries] == ["Mara", "Kim"]
    assert [e.transaction_item_id for e in entries] == [i.id for i in result["items"]]
    assert all(e.transaction_id == result["id"] for e in entries)
    assert product.stock_quantity == 18


@pytest.mark.parametrize("invalid", ["missing", "extra", "member", "wrong_product", "internal"])
def test_guest_validation_prevents_entire_sale(booking_db, invalid):
    db = booking_db
    user, product = seed(db, requires_guest_list=invalid != "wrong_product")
    guests = [{"guest_first_name": "Mara"}]
    if invalid == "missing": guests = []
    if invalid == "extra": guests *= 2
    if invalid == "member": guests[0]["member_id"] = 99999
    with pytest.raises(HTTPException):
        sale(db, user, product, items=[{"product_id": product.id, "quantity": 1, "unit_price_cents": 500,
                                     "is_internal_material": invalid == "internal", "guests": guests}])
    assert db.query(Transaction).count() == 0 and db.query(GuestListEntry).count() == 0
    assert product.stock_quantity == 20


def test_guest_insert_failure_rolls_back_stock_payment_and_guests(booking_db, monkeypatch):
    db = booking_db
    user, product = seed(db, requires_guest_list=True)
    original = db.add
    def add(value):
        if isinstance(value, GuestListEntry): fail()
        return original(value)
    with monkeypatch.context() as patch:
        patch.setattr(db, "add", add)
        with pytest.raises(RuntimeError):
            sale(db, user, product, items=[{"product_id": product.id, "quantity": 1, "unit_price_cents": 500,
                                         "guests": [{"guest_first_name": "Mara"}]}])
    assert db.query(Transaction).count() == 0 and db.query(GuestListEntry).count() == 0
    assert product.stock_quantity == 20


@pytest.mark.parametrize("case", ["guest_sale", "legacy_guest", "forged_guest", "member_deckel"])
def test_http_booking_contract(db_session, case):
    user, product = seed(db_session, requires_guest_list=True)
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="only-isolated-booking-test")
    app.dependency_overrides[get_db] = lambda: db_session
    for router in [transaction_api.router, guest_api.router, deckel_api.router]:
        app.include_router(router)
    from fastapi import Request as HttpRequest
    @app.get("/test-session")
    async def establish(request: HttpRequest):
        request.session.update(user_id=user.id, session_version=user.session_version)
        return {}
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            await client.get("/test-session")
            if case == "legacy_guest":
                response = await client.post("/api/guest-list/entries", json={"entries": [{"product_id": product.id, "guest_first_name": "Mara", "transaction_id": 999}]})
                assert response.status_code == 409
            elif case == "member_deckel":
                response = await client.post("/api/deckel", json={"name": "Test", "member_id": 1, "items": []})
                assert response.status_code == 422
            else:
                guest = {"guest_first_name": "Mara"}
                if case == "forged_guest": guest["transaction_id"] = 999
                response = await client.post("/api/transactions/sale", json={"user_id": user.id, "payment_method": "CASH", "cash_received_cents": 500,
                    "items": [{"product_id": product.id, "quantity": 1, "unit_price_cents": 500, "guests": [guest]}]})
                assert response.status_code == (201 if case == "guest_sale" else 422), response.text
                if case == "guest_sale":
                    entries = await client.get("/api/guest-list/entries")
                    entry = entries.json()[0]["entries"][0]
                    assert entry["transaction_id"] == response.json()["id"]
                    assert entry["transaction_item_id"] == response.json()["items"][0]["id"]
    asyncio.run(run())
    if case != "guest_sale":
        assert db_session.query(GuestListEntry).count() == 0
        assert db_session.query(Transaction).count() == 0
