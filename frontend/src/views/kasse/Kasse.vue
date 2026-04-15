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

    <div class="kasse-bon">
      <!-- Current receipt number -->
      <div v-if="currentReceiptNumber" class="bon-header">
        <div class="receipt-number-current">
          <strong>Belegnr.: {{ currentReceiptNumber }}</strong>
        </div>
      </div>

      <div class="bon-content">
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
          <div class="total-label">Gesamt:</div>
          <div class="total-amount">{{ formatPrice(cartStore.getTotalAmount()) }}</div>
        </div>

        <div v-if="lastTransaction && lastTransaction.receipt_number" class="receipt-number">
          <strong>Belegnummer: {{ lastTransaction.receipt_number }}</strong>
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
                @click="handlePaymentAndCheckout('CASH')"
                :disabled="cartStore.items.length === 0"
                :style="getPaymentButtonStyle('CASH')"
                class="payment-btn"
              >
                💰 Zahlen - BAR
              </button>

              <button
                @click="handlePaymentAndCheckout('BALANCE')"
                :disabled="!cartStore.selectedMemberId || cartStore.items.length === 0 || selectedMemberBalance < cartStore.total"
                :style="getPaymentButtonStyle('BALANCE')"
                class="payment-btn"
              >
                💳 Zahlen - Guthaben
              </button>

              <button
                @click="showVoucherModal = true"
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
          ✕ Abbrechen
        </button>
      </div>
    </div>

    <!-- Member Selection Modal -->
    <div v-if="showMemberModal" class="modal">
      <div class="modal-content">
        <h3>Mitglied auswählen</h3>
        <input
          v-model="memberSearch"
          type="text"
          placeholder="Nach Name suchen..."
          class="form-input"
        />
        <div class="member-list">
          <button
            v-for="member in filteredMembers"
            :key="member.id"
            @click="selectMember(member)"
            class="member-item"
          >
            <div v-if="member.photo_path" class="member-photo">
              <img :src="`/api/members/${member.id}/photo`" :alt="member.name" />
            </div>
            <div class="member-info-box">
              <div class="member-name-modal">{{ member.name }}</div>
              <div class="balance">{{ formatBalance(member.balance_cents) }}</div>
            </div>
          </button>
        </div>
        <button @click="showMemberModal = false" class="btn btn-danger">
          Abbrechen
        </button>
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
            <button @click="resetVoucher" class="btn btn-secondary">
              Abbrechen
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
                <td>{{ voucherValidation.voucher_type === 'GIFT' ? '🎁 Geschenk' : '💳 Guthaben' }}</td>
              </tr>
              <tr>
                <td>Wert:</td>
                <td><strong>{{ (voucherValidation.value_cents / 100).toFixed(2) }}€</strong></td>
              </tr>
              <tr>
                <td>Status:</td>
                <td>{{ voucherValidation.status === 'CREATED' ? '✅ Verfügbar' : '✓ Bereits eingelöst' }}</td>
              </tr>
              <tr v-if="voucherValidation.reason">
                <td>Grund:</td>
                <td>{{ voucherValidation.reason }}</td>
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
              {{ redeemingVoucher ? '⏳ Wird eingelöst...' : '✓ Einlösen' }}
            </button>
            <button @click="resetVoucher" class="btn btn-secondary">
              {{ voucherValidation.valid ? 'Neue Nummer' : 'Abbrechen' }}
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
                <td>{{ voucherRedeemed.voucher_type === 'GIFT' ? '🎁 Geschenk' : '💳 Guthaben' }}</td>
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
            <button @click="resetVoucher" class="btn btn-primary">
              ✓ Fertig
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useProductStore } from '@/stores/product'
import { useMemberStore } from '@/stores/member'
import { useCartStore } from '@/stores/cart'
import { useNotificationStore } from '@/stores/notification'
import { useAuthStore } from '@/stores/auth'
import { formatPrice, formatBalance } from '@/services/utils'
import apiService from '@/services/api'

const productStore = useProductStore()
const memberStore = useMemberStore()
const cartStore = useCartStore()
const notificationStore = useNotificationStore()
const authStore = useAuthStore()

const showMemberModal = ref(false)
const memberSearch = ref('')
const lastTransaction = ref(null)
const currentReceiptNumber = ref(null)
const expandedCategories = ref([])
const categories = ref([])

// Voucher redemption
const showVoucherModal = ref(false)
const voucherNumber = ref('')
const voucherValidation = ref(null)
const voucherValidated = ref(false)
const voucherRedeemed = ref(null)
const voucherError = ref(null)
const validatingVoucher = ref(false)
const redeemingVoucher = ref(false)

const loadNextReceiptNumber = async () => {
  try {
    const response = await apiService.get('/transactions/next-receipt-number')
    currentReceiptNumber.value = response.data.receipt_number
    console.log('[Kasse] Next receipt number loaded:', currentReceiptNumber.value)
  } catch (err) {
    console.error('[Kasse] Failed to load receipt number:', err)
  }
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

onMounted(() => {
  loadNextReceiptNumber()
})

const activeCategories = computed(() => {
  return categories.value.filter(c => c.is_active_in_kasse).sort((a, b) => a.display_order - b.display_order)
})

const productsWithoutCategory = computed(() => {
  return productStore.products.filter(p => !p.categories || p.categories.length === 0)
})

const selectedMemberName = computed(() => {
  const member = memberStore.members.find(m => m.id === cartStore.selectedMemberId)
  return member?.name || ''
})

const selectedMemberBalance = computed(() => {
  const member = memberStore.members.find(m => m.id === cartStore.selectedMemberId)
  console.log(`[Kasse] Balance for member ${cartStore.selectedMemberId}:`, member?.balance_cents)
  return member?.balance_cents || 0
})

const selectedMember = computed(() => {
  return memberStore.members.find(m => m.id === cartStore.selectedMemberId) || null
})

const filteredMembers = computed(() => {
  return memberStore.members.filter(m =>
    m.name.toLowerCase().includes(memberSearch.value.toLowerCase())
  )
})

const selectProduct = (product) => {
  cartStore.addItem(product)
}

const selectCustomer = () => {
  showMemberModal.value = true
}

const handlePaymentAndCheckout = async (method) => {
  // Validate balance payment
  if (method === 'BALANCE') {
    if (!cartStore.selectedMemberId) {
      notificationStore.error('Bitte wählen Sie ein Mitglied aus')
      return
    }
    
    if (selectedMemberBalance.value <= 0) {
      notificationStore.error('Das Mitglied hat kein Guthaben')
      return
    }
    
    if (selectedMemberBalance.value < cartStore.total) {
      notificationStore.error(
        `Unzureichendes Guthaben. Verfügbar: ${formatBalance(selectedMemberBalance.value)}, benötigt: ${formatBalance(cartStore.total)}`
      )
      return
    }
  }
  
  cartStore.paymentMethod = method
  await handleCheckout()
}

const selectMember = (member) => {
  cartStore.selectedMemberId = member.id
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
      voucher_number: voucherNumber.value
    })
    voucherValidation.value = response
    voucherValidated.value = true
    console.log('[Kasse] Voucher validated:', response)
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
    const response = await apiService.post('/transactions/voucher/redeem', {
      voucher_number: voucherNumber.value,
      member_id: cartStore.selectedMemberId || null
    })
    voucherRedeemed.value = response
    console.log('[Kasse] Voucher redeemed:', response)
    
    // Reload members to update balances (for PREPAID vouchers)
    await memberStore.getMembers()
    notificationStore.success(`Gutschein ${voucherNumber.value} eingelöst`)
  } catch (error) {
    const detail = error.response?.data?.detail || error.message || 'Fehler bei der Einlösung'
    voucherError.value = detail
    console.error('[Kasse] Voucher redemption failed:', error)
  } finally {
    redeemingVoucher.value = false
  }
}

const resetVoucher = () => {
  voucherNumber.value = ''
  voucherValidation.value = null
  voucherValidated.value = false
  voucherRedeemed.value = null
  voucherError.value = null
  showVoucherModal.value = false
}

const handleCheckout = async () => {
  try {
    console.log('[Kasse] Starting checkout...')
    const transaction = await cartStore.checkout(authStore.user.id)
    console.log('[Kasse] Checkout successful, transaction:', transaction)
    lastTransaction.value = transaction
    console.log('[Kasse] Set lastTransaction with receipt_number:', transaction?.receipt_number)
    notificationStore.success('Verkauf abgeschlossen')
    // Reload members to update balances
    await memberStore.getMembers()
    // Load next receipt number for the next transaction
    await loadNextReceiptNumber()
  } catch (err) {
    console.error('[Kasse] Checkout failed:', err)
    const errorMessage = err.response?.data?.detail || err.message || 'Fehler bei der Abrechnung'
    console.error('[Kasse] Showing error notification:', errorMessage)
    notificationStore.error(errorMessage)
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
      return { background: '#4caf50', color: 'white' } // Green
    } else {
      return { background: '#999', color: 'white', cursor: 'not-allowed' } // Gray, disabled
    }
  }

  // Member selected - check balance
  const hasEnoughBalance = balance >= total
  console.log(`[Kasse] HasEnoughBalance: ${hasEnoughBalance} (${balance} >= ${total})`)
  
  if (method === 'CASH') {
    return { background: '#81c784', color: 'white' } // Light green
  } else {
    if (hasEnoughBalance) {
      return { background: '#a5d6a7', color: 'white' } // Very light green
    } else {
      return { background: '#ccc', color: '#999', cursor: 'not-allowed' } // Gray, disabled
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
  console.log('[Kasse] Initial members loaded:', memberStore.members.length)
})
</script>

<style scoped lang="scss">
.kasse-container {
  display: grid;
  grid-template-columns: 3fr 1fr;
  gap: 1rem;
  padding: 1rem;
  height: calc(100vh - 70px);
  background: #e3e3e3;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }
}

.kasse-products {
  background: linear-gradient(135deg, #dddddd 0%, #cecece 100%);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow-y: auto;

  h2 {
    margin: 0 0 1rem 0;
    color: #333;
    font-size: 1.3rem;
  }
}

.kasse-bon {
  background: linear-gradient(135deg, #dddddd 0%, #cecece 100%);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  border-left: 5px solid #ff6b35;

  h2 {
    margin: 0 0 1rem 0;
    color: #333;
    font-size: 1.3rem;
  }
}

.products-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.category-section {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
}

.category-header {
  width: 100%;
  padding: 0.75rem 1rem;
  background: #e3e3e3;
  border: none;
  text-align: left;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.7rem;
  font-weight: 600;
  color: #333;
  transition: all 0.2s;

  &:hover {
    background: #d9d9d9;
  }

  &.expanded {
    background: linear-gradient(90deg, #fff5f0 0%, #fff9f7 100%);
    color: #ff6b35;
    border-left: 4px solid #ff6b35;
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
  background: #dcdcdc;

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
  background: white;
  border: 2px solid #e0e0e0;
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
    background: #fff9f7;
    border-color: #ff6b35;
    box-shadow: 0 2px 8px rgba(255, 107, 53, 0.15);
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
    background: white;
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
    color: #ff6b35;
    font-size: 1.1rem;
    font-weight: bold;
  }

  .product-stock {
    font-size: 0.85rem;
    color: #666;
  }
}

.member-info {
  background: #e1e1e1;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  border-left: 4px solid #ff6b35;

  .member-name {
    font-weight: 600;
    color: #ff6b35;
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
      background: #f5f5f5;
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

.bon-header {
  flex-shrink: 0;
  background: #dcdcdc;
  padding: 0.8rem;
  border-bottom: 2px solid #c7c7c7;
  display: flex;
  justify-content: center;
  align-items: center;
}

.receipt-number-current {
  font-size: 1.1rem;
  font-weight: bold;
  color: #333;
  padding: 0.5rem;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #ddd;
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
        background: linear-gradient(135deg, #ff9500 0%, #f57c00 100%);
        color: white;
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
    color: #667eea;
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
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f0f0f0;
  border-radius: 4px;

  .total-label {
    font-weight: 600;
  }

  .total-amount {
    color: #667eea;
    font-weight: bold;
    font-size: 1.3rem;
  }
}

.receipt-number {
  flex-shrink: 0;
  text-align: center;
  padding: 0.75rem;
  background: #e8f5e9;
  border: 1px solid #4caf50;
  border-radius: 4px;
  color: #2e7d32;
  font-size: 0.95rem;
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
    background: white;
    border: 2px solid #1976d2;
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
        border: 2px solid #1976d2;
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
        border: 2px solid #1976d2;
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
          color: #667eea;
          font-weight: 600;
        }
      }
    }

    .btn-change {
      width: 100%;
      padding: 0.5rem;
      background: white;
      border: 1px solid #1976d2;
      color: #1976d2;
      border-radius: 4px;
      cursor: pointer;
      font-weight: 600;
      font-size: 0.85rem;
      transition: all 0.2s;
      margin-bottom: 0.75rem;

      &:hover {
        background: #e3f2fd;
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
  background-color: #2196f3;
  color: white;

  &:not(:disabled):hover {
    background-color: #0b7dda;
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

.member-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
  max-height: 350px;
  overflow-y: auto;
}

.member-item {
  background: white;
  border: 2px solid #ddd;
  padding: 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  display: grid;
  grid-template-columns: 60px 1fr;
  gap: 0.75rem;
  align-items: center;
  text-align: left;

  &:hover {
    background: #f0f0f0;
    border-color: #1976d2;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .member-photo {
    width: 60px;
    height: 60px;
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

  .member-info-box {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;

    .member-name-modal {
      font-weight: 600;
      color: #333;
    }

    .balance {
      font-size: 0.85rem;
      color: #666;
    }
  }

  .balance {
    color: #667eea;
    font-weight: 600;
  }
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #999;
}
</style>
