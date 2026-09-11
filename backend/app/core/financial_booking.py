"""Shared receipt allocation and ordering of bookings against cash closures."""
from sqlalchemy import text, func

LOCK_ID = 716811


def lock_financial_period(db):
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": LOCK_ID})


def next_receipt_number(db, *, allocate=True):
    from app.models import Transaction, CashEntry, ReceiptCounter
    if allocate:
        lock_financial_period(db)
    highest = max(db.query(func.max(Transaction.receipt_number)).scalar() or 0,
                  db.query(func.max(CashEntry.receipt_number)).scalar() or 0)
    counter = db.get(ReceiptCounter, 1, populate_existing=True)
    value = max(highest, counter.last_number if counter else 0) + 1
    if allocate:
        if counter is None:
            counter = ReceiptCounter(id=1, last_number=value)
            db.add(counter)
        else:
            counter.last_number = value
        db.flush()
    return value
