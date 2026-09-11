from decimal import Decimal, InvalidOperation

COINS = {Decimal(x) for x in ("0.01", "0.02", "0.05", "0.10", "0.20", "0.50", "1", "2")}
NOTES = {Decimal(x) for x in ("5", "10", "20", "50", "100", "200", "500")}


def euro_cents(value):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0 or amount * 100 != (amount * 100).to_integral_value():
            raise ValueError()
        return int(amount * 100)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Der Zählbetrag muss endlich, nichtnegativ und centgenau sein.")


def cash_count_cents(count, total=None):
    supplied = euro_cents(total) if total is not None else None
    if count is None:
        return supplied
    if not isinstance(count, dict) or set(count) - {"coins", "notes"}:
        raise ValueError("Ungültiges Zählprotokoll.")
    result = 0
    for group, allowed in (("coins", COINS), ("notes", NOTES)):
        values = count.get(group) or {}
        if not isinstance(values, dict):
            raise ValueError("Ungültige Stückelungen.")
        seen = set()
        for denomination, quantity in values.items():
            try:
                denomination = Decimal(str(denomination))
            except InvalidOperation:
                raise ValueError("Ungültige Stückelung.")
            if denomination not in allowed or denomination in seen:
                raise ValueError("Unzulässige oder doppelte Stückelung.")
            seen.add(denomination)
            if type(quantity) is not int or quantity < 0 or quantity > 1000000:
                raise ValueError("Stückzahlen müssen nichtnegative ganze Zahlen sein (maximal 1.000.000).")
            result += int(denomination * 100) * quantity
    if supplied is not None and supplied != result:
        raise ValueError("Zählprotokoll und angegebene Summe stimmen nicht überein.")
    return result
