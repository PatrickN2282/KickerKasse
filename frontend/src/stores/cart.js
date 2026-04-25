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

  const normalizeItemNote = (note = '') => String(note || '').trim()

  const buildCartLineId = (productId, isInternalMaterial = false, note = '') => (
    `${productId}:${isInternalMaterial ? 'internal' : 'regular'}:${encodeURIComponent(normalizeItemNote(note) || '-')}`
  )

  const cloneCartItem = (item) => ({
    line_id: item.line_id || buildCartLineId(item.product_id, item.is_internal_material, item.note),
    product_id: item.product_id,
    product_name: item.product_name,
    quantity: item.quantity,
    unit_price_cents: item.unit_price_cents,
    total_price_cents: item.quantity * item.unit_price_cents,
    member_price_cents: item.member_price_cents ?? null,
    regular_price_cents: item.regular_price_cents ?? item.unit_price_cents,
    is_internal_material: !!item.is_internal_material,
    note: normalizeItemNote(item.note) || null,
  })

  const addItem = (product, maxQuantity = product.stock_quantity) => {
    const normalizedNote = normalizeItemNote(product.note)
    const lineId = buildCartLineId(product.id, product.is_internal_material, normalizedNote)
    const existingItem = items.value.find(item => item.line_id === lineId)
    const allowedQuantity = Math.max(Number(maxQuantity ?? product.stock_quantity ?? 0), 0)

    if (existingItem) {
      if (existingItem.quantity >= allowedQuantity) {
        return { success: false, quantity: existingItem.quantity }
      }
      existingItem.quantity++
      existingItem.total_price_cents = existingItem.quantity * existingItem.unit_price_cents
      return { success: true, quantity: existingItem.quantity }
    }

    if (allowedQuantity <= 0) {
      return { success: false, quantity: 0 }
    }

    // Use member price if member is selected and product has member price
    const unitPrice = product.is_internal_material
      ? 0
      : ((selectedMemberId.value && selectedMemberHasDiscount.value && product.member_price_cents)
          ? product.member_price_cents
          : product.price_cents)
    items.value.push({
      line_id: lineId,
      product_id: product.id,
      product_name: product.name,
      quantity: 1,
      unit_price_cents: unitPrice,
      total_price_cents: unitPrice,
      member_price_cents: product.member_price_cents,
      regular_price_cents: product.price_cents,
      is_internal_material: !!product.is_internal_material,
      note: normalizedNote || null,
    })
    return { success: true, quantity: 1 }
  }

  const recalculatePrices = () => {
    /**
     * Recalculate prices when member selection changes.
     * Updates all items in cart to use member or regular price.
     */
    items.value.forEach(item => {
      if (item.is_internal_material) {
        item.unit_price_cents = 0
      } else if (selectedMemberId.value && selectedMemberHasDiscount.value && item.member_price_cents) {
        item.unit_price_cents = item.member_price_cents
      } else {
        item.unit_price_cents = item.regular_price_cents
      }
      item.total_price_cents = item.quantity * item.unit_price_cents
    })
  }

  const removeItem = (lineId) => {
    items.value = items.value.filter(item => item.line_id !== lineId)
  }

  const updateItemQuantity = (lineId, quantity, maxQuantity = null) => {
    const item = items.value.find(item => item.line_id === lineId)
    if (item) {
      const maxAllowed = (maxQuantity === null || maxQuantity === undefined)
        ? Math.max(item.quantity, 0)
        : Math.max(Number(maxQuantity), 0)
      item.quantity = Math.min(Math.max(0, quantity), maxAllowed)
      item.total_price_cents = item.quantity * item.unit_price_cents
      if (item.quantity === 0) {
        removeItem(lineId)
      }
      return { success: quantity <= maxAllowed, quantity: item.quantity }
    }
    return { success: false, quantity: 0 }
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
            is_internal_material: item.is_internal_material,
            note: item.note,
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

  const replaceCart = (nextItems = []) => {
    items.value = nextItems.map(cloneCartItem)
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
    replaceCart,
  }
})
