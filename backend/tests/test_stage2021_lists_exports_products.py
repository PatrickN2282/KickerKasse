"""Etappen 20/21: für den gemeinsamen Abschlusslauf vorbereitet, noch nicht ausgeführt."""
import asyncio

from starlette.requests import Request

from app.api.guest_list import list_guest_list_entries_page
from app.api.voucher import _spreadsheet_safe
from app.models import Category, GuestListEntry, Member, Product, User, UserRole
from app.repositories import ProductRepository


def authenticated_request(user):
    return Request({
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "session": {"user_id": user.id, "session_version": user.session_version},
    })


def test_guest_list_page_filters_and_limits_result(db_session):
    user = User(username="listen-admin", password_hash="unused", role=UserRole.ADMIN)
    member = Member(member_number=31, name="Änne Gastgeber", first_name="Änne", last_name="Gastgeber")
    product = Product(name="Eintritt, Abend", price_cents=500, stock_quantity=10)
    db_session.add_all([user, member, product])
    db_session.flush()
    db_session.add_all([
        GuestListEntry(product_id=product.id, member_id=member.id, guest_name="Mara Muster", guest_first_name="Mara", guest_last_name="Muster"),
        GuestListEntry(product_id=product.id, member_id=member.id, guest_name="Andere Person", guest_first_name="Andere", guest_last_name="Person"),
    ])
    db_session.commit()

    result = asyncio.run(list_guest_list_entries_page(
        authenticated_request(user), search="Mara", page=1, page_size=1, db=db_session
    ))
    assert result.total == 1
    assert len(result.entries) == 1
    assert result.entries[0].guest_first_name == "Mara"


def test_csv_formula_prefix_and_product_reactivation(db_session):
    assert _spreadsheet_safe(" =2+2") == "' =2+2"
    assert _spreadsheet_safe('Text, mit "Zitat"') == 'Text, mit "Zitat"'
    repo = ProductRepository(db_session)
    product = repo.create(name="Wieder da", price_cents=100)
    category = Category(name="Kassenseite", is_active_in_kasse=True)
    product.categories.append(category)
    db_session.commit()
    assert repo.delete(product.id)
    assert repo.get_by_id(product.id).is_active is False
    reactivated = repo.update(product.id, is_active=True)
    assert reactivated.is_active is True
    assert reactivated.categories[0].name == "Kassenseite"
