def validate_cash_payment(
    payment_method: str,
    payable_amount_cents: int,
    tip_cents: int = 0,
    cash_received_cents: int | None = None,
) -> int | None:
    """Validate cash tendering and return the change that must be paid out."""
    tip_cents = int(tip_cents or 0)
    if tip_cents < 0:
        raise ValueError("Trinkgeld darf nicht negativ sein")

    if payment_method != "CASH":
        if tip_cents > 0:
            raise ValueError("Trinkgeld ist nur bei einer Barzahlung möglich")
        if cash_received_cents not in (None, 0):
            raise ValueError("Ein Barbetrag ist nur bei einer Barzahlung zulässig")
        return None

    if cash_received_cents is None:
        if tip_cents > 0:
            raise ValueError("Für Trinkgeld muss der gegebene Barbetrag übermittelt werden")
        if int(payable_amount_cents) > 0:
            raise ValueError("Für eine Barzahlung muss der gegebene Barbetrag übermittelt werden")
        return 0

    cash_received_cents = int(cash_received_cents)
    required_cents = int(payable_amount_cents) + tip_cents
    if cash_received_cents < required_cents:
        raise ValueError("Der gegebene Barbetrag reicht für Zahlung und Trinkgeld nicht aus")
    return cash_received_cents - required_cents
