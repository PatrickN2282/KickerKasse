import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles/main.scss'
import { useAppSettingsStore } from '@/stores/appSettings'

const appBuildId = __APP_BUILD_ID__

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

const registerServiceWorker = () => {
  if (!('serviceWorker' in navigator)) {
    return
  }

  let refreshing = false
  let approvedUpdate = false
  let reloadFallback = null
  const serviceWorkerUrl = `/sw.js?build=${encodeURIComponent(appBuildId)}`

  const performRegistration = async () => {
    try {
      const registration = await navigator.serviceWorker.register(serviceWorkerUrl, {
        updateViaCache: 'none',
      })
      const offerUpdate = (worker) => {
        if (!worker) return
        window.dispatchEvent(new CustomEvent('kicker:pwa-update-ready', { detail: { worker } }))
      }

      if (registration.waiting) {
        offerUpdate(registration.waiting)
      }

      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing
        if (!newWorker) return

        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            offerUpdate(newWorker)
          }
        })
      })

      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (refreshing || !approvedUpdate) return
        refreshing = true
        if (reloadFallback) window.clearTimeout(reloadFallback)
        window.location.reload()
      })

      window.addEventListener('kicker:pwa-update-apply', (event) => {
        const worker = event.detail?.worker || registration.waiting
        if (!worker) return
        approvedUpdate = true
        worker.postMessage({ type: 'SKIP_WAITING' })
        // Some browsers do not emit controllerchange reliably when the waiting
        // worker already became active. Keep the explicit update action useful.
        reloadFallback = window.setTimeout(() => {
          if (refreshing) return
          refreshing = true
          window.location.reload()
        }, 1500)
      })

      await registration.update()
    } catch (err) {
      console.log('ServiceWorker registration failed: ', err)
    }
  }

  if (document.readyState === 'complete') {
    performRegistration()
  } else {
    window.addEventListener('load', performRegistration, { once: true })
  }
}

const bootstrap = async () => {
  const appSettingsStore = useAppSettingsStore(pinia)
  try {
    await appSettingsStore.loadPublicSettings()
  } catch (err) {
    console.error('[Bootstrap] Public settings are not ready yet:', err)
  }
  registerServiceWorker()
  app.mount('#app')
}

bootstrap()
