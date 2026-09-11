"""Opt-in integration tests. Creates/drops only uniquely named temporary databases.

TEST_POSTGRES_URL must point to a disposable PostgreSQL server with CREATEDB rights.
"""
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db_migration import run_migrations
from app.core.schema_verification import verify_schema
from app.models import Base, Member, Product, User, UserRole, Voucher, VoucherStatus, VoucherType
from app.services.product_service import ProductService




def journal(engine):
    with engine.connect() as conn:
        return conn.execute(text("SELECT version,step,applied_at FROM schema_migrations ORDER BY version,step")).all()


def test_fresh_install_and_repeat_preserve_journal_and_data(pg_engine):
    assert run_migrations(pg_engine)
    before = journal(pg_engine)
    assert len(before) == 11
    with Session(pg_engine) as db:
        db.add(Product(name="Wasser", price_cents=0, stock_quantity=25))
        db.commit()
    assert run_migrations(pg_engine)
    assert journal(pg_engine) == before
    with Session(pg_engine) as db:
        assert db.query(Product).one().stock_quantity == 25
        db.add(Member(member_number=1, name="Mara Test", first_name="Mara", last_name="Test", balance_cents=-1))
        with pytest.raises(IntegrityError):
            db.commit()


def test_legacy_columns_enum_defaults_and_existing_roles_survive(pg_engine):
    Base.metadata.create_all(pg_engine)
    with Session(pg_engine) as db:
        user = User(username="manager", password_hash="unused", role=UserRole.MANAGER)
        db.add(user)
        db.flush()
        db.add(Member(member_number=1, name="Mara Test", first_name="Mara", last_name="Test", role=UserRole.MANAGER, balance_cents=1200))
        db.add(Product(name="Wasser", price_cents=200, stock_quantity=25))
        db.add(Voucher(voucher_number=1, voucher_type=VoucherType.GIFT, status=VoucherStatus.PARTIALLY_REDEEMED,
                       value_cents=1000, original_value_cents=1000, remaining_value_cents=400, created_by_user_id=user.id))
        db.commit()
    with pg_engine.begin() as conn:
        conn.execute(text("ALTER TYPE userrole ADD VALUE 'KASSENMITGLIED'"))
        conn.execute(text("ALTER TYPE voucherstatus ADD VALUE 'LEGACY'"))
    with pg_engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'KASSENMITGLIED'::userrole"))
        conn.execute(text("ALTER TABLE vouchers ALTER COLUMN status SET DEFAULT 'CREATED'::voucherstatus"))
        conn.execute(text("ALTER TABLE products DROP COLUMN warengruppe"))
        conn.execute(text("ALTER TABLE products DROP COLUMN minimum_stock_quantity"))
        conn.execute(text("ALTER TABLE products ALTER COLUMN price_cents DROP NOT NULL"))
        conn.execute(text("ALTER TABLE members DROP COLUMN first_name"))
        conn.execute(text("ALTER TABLE members DROP COLUMN last_name"))
    assert run_migrations(pg_engine)
    assert run_migrations(pg_engine)
    assert next(c for c in inspect(pg_engine).get_columns("products") if c["name"] == "price_cents")["nullable"] is False
    with Session(pg_engine) as db:
        assert db.query(User).filter_by(username="manager").one().role == UserRole.MANAGER
        member = db.query(Member).one()
        assert (member.first_name, member.last_name, member.role, member.balance_cents) == ("Mara", "Test", UserRole.MANAGER, 1200)
        voucher = db.query(Voucher).one()
        assert voucher.status == VoucherStatus.PARTIALLY_REDEEMED and voucher.remaining_value_cents == 400
        assert db.query(Product).one().stock_quantity == 25
    with pg_engine.begin() as conn:
        role = conn.execute(text("INSERT INTO users(username,password_hash,is_active,failed_login_attempts,created_at,updated_at) VALUES ('default-check','unused',true,0,now(),now()) RETURNING role::text")).scalar_one()
        assert role == "MANAGER"


def test_inner_sql_failure_is_not_swallowed_and_retry_completes(pg_engine):
    Base.metadata.create_all(pg_engine)
    with pg_engine.begin() as conn:
        conn.execute(text("ALTER TABLE products DROP COLUMN warengruppe"))
    def fail(connection, cursor, statement, parameters, context, executemany):
        if "ALTER TABLE products ADD COLUMN warengruppe" in statement:
            raise RuntimeError("simulated migration failure")
    event.listen(pg_engine, "before_cursor_execute", fail)
    try:
        assert run_migrations(pg_engine) is False
        assert "legacy_columns" not in [row.step for row in journal(pg_engine)]
    finally:
        event.remove(pg_engine, "before_cursor_execute", fail)
    assert run_migrations(pg_engine)
    verify_schema(pg_engine)


def test_invalid_legacy_balance_stops_upgrade_without_clamping(pg_engine, caplog):
    Base.metadata.create_all(pg_engine)
    with pg_engine.begin() as conn:
        conn.execute(text("ALTER TABLE members DROP CONSTRAINT ck_members_balance_nonnegative"))
    with Session(pg_engine) as db:
        db.add(Member(member_number=1, name="Mara Test", first_name="Mara", last_name="Test", balance_cents=-100))
        db.commit()
    assert run_migrations(pg_engine) is False
    assert "ck_members_balance_nonnegative: IDs [1]" in caplog.text
    assert "data_constraints" not in [row.step for row in journal(pg_engine)]
    with pg_engine.begin() as conn:
        assert conn.execute(text("SELECT balance_cents FROM members")).scalar_one() == -100
        # Simulate a separately reviewed correction, then retry the upgrade.
        conn.execute(text("UPDATE members SET balance_cents=0"))
    assert run_migrations(pg_engine)


def test_journal_does_not_hide_schema_drift(pg_engine):
    assert run_migrations(pg_engine)
    with pg_engine.begin() as conn:
        conn.execute(text("ALTER TABLE products DROP COLUMN description"))
    assert run_migrations(pg_engine) is False


def test_parallel_restock_and_stale_session_preserve_quantities(pg_engine):
    assert run_migrations(pg_engine)
    with Session(pg_engine) as db:
        product = Product(name="Wasser", price_cents=200, stock_quantity=25)
        db.add(product)
        db.commit()
        product_id = product.id
    with Session(pg_engine) as stale:
        loaded = stale.get(Product, product_id)
        assert loaded.stock_quantity == 25
        with pg_engine.begin() as conn:
            conn.execute(text("UPDATE products SET stock_quantity=24 WHERE id=:id"), {"id": product_id})
        updated = ProductService(stale).update_product(product_id, name="Wasser neu")
        assert updated.stock_quantity == 24
    def restock(_):
        with Session(pg_engine) as db:
            ProductService(db).adjust_stock(product_id, 1, "test")
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(restock, range(8)))
    with Session(pg_engine) as db:
        assert db.get(Product, product_id).stock_quantity == 32


def test_parallel_startup_applies_each_migration_once(pg_engine):
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(lambda _: run_migrations(pg_engine), range(2))) == [True, True]
    assert len(journal(pg_engine)) == 11


def test_missing_voucher_value_columns_backfill_once_even_after_interruption(pg_engine):
    Base.metadata.create_all(pg_engine)
    with Session(pg_engine) as db:
        user = User(username="test", password_hash="unused", role=UserRole.ADMIN)
        db.add(user)
        db.flush()
        db.add(Voucher(voucher_number=1, voucher_type=VoucherType.GIFT, value_cents=1000,
                       original_value_cents=1000, remaining_value_cents=1000, created_by_user_id=user.id))
        db.commit()
    with pg_engine.begin() as conn:
        conn.execute(text("ALTER TABLE vouchers DROP COLUMN original_value_cents"))
        conn.execute(text("ALTER TABLE vouchers DROP COLUMN remaining_value_cents"))
    def fail(connection, cursor, statement, parameters, context, executemany):
        if "UPDATE vouchers" in statement and "original_value_cents = CASE" in statement:
            raise RuntimeError("interrupted value backfill")
    event.listen(pg_engine, "before_cursor_execute", fail)
    try:
        assert run_migrations(pg_engine) is False
    finally:
        event.remove(pg_engine, "before_cursor_execute", fail)
    assert run_migrations(pg_engine)
    assert run_migrations(pg_engine)
    with Session(pg_engine) as db:
        voucher = db.query(Voucher).one()
        assert (voucher.original_value_cents, voucher.remaining_value_cents, voucher.status) == (1000, 1000, VoucherStatus.CREATED)
