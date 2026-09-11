from datetime import date

from app.models import ClubAccountEntry, PaymentMethod, Transaction, TransactionType, User, UserRole
from app.services.transaction_service import TransactionService
from app.services.voucher_service import VoucherService


def _user(db_session):
    user = User(username="voucher-admin", role=UserRole.TOP_ADMIN, password_hash="unused")
    db_session.add(user)
    db_session.commit()
    return user


def test_voucher_preparation_does_not_create_financial_transactions(db_session):
    user = _user(db_session)
    service = VoucherService(db_session)

    service.create_gift_voucher(500, "PROMOTION", user.id)
    service.create_prepaid_vouchers(1000, user.id, quantity=2)

    assert db_session.query(Transaction).count() == 0
    gift_entry = db_session.query(ClubAccountEntry).one()
    assert gift_entry.amount_cents == -500
    assert gift_entry.transaction_id is None


def test_legacy_voucher_creation_rows_are_hidden_from_transaction_lists(db_session):
    user = _user(db_session)
    db_session.add(Transaction(
        receipt_number=1,
        type=TransactionType.VOUCHER_CREATE,
        payment_method=PaymentMethod.VOUCHER_GIFT,
        total_amount_cents=0,
        user_id=user.id,
    ))
    db_session.commit()

    service = TransactionService(db_session)

    assert service.get_all_transactions() == []
    assert service.get_daily_stats(date.today())["transactions"] == []
    assert service.get_filtered_transactions(date.today(), date.today())["transactions"] == []
