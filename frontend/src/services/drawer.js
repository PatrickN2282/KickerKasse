import { LOCAL_HARDWARE_AGENT_BASE_URL } from '@/constants'

export const DRAWER_TARGETS = Object.freeze({
  MAIN: 'main',
  SMALL_PARTS: 'small_parts',
})

const normalizeTargets = (targets) => [...new Set(
  (Array.isArray(targets) ? targets : [])
    .filter(target => Object.values(DRAWER_TARGETS).includes(target))
)]

const targetPath = target => (
  target === DRAWER_TARGETS.SMALL_PARTS ? '/openDrawer/small_parts' : '/openDrawer'
)

const fetchWithTimeout = async (url, options = {}, timeoutMs = 2500) => {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    return await fetch(url, { ...options, signal: controller.signal })
  } finally {
    window.clearTimeout(timeoutId)
  }
}

export const openDrawer = async (target = DRAWER_TARGETS.MAIN) => {
  if (!Object.values(DRAWER_TARGETS).includes(target)) {
    throw new Error(`Unbekanntes Schubladenziel: ${target}`)
  }

  const url = `${LOCAL_HARDWARE_AGENT_BASE_URL}${targetPath(target)}`
  try {
    // Never retry here: the agent may have processed a pulse even when the
    // browser loses the response. A paired origin makes the result readable.
    const response = await fetchWithTimeout(url, { method: 'POST' })
    let data = {}
    try {
      data = await response.json()
    } catch {
      // Keep the status-based fallback when an older agent has no JSON body.
    }
    if (!response.ok) {
      throw new Error(data?.message || `Hardware-Agent antwortet mit Status ${response.status}`)
    }
    return { target, opened: true, data }
  } catch (error) {
    console.warn(`[Drawer] ${target} konnte nicht geöffnet werden`, error?.message)
    return { target, opened: false, error }
  }
}

export const openDrawerTargets = async (targets) => {
  const results = []
  for (const target of normalizeTargets(targets)) {
    results.push(await openDrawer(target))
  }
  return results
}

export const failedDrawerTargets = results => (
  (Array.isArray(results) ? results : []).filter(result => !result.opened).map(result => result.target)
)

export const drawerTargetLabel = target => (
  target === DRAWER_TARGETS.SMALL_PARTS ? 'Kleinteile-Lager' : 'Hauptschublade'
)

export const failedDrawerTargetLabels = results => (
  failedDrawerTargets(results).map(drawerTargetLabel)
)
