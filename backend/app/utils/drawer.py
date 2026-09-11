MAIN_DRAWER = "main"
SMALL_PARTS_DRAWER = "small_parts"


def requires_small_parts_drawer(products) -> bool:
    """Return whether at least one product is stored in the small-parts drawer."""
    return any(bool(getattr(product, "opens_small_parts_drawer", False)) for product in products)


def _payment_method_value(payment_method) -> str:
    value = getattr(payment_method, "value", payment_method)
    return str(value or "").strip().upper()


def requires_main_drawer(
    payment_method,
    payable_amount_cents: int = 0,
    tip_cents: int = 0,
    cash_received_cents: int | None = None,
    change_given_cents: int | None = None,
) -> bool:
    """Return whether a completed payment required physical cash handling."""
    if _payment_method_value(payment_method) != "CASH":
        return False

    return any(
        int(amount or 0) > 0
        for amount in (
            payable_amount_cents,
            tip_cents,
            cash_received_cents,
            change_given_cents,
        )
    )


def drawer_targets_for_sale(
    products,
    payment_method,
    payable_amount_cents: int = 0,
    tip_cents: int = 0,
    cash_received_cents: int | None = None,
    change_given_cents: int | None = None,
) -> list[str]:
    """Return ordered logical drawers for a completed sale."""
    products = list(products)
    targets = []
    if requires_main_drawer(
        payment_method,
        payable_amount_cents,
        tip_cents,
        cash_received_cents,
        change_given_cents,
    ):
        targets.append(MAIN_DRAWER)
    if requires_small_parts_drawer(products):
        targets.append(SMALL_PARTS_DRAWER)
    return targets


def drawer_targets_for_stock_change(
    product,
    old_stock_quantity: int,
    new_stock_quantity: int,
    *,
    open_for_decrease: bool = False,
) -> list[str]:
    """Open storage for restocking, or for an explicitly physical stock removal."""
    if not bool(getattr(product, "opens_small_parts_drawer", False)):
        return []
    if bool(getattr(product, "is_unlimited_stock", False)):
        return []

    delta = int(new_stock_quantity) - int(old_stock_quantity)
    if delta > 0 or (delta < 0 and open_for_decrease):
        return [SMALL_PARTS_DRAWER]
    return []
