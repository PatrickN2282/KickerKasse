import axios from 'axios'

// Use relative /api path (same-origin) instead of absolute URL
// This works both in dev (with vite proxy) and production (served from same backend)
const baseURL = '/api'

const apiClient = axios.create({
  baseURL,
  withCredentials: true,
  timeout: 10000,
})

// Add token to requests if available
apiClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// Handle response errors
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
