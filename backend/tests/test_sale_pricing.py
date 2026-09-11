from types import SimpleNamespace

import pytest

from app.constants import INTERNAL_MATERIAL_CATEGORY_NAME
from app.services.sale_pricing_service import (
    resolve_catalog_unit_price_cents,
    resolve_sale_unit_price_cents,
)


def product(**overrides):
    values = {
        "name": "Ball",
        "price_cents": 500,
        "member_price_cents": 350,
        "is_discountable": True,
        "is_variable_price": False,
        "categories": [],
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def member(*, has_discount=True):
    return SimpleNamespace(has_discount=has_discount)


def test_fixed_price_is_server_authoritative():
    assert resolve_sale_unit_price_cents(product(), 1) == 500


def test_eligible_member_gets_member_price():
    assert resolve_sale_unit_price_cents(product(), 999, member=member()) == 350


def test_zero_cent_member_price_is_valid():
    item = product(member_price_cents=0)
    assert resolve_catalog_unit_price_cents(item, member()) == 0
    assert resolve_sale_unit_price_cents(item, 500, member=member()) == 0


@pytest.mark.parametrize(
    "customer,discountable",
    [(None, True), (member(has_discount=False), True), (member(), False)],
)
def test_member_price_requires_member_discount_and_discountable_product(customer, discountable):
    assert resolve_sale_unit_price_cents(
        product(is_discountable=discountable),
        1,
        member=customer,
    ) == 500


@pytest.mark.parametrize("entered_price", [0, 225, 999])
def test_variable_price_keeps_cashier_entered_amount(entered_price):
    assert resolve_sale_unit_price_cents(
        product(is_variable_price=True),
        entered_price,
        member=member(),
    ) == entered_price


def test_internal_material_is_free_but_keeps_catalog_value_for_accounting():
    item = product(categories=[SimpleNamespace(name=INTERNAL_MATERIAL_CATEGORY_NAME)])
    assert resolve_sale_unit_price_cents(item, 500, is_internal_material=True, member=member()) == 0
    assert resolve_catalog_unit_price_cents(item, member()) == 350


def test_variable_internal_material_is_still_free_when_booked_as_internal():
    item = product(
        is_variable_price=True,
        categories=[SimpleNamespace(name=INTERNAL_MATERIAL_CATEGORY_NAME)],
    )
    assert resolve_sale_unit_price_cents(item, 275, is_internal_material=True) == 0


def test_internal_flag_is_rejected_outside_reserved_category():
    with pytest.raises(ValueError, match="gehört nicht zur Kategorie"):
        resolve_sale_unit_price_cents(product(), 0, is_internal_material=True)


def test_negative_variable_price_is_rejected_defensively():
    with pytest.raises(ValueError, match="nicht negativ"):
        resolve_sale_unit_price_cents(product(is_variable_price=True), -1)
