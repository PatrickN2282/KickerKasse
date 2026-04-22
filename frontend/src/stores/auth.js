import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiService from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isLoading = ref(false)
  const error = ref(null)
  const setupRequired = ref(false)
  const topAdminExists = ref(true)

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
  }

  const clearClientSession = () => {
    user.value = null
  }

  const login = async (username, password) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiService.post('/auth/login', {
        username,
        password,
      })

      setUser(response.data)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Login failed'
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
      const response = await apiService.get('/auth/me')
      setUser(response.data)
      return true
    } catch {
      clearClientSession()
      return false
    }
  }

  const fetchSetupStatus = async () => {
    try {
      const response = await apiService.get('/auth/setup-status')
      setupRequired.value = !!response.data?.setup_required
      topAdminExists.value = !!response.data?.top_admin_exists
      return response.data
    } catch {
      setupRequired.value = false
      topAdminExists.value = true
      return null
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
