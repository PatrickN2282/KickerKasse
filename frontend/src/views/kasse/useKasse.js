import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useProductStore } from '@/stores/product'
import { useMemberStore } from '@/stores/member'
import { useCartStore } from '@/stores/cart'
import { useNotificationStore } from '@/stores/notification'
import { useAuthStore } from '@/stores/auth'
import { formatPrice, formatBalance } from '@/services/utils'
import { getMemberFullName, getMemberShortName, getMemberSearchText } from '@/services/member'
import apiService from '@/services/api'

export default function useKasse() {
const productStore = useProductStore()
const memberStore = useMemberStore()
const cartStore = useCartStore()
const notificationStore = useNotificationStore()
const authStore = useAuthStore()
const INTERNAL_MATERIAL_CATEGORY_NAME = 'Verbrauchsmaterial - Intern'

const showMemberModal = ref(false)
const showPaymentConfirmModal = ref(false)
const showInternalMaterialNoteModal = ref(false)
const memberSearch = ref('')
const pendingPaymentMethod = ref(null)
const processingPayment = ref(false)
const paymentResult = ref(null)
const expandedCategories = ref([])
const categories = ref([])
const bonWidth = ref(420)
const nextReceiptNumber = ref(null)
const cashGiven = ref('')
const imageErrorMap = ref({})

const onImageError = (productId) => {
  imageErrorMap.value[productId] = true
}

// Voucher redemption
const showVoucherModal = ref(false)
const voucherNumber = ref('')
const voucherValidation = ref(null)
const voucherValidated = ref(false)
const voucherRedeemed = ref(null)
const voucherError = ref(null)
const validatingVoucher = ref(false)
const redeemingVoucher = ref(false)
const showDeckelCreateModal = ref(false)
const showDeckelOverviewModal = ref(false)
const showDeckelDetailsModal = ref(false)
const deckelName = ref('')
const deckelList = ref([])
const activeDeckel = ref(null)
const paymentSource = ref('cart')
const activePaymentDeckel = ref(null)
const pendingInternalMaterialProduct = ref(null)
const internalMaterialNote = ref('')

// Variable price modal
const showVariablePriceModal = ref(false)
const pendingVariablePriceProduct = ref(null)
const variablePrice = ref('')
const isVariablePriceValid = computed(() => {
  const price = parseFloat(variablePrice.value)
  return !isNaN(price) && price >= 0
})

const voucherReasonLabels = {
  DYP_SIEGER: 'DYP-Sieger',
  PROMOTION: 'Promotion',
}
const voucherPrefix = `V-${new Date().getFullYear()}-`
const normalizedVoucherPrefix = voucherPrefix.toUpperCase()

const isInternalMaterialSale = (product, categoryId = null) => (
  !!categoryId && !!product?.categories?.some(category => (
    category.id === categoryId && category.name === INTERNAL_MATERIAL_CATEGORY_NAME
  ))
)

const getDisplayedProductPriceCents = (product, categoryId = null) => (
  isInternalMaterialSale(product, categoryId)
    ? 0
    : ((cartStore.selectedMemberId && cartStore.selectedMemberHasDiscount && product.member_price_cents)
        ? product.member_price_cents
        : product.price_cents)
)

const loadCategories = async () => {
  try {
    const response = await apiService.get('/categories?only_active=true')
    categories.value = response.data
    // Auto-expand categories that have products
    expandedCategories.value = []
    categories.value.forEach(category => {
      const productsInCategory = getProductsByCategory(category.id)
      if (productsInCategory.length > 0) {
        expandedCategories.value.push(category.id)
      }
    })
    // Also expand "Ohne Kategorie" if there are products without categories
    if (productsWithoutCategory.value.length > 0) {
      expandedCategories.value.push(0)
    }
    console.log('[Kasse] Categories loaded:', categories.value)
    console.log('[Kasse] Auto-expanded categories:', expandedCategories.value)
  } catch (err) {
    console.error('[Kasse] Failed to load categories:', err)
  }
}

const getCategoryChipStyle = (category, isActive) => {
  if (!category.color) return {}
  const textColor = getContrastTextColor(category.color)
  if (isActive) {
    return {
      background: category.color,
      borderColor: category.color,
      color: textColor,
    }
  }
  return {
    borderColor: category.color,
    color: textColor,
  }
}

const getCategoryCardStyle = (category) => {
  if (!category || !category.color) return {}
  return { borderColor: category.color }
}

/**
 * Returns '#1e293b' (dark) or '#ffffff' (light) depending on the
 * perceived luminance of the hex background color.
 */
const getContrastTextColor = (hex) => {
  if (!hex) return '#1e293b'
  const clean = hex.replace('#', '')
  if (clean.length < 6) return '#1e293b'
  const r = parseInt(clean.slice(0, 2), 16)
  const g = parseInt(clean.slice(2, 4), 16)
  const b = parseInt(clean.slice(4, 6), 16)
  // Relative luminance (WCAG formula)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.5 ? '#1e293b' : '#ffffff'
}

const toggleCategory = (categoryId) => {
  const idx = expandedCategories.value.indexOf(categoryId)
  if (idx > -1) {
    expandedCategories.value.splice(idx, 1)
  } else {
    expandedCategories.value.push(categoryId)
  }
}

const sortProductsByAvailability = (products) => (
  products
    .map((product, index) => ({ product, index }))
    .sort((a, b) => {
      const aOutOfStock = isProductOutOfStock(a.product) ? 1 : 0
      const bOutOfStock = isProductOutOfStock(b.product) ? 1 : 0
      if (aOutOfStock !== bOutOfStock) {
        return aOutOfStock - bOutOfStock
      }
      return a.index - b.index
    })
    .map(({ product }) => product)
)

const getProductsByCategory = (categoryId) => {
  if (categoryId === 0) {
    return productsWithoutCategory.value
  }
  return sortProductsByAvailability(productStore.products.filter(p =>
    p.categories && p.categories.some(c => c.id === categoryId)
  ))
}

const activeCategories = computed(() => {
  return categories.value
    .filter(category => (
      category.is_active_in_kasse
      && (
        category.name !== INTERNAL_MATERIAL_CATEGORY_NAME
        || getProductsByCategory(category.id).length > 0
      )
    ))
    .sort((a, b) => a.display_order - b.display_order)
})

const productsWithoutCategory = computed(() => {
  return sortProductsByAvailability(
    productStore.products.filter(p => !p.categories || p.categories.length === 0)
  )
})

const selectedMemberName = computed(() => {
  const member = memberStore.members.find(m => m.id === cartStore.selectedMemberId)
  return getMemberShortName(member)
})

const selectedMemberBalance = computed(() => {
  const member = memberStore.members.find(m => m.id === cartStore.selectedMemberId)
  console.log(`[Kasse] Balance for member ${cartStore.selectedMemberId}:`, member?.balance_cents)
  return member?.balance_cents || 0
})

const selectedMember = computed(() => {
  return memberStore.members.find(m => m.id === cartStore.selectedMemberId) || null
})

const hasExpandedCategory = computed(() => expandedCategories.value.length > 0)

const cartSubtotal = computed(() => cartStore.getSubtotalAmount())
const voucherAppliedAmount = computed(() => cartStore.getVoucherAppliedAmount())
const balanceAppliedAmount = computed(() => cartStore.getBalanceAppliedAmount())
const hasAppliedVoucher = computed(() => cartStore.appliedVouchers.length > 0)
const hasAppliedBalance = computed(() => balanceAppliedAmount.value > 0)
const activeDeckelCount = computed(() => deckelList.value.length)
const paymentSummaryItems = computed(() => paymentSource.value === 'deckel'
  ? (activePaymentDeckel.value?.items || [])
  : cartStore.items
)
const paymentSubtotal = computed(() => paymentSource.value === 'deckel'
  ? (activePaymentDeckel.value?.total_amount_cents || 0)
  : cartSubtotal.value
)
const paymentTotal = computed(() => paymentSource.value === 'deckel'
  ? (activePaymentDeckel.value?.total_amount_cents || 0)
  : cartStore.getTotalAmount()
)
const isInsufficientBalance = computed(() => (
  pendingPaymentMethod.value === 'BALANCE'
  && !!cartStore.selectedMemberId
  && selectedMemberBalance.value > 0
  && selectedMemberBalance.value < paymentTotal.value
))

const effectiveCashTotal = computed(() => {
  if (isInsufficientBalance.value) {
    return paymentTotal.value - selectedMemberBalance.value
  }
  return paymentTotal.value
})

const cashChangeDisplay = computed(() => {
  const value = Number(cashGiven.value || 0)
  const change = Math.max(Math.round((value * 100) - effectiveCashTotal.value), 0)
  return formatPrice(change)
})

const cashChangeCents = computed(() => {
  const value = Number(cashGiven.value || 0)
  const given = Math.round(value * 100)
  if (given < effectiveCashTotal.value) return 0
  return given - effectiveCashTotal.value
})
const voucherActionLabel = computed(() => {
  if (redeemingVoucher.value) {
    return '⏳ Wird verarbeitet...'
  }

  return voucherValidation.value?.covers_cart_total
    ? '✓ Kauf abschließen'
    : '✓ Als Rabatt anwenden'
})
const hasValidVoucherInput = computed(() => {
  const normalizedVoucher = voucherNumber.value.trim().toUpperCase()
  return normalizedVoucher !== '' && normalizedVoucher !== normalizedVoucherPrefix
})

const bonPanelStyle = computed(() => ({
  width: `${bonWidth.value}px`,
  flexBasis: `${bonWidth.value}px`,
}))

const filteredMembers = computed(() => {
  const search = memberSearch.value.trim().toLowerCase()

  if (!search) {
    return memberStore.members
  }

  return memberStore.members.filter((member) => {
    return getMemberSearchText(member).includes(search)
  })
})

const getDeckelReservedQuantity = (productId, excludeDeckelId = null) => {
  return deckelList.value.reduce((sum, deckel) => {
    if (excludeDeckelId && deckel.id === excludeDeckelId) {
      return sum
    }
    return sum + deckel.items
      .filter(item => item.product_id === productId)
      .reduce((itemSum, item) => itemSum + item.quantity, 0)
  }, 0)
}

const getCartReservedQuantity = (productId, excludeLineId = null) => {
  return cartStore.items.reduce((sum, item) => {
    if (item.product_id !== productId || item.line_id === excludeLineId) {
      return sum
    }

    return sum + item.quantity
  }, 0)
}

const hasMemberPrice = (product) => product.member_price_cents !== null && product.member_price_cents !== undefined

const showProductBadge = (product) => hasMemberPrice(product) || product.is_unlimited_stock

const getAvailableStock = (product, excludeDeckelId = null, excludeLineId = null) => {
  if (product.is_unlimited_stock) {
    return Number.POSITIVE_INFINITY
  }

  return Math.max(
    (product.stock_quantity || 0)
      - getDeckelReservedQuantity(product.id, excludeDeckelId)
      - getCartReservedQuantity(product.id, excludeLineId),
    0
  )
}

const isProductOutOfStock = (product) => !product.is_unlimited_stock && getAvailableStock(product) === 0

const getStockLabel = (product) => (
  product.is_unlimited_stock
    ? 'Unbegrenzt verfügbar'
    : `Verfügbar: ${getAvailableStock(product)}`
)

const selectProduct = (product, categoryId = null) => {
  if (isInternalMaterialSale(product, categoryId)) {
    pendingInternalMaterialProduct.value = {
      ...product,
      is_internal_material: true,
    }
    internalMaterialNote.value = ''
    showInternalMaterialNoteModal.value = true
    return
  }

  if (product.is_variable_price) {
    pendingVariablePriceProduct.value = { ...product, categoryId }
    variablePrice.value = (product.price_cents / 100).toFixed(2)
    showVariablePriceModal.value = true
    return
  }

  const result = cartStore.addItem({
    ...product,
    is_internal_material: false,
  }, getAvailableStock(product))
  if (!result.success) {
    notificationStore.error(`Nur ${getAvailableStock(product)} Einheiten von ${product.name} verfügbar`)
  }
}

const closeVariablePriceModal = () => {
  showVariablePriceModal.value = false
  pendingVariablePriceProduct.value = null
  variablePrice.value = ''
}

const confirmVariablePriceSelection = () => {
  if (!pendingVariablePriceProduct.value || !isVariablePriceValid.value) return

  const product = pendingVariablePriceProduct.value
  const priceCents = Math.round(parseFloat(variablePrice.value) * 100)
  const result = cartStore.addItem({
    ...product,
    price_cents: priceCents,
    member_price_cents: null,
    is_internal_material: false,
  }, getAvailableStock(product))

  if (!result.success) {
    notificationStore.error(`Nur ${getAvailableStock(product)} Einheiten von ${product.name} verfügbar`)
    return
  }

  closeVariablePriceModal()
}

const closeInternalMaterialNoteModal = () => {
  showInternalMaterialNoteModal.value = false
  pendingInternalMaterialProduct.value = null
  internalMaterialNote.value = ''
}

const confirmInternalMaterialSelection = () => {
  if (!pendingInternalMaterialProduct.value) {
    return
  }

  const product = pendingInternalMaterialProduct.value
  const result = cartStore.addItem({
    ...product,
    note: internalMaterialNote.value,
  }, getAvailableStock(product))

  if (!result.success) {
    notificationStore.error(`Nur ${getAvailableStock(product)} Einheiten von ${product.name} verfügbar`)
    return
  }

  closeInternalMaterialNoteModal()
}

const changeCartItemQuantity = (item, quantity) => {
  const product = productStore.products.find(productEntry => productEntry.id === item.product_id)
  const maxQuantity = product ? getAvailableStock(product, null, item.line_id) : item.quantity
  const result = cartStore.updateItemQuantity(item.line_id, quantity, maxQuantity)
  if (!result.success && result.quantity > 0) {
    notificationStore.error(`Nur ${maxQuantity} Einheiten von ${item.product_name} verfügbar`)
  }
}

const selectCustomer = () => {
  showMemberModal.value = true
}

const validatePaymentMethod = (method) => {
  if (method === 'BALANCE') {
    if (!cartStore.selectedMemberId) {
      notificationStore.error('Bitte wählen Sie ein Mitglied aus')
      return false
    }

    if (selectedMemberBalance.value <= 0) {
      notificationStore.error('Das Mitglied hat kein Guthaben')
      return false
    }

  }

  return true
}

const applyPartialBalanceAndContinue = ({ notify = false } = {}) => {
  const currentlyAppliedBalance = cartStore.getBalanceAppliedAmount()
  const remainingMemberBalance = Math.max(selectedMemberBalance.value - currentlyAppliedBalance, 0)
  const remainingTotal = cartStore.getTotalAmount()

  if (cartStore.selectedMemberId && remainingMemberBalance > 0 && remainingMemberBalance < remainingTotal) {
    cartStore.applyBalanceDiscount(currentlyAppliedBalance + remainingMemberBalance)

    if (notify) {
      notificationStore.success('Verfügbares Mitgliedsguthaben wurde als Rabatt auf den Warenkorb angerechnet')
    }
  }

  openPaymentConfirmation('CASH')
}

const openPaymentConfirmation = (method, options = {}) => {
  const nextSource = options.source || 'cart'
  if (nextSource === 'cart' && !validatePaymentMethod(method)) {
    return
  }

  paymentSource.value = nextSource
  activePaymentDeckel.value = options.deckel || null
  pendingPaymentMethod.value = method
  showPaymentConfirmModal.value = true
  paymentResult.value = null
  if (method === 'CASH') {
    cashGiven.value = (paymentTotal.value / 100).toFixed(2)
  } else if (method === 'BALANCE' && selectedMemberBalance.value > 0 && selectedMemberBalance.value < paymentTotal.value) {
    cashGiven.value = (Math.max(paymentTotal.value - selectedMemberBalance.value, 0) / 100).toFixed(2)
  } else {
    cashGiven.value = ''
  }
}

const closePaymentConfirmation = () => {
  if (processingPayment.value) {
    return
  }

  showPaymentConfirmModal.value = false
  pendingPaymentMethod.value = null
  cashGiven.value = ''
  paymentResult.value = null
  paymentSource.value = 'cart'
  activePaymentDeckel.value = null
}

const confirmPayment = async () => {
  if (!pendingPaymentMethod.value) {
    return
  }

  if (pendingPaymentMethod.value === 'CASH') {
    const givenCents = Math.round(Number(cashGiven.value || 0) * 100)
    if (givenCents < paymentTotal.value) {
      notificationStore.error('Der gegebene Barbetrag reicht nicht aus')
      return
    }
  }

  if (isInsufficientBalance.value) {
    const givenCents = Math.round(Number(cashGiven.value || 0) * 100)
    const cashDue = paymentTotal.value - selectedMemberBalance.value
    if (givenCents < cashDue) {
      notificationStore.error('Der gegebene Barbetrag reicht nicht aus')
      return
    }
  }

  cartStore.tipCents = 0
  processingPayment.value = true
  const transaction = await handlePaymentAndCheckout(pendingPaymentMethod.value)
  processingPayment.value = false

  if (transaction?.appliedBalanceOnly) {
    closePaymentConfirmation()
    return
  }

  if (transaction) {
    if (transaction.issued_prepaid_voucher_numbers?.length) {
      paymentResult.value = transaction
      return
    }
    closePaymentConfirmation()
  }
}

const confirmPaymentWithTip = async () => {
  if (!pendingPaymentMethod.value || cashChangeCents.value <= 0) {
    return
  }

  if (pendingPaymentMethod.value === 'CASH') {
    const givenCents = Math.round(Number(cashGiven.value || 0) * 100)
    if (givenCents < paymentTotal.value) {
      notificationStore.error('Der gegebene Barbetrag reicht nicht aus')
      return
    }
  }

  if (isInsufficientBalance.value) {
    const givenCents = Math.round(Number(cashGiven.value || 0) * 100)
    const cashDue = paymentTotal.value - selectedMemberBalance.value
    if (givenCents < cashDue) {
      notificationStore.error('Der gegebene Barbetrag reicht nicht aus')
      return
    }
  }
  cartStore.tipCents = cashChangeCents.value
  processingPayment.value = true
  const transaction = await handlePaymentAndCheckout(pendingPaymentMethod.value)
  processingPayment.value = false

  if (transaction?.appliedBalanceOnly) {
    cartStore.tipCents = 0
    closePaymentConfirmation()
    return
  }

  if (transaction) {
    if (transaction.issued_prepaid_voucher_numbers?.length) {
      paymentResult.value = transaction
      return
    }
    closePaymentConfirmation()
  }
}

const handlePaymentAndCheckout = async (method) => {
  if (paymentSource.value === 'deckel') {
    return handleDeckelPayment()
  }

  if (!validatePaymentMethod(method)) {
    return false
  }

  if (method === 'BALANCE' && selectedMemberBalance.value < cartStore.getTotalAmount()) {
    // Balance insufficient: apply full available balance as discount, process rest as CASH
    const currentlyApplied = cartStore.getBalanceAppliedAmount()
    const availableBalance = Math.max(selectedMemberBalance.value - currentlyApplied, 0)
    if (availableBalance > 0) {
      cartStore.applyBalanceDiscount(currentlyApplied + availableBalance)
    }
    cartStore.paymentMethod = 'CASH'
    return handleCheckout()
  }

  cartStore.paymentMethod = method
  return handleCheckout()
}

const selectMember = (member) => {
  cartStore.removeBalanceDiscount()
  cartStore.selectedMemberId = member.id
  cartStore.selectedMemberHasDiscount = !!member.has_discount
  cartStore.recalculatePrices()  // Update prices to member prices
  showMemberModal.value = false
}

const openVoucherModal = () => {
  resetVoucherState()
  showVoucherModal.value = true
}

const validateVoucher = async () => {
  const normalizedVoucher = voucherNumber.value.trim().toUpperCase()
  if (!normalizedVoucher || normalizedVoucher === normalizedVoucherPrefix) return

  voucherNumber.value = normalizedVoucher

  validatingVoucher.value = true
  voucherError.value = null
  voucherValidation.value = null

  try {
    const response = await apiService.post('/transactions/voucher/validate', {
      voucher_number: voucherNumber.value,
      cart_total_cents: cartStore.getTotalAmount(),
    })
    voucherValidation.value = response.data
    voucherValidated.value = true
    console.log('[Kasse] Voucher validated:', response.data)
  } catch (error) {
    const detail = error.response?.data?.detail || error.message || 'Fehler bei der Validierung'
    voucherError.value = detail
    voucherValidated.value = false
    console.error('[Kasse] Voucher validation failed:', error)
  } finally {
    validatingVoucher.value = false
  }
}

const redeemVoucher = async () => {
  if (!voucherValidation.value || !voucherValidation.value.valid) return

  redeemingVoucher.value = true
  voucherError.value = null

  try {
    const appliedVoucher = {
      voucher_number: voucherValidation.value.voucher_number,
      voucher_type: voucherValidation.value.voucher_type,
      value_cents: voucherValidation.value.value_cents,
      applied_amount_cents: voucherValidation.value.applicable_amount_cents,
      message: voucherValidation.value.message,
    }

    cartStore.applyVoucher(appliedVoucher)

    if (voucherValidation.value.covers_cart_total) {
      voucherRedeemed.value = appliedVoucher
      cartStore.paymentMethod = 'CASH'
      const successMessage = voucherValidation.value.remaining_value_cents > 0
        ? 'Verkauf mit Gutschein abgeschlossen. Restguthaben bleibt erhalten.'
        : 'Verkauf mit Gutschein abgeschlossen'
      await handleCheckout(successMessage)
      closeVoucherModal()
      return
    }

    voucherRedeemed.value = {
      ...appliedVoucher,
      message: voucherValidation.value.remaining_value_cents > 0
        ? `Gutschein ${voucherValidation.value.voucher_number} wurde übernommen. Restguthaben bleibt erhalten.`
        : `Gutschein ${voucherValidation.value.voucher_number} wurde als Rabatt übernommen.`,
    }
    notificationStore.success(`Gutschein ${voucherValidation.value.voucher_number} als Rabatt übernommen`)
    closeVoucherModal()
    applyPartialBalanceAndContinue({ notify: true })
  } catch (error) {
    const detail = error.response?.data?.detail || error.message || 'Fehler bei der Einlösung'
    voucherError.value = detail
    console.error('[Kasse] Voucher redemption failed:', error)
  } finally {
    redeemingVoucher.value = false
  }
}

const resetVoucherState = () => {
  voucherNumber.value = voucherPrefix
  voucherValidation.value = null
  voucherValidated.value = false
  voucherRedeemed.value = null
  voucherError.value = null
}

const closeVoucherModal = () => {
  resetVoucherState()
  showVoucherModal.value = false
}

const backToVoucherInput = () => {
  resetVoucherState()
  showVoucherModal.value = true
}

const handleVoucherSecondaryAction = () => {
  if (voucherValidation.value?.valid) {
    backToVoucherInput()
    return
  }

  closeVoucherModal()
}

const removeAppliedVoucher = (voucherNumber) => {
  cartStore.removeVoucher(voucherNumber)
  notificationStore.success('Gutschein aus dem Bon entfernt')
}

const removeAppliedBalance = () => {
  cartStore.removeBalanceDiscount()
  notificationStore.success('Mitgliedsguthaben aus dem Bon entfernt')
}

const serializeCartItems = () => {
  return cartStore.items.map(item => ({
    product_id: item.product_id,
    quantity: item.quantity,
    unit_price_cents: item.unit_price_cents,
    is_internal_material: item.is_internal_material,
    note: item.note,
  }))
}

const loadDeckelList = async () => {
  try {
    const response = await apiService.get('/deckel')
    deckelList.value = response.data
    if (activeDeckel.value) {
      activeDeckel.value = deckelList.value.find(deckel => deckel.id === activeDeckel.value.id) || null
    }
    if (activePaymentDeckel.value) {
      activePaymentDeckel.value = deckelList.value.find(deckel => deckel.id === activePaymentDeckel.value.id) || null
    }
  } catch (error) {
    console.error('[Kasse] Failed to load deckel:', error)
    notificationStore.error(error.response?.data?.detail || 'Deckel konnten nicht geladen werden')
  }
}

const closeDeckelCreateModal = () => {
  showDeckelCreateModal.value = false
  deckelName.value = ''
}

const openDeckelCreateModalFromOverview = () => {
  closeDeckelOverviewModal()
  showDeckelCreateModal.value = true
}

const closeDeckelOverviewModal = () => {
  showDeckelOverviewModal.value = false
}

const closeDeckelDetailsModal = () => {
  showDeckelDetailsModal.value = false
  activeDeckel.value = null
}

const openDeckelOverview = async () => {
  await loadDeckelList()
  if (deckelList.value.length === 0) {
    if (cartStore.items.length === 0) {
      notificationStore.error('Keine gespeicherten Deckel vorhanden')
      return
    }
    showDeckelCreateModal.value = true
    return
  }

  showDeckelOverviewModal.value = true
}

const openDeckelDetails = (deckel) => {
  activeDeckel.value = deckel
  showDeckelDetailsModal.value = true
}

const openDeckelForPayment = (deckel) => {
  openDeckelDetails(deckel)
}

const createDeckel = async () => {
  try {
    const response = await apiService.post('/deckel', {
      name: deckelName.value,
      items: serializeCartItems(),
    })
    cartStore.clear()
    closeDeckelCreateModal()
    await Promise.all([loadDeckelList(), productStore.getProducts(), loadNextReceiptNumber()])
    notificationStore.success(`Deckel "${response.data.name}" gespeichert`)
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Deckel konnte nicht gespeichert werden')
  }
}

const bookCurrentCartToDeckel = async (deckel) => {
  try {
    await apiService.post(`/deckel/${deckel.id}/book`, {
      items: serializeCartItems(),
    })
    cartStore.clear()
    await Promise.all([loadDeckelList(), productStore.getProducts()])
    notificationStore.success(`Bon auf Deckel "${deckel.name}" gebucht`)
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Bon konnte nicht auf den Deckel gebucht werden')
  }
}

const openDeckelPaymentConfirmation = (deckel) => {
  activePaymentDeckel.value = deckel
  closeDeckelDetailsModal()
  closeDeckelOverviewModal()
  openPaymentConfirmation('CASH', { source: 'deckel', deckel })
}

const handleDeckelPayment = async () => {
  if (!activePaymentDeckel.value) {
    return null
  }

  try {
    const response = await apiService.post(`/deckel/${activePaymentDeckel.value.id}/pay`)
    notificationStore.success(`Deckel "${activePaymentDeckel.value.name}" wurde bezahlt`)
    await Promise.all([productStore.getProducts(), memberStore.getMembers(), loadDeckelList(), loadNextReceiptNumber()])
    return response.data
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Deckel konnte nicht abgerechnet werden')
    return null
  }
}

const clampBonWidth = (width) => {
  const minWidth = 340
  const maxWidth = Math.min(window.innerWidth * 0.7, 720)
  bonWidth.value = Math.min(Math.max(width, minWidth), maxWidth)
}

const BON_RESIZE_OFFSET = 16

const stopResizing = () => {
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  window.removeEventListener('mousemove', handleResize)
  window.removeEventListener('mouseup', stopResizing)
}

const handleResize = (event) => {
  const nextWidth = window.innerWidth - event.clientX - BON_RESIZE_OFFSET
  clampBonWidth(nextWidth)
}

const startResizing = (event) => {
  if (window.innerWidth <= 768) {
    return
  }

  event.preventDefault()
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  window.addEventListener('mousemove', handleResize)
  window.addEventListener('mouseup', stopResizing)
}

const formatVoucherReason = (reason) => {
  if (!reason) return '-'
  return voucherReasonLabels[reason] || reason
}

const getExpiredStatusLabel = (voucher) => {
  if (voucher?.status === 'EXPIRED') {
    return '⏰ Abgelaufen'
  }
  return ''
}

const getPaymentMethodLabel = (method) => {
  if (paymentSource.value === 'deckel') {
    return '💰 Zahlung in Bar'
  }
  if (method === 'BALANCE') {
    if (selectedMemberBalance.value >= cartStore.getTotalAmount()) {
      return '💳 Zahlung mit Guthaben'
    }
    return '💳 Zahlung mit Guthaben + Bar (Restbetrag)'
  }

  return '💰 Zahlung in Bar'
}

const loadNextReceiptNumber = async () => {
  try {
    const response = await apiService.get('/transactions/next-receipt-number')
    nextReceiptNumber.value = response.data.receipt_number
  } catch (error) {
    console.error('[Kasse] Failed to load next receipt number:', error)
  }
}

const handleCheckout = async (successMessage = 'Verkauf abgeschlossen') => {
  try {
    console.log('[Kasse] Starting checkout...')
    const transaction = await cartStore.checkout(authStore.user.id)
    console.log('[Kasse] Checkout successful, transaction:', transaction)
    notificationStore.success(successMessage)
    // Reload members to update balances
    await Promise.all([memberStore.getMembers(), productStore.getProducts(), loadNextReceiptNumber(), loadDeckelList()])
    return transaction
  } catch (err) {
    console.error('[Kasse] Checkout failed:', err)
    const errorMessage = err.response?.data?.detail || err.message || 'Fehler bei der Abrechnung'
    console.error('[Kasse] Showing error notification:', errorMessage)
    notificationStore.error(errorMessage)
    return null
  }
}

const getPaymentButtonStyle = (method) => {
  const balance = selectedMemberBalance.value
  const total = cartStore.getTotalAmount()
  const hasMember = !!cartStore.selectedMemberId

  console.log(`[Kasse] Button style for ${method}: hasMember=${hasMember}, balance=${balance}, total=${total}`)

  // No member selected - only BAR button is green
  if (!hasMember) {
    if (method === 'CASH') {
      return { background: 'var(--app-highlight-color)', color: 'var(--app-highlight-contrast)' }
    } else {
      return { background: '#999', color: 'white', cursor: 'not-allowed' }
    }
  }

  // Member selected - check balance
  const hasEnoughBalance = balance >= total
  console.log(`[Kasse] HasEnoughBalance: ${hasEnoughBalance} (${balance} >= ${total})`)

  if (method === 'CASH') {
    return { background: 'var(--app-highlight-color)', color: 'var(--app-highlight-contrast)' }
  } else {
    if (balance > 0) {
      return { background: 'var(--app-banner-color)', color: 'var(--app-banner-contrast)' }
    } else {
      return { background: '#ccc', color: '#999', cursor: 'not-allowed' }
    }
  }
}

// Watch für Member-Updates
watch(
  () => memberStore.members,
  (newMembers) => {
    if (newMembers && newMembers.length > 0) {
      const selectedMem = newMembers.find(m => m.id === cartStore.selectedMemberId)
      if (selectedMem) {
        console.log('[Kasse] Members updated, selected member balance is now:', selectedMem.balance_cents)
      }
    }
  },
  { deep: true }
)

onMounted(async () => {
  await productStore.getProducts()
  await memberStore.getMembers()
  await loadCategories()
  await loadDeckelList()
  await loadNextReceiptNumber()
  clampBonWidth(bonWidth.value)
  console.log('[Kasse] Initial members loaded:', memberStore.members.length)
})

onBeforeUnmount(() => {
  stopResizing()
})

  return {
    productStore, memberStore, cartStore, notificationStore, authStore,
    showMemberModal, showPaymentConfirmModal, showInternalMaterialNoteModal,
    memberSearch, pendingPaymentMethod, processingPayment, paymentResult,
    expandedCategories, categories, bonWidth, nextReceiptNumber, cashGiven,
    imageErrorMap, onImageError, showVoucherModal, voucherNumber, voucherValidation,
    voucherValidated, voucherRedeemed, voucherError, validatingVoucher, redeemingVoucher,
    showDeckelCreateModal, showDeckelOverviewModal, showDeckelDetailsModal, deckelName,
    deckelList, activeDeckel, paymentSource, activePaymentDeckel, pendingInternalMaterialProduct,
    internalMaterialNote, showVariablePriceModal, pendingVariablePriceProduct, variablePrice,
    isVariablePriceValid, voucherPrefix, normalizedVoucherPrefix,
    isInternalMaterialSale, getDisplayedProductPriceCents, loadCategories,
    getCategoryChipStyle, getCategoryCardStyle, getContrastTextColor, toggleCategory,
    getProductsByCategory, activeCategories, productsWithoutCategory,
    selectedMemberName, selectedMemberBalance, selectedMember, hasExpandedCategory,
    cartSubtotal, voucherAppliedAmount, balanceAppliedAmount, hasAppliedVoucher,
    hasAppliedBalance, activeDeckelCount, paymentSummaryItems, paymentSubtotal,
    paymentTotal, cashChangeDisplay, cashChangeCents, voucherActionLabel,
    hasValidVoucherInput, bonPanelStyle, filteredMembers, getDeckelReservedQuantity,
    getCartReservedQuantity, hasMemberPrice, showProductBadge, getAvailableStock,
    isProductOutOfStock, getStockLabel, selectProduct, closeVariablePriceModal,
    confirmVariablePriceSelection, closeInternalMaterialNoteModal, confirmInternalMaterialSelection,
    changeCartItemQuantity, selectCustomer, validatePaymentMethod, applyPartialBalanceAndContinue,
    openPaymentConfirmation, closePaymentConfirmation, confirmPayment, confirmPaymentWithTip,
    handlePaymentAndCheckout, selectMember, openVoucherModal, validateVoucher, redeemVoucher,
    resetVoucherState, closeVoucherModal, backToVoucherInput, handleVoucherSecondaryAction,
    removeAppliedVoucher, removeAppliedBalance, serializeCartItems, loadDeckelList,
    closeDeckelCreateModal, openDeckelCreateModalFromOverview, closeDeckelOverviewModal,
    closeDeckelDetailsModal, openDeckelOverview, openDeckelDetails, openDeckelForPayment,
    createDeckel, bookCurrentCartToDeckel, openDeckelPaymentConfirmation, handleDeckelPayment,
    clampBonWidth, BON_RESIZE_OFFSET, stopResizing, handleResize, startResizing,
    formatVoucherReason, getExpiredStatusLabel, getPaymentMethodLabel, loadNextReceiptNumber,
    handleCheckout, getPaymentButtonStyle, isInsufficientBalance, effectiveCashTotal,
    getMemberFullName, getMemberShortName, formatPrice, formatBalance,
  }
}
