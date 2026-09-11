import asyncio

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api.transaction import create_sale
from app.constants import INTERNAL_MATERIAL_CATEGORY_NAME
from app.models import Category, MaterialAccountEntry, Member, Product, User, UserRole
from app.schemas.transaction import TransactionCreate


def request_for(user_id: int) -> Request:
    return Request({
        "type": "http",
        "method": "POST",
        "path": "/api/transactions/sale",
        "headers": [],
        "session": {"user_id": user_id, "session_version": 1},
    })


def create_user(db_session) -> User:
    user = User(
        username="checkout-user",
        password_hash="test",
        role=UserRole.VERKAUF,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def create_member(db_session, *, balance_cents=0, has_discount=True) -> Member:
    member = Member(
        member_number=1,
        name="Mara Mitglied",
        first_name="Mara",
        last_name="Mitglied",
        balance_cents=balance_cents,
        has_discount=has_discount,
    )
    db_session.add(member)
    db_session.commit()
    return member


def create_product(db_session, name="Ball", **overrides) -> Product:
    values = {
        "name": name,
        "price_cents": 500,
        "member_price_cents": 350,
        "is_discountable": True,
        "stock_quantity": 10,
        "is_unlimited_stock": False,
        "is_variable_price": False,
        "opens_small_parts_drawer": False,
        "is_active": True,
    }
    values.update(overrides)
    product = Product(**values)
    db_session.add(product)
    db_session.commit()
    return product


def checkout(db_session, user, *, items, payment_method="CASH", member_id=None,
             cash_received_cents=0, balance_discount_cents=0):
    payload = TransactionCreate(
        user_id=user.id,
        payment_method=payment_method,
        member_id=member_id,
        cash_received_cents=cash_received_cents,
        balance_discount_cents=balance_discount_cents,
        items=items,
    )
    return asyncio.run(create_sale(payload, request_for(user.id), db_session))


def test_reported_internal_material_case_books_zero_and_material_value(db_session):
    user = create_user(db_session)
    category = Category(name=INTERNAL_MATERIAL_CATEGORY_NAME)
    ball = create_product(db_session, opens_small_parts_drawer=True)
    ball.categories.append(category)
    db_session.commit()

    result = checkout(db_session, user, items=[{
        "product_id": ball.id,
        "quantity": 1,
        "unit_price_cents": 0,
        "is_internal_material": True,
        "note": "Ligabetrieb",
    }])

    entry = db_session.query(MaterialAccountEntry).one()
    assert result["total_amount_cents"] == 0
    assert result["items"][0].unit_price_cents == 0
    assert result["items"][0].total_price_cents == 0
    assert result["cash_received_cents"] == 0
    assert result["change_given_cents"] == 0
    assert result["drawer_targets"] == ["small_parts"]
    assert entry.amount_cents == 500
    assert entry.reason == "1× Ball"
    assert ball.stock_quantity == 9


def test_internal_material_uses_eligible_member_price_only_for_material_account(db_session):
    user = create_user(db_session)
    member = create_member(db_session)
    category = Category(name=INTERNAL_MATERIAL_CATEGORY_NAME)
    ball = create_product(db_session)
    ball.categories.append(category)
    db_session.commit()

    result = checkout(db_session, user, member_id=member.id, items=[{
        "product_id": ball.id,
        "quantity": 2,
        "unit_price_cents": 999,
        "is_internal_material": True,
    }])

    assert result["total_amount_cents"] == 0
    assert result["items"][0].unit_price_cents == 0
    assert db_session.query(MaterialAccountEntry).one().amount_cents == 700


def test_fixed_member_price_is_server_authoritative(db_session):
    user = create_user(db_session)
    member = create_member(db_session)
    ball = create_product(db_session)

    result = checkout(
        db_session,
        user,
        member_id=member.id,
        cash_received_cents=350,
        items=[{"product_id": ball.id, "quantity": 1, "unit_price_cents": 1}],
    )

    assert result["items"][0].unit_price_cents == 350
    assert result["total_amount_cents"] == 350
    assert result["drawer_targets"] == ["main"]


def test_variable_price_is_the_cashier_entered_price(db_session):
    user = create_user(db_session)
    donation = create_product(
        db_session,
        name="Spende",
        price_cents=100,
        member_price_cents=50,
        is_variable_price=True,
        is_unlimited_stock=True,
    )

    result = checkout(
        db_session,
        user,
        cash_received_cents=225,
        items=[{"product_id": donation.id, "quantity": 1, "unit_price_cents": 225}],
    )

    assert result["items"][0].unit_price_cents == 225
    assert result["total_amount_cents"] == 225
    assert result["drawer_targets"] == ["main"]


def test_mixed_internal_and_regular_sale_opens_both_required_drawers(db_session):
    user = create_user(db_session)
    category = Category(name=INTERNAL_MATERIAL_CATEGORY_NAME)
    ball = create_product(db_session, opens_small_parts_drawer=True)
    ball.categories.append(category)
    drink = create_product(db_session, name="Getränk", price_cents=250, member_price_cents=None)
    db_session.commit()

    result = checkout(db_session, user, cash_received_cents=300, items=[
        {
            "product_id": ball.id,
            "quantity": 1,
            "unit_price_cents": 500,
            "is_internal_material": True,
        },
        {"product_id": drink.id, "quantity": 1, "unit_price_cents": 1},
    ])

    assert [item.unit_price_cents for item in result["items"]] == [0, 250]
    assert result["total_amount_cents"] == 250
    assert result["change_given_cents"] == 50
    assert result["drawer_targets"] == ["main", "small_parts"]


def test_balance_payment_uses_no_cash_drawer(db_session):
    user = create_user(db_session)
    member = create_member(db_session, balance_cents=1000)
    ball = create_product(db_session)

    result = checkout(
        db_session,
        user,
        payment_method="BALANCE",
        member_id=member.id,
        cash_received_cents=None,
        items=[{"product_id": ball.id, "quantity": 1, "unit_price_cents": 999}],
    )

    db_session.refresh(member)
    assert result["total_amount_cents"] == 0
    assert result["balance_applied_cents"] == 350
    assert result["drawer_targets"] == []
    assert member.balance_cents == 650


def test_internal_flag_is_rejected_for_product_outside_reserved_category(db_session):
    user = create_user(db_session)
    ball = create_product(db_session)

    with pytest.raises(HTTPException) as error:
        checkout(db_session, user, items=[{
            "product_id": ball.id,
            "quantity": 1,
            "unit_price_cents": 0,
            "is_internal_material": True,
        }])

    assert error.value.status_code == 400
    assert "gehört nicht zur Kategorie" in error.value.detail


def test_positive_cash_sale_without_tendered_amount_is_rejected(db_session):
    user = create_user(db_session)
    ball = create_product(db_session)

    with pytest.raises(HTTPException) as error:
        checkout(
            db_session,
            user,
            cash_received_cents=None,
            items=[{"product_id": ball.id, "quantity": 1, "unit_price_cents": 500}],
        )

    assert error.value.status_code == 400
    assert "Barbetrag" in error.value.detail
