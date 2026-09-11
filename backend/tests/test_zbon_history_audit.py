import json
from datetime import datetime
from types import SimpleNamespace

from app.services.zbon_service import ZBonService


def _history(summary=None, cash_calculated=0.0):
    return SimpleNamespace(
        sequence_number=12,
        business_date=datetime(2026, 8, 31),
        period_start=datetime(2026, 8, 30, 12),
        period_end=datetime(2026, 8, 31, 18),
        cash_calculated=cash_calculated,
        cash_counted=None,
        report_data=json.dumps({"summary": summary}) if summary is not None else None,
    )


def test_history_audit_accepts_consistent_cent_archive():
    history = _history({
        "cash_opening_balance_cents": 10000,
        "cash_sale_payments_cents": 2500,
        "member_recharges_cents": 1000,
        "tip_donations_cents": 150,
        "cash_deposits_cents": 500,
        "cash_withdrawals_cents": 2000,
        "cash_calculated_cents": 12150,
    })

    result = ZBonService._audit_history_record(history)

    assert result["status"] == "consistent"
    assert result["recalculated_cash_cents"] == 12150
    assert result["difference_cents"] == 0


def test_history_audit_flags_legacy_difference():
    history = _history({
        "opening_cash_balance": 100.0,
        "article_cash_sales_total": 25.0,
        "recharge_total": 10.0,
        "tip_total": 1.5,
        "cash_deposits_total": 5.0,
        "cash_withdrawals_total": 20.0,
    }, cash_calculated=120.0)

    result = ZBonService._audit_history_record(history)

    assert result["status"] == "mismatch"
    assert result["recalculated_cash_cents"] == 12150
    assert result["difference_cents"] == -150


def test_history_audit_does_not_guess_without_archived_components():
    result = ZBonService._audit_history_record(_history())

    assert result["status"] == "insufficient_data"
    assert result["difference_cents"] is None
