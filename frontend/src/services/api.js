import axios from 'axios'
import { installBookingRetry } from './booking-retry'

// Use relative /api path (same-origin) instead of absolute URL
// This works both in dev (with vite proxy) and production (served from same backend)
const baseURL = '/api'

const apiClient = axios.create({
  baseURL,
  withCredentials: true,
  timeout: 10000,
})

const shouldRedirectToLogin = (error) => {
  if (error.response?.status !== 401) return false

  const requestUrl = String(error.config?.url || '')
  const isAuthEntryRequest = /\/auth\/login-kasse\/?$/.test(requestUrl) || /\/auth\/login\/?$/.test(requestUrl)
  const isPasswordResetRequest = /\/auth\/password-reset\/request\/?$/.test(requestUrl)
  const onLoginScreen = window.location.pathname.startsWith('/login')

  return !isAuthEntryRequest && !isPasswordResetRequest && !onLoginScreen
}

// Handle response errors
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (shouldRedirectToLogin(error)) {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const pendingBookings = installBookingRetry(apiClient)

export default apiClient
