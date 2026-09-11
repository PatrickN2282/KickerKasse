import pytest

from app.constants import INTERNAL_MATERIAL_CATEGORY_NAME
from app.models import Category, Product, User, UserRole
from app.services.deckel_service import DeckelService


def create_user(db_session):
    user = User(
        username="cashier",
        password_hash="test",
        role=UserRole.VERKAUF,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def create_product(db_session, name, **overrides):
    values = {
        "name": name,
        "price_cents": 500,
        "member_price_cents": 350,
        "is_discountable": True,
        "stock_quantity": 0,
        "is_unlimited_stock": True,
        "is_variable_price": False,
        "is_active": True,
    }
    values.update(overrides)
    product = Product(**values)
    db_session.add(product)
    db_session.commit()
    return product


def test_deckel_resolves_fixed_variable_and_internal_prices(db_session):
    user = create_user(db_session)
    category = Category(name=INTERNAL_MATERIAL_CATEGORY_NAME)
    fixed = create_product(db_session, "Festpreis")
    variable = create_product(db_session, "Spende", is_variable_price=True)
    internal = create_product(db_session, "Ball")
    internal.categories.append(category)
    db_session.commit()

    deckel = DeckelService(db_session).create_deckel("Tisch 1", user.id, [
        {"product_id": fixed.id, "quantity": 1, "unit_price_cents": 1},
        {"product_id": variable.id, "quantity": 1, "unit_price_cents": 275},
        {
            "product_id": internal.id,
            "quantity": 2,
            "unit_price_cents": 999,
            "is_internal_material": True,
            "note": "Training",
        },
    ])

    prices = {item.product.name: item.unit_price_cents for item in deckel.items}
    assert prices == {"Festpreis": 500, "Spende": 275, "Ball": 0}
    assert sum(item.total_price_cents for item in deckel.items) == 775


def test_deckel_append_resolves_new_item_price(db_session):
    user = create_user(db_session)
    fixed = create_product(db_session, "Festpreis")
    service = DeckelService(db_session)
    deckel = service.create_deckel("Tisch 2", user.id, [
        {"product_id": fixed.id, "quantity": 1, "unit_price_cents": 500},
    ])

    updated = service.append_items(deckel.id, [
        {"product_id": fixed.id, "quantity": 2, "unit_price_cents": 1},
    ])

    assert len(updated.items) == 1
    assert updated.items[0].quantity == 3
    assert updated.items[0].unit_price_cents == 500
    assert updated.items[0].total_price_cents == 1500


def test_deckel_rejects_internal_flag_for_regular_product(db_session):
    user = create_user(db_session)
    fixed = create_product(db_session, "Festpreis")

    with pytest.raises(ValueError, match="gehört nicht zur Kategorie"):
        DeckelService(db_session).create_deckel("Tisch 3", user.id, [{
            "product_id": fixed.id,
            "quantity": 1,
            "unit_price_cents": 0,
            "is_internal_material": True,
        }])
