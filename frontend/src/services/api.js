import axios from 'axios'

// Use relative /api path (same-origin) instead of absolute URL
// This works both in dev (with vite proxy) and production (served from same backend)
const baseURL = '/api'

const apiClient = axios.create({
  baseURL,
  withCredentials: true,
  timeout: 10000,
})

// Handle response errors
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
