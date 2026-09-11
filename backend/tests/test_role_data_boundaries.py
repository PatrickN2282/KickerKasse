"""HTTP regressions for project audit tasks 14 and 16 (no production startup)."""
import asyncio

import httpx
import pytest
from fastapi import FastAPI

from app.api import member, user, transaction, voucher
from app.core import get_db
from app.core.security import get_password_hasher
from app.models import AuditLog, MaterialAccountEntry, Member, PaymentMethod, Transaction, User, UserRole


@pytest.fixture(scope="module")
def boundary_app():
    app = FastAPI()
    for router in (member.router, user.router, transaction.router, voucher.admin_router):
        app.include_router(router)

    @app.middleware("http")
    async def test_session(request, call_next):
        request.scope["session"] = app.state.session
        return await call_next(request)

    async def test_db():
        yield app.state.db

    app.dependency_overrides[get_db] = test_db
    return app


@pytest.fixture()
def send(boundary_app, db_session):
    boundary_app.state.db = db_session

    def call(actor, method, path, payload=None):
        boundary_app.state.session = {"user_id": actor.id, "session_version": actor.session_version} if actor else {}

        async def run():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=boundary_app), base_url="http://test") as client:
                return await client.request(method, path, json=payload)

        return asyncio.run(run())
    return call


def actor(db, role, *, active=True):
    record = User(username="actor", password_hash="unused", role=role, is_active=active)
    db.add(record)
    db.commit()
    return record


@pytest.fixture()
def linked(db_session):
    record = Member(member_number=1, first_name="Mara", last_name="Mitglied", name="Mara Mitglied",
                    role=UserRole.ADMIN, email="private@example.test", phone="12345", notes="Private Notiz",
                    balance_cents=1234, membership_number="M-1")
    db_session.add(record)
    db_session.flush()
    account = User(username="Mara.Mitglied", password_hash="original", role=UserRole.ADMIN,
                   member_id=record.id, is_active=True)
    db_session.add(account)
    db_session.commit()
    return record, account


@pytest.mark.parametrize("role", [UserRole.MANAGER, UserRole.ADMIN])
@pytest.mark.parametrize("requested", [None, "VERKAUF", "ADMIN", "TOP_ADMIN", ""])
def test_member_role_field_requires_top_admin_even_when_null(db_session, send, linked, role, requested):
    record, account = linked
    response = send(actor(db_session, role), "PUT", f"/api/members/{record.id}", {"role": requested, "notes": "changed"})
    assert response.status_code == 403, response.text
    db_session.refresh(record)
    db_session.refresh(account)
    assert record.role == account.role == UserRole.ADMIN
    assert account.is_active and record.notes == "Private Notiz"
    assert db_session.query(AuditLog).count() == 0


@pytest.mark.parametrize("payload", [{"first_name": "Maria"}, {"email": "updated@example.test"}, {"account_password": "new-password"}])
def test_member_edits_preserve_disabled_login(db_session, send, linked, payload):
    record, account = linked
    account.is_active = False
    db_session.commit()
    response = send(actor(db_session, UserRole.ADMIN), "PUT", f"/api/members/{record.id}", payload)
    assert response.status_code == 200, response.text
    db_session.refresh(account)
    assert account.is_active is False
    assert account.role == UserRole.ADMIN


def test_ordinary_edit_does_not_change_divergent_login_role(db_session, send, linked):
    record, account = linked
    account.role = UserRole.VERKAUF
    db_session.commit()
    response = send(actor(db_session, UserRole.MANAGER), "PUT", f"/api/members/{record.id}", {"notes": "changed"})
    assert response.status_code == 200, response.text
    db_session.refresh(account)
    assert account.role == UserRole.VERKAUF


def test_top_admin_can_remove_and_reassign_member_role(db_session, send, linked):
    record, account = linked
    top = actor(db_session, UserRole.TOP_ADMIN)
    for requested, expected_active in [(None, False), ("MANAGER", True)]:
        response = send(top, "PUT", f"/api/members/{record.id}", {"role": requested})
        assert response.status_code == 200, response.text
        db_session.refresh(record)
        db_session.refresh(account)
        assert record.role == requested
        assert account.is_active is expected_active
    assert account.role == UserRole.MANAGER


def test_resubmitted_unchanged_role_does_not_reactivate(db_session, send, linked):
    record, account = linked
    account.is_active = False
    db_session.commit()
    response = send(actor(db_session, UserRole.TOP_ADMIN), "PUT", f"/api/members/{record.id}", {"role": "ADMIN", "notes": "changed"})
    assert response.status_code == 200, response.text
    db_session.refresh(account)
    assert account.is_active is False


def test_imported_member_details_do_not_create_login(db_session, send, linked):
    record, account = linked
    db_session.delete(account)
    db_session.commit()
    manager = actor(db_session, UserRole.MANAGER)
    response = send(manager, "PUT", f"/api/members/{record.id}", {"notes": "changed"})
    assert response.status_code == 200, response.text
    assert db_session.query(User).filter_by(member_id=record.id).count() == 0


def test_admin_cannot_provision_imported_member_login(db_session, send, linked):
    record, account = linked
    db_session.delete(account)
    db_session.commit()
    response = send(actor(db_session, UserRole.ADMIN), "PUT", f"/api/members/{record.id}", {"account_password": "new-password"})
    assert response.status_code == 403, response.text
    assert db_session.query(User).filter_by(member_id=record.id).count() == 0


@pytest.mark.parametrize("requested", ["TOP_ADMIN", "top_admin"])
def test_top_admin_role_cannot_be_assigned_to_member(db_session, send, linked, requested):
    record, account = linked
    response = send(actor(db_session, UserRole.TOP_ADMIN), "PUT", f"/api/members/{record.id}", {"role": requested})
    assert response.status_code == 400, response.text
    db_session.refresh(record)
    assert record.role == UserRole.ADMIN


@pytest.mark.parametrize("payload", [{"role": "VERKAUF"}, {"role": None}, {"username": "other"}, {"email": "other@example.test"}])
def test_linked_login_cannot_be_changed_via_user_profile(db_session, send, linked, payload):
    record, account = linked
    response = send(actor(db_session, UserRole.ADMIN), "PUT", f"/api/users/{account.id}", payload)
    assert response.status_code == 400, response.text
    db_session.refresh(account)
    assert account.username == "Mara.Mitglied" and account.role == UserRole.ADMIN
    assert db_session.query(AuditLog).count() == 0


@pytest.mark.parametrize("field,value", [("is_active", False), ("member_id", None), ("password_hash", "bypass")])
def test_user_update_rejects_state_and_link_overrides(db_session, send, field, value):
    admin = actor(db_session, UserRole.ADMIN)
    response = send(admin, "PUT", f"/api/users/{admin.id}", {field: value, "username": "changed"})
    assert response.status_code == 422, response.text
    db_session.refresh(admin)
    assert admin.username == "actor" and admin.is_active
    assert db_session.query(AuditLog).count() == 0


@pytest.mark.parametrize("method,suffix", [("DELETE", ""), ("POST", "/reactivate")])
def test_linked_login_state_uses_member_role_workflow(db_session, send, linked, method, suffix):
    record, account = linked
    account.is_active = method != "POST"
    db_session.commit()
    response = send(actor(db_session, UserRole.ADMIN), method, f"/api/users/{account.id}{suffix}")
    assert response.status_code == 400, response.text
    db_session.refresh(account)
    assert account.is_active is (method != "POST")


def test_linked_password_reset_still_works_without_activation(db_session, send, linked):
    record, account = linked
    account.is_active = False
    db_session.commit()
    response = send(actor(db_session, UserRole.ADMIN), "PUT", f"/api/users/{account.id}", {"password": "new-password"})
    assert response.status_code == 200, response.text
    db_session.refresh(account)
    assert not account.is_active
    assert get_password_hasher().verify_password("new-password", account.password_hash)


def test_direct_accounts_remain_manageable_but_self_deactivation_fails(db_session, send):
    admin = actor(db_session, UserRole.ADMIN)
    response = send(admin, "POST", "/api/users", {"username": "direct", "password": "test-password", "role": "VERKAUF"})
    assert response.status_code == 201, response.text
    target = response.json()["id"]
    assert send(admin, "PUT", f"/api/users/{target}", {"role": "MANAGER"}).status_code == 200
    assert send(admin, "DELETE", f"/api/users/{target}").status_code == 204
    assert send(admin, "POST", f"/api/users/{target}/reactivate").status_code == 200
    assert send(admin, "DELETE", f"/api/users/{admin.id}").status_code == 400


@pytest.mark.parametrize("method,suffix,payload", [("PUT", "", {"username": "changed"}), ("DELETE", "", None), ("POST", "/reactivate", None)])
def test_top_admin_is_protected_on_all_management_paths(db_session, send, method, suffix, payload):
    top = actor(db_session, UserRole.TOP_ADMIN)
    response = send(top, method, f"/api/users/{top.id}{suffix}", payload)
    assert response.status_code == 400, response.text
    db_session.refresh(top)
    assert top.username == "actor" and top.is_active


FINANCE_ADMIN_PATHS = [
    "/api/transactions", "/api/transactions/1",
    "/api/transactions/filtered?start_date=2026-09-01&end_date=2026-09-07",
    "/api/transactions/revenue-stats", "/api/transactions/daily-stats?date=2026-09-07",
    "/api/members/statistics", "/api/admin/vouchers/material-account",
    "/api/admin/vouchers/club-account", "/api/transactions/cash/entries",
    "/api/transactions/cash/balance", "/api/transactions/scheduler/status",
    "/api/transactions/export/csv?start_date=2026-09-01&end_date=2026-09-07",
]


@pytest.mark.parametrize("role", [UserRole.MANAGER, UserRole.VERKAUF])
@pytest.mark.parametrize("path", FINANCE_ADMIN_PATHS)
def test_regular_finance_endpoints_require_admin(db_session, send, role, path):
    response = send(actor(db_session, role), "GET", path)
    assert response.status_code == 403, response.text


@pytest.mark.parametrize("path", ["/api/transactions/zbon/history", "/api/users/finance-options", "/api/admin/vouchers/material-transactions", "/api/transactions/daily-summary?date_param=2026-09-07"])
def test_manager_allowed_finance_and_material_paths_remain_available(db_session, send, path):
    response = send(actor(db_session, UserRole.MANAGER), "GET", path)
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.TOP_ADMIN])
def test_admin_finance_read_paths_remain_available(db_session, send, role):
    admin = actor(db_session, role)
    for path in FINANCE_ADMIN_PATHS:
        if path.endswith("scheduler/status"):
            continue  # No scheduler is started by this isolated test application.
        response = send(admin, "GET", path)
        assert response.status_code == (404 if path == "/api/transactions/1" else 200), (path, response.text)


@pytest.mark.parametrize("path", ["/api/members", "/api/members/1"])
def test_cashier_cannot_fetch_full_member_profiles(db_session, send, linked, path):
    response = send(actor(db_session, UserRole.VERKAUF), "GET", path)
    assert response.status_code == 403, response.text
    assert "Private Notiz" not in response.text


@pytest.mark.parametrize("role", list(UserRole))
def test_member_selection_contains_only_checkout_fields(db_session, send, linked, role):
    response = send(actor(db_session, role), "GET", "/api/members/selection")
    assert response.status_code == 200, response.text
    data = response.json()[0]
    assert set(data) == {"id", "member_number", "membership_number", "name", "first_name", "last_name", "photo_path", "has_discount", "balance_cents"}
    assert data["balance_cents"] == 1234 and data["name"] == "Mara Mitglied"


@pytest.mark.parametrize("path", ["/api/members/selection", "/api/members", "/api/transactions/revenue-stats", "/api/transactions/zbon/history"])
@pytest.mark.parametrize("anonymous", [True, False])
def test_missing_or_disabled_session_is_rejected(db_session, send, path, anonymous):
    account = None if anonymous else actor(db_session, UserRole.TOP_ADMIN, active=False)
    assert send(account, "GET", path).status_code == 401


@pytest.mark.parametrize("path", ["/api/transactions/cash/deposit", "/api/transactions/cash/withdrawal"])
def test_manager_cannot_book_cash_outside_zbon(db_session, send, path):
    from app.models import CashEntry
    response = send(actor(db_session, UserRole.MANAGER), "POST", path, {"amount_cents": 500, "reason": "test"})
    assert response.status_code == 403, response.text
    assert db_session.query(CashEntry).count() == 0


def test_material_list_keeps_operational_fields_without_sale_payment_details(db_session, send, linked):
    record, account = linked
    manager = actor(db_session, UserRole.MANAGER)
    sale = Transaction(user_id=manager.id, member_id=record.id, receipt_number=17,
                       total_amount_cents=500, payment_method=PaymentMethod.BALANCE, balance_applied_cents=500)
    db_session.add(sale)
    db_session.flush()
    db_session.add(MaterialAccountEntry(user_id=manager.id, transaction_id=sale.id, amount_cents=250, reason="2× Bälle"))
    db_session.commit()
    response = send(manager, "GET", "/api/admin/vouchers/material-transactions")
    assert response.status_code == 200, response.text
    entry = response.json()["entries"][0]
    assert entry["quantity"] == 2 and entry["amount_cents"] == 250 and entry["receipt_number"] == 17
    assert entry["transaction"] == {"member_name": "Mara Mitglied"}
    assert "balance_applied_cents" not in response.text
    assert "Private Notiz" not in response.text


def test_manager_can_preview_zbon_without_regular_statistics(db_session, send):
    response = send(actor(db_session, UserRole.MANAGER), "POST", "/api/transactions/zbon/preview", {})
    assert response.status_code == 200, response.text
    assert response.json()["report_content"]


@pytest.mark.parametrize("role", [UserRole.MANAGER, UserRole.ADMIN, UserRole.TOP_ADMIN])
def test_member_administration_retains_full_profile(db_session, send, linked, role):
    response = send(actor(db_session, role), "GET", "/api/members")
    assert response.status_code == 200, response.text
    assert response.json()[0]["notes"] == "Private Notiz"


@pytest.mark.parametrize("requested", ["TOP_ADMIN", "top_admin"])
def test_user_management_cannot_grant_top_admin_through_alias(db_session, send, requested):
    admin = actor(db_session, UserRole.ADMIN)
    response = send(admin, "PUT", f"/api/users/{admin.id}", {"role": requested})
    assert response.status_code == 400, response.text
    response = send(admin, "POST", "/api/users", {"username": "other", "role": requested, "password": "test-password"})
    assert response.status_code == 400, response.text
    db_session.refresh(admin)
    assert admin.role == UserRole.ADMIN
    assert db_session.query(User).count() == 1


def test_top_admin_can_provision_imported_member_login(db_session, send, linked):
    record, account = linked
    db_session.delete(account)
    db_session.commit()
    response = send(actor(db_session, UserRole.TOP_ADMIN), "PUT", f"/api/members/{record.id}", {"account_password": "new-password"})
    assert response.status_code == 200, response.text
    created = db_session.query(User).filter_by(member_id=record.id).one()
    assert created.is_active and created.role == UserRole.ADMIN


def test_user_service_cannot_override_account_state(db_session):
    from app.services.user_service import UserService
    admin = actor(db_session, UserRole.ADMIN)
    with pytest.raises(ValueError, match="Kontozustand"):
        UserService(db_session).update_user(admin.id, is_active=False, username="changed")
    db_session.refresh(admin)
    assert admin.is_active and admin.username == "actor"
