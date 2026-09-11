// Persist only identifiers and fingerprints, never passwords or guest/payment payloads.
const storageKey = 'kickerkasse.pending-bookings.v1'
const pattern = /^\/(transactions\/(sale|cash\/(deposit|withdrawal)|zbon\/create|voucher\/.*)|members\/\d+\/recharge|deckel(?:\/\d+\/(book|pay))?|admin\/vouchers(?:\/.*)?)$/
const canonical = value => Array.isArray(value) ? value.map(canonical)
  : value && typeof value === 'object' ? Object.fromEntries(Object.keys(value).sort()
    .filter(key => key !== 'auth_password').map(key => [key, canonical(value[key])])) : value

// getRandomValues also supports local HTTP installations without WebCrypto.subtle.
const operationId = () => {
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  bytes[6] = (bytes[6] & 15) | 64
  bytes[8] = (bytes[8] & 63) | 128
  const hex = [...bytes].map(byte => byte.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}
// Local equality check only; the server independently verifies a SHA-256 fingerprint.
const localFingerprint = bytes => {
  let a = 14695981039346656037n
  let b = 7809847782465536322n
  for (const byte of bytes) {
    a = BigInt.asUintN(64, (a ^ BigInt(byte)) * 1099511628211n)
    b = BigInt.asUintN(64, (b ^ BigInt(byte)) * 14029467366897019727n)
  }
  return a.toString(16).padStart(16, '0') + b.toString(16).padStart(16, '0')
}

export function installBookingRetry(client, storage = () => window.sessionStorage) {
  const running = new Set()
  let actor = null
  const scopedKey = () => `${storageKey}:${actor ?? "session"}`
  const read = () => JSON.parse(storage().getItem(scopedKey()) || '{}')
  const write = value => {
    storage().setItem(scopedKey(), JSON.stringify(value))
    if (typeof window !== 'undefined') window.dispatchEvent(new Event('pending-bookings-changed'))
  }
  const failure = detail => Object.assign(new Error(detail), { response: { data: { detail } } })
  client.interceptors.request.use(async config => {
    const path = String(config.url || '').replace(/\/$/, '')
    if (config.method !== 'post' || !pattern.test(path)) return config
    if (running.has(path)) throw failure('Dieser Vorgang wird bereits geprüft oder gebucht. Bitte warten.')
    running.add(path)
    try {
      const bytes = new TextEncoder().encode(JSON.stringify(canonical(config.data)))
      const digest = localFingerprint(bytes)
      const pending = read()
      const previous = pending[path]
      if (previous && previous.digest !== digest) {
        throw failure('Eine frühere Buchung ist noch ungeklärt. Bitte zuerst ihren Status prüfen oder die unveränderte Buchung erneut bestätigen.')
      }
      const entry = previous || { key: operationId(), digest, path }
      pending[path] = entry
      write(pending)
      config.bookingPath = path
      config.headers['Idempotency-Key'] = entry.key
      if (previous) {
        try {
          const status = await client.get(`/transactions/operations/${entry.key}`)
          config.adapter = async () => ({ data: { ...status.data.response, drawer_targets: [] },
            status: status.data.response_status, statusText: 'Recovered', headers: {}, config })
        } catch (error) {
          if (error.response?.status !== 404) throw error
        }
      }
      return config
    } catch (error) {
      running.delete(path)
      throw error
    }
  })
  client.interceptors.response.use(response => {
    const path = response.config?.bookingPath
    if (path) {
      const pending = read()
      delete pending[path]
      write(pending)
      running.delete(path)
      if (response.headers?.['idempotency-replayed'] === 'true') response.data.drawer_targets = []
    }
    return response
  }, error => {
    const path = error.config?.bookingPath
    if (path) {
      running.delete(path)
      // An explicit validation/auth rejection committed no booking. Unknown outcomes retain the key.
      if ([400, 401, 403, 404, 409, 422].includes(error.response?.status)) {
        const pending = read()
        delete pending[path]
        write(pending)
      } else if (!error.response || error.response.status >= 500) {
        error.response = { ...(error.response || {}), data: {
          detail: 'Buchung noch nicht bestätigt. Bitte unverändert erneut bestätigen: Zuerst wird der gespeicherte Status geprüft.' } }
      }
    }
    return Promise.reject(error)
  })
  return {
    setActor(id) { actor = id; if (typeof window !== 'undefined') window.dispatchEvent(new Event('pending-bookings-changed')) },
    list: () => Object.values(read()),
    async resolve(entry) {
      if (running.has(entry.path)) throw failure('Die Buchung läuft noch. Bitte warten.')
      const status = await client.get(`/transactions/operations/${entry.key}`)
      return status.data.response
    },
    acknowledge(entry) {
      const pending = read()
      if (pending[entry.path]?.key === entry.key) delete pending[entry.path]
      write(pending)
    },
  }
}
