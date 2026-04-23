import { defineStore } from 'pinia'
import { ref } from 'vue'
import apiService from '@/services/api'

export const useProductStore = defineStore('product', () => {
  const products = ref([])
  const isLoading = ref(false)
  const error = ref(null)

  const getProducts = async () => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiService.get('/products')
      products.value = response.data
      return products.value
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch products'
      return []
    } finally {
      isLoading.value = false
    }
  }

  const getProduct = async (productId) => {
    try {
      const response = await apiService.get(`/products/${productId}`)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch product'
      return null
    }
  }

  const createProduct = async (productData) => {
    error.value = null

    try {
      const response = await apiService.post('/products', productData)
      products.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to create product'
      return null
    }
  }

  const updateProduct = async (productId, productData) => {
    error.value = null

    try {
      const response = await apiService.put(`/products/${productId}`, productData)
      const index = products.value.findIndex(p => p.id === productId)
      if (index !== -1) {
        products.value[index] = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update product'
      return null
    }
  }

  const deleteProduct = async (productId) => {
    error.value = null

    try {
      await apiService.delete(`/products/${productId}`)
      products.value = products.value.filter(product => product.id !== productId)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to delete product'
      return false
    }
  }

  return {
    products,
    isLoading,
    error,
    getProducts,
    getProduct,
    createProduct,
    updateProduct,
    deleteProduct,
  }
})
