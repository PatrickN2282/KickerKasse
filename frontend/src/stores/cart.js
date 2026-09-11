import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import apiService from '@/services/api'
import { resolveDisplayedUnitPriceCents } from '@/services/pricing'

export const useCartStore = defineStore('cart', () => {
  const DRAFT_PREFIX = 'kicker_kasse_cart_draft_v1:'
  const LAST_BOOKING_PREFIX = 'kicker_kasse_last_booking_v1:'
  const items = ref([])
  const actorId = ref(null)
  const lastBooking = ref(null)
  let guestLineSequence = 0
  const selectedMemberId = ref(null)
  const selectedMemberHasDiscount = ref(false)
  const paymentMethod = ref('CASH')
  const appliedVouchers = ref([])
  const appliedBalanceCents = ref(0)
  const tipCents = ref(0)
  const cashReceivedCents = ref(null)
  const hasDraft = computed(() => items.value.length > 0)

  const resetMemory = () => {
    items.value = []
    selectedMemberId.value = null
    selectedMemberHasDiscount.value = false
    paymentMethod.value = 'CASH'
    appliedVouchers.value = []
    appliedBalanceCents.value = 0
    tipCents.value = 0
    cashReceivedCents.value = null
  }

  const persistDraft = () => {
    if (actorId.value == null) return
    const key = `${DRAFT_PREFIX}${actorId.value}`
    if (!hasDraft.value) {
      sessionStorage.removeItem(key)
      return
    }
    sessionStorage.setItem(key, JSON.stringify({
      actor_id: actorId.value,
      items: items.value,
      selected_member_id: selectedMemberId.value,
      selected_member_has_discount: selectedMemberHasDiscount.value,
      payment_method: paymentMethod.value,
      applied_vouchers: appliedVouchers.value,
      applied_balance_cents: appliedBalanceCents.value,
      tip_cents: tipCents.value,
      cash_received_cents: cashReceivedCents.value,
    }))
  }

  const bindActor = (nextActorId) => {
    const normalizedActorId = nextActorId == null ? null : Number(nextActorId)
    if (actorId.value === normalizedActorId) return
    persistDraft()
    actorId.value = normalizedActorId
    resetMemory()
    lastBooking.value = null
    if (normalizedActorId == null) return
    try {
      const draft = JSON.parse(sessionStorage.getItem(`${DRAFT_PREFIX}${normalizedActorId}`) || 'null')
      if (draft?.actor_id === normalizedActorId && Array.isArray(draft.items)) {
        items.value = draft.items.map(cloneCartItem)
        selectedMemberId.value = draft.selected_member_id ?? null
        selectedMemberHasDiscount.value = !!draft.selected_member_has_discount
        paymentMethod.value = draft.payment_method || 'CASH'
        appliedVouchers.value = Array.isArray(draft.applied_vouchers) ? draft.applied_vouchers : []
        appliedBalanceCents.value = Number(draft.applied_balance_cents || 0)
        tipCents.value = Number(draft.tip_cents || 0)
        cashReceivedCents.value = draft.cash_received_cents ?? null
      }
      const booking = JSON.parse(sessionStorage.getItem(`${LAST_BOOKING_PREFIX}${normalizedActorId}`) || 'null')
      if (booking?.actor_id === normalizedActorId) lastBooking.value = booking
    } catch {
      sessionStorage.removeItem(`${DRAFT_PREFIX}${normalizedActorId}`)
      sessionStorage.removeItem(`${LAST_BOOKING_PREFIX}${normalizedActorId}`)
    }
  }

  const rememberBooking = (transaction) => {
    if (!transaction || actorId.value == null) return
    lastBooking.value = { ...transaction, actor_id: actorId.value, confirmed_at: Date.now() }
    sessionStorage.setItem(`${LAST_BOOKING_PREFIX}${actorId.value}`, JSON.stringify(lastBooking.value))
  }

  const normalizeItemNote = (note = '') => String(note || '').trim()
  const hashItemNote = (note = '') => [...normalizeItemNote(note)].reduce(
    (hash, char) => ((hash * 31) + char.charCodeAt(0)) >>> 0,
    0
  ).toString(36)

  const buildCartLineId = (productId, isInternalMaterial = false, note = '') => (
    `${productId}:${isInternalMaterial ? 'internal' : 'regular'}:${hashItemNote(note)}`
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
    is_discountable: item.is_discountable !== false,
    is_internal_material: !!item.is_internal_material,
    note: normalizeItemNote(item.note) || null,
    guests: (item.guests || []).map(guest => ({ ...guest })),
    requires_guest_list: !!item.requires_guest_list,
    is_variable_price: !!item.is_variable_price,
  })

  const addItem = (product, maxQuantity = product.stock_quantity) => {
    const normalizedNote = normalizeItemNote(product.note)
    const lineId = buildCartLineId(product.id, product.is_internal_material, normalizedNote)
      + (product.is_variable_price ? `:price:${product.price_cents}` : '')
      + (product.requires_guest_list ? `:guest:${++guestLineSequence}` : '')
    const existingItem = items.value.find(item => item.line_id === lineId)
    const allowedQuantity = Math.max(Number(maxQuantity ?? product.stock_quantity ?? 0), 0)

    if (existingItem) {
      if (allowedQuantity <= 0) {
        return { success: false, quantity: existingItem.quantity }
      }
      existingItem.quantity++
      existingItem.total_price_cents = existingItem.quantity * existingItem.unit_price_cents
      return { success: true, quantity: existingItem.quantity }
    }

    if (allowedQuantity <= 0) {
      return { success: false, quantity: 0 }
    }

    const unitPrice = resolveDisplayedUnitPriceCents(product, {
      memberSelected: !!selectedMemberId.value,
      memberHasDiscount: selectedMemberHasDiscount.value,
    })
    items.value.push({
      line_id: lineId,
      product_id: product.id,
      product_name: product.name,
      quantity: 1,
      unit_price_cents: unitPrice,
      total_price_cents: unitPrice,
      member_price_cents: product.member_price_cents,
      regular_price_cents: product.price_cents,
      is_discountable: product.is_discountable !== false,
      is_internal_material: !!product.is_internal_material,
      note: normalizedNote || null,
      guests: (product.guests || []).map(guest => ({ ...guest })),
      requires_guest_list: !!product.requires_guest_list,
      is_variable_price: !!product.is_variable_price,
    })
    return { success: true, quantity: 1 }
  }

  const recalculatePrices = () => {
    /**
     * Recalculate prices when member selection changes.
     * Updates all items in cart to use member or regular price.
     */
    items.value.forEach(item => {
      item.unit_price_cents = resolveDisplayedUnitPriceCents(item, {
        memberSelected: !!selectedMemberId.value,
        memberHasDiscount: selectedMemberHasDiscount.value,
      })
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

  const checkout = async (userId, expectedMemberBalanceCents = null) => {
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
          tip_cents: tipCents.value,
          cash_received_cents: cashReceivedCents.value,
          expected_total_amount_cents: paymentMethod.value === 'BALANCE' ? 0 : getTotalAmount(),
          expected_member_balance_cents: selectedMemberId.value ? expectedMemberBalanceCents : null,
          trigger_cash_drawer: false,
          items: items.value.map(item => ({
            product_id: item.product_id,
            quantity: item.quantity,
            unit_price_cents: item.unit_price_cents,
            is_internal_material: item.is_internal_material,
            note: item.note,
            guests: item.guests || [],
          })),
      })

      console.log('[Cart] Checkout successful:', response.data)
      rememberBooking(response.data)
      resetMemory()

      return response.data
    } catch (err) {
      console.error('[Cart] Checkout error:', err.response?.data || err.message || err)
      throw err
    }
  }

  const clear = () => {
      resetMemory()
  }

  const replaceCart = (nextItems = []) => {
    items.value = nextItems.map(cloneCartItem)
    selectedMemberId.value = null
    selectedMemberHasDiscount.value = false
    paymentMethod.value = 'CASH'
    appliedVouchers.value = []
    appliedBalanceCents.value = 0
    tipCents.value = 0
    cashReceivedCents.value = null
  }

  watch(
    [items, selectedMemberId, selectedMemberHasDiscount, paymentMethod, appliedVouchers, appliedBalanceCents, tipCents, cashReceivedCents],
    persistDraft,
    { deep: true }
  )

  return {
    items,
    selectedMemberId,
    selectedMemberHasDiscount,
    paymentMethod,
    appliedVouchers,
    appliedBalanceCents,
    tipCents,
    cashReceivedCents,
    actorId,
    lastBooking,
    hasDraft,
    bindActor,
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
