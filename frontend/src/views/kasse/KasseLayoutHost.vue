<template>
  <component
    :is="currentLayoutComponent"
    v-if="currentLayoutComponent"
  />
</template>

<script setup>
import { markRaw, shallowRef, watch } from 'vue'
import { useAppSettingsStore } from '@/stores/appSettings'

const LAYOUT_STORAGE_KEY = 'kasseLayout'
const layoutModules = import.meta.glob('@/views/kasse/Kasse*.vue')
const defaultLayout = 'Kasse'
const currentLayoutComponent = shallowRef(null)
const appSettingsStore = useAppSettingsStore()

const getLayoutModule = (layoutName) => {
  const sanitizedLayout = typeof layoutName === 'string' && /^Kasse(?:\d+)?$/.test(layoutName)
    ? layoutName
    : defaultLayout

  return layoutModules[`/src/views/kasse/${sanitizedLayout}.vue`]
    ?? layoutModules[`/src/views/kasse/${defaultLayout}.vue`]
}

let activeLoadId = 0

watch(
  () => appSettingsStore.settings.kasse_layout || localStorage.getItem(LAYOUT_STORAGE_KEY) || defaultLayout,
  async (layoutName) => {
    const loadId = ++activeLoadId
    const moduleLoader = getLayoutModule(layoutName)
    const module = await moduleLoader()
    if (loadId !== activeLoadId) {
      return
    }
    currentLayoutComponent.value = markRaw(module.default)
  },
  { immediate: true }
)
</script>
