<template>
  <button
    v-if="canInstall"
    type="button"
    class="install-btn"
    @click="installApp"
  >
    ⬇️ App installieren
  </button>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'

const canInstall = ref(false)
let deferredPrompt = null

const isStandaloneMode = () => {
  return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true
}

const handleBeforeInstallPrompt = (event) => {
  event.preventDefault()
  deferredPrompt = event
  canInstall.value = !isStandaloneMode()
}

const handleAppInstalled = () => {
  deferredPrompt = null
  canInstall.value = false
}

const installApp = async () => {
  if (!deferredPrompt) {
    return
  }

  deferredPrompt.prompt()
  await deferredPrompt.userChoice
  deferredPrompt = null
  canInstall.value = false
}

onMounted(() => {
  canInstall.value = !isStandaloneMode() && !!deferredPrompt
  window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
  window.addEventListener('appinstalled', handleAppInstalled)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
  window.removeEventListener('appinstalled', handleAppInstalled)
})
</script>

<style scoped lang="scss">
.install-btn {
  background: var(--app-highlight-color);
  color: white;
  border: none;
  border-radius: 999px;
  padding: 0.28rem 0.6rem;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s ease;
  white-space: nowrap;

  &:hover {
    opacity: 0.9;
  }
}
</style>
