import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles/main.scss'
import { useAppSettingsStore } from '@/stores/appSettings'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

const bootstrap = async () => {
  const appSettingsStore = useAppSettingsStore(pinia)
  await appSettingsStore.loadPublicSettings()

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch(err => {
        console.log('ServiceWorker registration failed: ', err)
      })
    })
  }

  app.mount('#app')
}

bootstrap()
