import test from 'node:test'
import assert from 'node:assert/strict'

import {
  hasConfiguredMemberPrice,
  resolveDisplayedUnitPriceCents,
} from '../src/services/pricing.js'

const fixedProduct = {
  price_cents: 500,
  member_price_cents: 350,
  is_discountable: true,
}

test('uses the configured regular price without an eligible member', () => {
  assert.equal(resolveDisplayedUnitPriceCents(fixedProduct), 500)
})

test('uses the member price only for an eligible member and discountable product', () => {
  assert.equal(resolveDisplayedUnitPriceCents(fixedProduct, {
    memberSelected: true,
    memberHasDiscount: true,
  }), 350)
  assert.equal(resolveDisplayedUnitPriceCents({ ...fixedProduct, is_discountable: false }, {
    memberSelected: true,
    memberHasDiscount: true,
  }), 500)
})

test('accepts a configured zero-cent member price', () => {
  const product = { ...fixedProduct, member_price_cents: 0 }
  assert.equal(hasConfiguredMemberPrice(product), true)
  assert.equal(resolveDisplayedUnitPriceCents(product, {
    memberSelected: true,
    memberHasDiscount: true,
  }), 0)
})

test('always displays explicitly booked internal material at zero euros', () => {
  assert.equal(resolveDisplayedUnitPriceCents({ ...fixedProduct, is_internal_material: true }, {
    memberSelected: true,
    memberHasDiscount: true,
  }), 0)
})

test('keeps the cashier-entered price of a variable-price cart product', () => {
  const variableCartProduct = {
    price_cents: 225,
    member_price_cents: null,
    is_variable_price: true,
  }
  assert.equal(resolveDisplayedUnitPriceCents(variableCartProduct), 225)
})
