from app.constants import INTERNAL_MATERIAL_CATEGORY_NAME


def is_internal_material_product(product) -> bool:
    """Return whether a product belongs to the reserved internal-material category."""
    categories = getattr(product, "categories", None) or []
    return any(
        (getattr(category, "name", None) or "").strip() == INTERNAL_MATERIAL_CATEGORY_NAME
        for category in categories
    )


def resolve_catalog_unit_price_cents(product, member=None) -> int:
    """Resolve the configured regular/member price, including a valid 0-cent member price."""
    use_member_price = bool(
        member
        and getattr(member, "has_discount", False)
        and getattr(product, "is_discountable", False)
        and getattr(product, "member_price_cents", None) is not None
    )
    return int(product.member_price_cents if use_member_price else product.price_cents)


def resolve_sale_unit_price_cents(
    product,
    requested_unit_price_cents: int,
    *,
    is_internal_material: bool = False,
    member=None,
) -> int:
    """Resolve the authoritative sale price for direct sales and new Deckel items.

    Internal material is issued for 0 EUR and accounted for separately at its catalog
    value. Variable-price products retain the amount entered during checkout. All other
    client-supplied prices are replaced with the configured catalog/member price.
    """
    requested_unit_price_cents = int(requested_unit_price_cents)
    if requested_unit_price_cents < 0:
        raise ValueError("Der Artikelpreis darf nicht negativ sein")

    if is_internal_material:
        if not is_internal_material_product(product):
            raise ValueError(
                f"Produkt {product.name} gehört nicht zur Kategorie {INTERNAL_MATERIAL_CATEGORY_NAME}"
            )
        return 0

    if getattr(product, "is_variable_price", False):
        return requested_unit_price_cents

    return resolve_catalog_unit_price_cents(product, member)
