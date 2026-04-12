<template>
  <div class="kasse-container">
    <div class="kasse-products">
      <h2>Produkte</h2>
      <div v-if="productStore.isLoading" class="loading">Läuft...</div>
      <div v-else class="products-grid">
        <button
          v-for="product in productStore.products"
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

const loadNextReceiptNumber = async () => {
  try {
    const response = await apiService.get('/transactions/next-receipt-number')
    currentReceiptNumber.value = response.data.receipt_number
    console.log('[Kasse] Next receipt number loaded:', currentReceiptNumber.value)
  } catch (err) {
    console.error('[Kasse] Failed to load receipt number:', err)
  }
}

onMounted(() => {
  loadNextReceiptNumber()
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
  console.log('[Kasse] Initial members loaded:', memberStore.members.length)
})
</script>

<style scoped lang="scss">
.kasse-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  padding: 1rem;
  height: calc(100vh - 70px);
  background: #f5f5f5;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }
}

.kasse-products,
.kasse-bon {
  background: white;
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

.products-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
}

.product-btn {
  background: #f0f0f0;
  border: 2px solid #ddd;
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
    background: #e0e0e0;
    border-color: #1976d2;
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
    color: #667eea;
    font-size: 1.1rem;
    font-weight: bold;
  }

  .product-stock {
    font-size: 0.85rem;
    color: #666;
  }
}

.member-info {
  background: #e3f2fd;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;

  .member-name {
    font-weight: 600;
    color: #1976d2;
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
  background: #f5f5f5;
  padding: 0.8rem;
  border-bottom: 2px solid #ddd;
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
    }
  }
}

.bon-items {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #eee;
  border-radius: 4px;
  padding: 0.5rem;
  background: #fafafa;
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
