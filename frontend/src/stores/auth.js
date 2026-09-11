import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiService, { pendingBookings } from '@/services/api'
import { useCartStore } from '@/stores/cart'

export const useAuthStore = defineStore('auth', () => {
  const cartStore = useCartStore()
  const user = ref(null)
  const isLoading = ref(false)
  const error = ref(null)
  const setupRequired = ref(false)
  const topAdminExists = ref(null)
  const setupStatusLoading = ref(false)
  const setupStatusError = ref(null)
  // Anforderung 1: Nach 5 aufeinanderfolgenden TopAdmin-Fehlversuchen liefert das Backend
  // dieses Signal im Login-Fehler mit, damit das Login-Formular automatisch den
  // Self-Service-Reset-Dialog öffnen kann.
  const topAdminResetAvailable = ref(false)

  const isAuthenticated = computed(() => !!user.value)
  const role = computed(() => user.value?.role || null)
  const isTopAdmin = computed(() => role.value === 'TOP_ADMIN')
  const isAdmin = computed(() => ['TOP_ADMIN', 'ADMIN'].includes(role.value))
  const isManager = computed(() => role.value === 'MANAGER')
  const isKasseUser = computed(() => user.value?.username === 'Kasse')
  const canAccessAdminPanel = computed(() => ['TOP_ADMIN', 'ADMIN', 'MANAGER'].includes(role.value))
  const hasRole = (...roles) => roles.includes(role.value)

  const setUser = (payload) => {
    user.value = payload
    pendingBookings.setActor(payload?.id ?? null)
    cartStore.bindActor(payload?.id ?? null)
  }

  const clearClientSession = () => {
    user.value = null
    pendingBookings.setActor(null)
    cartStore.bindActor(null)
  }

  const login = async (username, password) => {
    isLoading.value = true
    error.value = null
    topAdminResetAvailable.value = false

    try {
      const response = await apiService.post('/auth/login', {
        username,
        password,
      })

      setUser(response.data)
      return true
    } catch (err) {
      const detail = err.response?.data?.detail
      if (detail && typeof detail === 'object') {
        error.value = detail.message || 'Login failed'
        topAdminResetAvailable.value = Boolean(detail.top_admin_reset_available)
      } else {
        error.value = detail || 'Login failed'
      }
      return false
    } finally {
      isLoading.value = false
    }
  }

  const loginAsKasse = async () => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiService.post('/auth/login-kasse')
      setUser(response.data)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Kasse-Anmeldung fehlgeschlagen'
      return false
    } finally {
      isLoading.value = false
    }
  }

  const logout = async () => {
    try {
      await apiService.post('/auth/logout')
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      clearClientSession()
    }
  }

  const checkAuth = async () => {
    try {
      const response = await apiService.get('/auth/me', {
        params: { _t: Date.now() },
        headers: {
          'Cache-Control': 'no-cache',
          Pragma: 'no-cache',
        },
      })
      setUser(response.data)
      return true
    } catch {
      clearClientSession()
      return false
    }
  }

  const fetchSetupStatus = async ({ retries = 2 } = {}) => {
    setupStatusLoading.value = true
    setupStatusError.value = null
    try {
      for (let attempt = 0; attempt <= retries; attempt += 1) {
        try {
          const response = await apiService.get('/auth/setup-status', {
            params: { _t: Date.now() },
            headers: { 'Cache-Control': 'no-cache', Pragma: 'no-cache' },
          })
          setupRequired.value = !!response.data?.setup_required
          topAdminExists.value = !!response.data?.top_admin_exists
          return response.data
        } catch (err) {
          if (attempt >= retries) throw err
          await new Promise(resolve => window.setTimeout(resolve, 400 * (attempt + 1)))
        }
      }
    } catch {
      // Unknown is deliberately kept separate from "setup not required".  A
      // transient startup error must never hide the initial setup.
      topAdminExists.value = null
      setupStatusError.value = 'Der Erststart-Status konnte nicht geladen werden.'
      return null
    } finally {
      setupStatusLoading.value = false
    }
  }

  const completeTopAdminSetup = async ({ username, password, email }) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiService.post('/auth/setup-top-admin', {
        username,
        password,
        email: email?.trim() || null,
      })

      setUser(response.data)
      setupRequired.value = false
      topAdminExists.value = true
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Setup failed'
      return false
    } finally {
      isLoading.value = false
    }
  }

  return {
    user,
    isLoading,
    error,
    setupRequired,
    topAdminExists,
    setupStatusLoading,
    setupStatusError,
    topAdminResetAvailable,
    isAuthenticated,
    role,
    isTopAdmin,
    isAdmin,
    isManager,
    isKasseUser,
    canAccessAdminPanel,
    hasRole,
    setUser,
    clearClientSession,
    login,
    loginAsKasse,
    logout,
    checkAuth,
    fetchSetupStatus,
    completeTopAdminSetup,
  }
})
