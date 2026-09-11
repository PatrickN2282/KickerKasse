from app.models import ZBonHistory


CENT_FIELDS = {
    "article_revenue_cents",
    "cash_sale_payments_cents",
    "balance_redeemed_cents",
    "voucher_redeemed_cents",
    "member_recharges_cents",
    "club_account_recharges_cents",
    "prepaid_sales_cents",
    "tip_donations_cents",
    "cash_opening_balance_cents",
    "cash_deposits_cents",
    "cash_withdrawals_cents",
    "cash_calculated_cents",
    "total_revenue_cents",
}


def test_zbon_history_persists_canonical_cent_fields_without_faking_old_values():
    columns = ZBonHistory.__table__.columns

    assert CENT_FIELDS <= set(columns.keys())
    assert all(columns[name].nullable for name in CENT_FIELDS)
