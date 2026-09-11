import pytest

from app.utils.cash_payment import validate_cash_payment


def test_variable_tip_reduces_change():
    change = validate_cash_payment(
        "CASH",
        payable_amount_cents=1000,
        tip_cents=200,
        cash_received_cents=1500,
    )

    assert change == 300


def test_full_change_can_be_donated():
    change = validate_cash_payment(
        "CASH",
        payable_amount_cents=1000,
        tip_cents=500,
        cash_received_cents=1500,
    )

    assert change == 0


def test_tip_cannot_exceed_available_change():
    with pytest.raises(ValueError, match="reicht für Zahlung und Trinkgeld nicht aus"):
        validate_cash_payment(
            "CASH",
            payable_amount_cents=1000,
            tip_cents=501,
            cash_received_cents=1500,
        )


def test_tip_is_rejected_for_non_cash_payment():
    with pytest.raises(ValueError, match="nur bei einer Barzahlung"):
        validate_cash_payment(
            "BALANCE",
            payable_amount_cents=1000,
            tip_cents=100,
        )


def test_positive_cash_checkout_requires_tendered_amount():
    with pytest.raises(ValueError, match="Barbetrag.*übermittelt"):
        validate_cash_payment("CASH", 1000)


def test_zero_euro_cash_checkout_does_not_require_tendered_amount():
    assert validate_cash_payment("CASH", 0) == 0


def test_zero_euro_cash_checkout_accepts_explicit_zero():
    assert validate_cash_payment("CASH", 0, cash_received_cents=0) == 0
