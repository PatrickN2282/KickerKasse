import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import apiService from '@/services/api'
import { getContrastColor } from '@/services/utils'

const fallbackSettings = {
  app_name: 'KGB - KickerKasse Test',
  background_color: '#D7DCE2',
  banner_color: '#131820',
  highlight_color: '#5C8F3A',
  kasse_area_background_color: '#FFFFFF',
  logo_url: '/api/app-settings/logo',
  favicon_ico_url: '/api/app-settings/favicon.ico',
  favicon_16_url: '/api/app-settings/favicon-16x16.png',
  favicon_32_url: '/api/app-settings/favicon-32x32.png',
  favicon_url: '/api/app-settings/favicon.png',
  apple_touch_icon_url: '/api/app-settings/apple-touch-icon.png',
  icon_192_url: '/api/app-settings/icon-192.png',
  icon_512_url: '/api/app-settings/icon-512.png',
  manifest_url: '/api/app-settings/manifest.webmanifest',
  asset_version: '1',
  kasse_products_background_url: '',
  kasse_products_background_scale: 100,
  kasse_products_background_opacity: 100,
  kasse_products_background_enabled: true,
  kasse_layout: null,
  session_timer_enabled: false,
  session_timer_minutes: 15,
  deckel_enabled: true,
  business_name: '',
  business_street: '',
  business_zip: '',
  business_city: '',
  business_phone: '',
  business_email: '',
  business_tax_number: '',
  business_registration_number: '',
  email_enabled: false,
  email_sender: 'noreply@kassensystem.local',
  email_recipient_zbon: '',
  email_subject_suffix: '',
  email_critical_stock_enabled: false,
  smtp_host: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  smtp_use_tls: true,
  send_zbon_on_create_enabled: false,
  scheduled_zbon_enabled: false,
  scheduled_zbon_time: '23:59',
  scheduled_zbon_report_type: 'full-zbon',
}

const setLinkTag = (id, rel, href, type = null, attributes = {}) => {
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
  Object.entries(attributes).forEach(([name, value]) => {
    if (value == null) {
      link.removeAttribute(name)
      return
    }
    link.setAttribute(name, value)
  })
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
    document.documentElement.style.setProperty('--kasse-area-background-color', settings.value.kasse_area_background_color || '#FFFFFF')
    document.documentElement.style.setProperty('--app-surface-color', '#ffffff')
    document.documentElement.style.setProperty('--app-banner-contrast', getContrastColor(settings.value.banner_color))
    document.documentElement.style.setProperty('--app-highlight-contrast', getContrastColor(settings.value.highlight_color))
    document.documentElement.style.setProperty('--app-background-contrast', getContrastColor(settings.value.background_color))
    const backgroundEnabled = settings.value.kasse_products_background_enabled !== false
    const backgroundImageUrl = settings.value.kasse_products_background_url && backgroundEnabled
      ? `url(${versionedUrl(settings.value.kasse_products_background_url)})`
      : 'none'
    document.documentElement.style.setProperty('--kasse-products-background-image', backgroundImageUrl)
    document.documentElement.style.setProperty('--kasse-products-background-size', `${settings.value.kasse_products_background_scale || 100}%`)
    const backgroundOpacityPercent = settings.value.kasse_products_background_opacity ?? 100
    document.documentElement.style.setProperty('--kasse-products-background-opacity', `${backgroundOpacityPercent}%`)
    document.title = settings.value.app_name

    const themeMeta = document.getElementById('theme-color-meta')
    if (themeMeta) {
      themeMeta.setAttribute('content', settings.value.banner_color)
    }

    setLinkTag('app-shortcut-icon', 'shortcut icon', versionedUrl(settings.value.favicon_ico_url), 'image/x-icon')
    setLinkTag('app-favicon-16', 'icon', versionedUrl(settings.value.favicon_16_url), 'image/png', { sizes: '16x16' })
    setLinkTag('app-favicon-32', 'icon', versionedUrl(settings.value.favicon_32_url), 'image/png', { sizes: '32x32' })
    setLinkTag('app-favicon', 'icon', versionedUrl(settings.value.favicon_url), 'image/png', { sizes: '64x64' })
    setLinkTag('app-apple-touch-icon', 'apple-touch-icon', versionedUrl(settings.value.apple_touch_icon_url), null, { sizes: '180x180' })
    setLinkTag('app-pwa-icon-192', 'icon', versionedUrl(settings.value.icon_192_url), 'image/png', { sizes: '192x192' })
    setLinkTag('app-pwa-icon-512', 'icon', versionedUrl(settings.value.icon_512_url), 'image/png', { sizes: '512x512' })
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

  const saveAdminSettings = async (payload) => {
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

  const uploadKasseProductsBackground = async (file) => {
    isSaving.value = true
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await apiService.post('/app-settings/kasse-products-background', formData, {
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
    saveAdminSettings,
    uploadLogo,
    uploadKasseProductsBackground,
  }
})
