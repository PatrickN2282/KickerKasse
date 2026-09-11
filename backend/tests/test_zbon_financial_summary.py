from types import SimpleNamespace

from app.models import PaymentMethod
from app.services.zbon_service import ZBonService


def _item(total_cents: int, description: str = ""):
    return SimpleNamespace(
        total_price_cents=total_cents,
        product=SimpleNamespace(description=description),
    )


def _transaction(
    *,
    total_cents: int,
    payment_method=PaymentMethod.CASH,
    item_totals=(1000,),
    balance_cents: int = 0,
    voucher_cents: int = 0,
    tip_cents: int = 0,
):
    return SimpleNamespace(
        total_amount_cents=total_cents,
        payment_method=payment_method,
        balance_applied_cents=balance_cents,
        voucher_applied_cents=voucher_cents,
        tip_cents=tip_cents,
        items=[_item(value) for value in item_totals],
    )


def test_canonical_summary_separates_revenue_and_cash_movements():
    service = ZBonService(None)
    cash_sale = _transaction(total_cents=1000, tip_cents=200)
    mixed_sale = _transaction(
        total_cents=300,
        item_totals=(1000,),
        balance_cents=400,
        voucher_cents=300,
    )
    recharge = SimpleNamespace(total_amount_cents=2500)
    club_account_recharge = SimpleNamespace(total_amount_cents=9000)

    summary = service._build_financial_summary_cents(
        sales=[cash_sale, mixed_sale],
        member_recharges=[recharge],
        club_account_recharges=[club_account_recharge],
        prepaid_voucher_sales_cents=500,
        opening_cash_balance_cents=10000,
        cash_deposits_cents=700,
        cash_withdrawals_cents=1200,
    )

    assert summary["article_revenue_cents"] == 2000
    assert summary["cash_sale_payments_cents"] == 1300
    assert summary["balance_redeemed_cents"] == 400
    assert summary["voucher_redeemed_cents"] == 300
    assert summary["member_recharges_cents"] == 2500
    assert summary["club_account_recharges_cents"] == 9000
    assert summary["tip_donations_cents"] == 200
    assert summary["total_revenue_cents"] == 5000
    assert summary["cash_calculated_cents"] == 13500


def test_prepaid_items_are_reported_outside_article_revenue():
    service = ZBonService(None)
    sale = _transaction(total_cents=1500, item_totals=())
    sale.items = [
        _item(1000),
        _item(500, "VERZEHRKARTE:500"),
    ]

    summary = service._build_financial_summary_cents(
        sales=[sale],
        member_recharges=[],
        club_account_recharges=[],
        prepaid_voucher_sales_cents=500,
        opening_cash_balance_cents=0,
        cash_deposits_cents=0,
        cash_withdrawals_cents=0,
    )

    assert summary["article_revenue_cents"] == 1000
    assert summary["prepaid_sales_cents"] == 500
    assert summary["total_revenue_cents"] == 1500
    assert summary["cash_sale_payments_cents"] == 1500
    assert summary["cash_calculated_cents"] == 1500


def test_club_account_recharge_does_not_change_cash_target():
    service = ZBonService(None)
    summary = service._build_financial_summary_cents(
        sales=[],
        member_recharges=[],
        club_account_recharges=[SimpleNamespace(total_amount_cents=5000)],
        prepaid_voucher_sales_cents=0,
        opening_cash_balance_cents=1000,
        cash_deposits_cents=0,
        cash_withdrawals_cents=0,
    )

    assert summary["club_account_recharges_cents"] == 5000
    assert summary["cash_calculated_cents"] == 1000
