from types import SimpleNamespace

from app.models import Product
from app.schemas.product import ProductCreate
from app.schemas.transaction import TransactionCreate
from app.utils.drawer import (
    drawer_targets_for_sale,
    drawer_targets_for_stock_change,
    requires_main_drawer,
    requires_small_parts_drawer,
)


def test_product_flag_defaults_to_disabled():
    payload = ProductCreate(name="Schraube", price_cents=50)

    assert payload.opens_small_parts_drawer is False
    assert Product.__table__.columns["opens_small_parts_drawer"].default.arg is False


def test_any_flagged_product_requests_small_parts_drawer():
    products = [
        SimpleNamespace(opens_small_parts_drawer=False),
        SimpleNamespace(opens_small_parts_drawer=True),
    ]

    assert requires_small_parts_drawer(products) is True


def test_regular_products_do_not_request_small_parts_drawer():
    assert requires_small_parts_drawer([
        SimpleNamespace(opens_small_parts_drawer=False),
        SimpleNamespace(),
    ]) is False


def test_cash_drawer_requires_real_cash_handling():
    assert requires_main_drawer("CASH", payable_amount_cents=500) is True
    assert requires_main_drawer("CASH", payable_amount_cents=0) is False
    assert requires_main_drawer("BALANCE", payable_amount_cents=500) is False
    assert requires_main_drawer("CASH", payable_amount_cents=0, tip_cents=100) is True


def test_sale_targets_combine_cash_and_storage_independently():
    storage_product = SimpleNamespace(opens_small_parts_drawer=True)

    assert drawer_targets_for_sale([storage_product], "CASH", 500) == ["main", "small_parts"]
    assert drawer_targets_for_sale([storage_product], "BALANCE", 0) == ["small_parts"]
    assert drawer_targets_for_sale([], "CASH", 0) == []


def test_stock_change_opens_storage_for_restock_and_explicit_removal_only():
    product = SimpleNamespace(opens_small_parts_drawer=True, is_unlimited_stock=False)

    assert drawer_targets_for_stock_change(product, 2, 8) == ["small_parts"]
    assert drawer_targets_for_stock_change(product, 8, 2) == []
    assert drawer_targets_for_stock_change(product, 8, 2, open_for_decrease=True) == ["small_parts"]


def test_legacy_client_flag_defaults_to_no_hardware_instruction():
    payload = TransactionCreate(
        payment_method="CASH",
        user_id=1,
        items=[{"product_id": 1, "quantity": 1, "unit_price_cents": 100}],
    )

    assert payload.trigger_cash_drawer is False
