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
  const serviceWorkerUrl = `/sw.js?build=${encodeURIComponent(appBuildId)}`

  window.addEventListener('load', async () => {
    try {
      const registration = await navigator.serviceWorker.register(serviceWorkerUrl, {
        updateViaCache: 'none',
      })
      const activateWorker = (worker) => worker?.postMessage({ type: 'SKIP_WAITING' })

      if (registration.waiting) {
        activateWorker(registration.waiting)
      }

      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing
        if (!newWorker) return

        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            activateWorker(newWorker)
          }
        })
      })

      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (refreshing) return
        refreshing = true
        window.location.reload()
      })

      await registration.update()
    } catch (err) {
      console.log('ServiceWorker registration failed: ', err)
    }
  })
}

const bootstrap = async () => {
  const appSettingsStore = useAppSettingsStore(pinia)
  await appSettingsStore.loadPublicSettings()
  registerServiceWorker()
  app.mount('#app')
}

bootstrap()
