import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiService from '@/services/api'

export const useCartStore = defineStore('cart', () => {
  const items = ref([])
  const selectedMemberId = ref(null)
  const selectedMemberHasDiscount = ref(false)
  const paymentMethod = ref('CASH')
  const appliedVouchers = ref([])
  const appliedBalanceCents = ref(0)

  const addItem = (product) => {
    const existingItem = items.value.find(item => item.product_id === product.id)

    if (existingItem) {
      existingItem.quantity++
      existingItem.total_price_cents = existingItem.quantity * existingItem.unit_price_cents
    } else {
      // Use member price if member is selected and product has member price
      const unitPrice = (selectedMemberId.value && selectedMemberHasDiscount.value && product.member_price_cents)
        ? product.member_price_cents
        : product.price_cents
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
      if (selectedMemberId.value && selectedMemberHasDiscount.value && item.member_price_cents) {
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

  const getSubtotalAmount = () => {
    return items.value.reduce((sum, item) => sum + item.total_price_cents, 0)
  }

  const getVoucherAppliedAmount = () => {
    return Math.min(
      appliedVouchers.value.reduce((sum, voucher) => sum + (voucher.applied_amount_cents || 0), 0),
      getSubtotalAmount()
    )
  }

  const getBalanceAppliedAmount = () => {
    const remainingAfterVouchers = Math.max(getSubtotalAmount() - getVoucherAppliedAmount(), 0)
    return Math.min(appliedBalanceCents.value, remainingAfterVouchers)
  }

  const getTotalAmount = () => {
    return Math.max(getSubtotalAmount() - getVoucherAppliedAmount() - getBalanceAppliedAmount(), 0)
  }

  // Computed-like getter for total
  const total = computed(() => getTotalAmount())

  const applyVoucher = (voucher) => {
    appliedVouchers.value.push(voucher)
  }

  const removeVoucher = (voucherNumber = null) => {
    if (!voucherNumber) {
      appliedVouchers.value = []
      return
    }

    appliedVouchers.value = appliedVouchers.value.filter(voucher => voucher.voucher_number !== voucherNumber)
  }

  const applyBalanceDiscount = (amountCents) => {
    appliedBalanceCents.value = Math.max(amountCents, 0)
  }

  const removeBalanceDiscount = () => {
    appliedBalanceCents.value = 0
  }

  const checkout = async (userId) => {
    if (items.value.length === 0) {
      throw new Error('Cart is empty')
    }

      try {
        console.log('[Cart] Starting checkout with paymentMethod:', paymentMethod.value)
        const response = await apiService.post('/transactions/sale', {
          user_id: userId,
          payment_method: paymentMethod.value,
          member_id: selectedMemberId.value,
          voucher_redemptions: appliedVouchers.value.map(voucher => ({
            voucher_number: voucher.voucher_number,
          })),
          balance_discount_cents: appliedBalanceCents.value,
          items: items.value.map(item => ({
            product_id: item.product_id,
            quantity: item.quantity,
            unit_price_cents: item.unit_price_cents,
          })),
      })

      console.log('[Cart] Checkout successful:', response.data)
      items.value = []
      selectedMemberId.value = null
      selectedMemberHasDiscount.value = false
      paymentMethod.value = 'CASH'
      appliedVouchers.value = []
      appliedBalanceCents.value = 0

      return response.data
    } catch (err) {
      console.error('[Cart] Checkout error:', err.response?.data || err.message || err)
      throw err
    }
  }

  const clear = () => {
      items.value = []
      selectedMemberId.value = null
      selectedMemberHasDiscount.value = false
      paymentMethod.value = 'CASH'
      appliedVouchers.value = []
      appliedBalanceCents.value = 0
  }

  return {
    items,
    selectedMemberId,
    selectedMemberHasDiscount,
    paymentMethod,
    appliedVouchers,
    appliedBalanceCents,
    total,
    addItem,
    removeItem,
    updateItemQuantity,
    recalculatePrices,
    getSubtotalAmount,
    getVoucherAppliedAmount,
    getBalanceAppliedAmount,
    getTotalAmount,
    applyVoucher,
    removeVoucher,
    applyBalanceDiscount,
    removeBalanceDiscount,
    checkout,
    clear,
  }
})
