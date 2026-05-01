import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import apiService from '@/services/api'
import { getContrastColor } from '@/services/utils'

const fallbackSettings = {
  app_name: 'KGB - KickerKasse',
  background_color: '#D7DCE2',
  banner_color: '#131820',
  highlight_color: '#5C8F3A',
  logo_url: '/api/app-settings/logo',
  favicon_url: '/api/app-settings/favicon.png',
  apple_touch_icon_url: '/api/app-settings/apple-touch-icon.png',
  manifest_url: '/api/app-settings/manifest.webmanifest',
  asset_version: '1',
  kasse_layout: null,
}

const setLinkTag = (id, rel, href, type = null) => {
  let link = document.getElementById(id)
  if (!link) {
    link = document.createElement('link')
    link.id = id
    link.rel = rel
    if (type) {
      link.type = type
    }
    document.head.appendChild(link)
  }
  link.href = href
}

export const useAppSettingsStore = defineStore('app-settings', () => {
  const settings = ref({ ...fallbackSettings })
  const isLoaded = ref(false)
  const isSaving = ref(false)

  const versionedUrl = (url) => {
    if (!url) return ''
    const separator = url.includes('?') ? '&' : '?'
    return `${url}${separator}v=${settings.value.asset_version}`
  }

  const applyToDocument = () => {
    document.documentElement.style.setProperty('--app-background-color', settings.value.background_color)
    document.documentElement.style.setProperty('--app-banner-color', settings.value.banner_color)
    document.documentElement.style.setProperty('--app-highlight-color', settings.value.highlight_color)
    document.documentElement.style.setProperty('--app-surface-color', '#ffffff')
    document.documentElement.style.setProperty('--app-banner-contrast', getContrastColor(settings.value.banner_color))
    document.documentElement.style.setProperty('--app-highlight-contrast', getContrastColor(settings.value.highlight_color))
    document.documentElement.style.setProperty('--app-background-contrast', getContrastColor(settings.value.background_color))
    document.title = settings.value.app_name

    const themeMeta = document.getElementById('theme-color-meta')
    if (themeMeta) {
      themeMeta.setAttribute('content', settings.value.banner_color)
    }

    setLinkTag('app-favicon', 'icon', versionedUrl(settings.value.favicon_url), 'image/png')
    setLinkTag('app-favicon-32', 'icon', versionedUrl(settings.value.favicon_url), 'image/png')
    setLinkTag('app-apple-touch-icon', 'apple-touch-icon', versionedUrl(settings.value.apple_touch_icon_url))
    setLinkTag('app-manifest-link', 'manifest', versionedUrl(settings.value.manifest_url))
  }

  const mergeAndApply = (payload) => {
    settings.value = {
      ...fallbackSettings,
      ...payload,
    }
    applyToDocument()
    isLoaded.value = true
    return settings.value
  }

  const loadPublicSettings = async () => {
    try {
      const response = await apiService.get('/app-settings/public')
      return mergeAndApply(response.data)
    } catch (error) {
      console.error('Error loading public app settings:', error)
      applyToDocument()
      isLoaded.value = true
      return settings.value
    }
  }

  const loadAdminSettings = async () => {
    const response = await apiService.get('/app-settings')
    return mergeAndApply(response.data)
  }

  const saveThemeSettings = async (payload) => {
    isSaving.value = true
    try {
      const response = await apiService.put('/app-settings', payload)
      return mergeAndApply(response.data)
    } finally {
      isSaving.value = false
    }
  }

  const uploadLogo = async (file) => {
    isSaving.value = true
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await apiService.post('/app-settings/logo', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return mergeAndApply(response.data)
    } finally {
      isSaving.value = false
    }
  }

  const logoUrl = computed(() => versionedUrl(settings.value.logo_url))

  return {
    settings,
    isLoaded,
    isSaving,
    logoUrl,
    applyToDocument,
    loadPublicSettings,
    loadAdminSettings,
    saveThemeSettings,
    uploadLogo,
  }
})
