import test from 'node:test'
import assert from 'node:assert/strict'
import axios from 'axios'
import { installBookingRetry } from '../src/services/booking-retry.js'

const storage = () => {
  const values = new Map()
  return { getItem: key => values.get(key), setItem: (key, value) => values.set(key, value) }
}
const reply = (config, data) => ({ config, data, status: 200, statusText: 'OK', headers: {} })

test('lost response recovers server result before retrying and never repeats drawer action', async () => {
  const store = storage()
  let posts = 0
  const client = axios.create({ adapter: async config => {
    if (config.method === 'get') return reply(config, { response: { id: 17, receipt_number: 82, drawer_targets: ['main'] }, response_status: 201 })
    posts++
    throw Object.assign(new Error('connection lost after commit'), { config })
  } })
  const pending = installBookingRetry(client, () => store)
  const body = { amount_cents: 500, auth_password: 'never-persist-this' }
  await assert.rejects(client.post('/members/1/recharge', body))
  assert.equal(pending.list().length, 1)
  assert.ok(!store.getItem('kickerkasse.pending-bookings.v1:session').includes('never-persist-this'))
  const result = await client.post('/members/1/recharge', { ...body, auth_password: 'fresh-confirmation' })
  assert.equal(posts, 1)
  assert.equal(result.data.receipt_number, 82)
  assert.deepEqual(result.data.drawer_targets, [])
  assert.equal(pending.list().length, 0)
})

test('unknown operation retries with the same key; changed payload remains blocked', async () => {
  const keys = []
  const client = axios.create({ adapter: async config => {
    if (config.method === 'get') throw Object.assign(new Error('not committed'), { config, response: { status: 404 } })
    keys.push(config.headers['Idempotency-Key'])
    if (keys.length === 1) throw Object.assign(new Error('offline'), { config })
    return reply(config, { id: 8 })
  } })
  const pending = installBookingRetry(client, () => store)
  const store = storage()
  await assert.rejects(client.post('/deckel', { name: 'Test', items: [] }))
  await assert.rejects(client.post('/deckel', { name: 'Changed', items: [] }), /ungeklärt/)
  assert.equal(keys.length, 1)
  await client.post('/deckel', { name: 'Test', items: [] })
  assert.equal(keys[0], keys[1])
  assert.equal(pending.list().length, 0)
})

test('reloaded client keeps pending identifier, while explicit validation rejection releases it', async () => {
  const store = storage()
  const create = () => axios.create({ adapter: async config => {
    throw Object.assign(new Error('offline'), { config })
  } })
  const first = create()
  const pending = installBookingRetry(first, () => store)
  await assert.rejects(first.post('/transactions/sale', { items: [] }))
  const saved = pending.list()[0].key
  const second = axios.create({ adapter: async config => {
    throw Object.assign(new Error('invalid'), { config, response: { status: config.method === 'get' ? 404 : 422 } })
  } })
  const restored = installBookingRetry(second, () => store)
  assert.equal(restored.list()[0].key, saved)
  await assert.rejects(second.post('/transactions/sale', { items: [] }))
  assert.equal(restored.list().length, 0)
})

test('a confirmed conflict releases the pending operation for corrected input', async () => {
  const store = storage()
  const client = axios.create({ adapter: async config => {
    throw Object.assign(new Error('confirmation changed'), {
      config,
      response: { status: 409, data: { detail: { code: 'SALE_CONFIRMATION_CHANGED' } } },
    })
  } })
  const pending = installBookingRetry(client, () => store)

  await assert.rejects(client.post('/transactions/sale', { items: [{ product_id: 1 }] }))

  assert.equal(pending.list().length, 0)
})
