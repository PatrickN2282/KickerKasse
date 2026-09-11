import test from 'node:test'
import assert from 'node:assert/strict'
import {
  getLastBookingGrossAmountCents,
  getLastBookingPaymentLabel,
} from '../src/services/lastBooking.js'

test('last booking shows the merchandise value for a full balance payment', () => {
  const booking = {
    payment_method: 'BALANCE',
    total_amount_cents: 0,
    balance_applied_cents: 650,
    voucher_applied_cents: 0,
    items: [{ quantity: 1, unit_price_cents: 650, total_price_cents: 650 }],
  }

  assert.equal(getLastBookingGrossAmountCents(booking), 650)
  assert.equal(getLastBookingPaymentLabel(booking), 'Guthaben')
})

test('last booking describes combined voucher, balance and cash payment', () => {
  const booking = {
    payment_method: 'CASH',
    voucher_type: 'GIFT',
    total_amount_cents: 200,
    balance_applied_cents: 300,
    voucher_applied_cents: 500,
    items: [{ quantity: 2, unit_price_cents: 500, total_price_cents: 1000 }],
  }

  assert.equal(getLastBookingGrossAmountCents(booking), 1000)
  assert.equal(getLastBookingPaymentLabel(booking), 'Gutschein + Guthaben + Bar')
})
