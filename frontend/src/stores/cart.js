import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiService from '@/services/api'

export const useCartStore = defineStore('cart', () => {
  const items = ref([])
  const selectedMemberId = ref(null)
  const paymentMethod = ref('CASH')

  const addItem = (product) => {
    const existingItem = items.value.find(item => item.product_id === product.id)

    if (existingItem) {
      existingItem.quantity++
      existingItem.total_price_cents = existingItem.quantity * existingItem.unit_price_cents
    } else {
      // Use member price if member is selected and product has member price
      const unitPrice = (selectedMemberId.value && product.member_price_cents) ? product.member_price_cents : product.price_cents
      items.value.push({
        product_id: product.id,
        product_name: product.name,
        quantity: 1,
        unit_price_cents: unitPrice,
        total_price_cents: unitPrice,
        member_price_cents: product.member_price_cents,
        regular_price_cents: product.price_cents,
      })
    }
  }

  const recalculatePrices = () => {
    /**
     * Recalculate prices when member selection changes.
     * Updates all items in cart to use member or regular price.
     */
    items.value.forEach(item => {
      if (selectedMemberId.value && item.member_price_cents) {
        item.unit_price_cents = item.member_price_cents
      } else {
        item.unit_price_cents = item.regular_price_cents
      }
      item.total_price_cents = item.quantity * item.unit_price_cents
    })
  }

  const removeItem = (productId) => {
    items.value = items.value.filter(item => item.product_id !== productId)
  }

  const updateItemQuantity = (productId, quantity) => {
    const item = items.value.find(item => item.product_id === productId)
    if (item) {
      item.quantity = Math.max(0, quantity)
      item.total_price_cents = item.quantity * item.unit_price_cents
      if (item.quantity === 0) {
        removeItem(productId)
      }
    }
  }

  const getTotalAmount = () => {
    return items.value.reduce((sum, item) => sum + item.total_price_cents, 0)
  }

  // Computed-like getter for total
  const total = computed(() => getTotalAmount())

  const checkout = async (userId) => {
    if (items.value.length === 0) {
      throw new Error('Cart is empty')
    }

    const totalAmount = getTotalAmount()

    try {
      console.log('[Cart] Starting checkout with paymentMethod:', paymentMethod.value)
      const response = await apiService.post('/transactions/sale', {
        user_id: userId,
        payment_method: paymentMethod.value,
        member_id: selectedMemberId.value,
        items: items.value.map(item => ({
          product_id: item.product_id,
          quantity: item.quantity,
          unit_price_cents: item.unit_price_cents,
        })),
      })

      console.log('[Cart] Checkout successful:', response.data)
      items.value = []
      selectedMemberId.value = null
      paymentMethod.value = 'CASH'

      return response.data
    } catch (err) {
      console.error('[Cart] Checkout error:', err.response?.data || err.message || err)
      throw err
    }
  }

  const clear = () => {
    items.value = []
    selectedMemberId.value = null
    paymentMethod.value = 'CASH'
  }

  return {
    items,
    selectedMemberId,
    paymentMethod,
    total,
    addItem,
    removeItem,
    updateItemQuantity,
    recalculatePrices,
    getTotalAmount,
    checkout,
    clear,
  }
})
