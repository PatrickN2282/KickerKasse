"""Audit 06/07: real HTTP boundaries, import preflight and stock history."""
import asyncio
import csv
import io
import json

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.api import product as product_api
from app.core import get_db
from app.models import AuditLog, Member, Product, ProductStockCorrectionLog, User, UserRole
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.member import MemberCreate, MemberUpdate
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.import_export_service import ImportExportService, SECTION_HEADERS
from app.services.member_service import MemberService
from app.services.product_service import ProductService


@pytest.fixture()
def product(db_session):
    record = Product(name="Wasser", price_cents=200, stock_quantity=25)
    db_session.add(record)
    db_session.commit()
    return record


@pytest.fixture()
def request_product(db_session):
    app = FastAPI()
    app.include_router(product_api.router)
    user = User(username="stock-admin", password_hash="unused", role=UserRole.ADMIN, is_active=True)
    db_session.add(user)
    db_session.commit()

    @app.middleware("http")
    async def session(request, call_next):
        request.scope["session"] = {"user_id": user.id, "session_version": user.session_version}
        return await call_next(request)

    async def isolated_db():
        yield db_session

    app.dependency_overrides[get_db] = isolated_db

    def send(method, path, payload=None):
        async def run():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                return await client.request(method, path, json=payload)
        return asyncio.run(run())
    return send


@pytest.mark.parametrize("payload", [
    {"price_cents": -1}, {"price_cents": 2**31}, {"member_price_cents": -1},
    {"price_cents": None}, {"name": None}, {"name": " \t "}, {"name": "a" * 121},
    {"description": "a" * 256}, {"minimum_stock_quantity": -1},
    {"stock_quantity": 25}, {"stock_quantity": None}, {"is_active": None},
])
def test_bad_update_is_rejected_before_commit_and_list_stays_usable(db_session, product, request_product, payload):
    response = request_product("PUT", f"/api/products/{product.id}", {"warengruppe": "changed", **payload})
    assert response.status_code == 422, response.text
    db_session.refresh(product)
    assert (product.name, product.price_cents, product.stock_quantity, product.warengruppe) == ("Wasser", 200, 25, None)
    assert db_session.query(AuditLog).count() == 0
    assert request_product("GET", "/api/products").status_code == 200


def test_profile_save_keeps_stock_changed_since_opening(db_session, product, request_product):
    opened = request_product("GET", f"/api/products/{product.id}").json()
    assert opened["stock_quantity"] == 25
    # A checkout has persisted its stock deduction after the form was loaded.
    db_session.execute(text("UPDATE products SET stock_quantity=24 WHERE id=:id"), {"id": product.id})
    db_session.commit()
    response = request_product("PUT", f"/api/products/{product.id}", {"name": "  Wasser neu  ", "price_cents": 0, "member_price_cents": 0})
    assert response.status_code == 200, response.text
    assert response.json()["stock_quantity"] == 24
    assert response.json()["name"] == "Wasser neu"
    assert response.json()["member_price_cents"] == 0


def test_stock_mode_requires_zero_and_corrections_have_history(db_session, product, request_product):
    response = request_product("PUT", f"/api/products/{product.id}", {"name": "changed", "is_unlimited_stock": True})
    assert response.status_code == 400
    db_session.refresh(product)
    assert product.name == "Wasser" and product.stock_quantity == 25
    response = request_product("POST", f"/api/products/{product.id}/stock-correction", {"new_stock_quantity": 0, "reason": "Bestandsart wechseln"})
    assert response.status_code == 200, response.text
    log = db_session.query(ProductStockCorrectionLog).one()
    assert (log.old_stock_quantity, log.new_stock_quantity, log.change_quantity, log.executed_by_username) == (25, 0, -25, "stock-admin")
    assert request_product("PUT", f"/api/products/{product.id}", {"is_unlimited_stock": True}).status_code == 200
    assert request_product("POST", f"/api/products/{product.id}/adjust-stock?quantity=3").status_code == 400
    assert request_product("PUT", f"/api/products/{product.id}", {"is_unlimited_stock": False}).status_code == 200
    assert request_product("POST", f"/api/products/{product.id}/adjust-stock?quantity=3").status_code == 200
    audit = db_session.query(AuditLog).filter_by(action="RESTOCKED").one()
    assert json.loads(audit.new_value)["stock_quantity"] == 3


@pytest.mark.parametrize("quantity", [-1, 0, 2**31])
def test_restock_cannot_bypass_correction_or_overflow(db_session, product, request_product, quantity):
    response = request_product("POST", f"/api/products/{product.id}/adjust-stock?quantity={quantity}")
    assert response.status_code == 400
    db_session.refresh(product)
    assert product.stock_quantity == 25


@pytest.mark.parametrize("schema,data", [
    (ProductCreate, {"name": " ", "price_cents": 0}),
    (ProductCreate, {"name": "A", "price_cents": -1}),
    (CategoryCreate, {"name": " ", "description": "valid"}),
    (CategoryUpdate, {"name": None}),
    (CategoryUpdate, {"description": "a" * 256}),
    (CategoryUpdate, {"display_order": 2**31}),
    (MemberCreate, {"first_name": "a" * 80, "last_name": "b" * 80}),
    (MemberUpdate, {"first_name": None}),
    (MemberUpdate, {"last_name": " "}),
    (MemberUpdate, {"phone": "a" * 21}),
    (MemberUpdate, {"email": "a" * 121}),
    (MemberUpdate, {"membership_number": "a" * 51}),
])
def test_shared_input_boundaries(schema, data):
    with pytest.raises(ValidationError):
        schema.model_validate(data)


def test_partial_member_name_update_checks_combined_persisted_name(db_session):
    member = Member(member_number=1, name="A B", first_name="a" * 70, last_name="B")
    db_session.add(member)
    db_session.commit()
    with pytest.raises(ValueError, match="120"):
        MemberService(db_session).update_member(member.id, last_name="b" * 60)
    db_session.refresh(member)
    assert member.last_name == "B"
    assert MemberUpdate(email="  ", phone="  ").model_dump(exclude_unset=True) == {"email": None, "phone": None}


def csv_bytes(section, rows):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=SECTION_HEADERS[section])
    writer.writeheader()
    for row in rows:
        writer.writerow({"dataset": section, **row})
    return buffer.getvalue().encode()


@pytest.mark.parametrize("section,bad", [
    ("products", {"price_cents": -1}), ("products", {"stock_quantity": -1}),
    ("products", {"member_price_cents": "abc"}), ("products", {"tax_rate": "NaN"}),
    ("products", {"tax_rate": "inf"}), ("products", {"name": "a" * 121}),
    ("products", {"is_active": "perhaps"}), ("products", {"id": "abc"}),
    ("products", {"price_cents": 2**31}), ("members", {"balance_cents": -1}),
    ("members", {"phone": "a" * 21}), ("members", {"first_name": "a" * 80, "last_name": "b" * 80}),
    ("categories", {"name": "  "}), ("categories", {"description": "a" * 256}),
])
def test_import_preflight_rejects_entire_file_before_replacement(db_session, product, monkeypatch, section, bad):
    valid = {"products": {"name": "Valid", "price_cents": 0, "stock_quantity": 0},
             "members": {"first_name": "Mara", "last_name": "Test", "balance_cents": 0},
             "categories": {"name": "Valid", "display_order": 0, "is_active_in_kasse": True}}[section]
    service = ImportExportService(db_session)
    def forbidden(*args):
        pytest.fail("Replacement/media must not run before complete validation")
    monkeypatch.setattr(service, "_replace_selected_sections", forbidden)
    monkeypatch.setattr(service, "_store_media_file", forbidden)
    with pytest.raises(HTTPException) as exc:
        service.import_sections(f"{section}.csv", csv_bytes(section, [valid, {**valid, **bad}]), replace_sections=[section])
    assert exc.value.status_code == 400
    assert "Zeile 3" in exc.value.detail
    assert db_session.query(Product).one().name == "Wasser"


def test_valid_zero_price_import_and_export_roundtrip(db_session):
    service = ImportExportService(db_session)
    service.import_sections("products.csv", csv_bytes("products", [{"name": "  Wasser  ", "price_cents": 0, "member_price_cents": 0, "stock_quantity": 0}]))
    product = db_session.query(Product).one()
    assert (product.name, product.price_cents, product.member_price_cents) == ("Wasser", 0, 0)
    payload, _, filename = service.export_sections(["products"], False)
    service.import_sections(filename, payload)
    assert db_session.query(Product).count() == 1


@pytest.mark.parametrize("assignment", ["price_cents=-1", "member_price_cents=-1", "stock_quantity=-1", "minimum_stock_quantity=-1", "tax_rate=101", "name=' '"])
def test_database_rejects_invalid_products(db_session, product, assignment):
    with pytest.raises(IntegrityError):
        db_session.execute(text(f"UPDATE products SET {assignment}"))
        db_session.commit()
    db_session.rollback()
    db_session.refresh(product)
    assert product.price_cents == 200 and product.stock_quantity == 25
