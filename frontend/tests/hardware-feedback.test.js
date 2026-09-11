import test from 'node:test'
import assert from 'node:assert/strict'
import { createServer } from 'vite'

test('drawer failures retain distinct user-facing target names', async () => {
  const server = await createServer({ server: { middlewareMode: true }, appType: 'custom' })
  try {
    const { failedDrawerTargetLabels } = await server.ssrLoadModule('/src/services/drawer.js')
    const labels = failedDrawerTargetLabels([
      { target: 'main', opened: false },
      { target: 'small_parts', opened: false },
      { target: 'main', opened: true },
    ])
    assert.deepEqual(labels, ['Hauptschublade', 'Kleinteile-Lager'])
  } finally {
    await server.close()
  }
})
