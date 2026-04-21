<template>
  <div class="kasse-container">
    <div class="kasse-products">
      <h2>Produkte</h2>
      <div v-if="productStore.isLoading" class="loading">Läuft...</div>
      <div v-else class="products-section">
        <!-- Active Categories with Expandable Sections -->
        <div
          v-for="category in activeCategories"
          :key="category.id"
          class="category-section"
        >
          <button
            @click="toggleCategory(category.id)"
            class="category-header"
            :class="{ expanded: expandedCategories.includes(category.id) }"
          >
            <span class="category-toggle">{{ expandedCategories.includes(category.id) ? '▼' : '▶' }}</span>
            <span class="category-name">{{ category.name }}</span>
            <span class="category-count">({{ getProductsByCategory(category.id).length }})</span>
          </button>
          
          <div
            v-if="expandedCategories.includes(category.id)"
            class="products-grid"
          >
            <button
              v-for="product in getProductsByCategory(category.id)"
              :key="product.id"
              :disabled="product.stock_quantity === 0"
              class="product-btn"
              @click="selectProduct(product)"
            >
              <div v-if="product.image_path" class="product-image">
                <img :src="`/api/products/${product.id}/image`" :alt="product.name" />
              </div>
              <div class="product-name">{{ product.name }}</div>
              <div class="product-price">{{ formatPrice(product.price_cents) }}</div>
              <div class="product-stock">
                Lager: {{ product.stock_quantity }}
              </div>
            </button>
          </div>
        </div>

        <!-- Products without Categories -->
        <div v-if="productsWithoutCategory.length > 0" class="category-section">
          <button
            @click="toggleCategory(0)"
            class="category-header"
            :class="{ expanded: expandedCategories.includes(0) }"
          >
            <span class="category-toggle">{{ expandedCategories.includes(0) ? '▼' : '▶' }}</span>
            <span class="category-name">Ohne Kategorie</span>
            <span class="category-count">({{ productsWithoutCategory.length }})</span>
          </button>
          
          <div
            v-if="expandedCategories.includes(0)"
            class="products-grid"
          >
            <button
              v-for="product in productsWithoutCategory"
              :key="product.id"
              :disabled="product.stock_quantity === 0"
              class="product-btn"
              @click="selectProduct(product)"
            >
              <div v-if="product.image_path" class="product-image">
                <img :src="`/api/products/${product.id}/image`" :alt="product.name" />
              </div>
              <div class="product-name">{{ product.name }}</div>
              <div class="product-price">{{ formatPrice(product.price_cents) }}</div>
              <div class="product-stock">
                Lager: {{ product.stock_quantity }}
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div
      class="kasse-resizer"
      @mousedown="startResizing"
    ></div>

    <div class="kasse-bon" :style="bonPanelStyle">
      <div class="bon-content">
        <div class="receipt-number-banner">
          Laufende Belegnummer: <strong>#{{ nextReceiptNumber || '-' }}</strong>
        </div>
        <!-- Top section: Items -->
        <div class="bon-items">
          <div
            v-for="item in cartStore.items"
            :key="item.product_id"
            class="bon-item"
          >
            <div class="item-name">{{ item.product_name }}</div>
            <div class="item-controls">
              <button @click="cartStore.updateItemQuantity(item.product_id, item.quantity - 1)" class="btn-qty">−</button>
              <input
                v-model.number="item.quantity"
                type="number"
                min="1"
                @change="cartStore.updateItemQuantity(item.product_id, item.quantity)"
                class="qty-input"
              />
              <button @click="cartStore.updateItemQuantity(item.product_id, item.quantity + 1)" class="btn-qty">+</button>
            </div>
            <div class="item-price">{{ formatPrice(item.total_price_cents) }}</div>
            <button @click="cartStore.removeItem(item.product_id)" class="btn-remove">✕</button>
          </div>
        </div>

        <div v-if="cartStore.items.length === 0" class="empty-bon">
          Keine Artikel im Bon
        </div>

        <div class="bon-total">
          <div class="total-row">
            <div class="total-label">Zwischensumme:</div>
            <div class="total-amount">{{ formatPrice(cartSubtotal) }}</div>
          </div>
          <div v-for="voucher in cartStore.appliedVouchers" :key="voucher.voucher_number" class="total-row voucher-row">
            <div class="total-label">
              Gutscheineinlösung
              <small>{{ voucher.voucher_number }}</small>
            </div>
            <div class="total-amount">-{{ formatPrice(voucher.applied_amount_cents) }}</div>
          </div>
          <div v-if="hasAppliedBalance" class="total-row voucher-row">
            <div class="total-label">
              Mitgliedsguthaben
              <small>{{ selectedMemberName }}</small>
            </div>
            <div class="total-amount">-{{ formatPrice(balanceAppliedAmount) }}</div>
          </div>
          <div class="total-row grand-total">
            <div class="total-label">Zu zahlen:</div>
            <div class="total-amount">{{ formatPrice(cartStore.getTotalAmount()) }}</div>
          </div>
        </div>

        <div v-if="hasAppliedVoucher || hasAppliedBalance" class="voucher-applied-card">
          <div class="applied-discounts">
            <div v-for="voucher in cartStore.appliedVouchers" :key="voucher.voucher_number" class="applied-discount-line">
              <div>
                <strong>🎫 Gutschein aktiv</strong>
                <div class="voucher-applied-hint">
                  {{ voucher.message }}
                </div>
              </div>
              <button @click="removeAppliedVoucher(voucher.voucher_number)" class="btn-remove-voucher">
                Entfernen
              </button>
            </div>
            <div v-if="hasAppliedBalance" class="applied-discount-line">
              <div>
                <strong>💳 Mitgliedsguthaben aktiv</strong>
                <div class="voucher-applied-hint">
                  {{ selectedMemberName }}: {{ formatBalance(balanceAppliedAmount) }} angerechnet
                </div>
              </div>
              <button @click="removeAppliedBalance" class="btn-remove-voucher">
                Entfernen
              </button>
            </div>
          </div>
        </div>

        <!-- Bottom section: Member selection -->
        <div class="member-selection-bottom">
          <div v-if="!cartStore.selectedMemberId" class="member-selector">
            <button
              @click="selectCustomer"
              class="btn btn-info full-width"
            >
              + Mitglied auswählen
            </button>
          </div>

          <div v-else class="member-card">
            <div class="member-card-header">
              <div v-if="selectedMember && selectedMember.photo_path" class="member-avatar">
                <img :src="`/api/members/${cartStore.selectedMemberId}/photo`" :alt="selectedMemberName" />
              </div>
              <div v-else class="member-avatar-placeholder">
                👤
              </div>
              <div class="member-card-info">
                <div class="member-name">{{ selectedMemberName }}</div>
                <div class="member-balance-display">
                  Guthaben: {{ formatBalance(selectedMemberBalance) }}
                </div>
              </div>
            </div>
            <button 
               @click="() => { 
                 cartStore.selectedMemberId = null; 
                 cartStore.selectedMemberHasDiscount = false;
                 cartStore.removeBalanceDiscount();
                 cartStore.recalculatePrices(); 
               }" 
              class="btn-change"
            >
              Wechseln
            </button>
          </div>

          <!-- Payment buttons at bottom -->
          <div class="payment-section">
            <div class="payment-buttons">
              <button
                @click="openPaymentConfirmation('CASH')"
                :disabled="cartStore.items.length === 0"
                :style="getPaymentButtonStyle('CASH')"
                class="payment-btn"
              >
                💰 Zahlen - BAR
              </button>

              <button
                @click="openPaymentConfirmation('BALANCE')"
                :disabled="!cartStore.selectedMemberId || cartStore.items.length === 0 || selectedMemberBalance <= 0"
                :style="getPaymentButtonStyle('BALANCE')"
                class="payment-btn"
              >
                💳 Guthaben nutzen
              </button>

              <button
                @click="showVoucherModal = true"
                :disabled="cartStore.items.length === 0"
                class="payment-btn voucher-btn"
              >
                🎫 Gutschein
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="cancel-section">
        <button @click="cartStore.clear()" class="btn-cancel" title="Kassiervorgang abbrechen">
          ✕ Abbrechen / Zurück
        </button>
      </div>
    </div>

    <!-- Member Selection Modal -->
    <div v-if="showMemberModal" class="modal">
      <div class="modal-content member-modal">
        <h3>Mitglied auswählen</h3>
        <input
          v-model="memberSearch"
          type="text"
          placeholder="Nach Name oder Nummer suchen..."
          class="form-input"
        />
        <div v-if="filteredMembers.length > 0" class="member-grid">
          <button
            v-for="member in filteredMembers"
            :key="member.id"
            @click="selectMember(member)"
            class="member-item"
          >
            <div v-if="member.photo_path" class="member-photo">
              <img :src="`/api/members/${member.id}/photo`" :alt="getMemberFullName(member)" />
            </div>
            <div v-else class="member-photo member-photo-placeholder">👤</div>
            <div class="member-info-box">
              <div class="member-number-badge">Nr. {{ member.member_number }}</div>
              <div class="member-name-modal">{{ getMemberShortName(member) }}</div>
              <div class="balance">{{ formatBalance(member.balance_cents) }}</div>
            </div>
          </button>
        </div>
        <div v-else class="empty-bon">Keine Mitglieder gefunden</div>
        <div class="modal-actions">
          <button @click="showMemberModal = false" class="btn btn-danger">
            Abbrechen / Zurück
          </button>
        </div>
      </div>
    </div>

    <div v-if="showPaymentConfirmModal" class="modal">
      <div class="modal-content payment-modal">
        <h3>Zahlung bestätigen</h3>
        <div class="payment-method-chip">
          {{ getPaymentMethodLabel(pendingPaymentMethod) }}
        </div>
        <div class="payment-summary-list">
          <div v-for="item in cartStore.items" :key="item.product_id" class="payment-summary-item">
            <span>{{ item.quantity }}× {{ item.product_name }}</span>
            <strong>{{ formatPrice(item.total_price_cents) }}</strong>
          </div>
        </div>
        <div class="payment-summary-totals">
          <div class="total-row">
            <span>Zwischensumme</span>
            <strong>{{ formatPrice(cartSubtotal) }}</strong>
          </div>
          <div v-if="hasAppliedVoucher" class="total-row">
            <span>Gutscheine</span>
            <strong>-{{ formatPrice(voucherAppliedAmount) }}</strong>
          </div>
          <div v-if="hasAppliedBalance" class="total-row">
            <span>Mitgliedsguthaben</span>
            <strong>-{{ formatPrice(balanceAppliedAmount) }}</strong>
          </div>
          <div v-if="pendingPaymentMethod === 'BALANCE'" class="total-row">
            <span>Mitglied</span>
            <strong>{{ selectedMemberName }}</strong>
          </div>
          <div class="total-row grand-total">
            <span>Zu zahlen</span>
            <strong>{{ formatPrice(cartStore.getTotalAmount()) }}</strong>
          </div>
        </div>
        <div v-if="pendingPaymentMethod === 'CASH'" class="cash-payment-fields">
          <label>
            Bar gegeben
            <input
              ref="cashGivenInput"
              v-model="cashGiven"
              type="number"
              min="0"
              step="0.01"
              class="form-input"
              @keyup.enter="confirmPayment"
            />
          </label>
          <label>
            Rückgeld
            <input :value="cashChangeDisplay" type="text" class="form-input" readonly />
          </label>
        </div>
        <div class="modal-actions">
          <button @click="confirmPayment" class="btn btn-confirm-payment" :class="{ selected: true }" :disabled="processingPayment">
            {{ processingPayment ? '⏳ Wird verarbeitet...' : 'Bestätigen' }}
          </button>
          <button @click="closePaymentConfirmation" class="btn btn-danger" :disabled="processingPayment">
            Abbrechen / Zurück
          </button>
        </div>
      </div>
    </div>

    <!-- Voucher Redemption Modal -->
    <div v-if="showVoucherModal" class="modal">
      <div class="modal-content voucher-modal">
        <h3>🎫 Gutschein einlösen</h3>

        <!-- Step 1: Input Voucher Number -->
        <div v-if="!voucherValidated" class="step">
          <input
            v-model="voucherNumber"
            type="text"
            placeholder="Gutscheinnummer eingeben (z.B. V-001)"
            class="form-input voucher-input"
            @keyup.enter="validateVoucher"
            autocomplete="off"
          />

          <div v-if="voucherError" class="error-message">
            ❌ {{ voucherError }}
          </div>

          <div class="button-group">
            <button
              @click="validateVoucher"
              :disabled="!voucherNumber || validatingVoucher"
              class="btn btn-primary"
            >
              {{ validatingVoucher ? '⏳ Wird überprüft...' : '✓ Überprüfen' }}
            </button>
            <button @click="closeVoucherModal" class="btn btn-secondary">
              Abbrechen / Zurück
            </button>
          </div>
        </div>

        <!-- Step 2: Show Validation Result -->
        <div v-else-if="voucherValidation && !voucherRedeemed" class="step">
          <div
            :class="['validation-result', voucherValidation.valid ? 'valid' : 'invalid']"
          >
            <h4>{{ voucherValidation.valid ? '✅ Gültig' : '❌ Ungültig' }}</h4>
            <table class="voucher-details">
              <tr>
                <td>Nummer:</td>
                <td><strong>{{ voucherValidation.voucher_number }}</strong></td>
              </tr>
              <tr>
                <td>Typ:</td>
                <td>{{ voucherValidation.voucher_type === 'GIFT' ? '🎁 Geschenk' : '💳 Guthabenkarte' }}</td>
              </tr>
              <tr>
                <td>Wert:</td>
                <td><strong>{{ (voucherValidation.value_cents / 100).toFixed(2) }}€</strong></td>
              </tr>
              <tr v-if="voucherValidation.valid && cartSubtotal > 0">
                <td>Anrechnung:</td>
                <td><strong>{{ (voucherValidation.applicable_amount_cents / 100).toFixed(2) }}€</strong></td>
              </tr>
              <tr v-if="voucherValidation.valid && voucherValidation.remaining_value_cents > 0">
                <td>Restwert:</td>
                <td>{{ (voucherValidation.remaining_value_cents / 100).toFixed(2) }}€</td>
              </tr>
              <tr>
                <td>Status:</td>
                <td>{{ voucherValidation.status === 'CREATED' ? '✅ Verfügbar' : '✓ Bereits eingelöst' }}</td>
              </tr>
              <tr v-if="voucherValidation.reason">
                <td>Grund:</td>
                <td>{{ formatVoucherReason(voucherValidation.reason) }}</td>
              </tr>
            </table>
            <p v-if="voucherValidation.message" class="info-text">
              ℹ️ {{ voucherValidation.message }}
            </p>
          </div>

          <div class="button-group">
            <button
              v-if="voucherValidation.valid"
              @click="redeemVoucher"
              :disabled="redeemingVoucher"
              class="btn btn-primary"
            >
              {{ voucherActionLabel }}
            </button>
            <button @click="handleVoucherSecondaryAction" class="btn btn-secondary">
              Abbrechen / Zurück
            </button>
          </div>
        </div>

        <!-- Step 3: Success Message -->
        <div v-else-if="voucherRedeemed" class="step">
          <div class="success-message">
            <h4>✅ Gutschein eingelöst!</h4>
            <table class="voucher-details">
              <tr>
                <td>Nummer:</td>
                <td><strong>{{ voucherRedeemed.voucher_number }}</strong></td>
              </tr>
              <tr>
                <td>Typ:</td>
                <td>{{ voucherRedeemed.voucher_type === 'GIFT' ? '🎁 Geschenk' : '💳 Guthabenkarte' }}</td>
              </tr>
              <tr>
                <td>Wert:</td>
                <td><strong>{{ (voucherRedeemed.value_cents / 100).toFixed(2) }}€</strong></td>
              </tr>
            </table>
            <p class="info-text">
              {{ voucherRedeemed.message }}
            </p>
          </div>

          <div class="button-group">
            <button @click="closeVoucherModal" class="btn btn-primary">
              ✓ Fertig
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useProductStore } from '@/stores/product'
import { useMemberStore } from '@/stores/member'
import { useCartStore } from '@/stores/cart'
import { useNotificationStore } from '@/stores/notification'
import { useAuthStore } from '@/stores/auth'
import { formatPrice, formatBalance } from '@/services/utils'
import { getMemberFullName, getMemberShortName, getMemberSearchText } from '@/services/member'
import apiService from '@/services/api'

const productStore = useProductStore()
const memberStore = useMemberStore()
const cartStore = useCartStore()
const notificationStore = useNotificationStore()
const authStore = useAuthStore()

const showMemberModal = ref(false)
const showPaymentConfirmModal = ref(false)
const memberSearch = ref('')
const pendingPaymentMethod = ref(null)
const processingPayment = ref(false)
const expandedCategories = ref([])
const categories = ref([])
const bonWidth = ref(420)
const nextReceiptNumber = ref(null)
const cashGiven = ref('')
const cashGivenInput = ref(null)

// Voucher redemption
const showVoucherModal = ref(false)
const voucherNumber = ref('')
const voucherValidation = ref(null)
const voucherValidated = ref(false)
const voucherRedeemed = ref(null)
const voucherError = ref(null)
const validatingVoucher = ref(false)
const redeemingVoucher = ref(false)

const voucherReasonLabels = {
  DYP_SIEGER: 'Dyp-Sieger',
  PROMOTION: 'Promotion',
}

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

const toggleCategory = (categoryId) => {
  const idx = expandedCategories.value.indexOf(categoryId)
  if (idx > -1) {
    expandedCategories.value.splice(idx, 1)
  } else {
    expandedCategories.value.push(categoryId)
  }
}

const getProductsByCategory = (categoryId) => {
  if (categoryId === 0) {
    return productsWithoutCategory.value
  }
  return productStore.products.filter(p =>
    p.categories && p.categories.some(c => c.id === categoryId)
  )
}

const activeCategories = computed(() => {
  return categories.value.filter(c => c.is_active_in_kasse).sort((a, b) => a.display_order - b.display_order)
})

const productsWithoutCategory = computed(() => {
  return productStore.products.filter(p => !p.categories || p.categories.length === 0)
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

const cartSubtotal = computed(() => cartStore.getSubtotalAmount())
const voucherAppliedAmount = computed(() => cartStore.getVoucherAppliedAmount())
const balanceAppliedAmount = computed(() => cartStore.getBalanceAppliedAmount())
const hasAppliedVoucher = computed(() => cartStore.appliedVouchers.length > 0)
const hasAppliedBalance = computed(() => balanceAppliedAmount.value > 0)
const cashChangeDisplay = computed(() => {
  const value = Number(cashGiven.value || 0)
  const change = Math.max(Math.round((value * 100) - cartStore.getTotalAmount()), 0)
  return formatPrice(change)
})
const voucherActionLabel = computed(() => {
  if (redeemingVoucher.value) {
    return '⏳ Wird verarbeitet...'
  }

  return voucherValidation.value?.covers_cart_total
    ? '✓ Kauf abschließen'
    : '✓ Als Rabatt anwenden'
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

const selectProduct = (product) => {
  cartStore.addItem(product)
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

const openPaymentConfirmation = (method) => {
  if (!validatePaymentMethod(method)) {
    return
  }

  pendingPaymentMethod.value = method
  showPaymentConfirmModal.value = true
  cashGiven.value = method === 'CASH' ? (cartStore.getTotalAmount() / 100).toFixed(2) : ''
  nextTick(() => {
    if (method === 'CASH') {
      cashGivenInput.value?.focus()
      cashGivenInput.value?.select?.()
    }
  })
}

const closePaymentConfirmation = () => {
  if (processingPayment.value) {
    return
  }

  showPaymentConfirmModal.value = false
  pendingPaymentMethod.value = null
  cashGiven.value = ''
}

const confirmPayment = async () => {
  if (!pendingPaymentMethod.value) {
    return
  }

  if (pendingPaymentMethod.value === 'CASH') {
    const givenCents = Math.round(Number(cashGiven.value || 0) * 100)
    if (givenCents < cartStore.getTotalAmount()) {
      notificationStore.error('Der gegebene Barbetrag reicht nicht aus')
      return
    }
  }

  processingPayment.value = true
  const success = await handlePaymentAndCheckout(pendingPaymentMethod.value)
  processingPayment.value = false

  if (success) {
    closePaymentConfirmation()
  }
}

const handlePaymentAndCheckout = async (method) => {
  if (!validatePaymentMethod(method)) {
    return false
  }

  if (method === 'BALANCE' && selectedMemberBalance.value < cartStore.getTotalAmount()) {
    cartStore.applyBalanceDiscount(selectedMemberBalance.value)
    notificationStore.success('Mitgliedsguthaben wurde als Rabatt auf den Warenkorb angerechnet')
    pendingPaymentMethod.value = null
    showPaymentConfirmModal.value = false
    return true
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

const validateVoucher = async () => {
  if (!voucherNumber.value) return
  
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
  } catch (error) {
    const detail = error.response?.data?.detail || error.message || 'Fehler bei der Einlösung'
    voucherError.value = detail
    console.error('[Kasse] Voucher redemption failed:', error)
  } finally {
    redeemingVoucher.value = false
  }
}

const resetVoucherState = () => {
  voucherNumber.value = ''
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

const getPaymentMethodLabel = (method) => {
  if (method === 'BALANCE') {
    return selectedMemberBalance.value >= cartStore.getTotalAmount()
      ? '💳 Zahlung mit Guthaben'
      : '💳 Guthaben als Rabatt anwenden'
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
    await memberStore.getMembers()
    await loadNextReceiptNumber()
    return true
  } catch (err) {
    console.error('[Kasse] Checkout failed:', err)
    const errorMessage = err.response?.data?.detail || err.message || 'Fehler bei der Abrechnung'
    console.error('[Kasse] Showing error notification:', errorMessage)
    notificationStore.error(errorMessage)
    return false
  }
}

const getPaymentButtonStyle = (method) => {
  const balance = selectedMemberBalance.value
  const total = cartStore.total
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
  await loadNextReceiptNumber()
  clampBonWidth(bonWidth.value)
  console.log('[Kasse] Initial members loaded:', memberStore.members.length)
})

onBeforeUnmount(() => {
  stopResizing()
})
</script>

<style scoped lang="scss">
.kasse-container {
  display: flex;
  gap: 0;
  padding: 1rem;
  height: calc(100vh - 70px);
  background: var(--app-background-color);

  @media (max-width: 768px) {
    flex-direction: column;
  }
}

.kasse-products {
  flex: 1 1 auto;
  min-width: 0;
  margin-right: 1rem;
  background: var(--app-surface-color);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 10px 24px rgba(24, 28, 34, 0.14);
  overflow-y: auto;
  border: 1px solid var(--app-banner-color);

  h2 {
    margin: 0 0 1rem 0;
    color: var(--app-banner-color);
    font-size: 1.3rem;
  }
}

.kasse-resizer {
  width: 12px;
  margin: 0 0.5rem;
  border-radius: 999px;
  background: var(--app-highlight-color);
  cursor: col-resize;
  flex: 0 0 12px;
  align-self: stretch;
  transition: background 0.2s ease;

  &:hover {
    opacity: 0.85;
  }

  @media (max-width: 768px) {
    display: none;
  }
}

.kasse-bon {
  flex: 0 0 420px;
  width: 420px;
  min-width: 320px;
  max-width: min(70vw, 720px);
  background: var(--app-surface-color);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 10px 24px rgba(24, 28, 34, 0.14);
  overflow-y: auto;
  border: 1px solid var(--app-banner-color);
  border-left: 5px solid var(--app-highlight-color);

  h2 {
    margin: 0 0 1rem 0;
    color: var(--app-banner-color);
    font-size: 1.3rem;
  }

  @media (max-width: 768px) {
    width: 100%;
    min-width: 0;
    max-width: 100%;
    flex-basis: auto !important;
  }
}

.products-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.category-section {
  border: 1px solid var(--app-banner-color);
  border-radius: 6px;
  overflow: hidden;
}

.category-header {
  width: 100%;
  padding: 0.75rem 1rem;
  background: var(--app-banner-color);
  border: none;
  text-align: left;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.7rem;
  font-weight: 600;
  color: var(--app-banner-contrast);
  transition: all 0.2s;

  &:hover {
    opacity: 0.92;
  }

  &.expanded {
    background: var(--app-highlight-color);
    color: var(--app-highlight-contrast);
    border-left: 4px solid var(--app-highlight-color);
  }

  .category-toggle {
    display: inline-block;
    font-size: 0.9rem;
    transition: transform 0.2s;
  }

  .category-name {
    flex: 1;
  }

  .category-count {
    font-size: 0.85rem;
    color: #999;
    font-weight: normal;
  }
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--app-background-color);

  @media (max-width: 1400px) {
    grid-template-columns: repeat(4, 1fr);
  }

  @media (max-width: 1100px) {
    grid-template-columns: repeat(3, 1fr);
  }

  @media (max-width: 800px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
}

.product-btn {
  background: #fff;
  border: 2px solid color-mix(in srgb, var(--app-banner-color) 30%, white 70%);
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
  font-size: 0.9rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;

  &:hover:not(:disabled) {
    background: color-mix(in srgb, var(--app-highlight-color) 10%, white 90%);
    border-color: var(--app-highlight-color);
    box-shadow: 0 2px 8px color-mix(in srgb, var(--app-highlight-color) 25%, transparent);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .product-image {
    width: 100%;
    height: 80px;
    overflow: hidden;
    border-radius: 4px;
    background: #f6f7f9;
    display: flex;
    align-items: center;
    justify-content: center;

    img {
      max-width: 100%;
      max-height: 100%;
      object-fit: cover;
    }
  }

  .product-name {
    font-weight: 600;
  }

  .product-price {
    color: var(--app-highlight-color);
    font-size: 1.1rem;
    font-weight: bold;
  }

  .product-stock {
    font-size: 0.85rem;
    color: #666;
  }
}

.member-info {
  background: color-mix(in srgb, var(--app-background-color) 55%, white 45%);
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  border-left: 4px solid var(--app-highlight-color);

  .member-name {
    font-weight: 600;
    color: var(--app-highlight-color);
    margin-bottom: 0.5rem;
  }

  .member-balance {
    color: #666;
    margin-bottom: 0.5rem;
  }

  .btn-small {
    background: white;
    border: 1px solid #ddd;
    padding: 0.4rem 0.8rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85rem;

    &:hover {
      background: #d5dae0;
    }
  }
}

.bon-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  flex: 1;
  overflow: hidden;
}

.payment-section {
  flex-shrink: 0;
  margin-top: 1.5rem;
  
  .payment-buttons {
    display: flex;
    flex-direction: row;
    gap: 0.75rem;

    .payment-btn {
      flex: 1;
      font-size: 0.95rem;
      padding: 0.8rem;
      border-radius: 6px;
      font-weight: 600;
      transition: all 0.2s;
      border: none;
      cursor: pointer;

      &:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      &:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
      }

      &.active {
        box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.3);
        transform: scale(1.02);
      }

      &.voucher-btn {
        background: var(--app-banner-color);
        color: var(--app-banner-contrast);
      }
    }
  }
}

.bon-items {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #cfcfcf;
  border-radius: 4px;
  padding: 0.5rem;
  background: #e7e7e7;
  min-height: 50px;
}

.bon-item {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  padding: 0.75rem;
  background: white;
  border-radius: 4px;
  margin-bottom: 0.5rem;

  .item-name {
    flex: 1;
    font-weight: 500;
  }

  .item-controls {
    display: flex;
    gap: 0.3rem;
    align-items: center;

    button {
      width: 28px;
      height: 28px;
      border: 1px solid #ddd;
      background: white;
      cursor: pointer;
      border-radius: 4px;
      font-size: 0.9rem;

      &:hover {
        background: #f0f0f0;
      }
    }
  }

  .qty-input {
    width: 40px;
    border: 1px solid #ddd;
    border-radius: 4px;
    text-align: center;
    font-size: 0.9rem;
    padding: 0.3rem;
  }

  .item-price {
    font-weight: 600;
    min-width: 70px;
    text-align: right;
    color: var(--app-highlight-color);
  }

  .btn-remove {
    background: #ffebee;
    color: #c62828;
    border: none;
    border-radius: 4px;
    width: 28px;
    height: 28px;
    cursor: pointer;
    font-weight: bold;
    font-size: 0.9rem;

    &:hover {
      background: #ffcdd2;
    }
  }
}

.empty-bon {
  text-align: center;
  color: #999;
  padding: 2rem 1rem;
  font-size: 0.95rem;
}

.bon-total {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  padding: 0.75rem;
  background: color-mix(in srgb, var(--app-background-color) 65%, white 35%);
  border-radius: 4px;

  .total-label {
    font-weight: 600;
  }

  .total-amount {
    color: var(--app-highlight-color);
    font-weight: bold;
    font-size: 1.1rem;
  }
}

.receipt-number-banner {
  margin-bottom: 0.75rem;
  padding: 0.65rem 0.85rem;
  background: color-mix(in srgb, var(--app-banner-color) 12%, white 88%);
  border-radius: 8px;
  color: var(--app-banner-color);
  font-weight: 600;
}

.total-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  width: 100%;
}

.grand-total {
  padding-top: 0.55rem;
  border-top: 1px solid color-mix(in srgb, var(--app-banner-color) 25%, white 75%);

  .total-amount {
    font-size: 1.3rem;
  }
}

.voucher-row {
  color: var(--app-highlight-color);

  small {
    display: block;
    color: #5d646d;
    font-weight: 500;
  }
}

.voucher-applied-card {
  display: flex;
  gap: 1rem;
  padding: 0.85rem 1rem;
  border-radius: 8px;
  background: color-mix(in srgb, var(--app-highlight-color) 12%, white 88%);
  border: 1px solid color-mix(in srgb, var(--app-highlight-color) 30%, white 70%);
}

.applied-discounts {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
}

.applied-discount-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.voucher-applied-hint {
  color: #4f555d;
  font-size: 0.85rem;
}

.btn-remove-voucher {
  border: 1px solid color-mix(in srgb, var(--app-highlight-color) 35%, white 65%);
  background: #eef1f4;
  color: var(--app-highlight-color);
  border-radius: 6px;
  padding: 0.45rem 0.75rem;
  cursor: pointer;
}

.member-selection-bottom {
  flex-shrink: 0;
  
  .member-selector {
    width: 100%;
    
    .full-width {
      width: 100%;
    }
  }

  .member-card {
    background: #eef1f4;
    border: 2px solid var(--app-banner-color);
    border-radius: 8px;
    padding: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 0.75rem;

    .member-card-header {
      display: flex;
      gap: 0.75rem;
      align-items: center;

      .member-avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        overflow: hidden;
        border: 2px solid var(--app-banner-color);
        flex-shrink: 0;

        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      }

      .member-avatar-placeholder {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: #e3f2fd;
        border: 2px solid var(--app-banner-color);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        flex-shrink: 0;
      }

      .member-card-info {
        flex: 1;
        min-width: 0;

        .member-name {
          font-weight: 600;
          color: #333;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .member-balance-display {
          font-size: 0.85rem;
          color: var(--app-highlight-color);
          font-weight: 600;
        }
      }
    }

    .btn-change {
      width: 100%;
      padding: 0.5rem;
      background: white;
      border: 1px solid var(--app-banner-color);
      color: var(--app-banner-color);
      border-radius: 4px;
      cursor: pointer;
      font-weight: 600;
      font-size: 0.85rem;
      transition: all 0.2s;
      margin-bottom: 0.75rem;

      &:hover {
        background: color-mix(in srgb, var(--app-banner-color) 10%, white 90%);
      }
    }
  }

  .payment-section {
    width: 100%;
    
    .payment-buttons {
      display: flex;
      flex-direction: row;
      gap: 0.75rem;

      .payment-btn {
        flex: 1;
        font-size: 0.95rem;
        padding: 0.8rem;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s;
        border: none;
        cursor: pointer;

        &:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        &:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
      }
    }
  }
}

.member-selection {
  display: none;
}

.cancel-section {
  position: fixed;
  bottom: 1rem;
  right: 1rem;
  z-index: 100;
}

.btn-cancel {
  background-color: #f5f5f5;
  color: #999;
  border: 2px solid #ddd;
  padding: 0.8rem 1.2rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s;

  &:hover {
    background-color: #f0f0f0;
    border-color: #999;
    color: #666;
  }

  &:active {
    transform: scale(0.95);
  }
}

.btn {
  padding: 0.75rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:not(:disabled):hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
}

.btn-success {
  background-color: #4caf50;
  color: white;

  &:not(:disabled):hover {
    background-color: #45a049;
  }
}

.btn-danger {
  background-color: #f44336;
  color: white;

  &:not(:disabled):hover {
    background-color: #da190b;
  }
}

.btn-info {
  background-color: var(--app-banner-color);
  color: var(--app-banner-contrast);

  &:not(:disabled):hover {
    opacity: 0.9;
  }
}

.btn-subtle {
  background-color: #f5f5f5;
  color: #666;
  border: 1px solid #ddd;
  font-size: 0.85rem;

  &:not(:disabled):hover {
    background-color: #e0e0e0;
    border-color: #999;
  }
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;

  .modal-content {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    width: 90%;
    max-width: 400px;
    max-height: 80vh;
    overflow-y: auto;

    h3 {
      margin-top: 0;
      color: #333;
    }

    .form-input {
      width: 100%;
      padding: 0.75rem;
      border: 1px solid #ddd;
      border-radius: 4px;
      margin-bottom: 1rem;
      font-size: 1rem;
    }

    &.member-modal {
      max-width: 960px;
    }

    &.payment-modal {
      max-width: 560px;

      .cash-payment-fields {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 1rem;
        margin-bottom: 1rem;

        label {
          font-weight: 600;
          color: #334155;
        }

        .form-input {
          margin-bottom: 0;
          margin-top: 0.5rem;
        }
      }
    }

    &.voucher-modal {
      max-width: 500px;

      .voucher-input {
        text-transform: uppercase;
        font-family: monospace;
        letter-spacing: 0.1em;
      }

      .step {
        animation: fadeIn 0.2s;
      }

      .validation-result {
        border: 2px solid #ddd;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;

        h4 {
          margin-top: 0;
          margin-bottom: 1rem;
        }

        &.valid {
          background: #d4edda;
          border-color: #c3e6cb;
          color: #155724;

          h4 {
            color: #155724;
          }
        }

        &.invalid {
          background: #f8d7da;
          border-color: #f5c6cb;
          color: #721c24;

          h4 {
            color: #721c24;
          }
        }
      }

      .voucher-details {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 1rem;
        font-size: 0.9rem;

        tr {
          border-bottom: 1px solid rgba(0, 0, 0, 0.1);
        }

        td {
          padding: 0.5rem;

          &:first-child {
            color: #666;
            font-weight: 500;
            width: 100px;
          }

          &:last-child {
            text-align: right;
          }
        }
      }

      .success-message {
        background: #d4edda;
        border: 2px solid #c3e6cb;
        border-radius: 8px;
        padding: 1.5rem;
        color: #155724;
        margin-bottom: 1.5rem;

        h4 {
          margin-top: 0;
          margin-bottom: 1rem;
          color: #155724;
        }
      }

      .info-text {
        font-size: 0.85rem;
        color: #666;
        margin: 0;
        padding: 0.5rem;
        background: #f9f9f9;
        border-radius: 4px;
      }

      .error-message {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 4px;
        color: #721c24;
        padding: 0.75rem;
        margin-bottom: 1rem;
        font-size: 0.9rem;
      }

      .button-group {
        display: flex;
        gap: 0.75rem;
        justify-content: flex-end;

        button {
          flex: 1;
        }
      }
    }
  }
}

.btn-confirm-payment {
  background: #2e7d32;
  color: #fff;
  box-shadow: 0 0 0 2px rgba(46, 125, 50, 0.2);

  &.selected {
    box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.24), 0 0 16px rgba(46, 125, 50, 0.45);
  }

  &:not(:disabled):hover {
    background: #256a29;
  }
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
}

.member-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
  max-height: 60vh;
  overflow-y: auto;
}

.member-item {
  background: white;
  border: 2px solid #ddd;
  padding: 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: center;
  text-align: left;

  &:hover {
    background: #f0f0f0;
    border-color: var(--app-banner-color);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .member-photo {
    width: 84px;
    height: 84px;
    border-radius: 50%;
    overflow: hidden;
    background: #e0e0e0;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }

  .member-photo-placeholder {
    font-size: 2rem;
  }

  .member-info-box {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    width: 100%;
    align-items: center;

    .member-number-badge {
      font-size: 0.8rem;
      color: var(--app-banner-color);
      font-weight: 600;
    }

    .member-name-modal {
      font-weight: 600;
      color: #333;
      text-align: center;
    }

    .balance {
      font-size: 0.85rem;
      color: #666;
    }
  }

  .balance {
    color: var(--app-highlight-color);
    font-weight: 600;
  }
}

.payment-method-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
  padding: 0.45rem 0.85rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-banner-color) 12%, white 88%);
  color: var(--app-banner-color);
  font-weight: 600;
}

.payment-summary-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 280px;
  overflow-y: auto;
  margin-bottom: 1rem;
}

.payment-summary-item,
.payment-summary-totals .total-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.payment-summary-item {
  padding: 0.65rem 0.75rem;
  border-radius: 6px;
  background: #f5f5f5;
}

.payment-summary-totals {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #999;
}
</style>
