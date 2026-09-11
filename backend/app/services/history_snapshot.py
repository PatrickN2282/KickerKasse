from types import SimpleNamespace

LEGACY_GROUP = "Altbestand – Warengruppe unbekannt"
LEGACY_CATEGORY = "Altbestand – Kategorie unbekannt"


def historical_product(item):
    """Never substitute today's catalog for missing historical assignments."""
    category = getattr(item, "category_name", None) or LEGACY_CATEGORY
    return SimpleNamespace(
        name=getattr(item, "product_name", None) or f"Altbestand – Produkt #{item.product_id}",
        warengruppe=getattr(item, "product_group_name", None) or LEGACY_GROUP,
        tax_rate=getattr(item, "tax_rate_snapshot", None) or 0,
        categories=[SimpleNamespace(name=category)],
    )


def booking_type(transaction, club_ids):
    value = getattr(transaction, "booking_type", None)
    if value:
        return value
    if transaction.type.value == "RECHARGE":
        return "CLUB_ACCOUNT_TOP_UP" if transaction.id in club_ids else "MEMBER_BALANCE_RECHARGE"
    return transaction.type.value
