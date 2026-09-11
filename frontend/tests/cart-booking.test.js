import test from 'node:test'
import assert from 'node:assert/strict'
import { createServer } from 'vite'
import { createPinia, setActivePinia } from 'pinia'

test('guest lines preserve names and entered prices through failed checkout and removal', async () => {
  const server = await createServer({ server: { middlewareMode: true }, appType: 'custom' })
  try {
    const { useCartStore } = await server.ssrLoadModule('/src/stores/cart.js')
    const { default: api } = await server.ssrLoadModule('/src/services/api.js')
    setActivePinia(createPinia())
    const cart = useCartStore()
    const product = { id: 1, name: 'Gastbeitrag', price_cents: 125, stock_quantity: 10,
      is_variable_price: true, requires_guest_list: true, guests: [{ guest_first_name: 'Mara' }] }
    cart.addItem(product)
    cart.addItem({ ...product, price_cents: 275, guests: [{ guest_first_name: 'Kim' }] })
    assert.equal(cart.items.length, 2)
    assert.equal(cart.getTotalAmount(), 400)
    let sent
    api.post = async (path, body) => { sent = body; throw new Error('Simulated connection failure') }
    await assert.rejects(cart.checkout(1), /Simulated/)
    assert.equal(cart.items.length, 2)
    assert.deepEqual(sent.items.map(item => item.guests[0].guest_first_name), ['Mara', 'Kim'])
    cart.removeItem(cart.items[0].line_id)
    assert.equal(cart.items[0].guests[0].guest_first_name, 'Kim')
    api.post = async (path, body) => { sent = body; return { data: { id: 7 } } }
    await cart.checkout(1)
    assert.equal(sent.items.length, 1)
    assert.equal(sent.items[0].unit_price_cents, 275)
    assert.equal(cart.items.length, 0)
  } finally {
    await server.close()
  }
})

test('full member balance checkout confirms a zero cash remainder', async () => {
  const server = await createServer({ server: { middlewareMode: true }, appType: 'custom' })
  try {
    const { useCartStore } = await server.ssrLoadModule('/src/stores/cart.js')
    const { default: api } = await server.ssrLoadModule('/src/services/api.js')
    setActivePinia(createPinia())
    const cart = useCartStore()
    cart.selectedMemberId = 4
    cart.paymentMethod = 'BALANCE'
    cart.addItem({ id: 1, name: 'Getränk', price_cents: 500, stock_quantity: 10 })
    let sent
    api.post = async (_path, body) => { sent = body; return { data: { id: 8 } } }

    await cart.checkout(1, 1000)

    assert.equal(sent.expected_total_amount_cents, 0)
    assert.equal(sent.expected_member_balance_cents, 1000)
  } finally {
    await server.close()
  }
})
