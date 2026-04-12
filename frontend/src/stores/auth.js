import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiService from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || null)
  const isLoading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => !!user.value)

  const login = async (username, password) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiService.post('/auth/login', {
        username,
        password,
      })

      user.value = response.data
      localStorage.setItem('token', response.data.id)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Login failed'
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
      user.value = null
      localStorage.removeItem('token')
    }
  }

  const checkAuth = async () => {
    try {
      const response = await apiService.get('/auth/me')
      user.value = response.data
      return true
    } catch (err) {
      user.value = null
      localStorage.removeItem('token')
      return false
    }
  }

  return {
    user,
    token,
    isLoading,
    error,
    isAuthenticated,
    login,
    logout,
    checkAuth,
  }
})
