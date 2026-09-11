import asyncio
from datetime import datetime
import httpx
import pytest
from sqlalchemy.orm import Session
from app.models import Member, User, UserRole, Transaction, GuestListEntry, BalanceLog, MemberBalanceCorrectionLog, Category
from app.core.db_migration import run_migrations
from app.services.member_service import MemberService
from app.services.zbon_service import ZBonService
from app.services.deckel_service import DeckelService
from app.services.audit_log_service import AuditLogService
from app.services.transaction_service import TransactionService
from .test_stage789_bookings import seed, sale
from .test_stage1112_bookings import make_app


@pytest.fixture(params=["sqlite", "postgres"])
def history_db(request):
    if request.param == "sqlite":
        yield request.getfixturevalue("db_session")
    else:
        engine = request.getfixturevalue("pg_engine")
        assert run_migrations(engine)
        with Session(engine, autoflush=False) as db:
            yield db


def person(db, **kwargs):
    member = Member(member_number=1, name="Mara Test", first_name="Mara", last_name="Test", balance_cents=0, **kwargs)
    db.add(member); db.commit()
    return member


def test_sale_and_deckel_snapshots_survive_catalog_changes(history_db):
    db = history_db
    user, product = seed(db, warengruppe="Getränke", tax_rate=19)
    member = person(db)
    category = Category(name="Kalt", display_order=1)
    product.categories.append(category); db.commit()
    result = sale(db, user, product, member_id=member.id)
    deckel = DeckelService(db).create_deckel("Test", user.id, [{"product_id": product.id, "quantity": 1, "unit_price_cents": 500}])
    paid = DeckelService(db).settle(deckel.id, user, 500)
    rows = db.query(Transaction).order_by(Transaction.id).all()
    report = ZBonService(db)
    methods = [report._aggregate_by_product, report._aggregate_by_warengruppe, report._aggregate_by_category,
               report._aggregate_by_customer, report._aggregate_by_customer_group, report._aggregate_by_tax_rate]
    before = [method(rows) for method in methods]
    product.name = "Heute anders"; product.warengruppe = "Andere Gruppe"; product.tax_rate = 7
    category.name = "Neue Kategorie"; member.name = "Mara Neu"; member.last_name = "Neu"; user.username = "Neuer Name"
    db.commit(); db.expire_all()
    assert [method(rows) for method in methods] == before
    assert all(t.items[0].snapshot_version == 1 for t in rows)
    assert all(t.items[0].product_name == "Testartikel" for t in rows)
    assert all(t.performed_by_username == "booking-test" for t in rows)
    assert report._serialize_transaction(rows[0], set())["member_name"] == "Mara Test"


def test_archiving_retains_all_references_and_report_totals(history_db):
    db = history_db
    user, product = seed(db)
    member = person(db)
    service = MemberService(db)
    service.recharge_balance(member.id, 1000, "RECHARGE", user.username, executed_by_user_id=user.id)
    service.correct_balance(member.id, 0, executed_by_username=user.username, executed_by_user_id=user.id, reason="Testausgleich")
    db.add(GuestListEntry(member_id=member.id, product_id=product.id, guest_name="Gast Test", guest_first_name="Gast", guest_last_name="Test"))
    db.commit()
    before = ZBonService(db).build_current_zbon_preview()["summary"]
    assert service.delete_member(member.id, user.username)
    after = ZBonService(db).build_current_zbon_preview()["summary"]
    for key in ("cash_calculated_cents", "member_recharges_cents", "article_revenue_cents", "total_revenue_cents"):
        assert before[key] == after[key]
    assert db.get(Member, member.id).archived_at is not None
    assert service.get_all_members() == []
    assert len(service.get_all_members(include_archived=True)) == 1
    assert db.query(Transaction).one().member_id == member.id
    assert db.query(BalanceLog).count() >= 1
    assert db.query(MemberBalanceCorrectionLog).count() == db.query(GuestListEntry).count() == 1
    assert service.set_archived(member.id, False, user.username)
    assert len(service.get_all_members()) == 1


def test_restguthaben_blocks_archiving_without_side_effects(history_db):
    db = history_db
    user, _ = seed(db)
    member = person(db)
    member.balance_cents = 1; db.commit()
    with pytest.raises(ValueError, match="Restguthaben"):
        MemberService(db).delete_member(member.id, user.username)
    assert db.get(Member, member.id).archived_at is None
    assert member.balance_cents == 1


def test_archiving_revokes_linked_login_atomically(history_db, monkeypatch):
    db = history_db
    actor, _ = seed(db)
    member = person(db, role=UserRole.VERKAUF)
    account = User(username="linked", password_hash="unused", role=UserRole.VERKAUF, member_id=member.id)
    db.add(account); db.commit()
    initial_version = account.session_version
    def fail(*args, **kwargs): raise RuntimeError("audit failed")
    with monkeypatch.context() as patch:
        patch.setattr(AuditLogService, "log", fail)
        with pytest.raises(RuntimeError): MemberService(db).delete_member(member.id, actor.username)
    assert member.archived_at is None and account.is_active
    MemberService(db).delete_member(member.id, actor.username)
    db.expire_all()
    assert not account.is_active and account.session_version > initial_version
    MemberService(db).set_archived(member.id, False, actor.username)
    assert not account.is_active


def test_recharge_classification_does_not_depend_on_member_fk(history_db):
    db = history_db
    actor, _ = seed(db)
    member = person(db)
    MemberService(db).recharge_balance(member.id, 500, "RECHARGE", actor.username, executed_by_user_id=actor.id)
    transaction = db.query(Transaction).one()
    transaction.member_id = None; db.commit()
    summary = ZBonService(db).build_current_zbon_preview()["summary"]
    assert summary["member_recharges_cents"] == 500
    assert TransactionService._get_booking_type(transaction, set()) == "MEMBER_BALANCE_RECHARGE"
    assert TransactionService(db)._serialize_transaction(transaction, set())["member"]["name"] == "Mara Test"


def test_archive_http_hides_selection_rejects_sale_and_can_restore(db_session):
    user, product = seed(db_session)
    member = person(db_session)
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=make_app(db_session)), base_url="http://test") as client:
            await client.get(f"/test-session/{user.id}")
            assert (await client.delete(f"/api/members/{member.id}")).status_code == 204
            assert (await client.get("/api/members/selection")).json() == []
            archived = (await client.get("/api/members?include_archived=true")).json()
            assert archived[0]["archived_at"]
            response = await client.post("/api/transactions/sale", json={"user_id": user.id, "member_id": member.id,
                "payment_method": "CASH", "cash_received_cents": 500,
                "items": [{"product_id": product.id, "quantity": 1, "unit_price_cents": 500}]})
            assert response.status_code == 404, response.text
            assert (await client.post(f"/api/members/{member.id}/restore")).status_code == 204
            assert len((await client.get("/api/members/selection")).json()) == 1
    asyncio.run(run())
    assert db_session.query(Transaction).count() == 0


def test_missing_legacy_snapshot_is_labelled_and_never_reconstructed(history_db):
    db = history_db
    user, product = seed(db, warengruppe="Heute")
    result = sale(db, user, product)
    transaction = db.get(Transaction, result["id"])
    item = transaction.items[0]
    item.snapshot_version = item.product_group_name = item.category_name = item.tax_rate_snapshot = None
    db.commit()
    preview = ZBonService(db).build_current_zbon_preview()
    assert preview["history_incomplete"]
    assert "Altbestand" in preview["report_content"]
    before = preview["breakdowns"]["product_groups"]
    product.warengruppe = "Morgen"; db.commit()
    assert ZBonService(db).build_current_zbon_preview()["breakdowns"]["product_groups"] == before


def test_material_value_and_classification_survive_category_and_price_changes(history_db):
    from app.constants import INTERNAL_MATERIAL_CATEGORY_NAME
    from app.repositories import TransactionRepository
    from app.models import TransactionType, PaymentMethod
    from app.services.material_account_service import MaterialAccountService
    db = history_db
    user, product = seed(db)
    category = db.query(Category).filter_by(name=INTERNAL_MATERIAL_CATEGORY_NAME).first()
    product.categories.append(category or Category(name=INTERNAL_MATERIAL_CATEGORY_NAME, display_order=1))
    db.commit()
    transaction = TransactionRepository(db).create(type=TransactionType.SALE, payment_method=PaymentMethod.CASH,
        total_amount_cents=0, user_id=user.id, performed_by_username=user.username,
        items=[{"product_id": product.id, "quantity": 2, "unit_price_cents": 0, "is_internal_material": True}])
    MaterialAccountService(db).record_sale_transaction(transaction); db.commit()
    before = MaterialAccountService(db).get_account_summary()
    product.categories.clear(); product.price_cents = 900; product.name = "Geändert"; db.commit()
    item = transaction.items[0]
    assert MaterialAccountService._resolve_material_amount_cents(transaction, item) == 1000
    assert ZBonService(db)._count_internal_material_sales([transaction]) == 1
    assert MaterialAccountService(db).get_account_summary() == before


def test_upgrade_keeps_legacy_archive_and_does_not_guess_product_snapshots(pg_engine):
    from sqlalchemy import text
    from app.core.history_migration import migrate_history
    assert run_migrations(pg_engine)
    with Session(pg_engine) as db:
        actor, product = seed(db, warengruppe="Heute")
        sale(db, actor, product)
        report = ZBonService(db).create_zbon(created_by_name=actor.username)
        from app.models import ZBonHistory
        html = db.get(ZBonHistory, report["history_id"]).report_content
    with pg_engine.begin() as conn:
        for column in ("snapshot_version", "product_group_name", "category_name", "tax_rate_snapshot", "internal_material_unit_value_cents"):
            conn.execute(text(f"ALTER TABLE transaction_items DROP COLUMN {column}"))
        conn.execute(text("ALTER TABLE members DROP COLUMN archived_at"))
        conn.execute(text("ALTER TABLE transactions DROP COLUMN booking_type"))
    migrate_history(pg_engine)
    migrate_history(pg_engine)
    with Session(pg_engine) as db:
        item = db.query(Transaction).one().items[0]
        assert item.snapshot_version is None and item.product_group_name is None
        assert db.get(ZBonHistory, report["history_id"]).report_content == html
