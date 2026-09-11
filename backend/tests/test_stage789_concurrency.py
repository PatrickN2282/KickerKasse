from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.db_migration import run_migrations
from app.models import User, UserRole, Product, Transaction, Deckel, Voucher, AuditLog, Category, MaterialAccountEntry, GuestListEntry, TransactionType, PaymentMethod
from app.constants import INTERNAL_MATERIAL_CATEGORY_NAME
from app.services.deckel_service import DeckelService
from app.services.voucher_service import VoucherService


def seed(engine):
    assert run_migrations(engine)
    with Session(engine) as db:
        user = User(username="parallel-bookings", role=UserRole.TOP_ADMIN, password_hash="test-unused")
        product = Product(name="Ball", price_cents=500, stock_quantity=20)
        db.add_all([user, product]); db.commit()
        return user.id, product.id


def test_parallel_deckel_payment_commits_exactly_once(pg_engine):
    user_id, product_id = seed(pg_engine)
    with Session(pg_engine) as db:
        deckel_id = DeckelService(db).create_deckel("Parallel", user_id,
            [{"product_id": product_id, "quantity": 2, "unit_price_cents": 500}]).id
    barrier = Barrier(2)
    def pay(_):
        with Session(pg_engine, autoflush=False) as db:
            user = db.get(User, user_id)
            DeckelService(db).get_deckel(deckel_id)  # Deliberately cache old state.
            barrier.wait(timeout=10)
            try:
                return DeckelService(db).settle(deckel_id, user, 1000).id
            except LookupError:
                return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(pay, range(2)))
    assert sum(result is not None for result in results) == 1
    with Session(pg_engine) as db:
        assert db.query(Transaction).count() == 1
        assert db.get(Product, product_id).stock_quantity == 18
        assert db.query(Deckel).count() == 0
        assert db.query(AuditLog).filter_by(action="SETTLED").count() == 1


def test_parallel_prepaid_series_share_product_and_unique_numbers(pg_engine):
    user_id, _ = seed(pg_engine)
    barrier = Barrier(2)
    def prepare(_):
        with Session(pg_engine, autoflush=False) as db:
            barrier.wait(timeout=10)
            vouchers, product = VoucherService(db).create_prepaid_vouchers(1000, user_id, quantity=3)
            return [voucher.voucher_code for voucher in vouchers], product.id
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(prepare, range(2)))
    assert results[0][1] == results[1][1]
    assert len(set(results[0][0] + results[1][0])) == 6
    with Session(pg_engine) as db:
        assert db.get(Product, results[0][1]).stock_quantity == 6
        assert db.query(Voucher).count() == 6 and db.query(Transaction).count() == 2


def test_internal_material_deckel_records_account_without_cash(pg_engine):
    user_id, product_id = seed(pg_engine)
    with Session(pg_engine, autoflush=False) as db:
        product = db.get(Product, product_id)
        product.categories.append(db.query(Category).filter_by(name=INTERNAL_MATERIAL_CATEGORY_NAME).one()); db.commit()
        deckel_id = DeckelService(db).create_deckel("Training", user_id,
            [{"product_id": product_id, "quantity": 2, "unit_price_cents": 500, "is_internal_material": True}]).id
        transaction = DeckelService(db).settle(deckel_id, db.get(User, user_id), 0)
        assert transaction.total_amount_cents == 0
        entry = db.query(MaterialAccountEntry).one()
        assert entry.amount_cents == 1000 and entry.transaction_id == transaction.id
        assert product.stock_quantity == 18


def test_booking_upgrade_preserves_historical_codes_and_guests(pg_engine):
    user_id, product_id = seed(pg_engine)
    with Session(pg_engine) as db:
        transaction = Transaction(user_id=user_id, payment_method=PaymentMethod.CASH,
            type=TransactionType.SALE, total_amount_cents=500, voucher_code="V-2026-001")
        db.add(transaction); db.flush()
        db.add(GuestListEntry(product_id=product_id, guest_name="Historischer Gast", transaction_id=transaction.id))
        db.commit()
    with pg_engine.begin() as conn:
        conn.execute(text("DELETE FROM schema_migrations WHERE version IN ('1.6.10', '1.6.11')"))
        conn.execute(text("DROP TABLE voucher_redemptions"))
        conn.execute(text("ALTER TABLE transactions ALTER COLUMN voucher_code TYPE VARCHAR(20)"))
        conn.execute(text("CREATE INDEX ix_transactions_voucher_code ON transactions(voucher_code)"))
        conn.execute(text("ALTER TABLE guest_list_entries DROP COLUMN transaction_item_id"))
    assert run_migrations(pg_engine)
    assert run_migrations(pg_engine)
    columns = {c["name"]: c for c in inspect(pg_engine).get_columns("transactions")}
    assert getattr(columns["voucher_code"]["type"], "length", None) is None
    assert "voucher_redemptions" in inspect(pg_engine).get_table_names()
    assert "transaction_item_id" in {c["name"] for c in inspect(pg_engine).get_columns("guest_list_entries")}

    with Session(pg_engine) as db:
        assert db.query(Transaction).one().voucher_code == "V-2026-001"
        entry = db.query(GuestListEntry).one()
        assert entry.guest_name == "Historischer Gast" and entry.transaction_item_id is None

        # Aggregated display text must not hit PostgreSQL B-tree entry-size limits.
        long_codes = ", ".join(uuid4().hex for _ in range(300))
        db.query(Transaction).one().voucher_code = long_codes
        db.commit()
        assert db.query(Transaction).one().voucher_code == long_codes
    assert "ix_transactions_voucher_code" not in {i["name"] for i in inspect(pg_engine).get_indexes("transactions")}
