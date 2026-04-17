const CACHE_NAME = 'kickerkasse-v2'
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

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  )
})

self.addEventListener('fetch', event => {
  const requestUrl = event.request.url

  if (requestUrl.includes('/api/') && !isCacheableAppSettingsAsset(requestUrl)) {
    return
  }

  event.respondWith(
    caches.match(event.request).then(response => {
      if (response) {
        return response
      }

      return fetch(event.request).then(networkResponse => {
        if (networkResponse.status === 200 && event.request.method === 'GET') {
          const responseToCache = networkResponse.clone()
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseToCache)
          })
        }

        return networkResponse
      }).catch(() => caches.match('/index.html'))
    })
  )
})

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => Promise.all(
      cacheNames.map(cacheName => {
        if (cacheName !== CACHE_NAME) {
          return caches.delete(cacheName)
        }
      })
    ))
  )
})
