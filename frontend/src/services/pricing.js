export const hasConfiguredMemberPrice = (product) => (
  product?.member_price_cents !== null && product?.member_price_cents !== undefined
)

export const resolveDisplayedUnitPriceCents = (
  product,
  { memberSelected = false, memberHasDiscount = false, internalMaterial = false } = {}
) => {
  if (internalMaterial || product?.is_internal_material) {
    return 0
  }

  if (
    memberSelected
    && memberHasDiscount
    && product?.is_discountable !== false
    && hasConfiguredMemberPrice(product)
  ) {
    return Number(product.member_price_cents)
  }

  return Number(product?.price_cents ?? product?.regular_price_cents ?? 0)
}
