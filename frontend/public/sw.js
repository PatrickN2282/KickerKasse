const buildId = new URL(self.location.href).searchParams.get('build') || 'dev'
const CACHE_NAME = `kickerkasse-${buildId}`
const urlsToCache = [
  '/',
  '/index.html',
  '/api/app-settings/manifest.webmanifest',
  '/api/app-settings/logo',
  '/api/app-settings/favicon.png',
  '/api/app-settings/icon-192.png',
  '/api/app-settings/icon-512.png',
]

const isCacheableAppSettingsAsset = (url) => {
  return url.includes('/api/app-settings/manifest.webmanifest')
    || url.includes('/api/app-settings/logo')
    || url.includes('/api/app-settings/favicon.png')
    || url.includes('/api/app-settings/icon-192.png')
    || url.includes('/api/app-settings/icon-512.png')
    || url.includes('/api/app-settings/apple-touch-icon.png')
}

self.addEventListener('message', event => {
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting()
  }
})

const updateCache = async (request, response) => {
  if (!response || response.status !== 200 || request.method !== 'GET') {
    return response
  }

  const responseToCache = response.clone()
  const cache = await caches.open(CACHE_NAME)
  await cache.put(request, responseToCache)
  return response
}

const networkFirst = async (request, fallbackUrl = null) => {
  try {
    const response = await fetch(request, { cache: 'no-store' })
    return updateCache(request, response)
  } catch {
    const cachedResponse = await caches.match(request)
    if (cachedResponse) {
      return cachedResponse
    }
    return fallbackUrl ? caches.match(fallbackUrl) : Response.error()
  }
}

const cacheFirst = async (request) => {
  const cachedResponse = await caches.match(request)
  if (cachedResponse) {
    return cachedResponse
  }

  const response = await fetch(request)
  return updateCache(request, response)
}

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  )
  self.skipWaiting()
})

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') {
    return
  }

  const requestUrl = event.request.url

  if (requestUrl.includes('/api/') && !isCacheableAppSettingsAsset(requestUrl)) {
    return
  }

  if (event.request.mode === 'navigate' || event.request.destination === 'document') {
    event.respondWith(networkFirst(event.request, '/index.html'))
    return
  }

  if (isCacheableAppSettingsAsset(requestUrl)) {
    event.respondWith(networkFirst(event.request))
    return
  }

  event.respondWith(cacheFirst(event.request))
})

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => Promise.all(
      cacheNames.map(cacheName => {
        if (cacheName !== CACHE_NAME) {
          return caches.delete(cacheName)
        }
        return Promise.resolve()
      })
    )).then(() => self.clients.claim())
  )
})
