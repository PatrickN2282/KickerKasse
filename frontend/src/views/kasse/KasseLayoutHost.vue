<template>
  <component
    :is="currentLayoutComponent"
    v-if="currentLayoutComponent"
  />
</template>

<script setup>
import { markRaw, ref, shallowRef, watch } from 'vue'
import { useAppSettingsStore } from '@/stores/appSettings'

const LAYOUT_STORAGE_KEY = 'kasseLayout'
const layoutModules = import.meta.glob('@/views/kasse/Kasse*.vue')
const defaultLayout = 'Kasse'
const validLayouts = new Set(
  Object.keys(layoutModules).map((path) => path.match(/\/(Kasse(?:\d+)?)\.vue$/)?.[1]).filter(Boolean)
)
const currentLayoutComponent = shallowRef(null)
const appSettingsStore = useAppSettingsStore()

const getPreferredLayout = () => {
  const serverLayout = appSettingsStore.settings.kasse_layout
  if (serverLayout) {
    return serverLayout
  }

  return localStorage.getItem(LAYOUT_STORAGE_KEY) || defaultLayout
}

const getLayoutModule = (layoutName) => {
  const sanitizedLayout = typeof layoutName === 'string' && validLayouts.has(layoutName)
    ? layoutName
    : defaultLayout

  return layoutModules[`/src/views/kasse/${sanitizedLayout}.vue`]
    ?? layoutModules[`/src/views/kasse/${defaultLayout}.vue`]
}

const activeLoadId = ref(0)

watch(
  () => getPreferredLayout(),
  async (layoutName) => {
    const loadId = ++activeLoadId.value
    const moduleLoader = getLayoutModule(layoutName)
    const module = await moduleLoader()
    if (loadId !== activeLoadId.value) {
      return
    }
    currentLayoutComponent.value = markRaw(module.default)
  },
  { immediate: true }
)
</script>
