from sqlalchemy import inspect, text
from app.models.transaction import VoucherRedemption


def migrate_vouchers(engine):
    with engine.begin() as conn:
        if conn.dialect.name == "postgresql":
            conn.execute(text("DROP INDEX IF EXISTS ix_transactions_voucher_code"))
            conn.execute(text("ALTER TABLE transactions ALTER COLUMN voucher_code TYPE TEXT"))
        VoucherRedemption.__table__.create(conn, checkfirst=True)


def migrate_guests(engine):
    with engine.begin() as conn:
        columns = {c["name"] for c in inspect(conn).get_columns("guest_list_entries")}
        if "transaction_item_id" not in columns:
            conn.execute(text("ALTER TABLE guest_list_entries ADD COLUMN transaction_item_id INTEGER REFERENCES transaction_items(id)"))
            conn.execute(text("CREATE INDEX ix_guest_list_entries_transaction_item_id ON guest_list_entries(transaction_item_id)"))
