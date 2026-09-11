from sqlalchemy import inspect, text
from app.models import ReceiptCounter, BookingOperation


def migrate_closures(engine):
    ReceiptCounter.__table__.create(engine, checkfirst=True)
    with engine.begin() as conn:
        for table in ("transactions", "cash_entries"):
            if "zbon_history_id" not in {c["name"] for c in inspect(conn).get_columns(table)}:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN zbon_history_id INTEGER REFERENCES zbon_history(id)"))
                conn.execute(text(f"CREATE INDEX ix_{table}_zbon_history_id ON {table}(zbon_history_id)"))
                # Preserve existing archive boundaries; never change archived report snapshots.
                conn.execute(text(f"""UPDATE {table} SET zbon_history_id = (
                    SELECT id FROM zbon_history z WHERE {table}.created_at <= z.period_end
                    ORDER BY z.sequence_number LIMIT 1)"""))


def migrate_operations(engine):
    BookingOperation.__table__.create(engine, checkfirst=True)
