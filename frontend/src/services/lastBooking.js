const asCents = (value) => {
  const cents = Number(value || 0)
  return Number.isFinite(cents) ? cents : 0
}

export const getLastBookingGrossAmountCents = (booking) => {
  if (!booking) return 0
  if (Array.isArray(booking.items) && booking.items.length > 0) {
    return booking.items.reduce((sum, item) => {
      const lineTotal = item.total_price_cents == null
        ? asCents(item.quantity) * asCents(item.unit_price_cents)
        : asCents(item.total_price_cents)
      return sum + lineTotal
    }, 0)
  }
  return asCents(booking.total_amount_cents)
    + asCents(booking.balance_applied_cents)
    + asCents(booking.voucher_applied_cents)
}

const voucherLabel = (voucherType) => {
  if (voucherType === 'GIFT') return 'Gutschein'
  if (voucherType === 'PREPAID') return 'Verzehrkarte'
  return 'Gutschein / Verzehrkarte'
}

export const getLastBookingPaymentLabel = (booking) => {
  if (!booking) return ''
  const parts = []
  if (asCents(booking.voucher_applied_cents) > 0
      || ['VOUCHER_GIFT', 'VOUCHER_PREPAID'].includes(booking.payment_method)) {
    const type = booking.voucher_type
      || (booking.payment_method === 'VOUCHER_GIFT' ? 'GIFT' : null)
      || (booking.payment_method === 'VOUCHER_PREPAID' ? 'PREPAID' : null)
    parts.push(voucherLabel(type))
  }
  if (asCents(booking.balance_applied_cents) > 0 || booking.payment_method === 'BALANCE') {
    parts.push('Guthaben')
  }
  if (booking.payment_method === 'CASH' && asCents(booking.total_amount_cents) > 0) {
    parts.push('Bar')
  }
  if (parts.length === 0 && booking.payment_method === 'CASH') parts.push('Bar')
  return [...new Set(parts)].join(' + ')
}
