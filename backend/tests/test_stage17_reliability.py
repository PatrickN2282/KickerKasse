"""Etappe 17 and first-start regression checks; prepared for the combined final run."""
import asyncio

import pytest
from fastapi import HTTPException

from app.api.auth import get_setup_status
from app.api.transaction import create_sale
from app.models import Transaction, User, UserRole
from app.schemas.transaction import TransactionCreate
from app.services.app_settings_service import AppSettingsService
from .test_sale_checkout_pricing import create_member, create_product, create_user, request_for


def ensure_top_admin(db_session):
    db_session.add(User(
        username="setup-owner",
        password_hash="test-unused",
        role=UserRole.TOP_ADMIN,
        is_active=True,
    ))
    db_session.commit()


def test_empty_database_reports_setup_even_if_optional_settings_are_not_ready(db_session, monkeypatch):
    monkeypatch.setattr(
        AppSettingsService,
        "get_email_settings",
        lambda _self: (_ for _ in ()).throw(RuntimeError("settings unavailable")),
    )

    status = asyncio.run(get_setup_status(db_session))

    assert status.setup_required is True
    assert status.top_admin_exists is False


def test_changed_catalog_price_requires_a_second_confirmation_without_booking(db_session):
    ensure_top_admin(db_session)
    user = create_user(db_session)
    product = create_product(db_session, price_cents=700)
    payload = TransactionCreate(
        user_id=user.id,
        payment_method="CASH",
        cash_received_cents=1000,
        expected_total_amount_cents=500,
        items=[{"product_id": product.id, "quantity": 1, "unit_price_cents": 500}],
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(create_sale(payload, request_for(user.id), db_session))

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "SALE_CONFIRMATION_CHANGED"
    assert exc_info.value.detail["actual_total_amount_cents"] == 700
    assert db_session.query(Transaction).count() == 0
    db_session.refresh(product)
    assert product.stock_quantity == 10


def test_changed_member_balance_requires_a_second_confirmation_without_booking(db_session):
    ensure_top_admin(db_session)
    user = create_user(db_session)
    member = create_member(db_session, balance_cents=200)
    product = create_product(db_session, price_cents=500, member_price_cents=500)
    payload = TransactionCreate(
        user_id=user.id,
        member_id=member.id,
        payment_method="BALANCE",
        expected_total_amount_cents=0,
        expected_member_balance_cents=1000,
        items=[{"product_id": product.id, "quantity": 1, "unit_price_cents": 500}],
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(create_sale(payload, request_for(user.id), db_session))

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["actual_member_balance_cents"] == 200
    assert exc_info.value.detail["actual_total_amount_cents"] == 300
    assert db_session.query(Transaction).count() == 0
