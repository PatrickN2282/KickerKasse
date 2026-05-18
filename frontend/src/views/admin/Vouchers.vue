<template>
  <div class="vouchers-container">
    <h2>🎫 Gutscheine Verwaltung</h2>

    <!-- Sub-tabs -->
    <div class="voucher-subtabs">
      <button
        :class="['subtab-button', { active: activeSubTab === 'create' }]"
        @click="activeSubTab = 'create'"
      >
        ➕ Erstellen
      </button>
      <button
        :class="['subtab-button', { active: activeSubTab === 'manage' }]"
        @click="activeSubTab = 'manage'"
      >
        📋 Verwaltung
      </button>
      <button
        v-if="authStore.isAdmin"
        :class="['subtab-button', { active: activeSubTab === 'club-account' }]"
        @click="activeSubTab = 'club-account'; loadClubAccount()"
      >
        🏦 Gutscheinkonto
      </button>
    </div>

    <!-- CREATE TAB -->
    <div
      v-if="activeSubTab === 'create'"
      class="create-section"
    >
      <div class="form-grid">
        <!-- GIFT Voucher Form -->
        <div class="form-card">
          <h3>🎁 Gutschein</h3>
          <p class="form-description">
            Kostenlos erstellt, wird bei Einlösung als Verlust verbucht
          </p>
          <p class="form-help">
            Gutscheinwert eintragen und danach die Zugangsdaten bestätigen.
          </p>
          <p
            v-if="authStore.isAdmin"
            class="info-text"
          >
            Gutscheinkonto: {{ formatCurrency(clubAccount.balance_cents) }}
          </p>

          <form @submit.prevent="createGiftVoucher">
            <div class="form-group">
              <label>Wert (€)</label>
              <input
                v-model="giftForm.valueDisplay"
                type="number"
                min="0.01"
                step="0.01"
                placeholder="z.B. 10.00"
                required
                @input="handleGiftValueInput"
                @blur="formatGiftValue"
              >
            </div>

            <div class="form-group">
              <label>Grund</label>
              <select
                v-model="giftForm.reason"
                required
              >
                <option value="DYP_SIEGER">
                  DYP-Sieger
                </option>
                <option value="PROMOTION">
                  Promotion
                </option>
              </select>
            </div>

            <button
              type="submit"
              class="btn-primary"
              :disabled="creatingGift"
            >
              {{ creatingGift ? '⏳ Wird erstellt...' : '✓ Erstellen' }}
            </button>
          </form>

        </div>

        <!-- PREPAID Voucher Form -->
        <div
          v-if="authStore.isAdmin"
          class="form-card"
        >
          <h3>💳 Verzehrkarte</h3>
          <p class="form-description">
            Wird vorbereitet und später in der Kasse verkauft
          </p>
          <p class="form-help">
            Standardwert ist 10,00 €. Für abweichende Werte wird automatisch ein weiterer Produktartikel angelegt.
          </p>

          <form @submit.prevent="createPrepaidVoucher">
            <div class="form-group">
              <label>Wert (€)</label>
              <input
                v-model="prepaidForm.valueDisplay"
                type="number"
                min="0.01"
                step="0.01"
                placeholder="z.B. 10.00"
                required
                @input="handlePrepaidValueInput"
                @blur="formatPrepaidValue"
              >
            </div>

            <div class="form-group">
              <label>Anzahl</label>
              <input
                v-model.number="prepaidForm.quantity"
                type="number"
                min="1"
                step="1"
                required
              >
            </div>

            <button
              type="submit"
              class="btn-primary"
              :disabled="creatingPrepaid"
            >
              {{ creatingPrepaid ? '⏳ Wird erstellt...' : '✓ Erstellen' }}
            </button>
          </form>

        </div>
        <div
          v-else
          class="form-card"
        >
          <h3>💳 Verzehrkarte</h3>
          <p class="form-description">
            Nur Admin oder TopAdmin dürfen Verzehrkarten erstellen.
          </p>
        </div>
      </div>

      <!-- Error messages -->
      <div
        v-if="createError"
        class="error-message"
      >
        ❌ {{ createError }}
      </div>
    </div>

    <!-- MANAGE TAB -->
    <div
      v-if="activeSubTab === 'manage'"
      class="manage-section"
    >
      <!-- Filters -->
      <div class="filter-section">
        <div class="filter-group">
          <label>Typ</label>
          <select v-model="filters.type">
            <option value="">
              Alle
            </option>
            <option value="GIFT">
              🎁 Gutschein
            </option>
            <option value="PREPAID">
              💳 Verzehrkarte
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>Status</label>
          <select v-model="filters.status">
            <option value="">
              Alle
            </option>
            <option value="CREATED">
              Erstellt / Aktiviert
            </option>
            <option value="PARTIALLY_REDEEMED">
              Teilweise eingelöst
            </option>
            <option value="REDEEMED">
              Verbraucht
            </option>
          </select>
        </div>

        <button
          class="btn-secondary"
          @click="applyFilters"
        >
          🔍 Filtern
        </button>

        <button
          class="btn-secondary"
          @click="exportAsCSV"
        >
          📥 CSV Export
        </button>
      </div>

      <!-- Vouchers Table -->
      <div class="table-container">
        <table
          v-if="filteredVouchers.length > 0"
          class="vouchers-table"
        >
          <thead>
            <tr>
              <th>Nummer</th>
              <th>Typ</th>
              <th>Wert</th>
              <th>Status</th>
              <th>Grund</th>
              <th>Erstellt von</th>
              <th>Erstellt</th>
              <th>Eingelöst</th>
              <th class="text-right">Aktionen</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="voucher in filteredVouchers"
              :key="voucher.id"
            >
              <td class="voucher-number">
                {{ getVoucherCode(voucher) }}
              </td>
              <td>
                <span :class="['type-badge', voucher.voucher_type.toLowerCase()]">
                  {{ voucher.voucher_type === 'GIFT' ? '🎁 Gutschein' : '💳 Verzehrkarte' }}
                </span>
              </td>
              <td class="currency">
                <div>{{ (voucher.original_value_cents / 100).toFixed(2) }}€</div>
                <small v-if="voucher.remaining_value_cents !== voucher.original_value_cents">
                  Rest: {{ (voucher.remaining_value_cents / 100).toFixed(2) }}€
                </small>
              </td>
              <td>
                <span :class="['status-badge', getVoucherStatusPresentation(voucher).className]">
                  {{ getVoucherStatusPresentation(voucher).label }}
                </span>
              </td>
              <td>{{ formatReason(voucher.reason) }}</td>
              <td>{{ formatVoucherCreator(voucher) }}</td>
              <td class="date">
                {{ formatDate(voucher.created_at) }}
              </td>
              <td class="date">
                {{ voucher.redeemed_at ? formatDate(voucher.redeemed_at) : '-' }}
              </td>
              <td class="text-right">
                <div class="action-cell">
                  <button
                    v-if="authStore.isAdmin && voucher.status === 'CREATED'"
                    class="btn-small btn-edit"
                    @click="openEditVoucher(voucher)"
                  >
                    ✏️
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div
          v-else
          class="no-data"
        >
          Keine Gutscheine gefunden
        </div>
      </div>

      <!-- Pagination -->
      <div
        v-if="totalPages > 1"
        class="pagination"
      >
        <button
          :disabled="currentPage === 1"
          class="btn-secondary"
          @click="currentPage--"
        >
          ◀ Zurück
        </button>
        <span>Seite {{ currentPage }} von {{ totalPages }}</span>
        <button
          :disabled="currentPage === totalPages"
          class="btn-secondary"
          @click="currentPage++"
        >
          Weiter ▶
        </button>
      </div>
    </div>

    <div
      v-if="activeSubTab === 'club-account' && authStore.isAdmin"
      class="manage-section"
    >
      <div class="summary-grid">
        <div class="form-card">
          <h3>Kontostand</h3>
          <p class="voucher-number">
            {{ formatCurrency(clubAccount.balance_cents) }}
          </p>
        </div>
        <div class="form-card">
          <h3>Konto aufladen</h3>
          <div class="form-group">
            <label>Betrag (€)</label>
            <input
              v-model="clubAccountTopUp"
              type="number"
              min="0.01"
              step="0.01"
            >
          </div>
          <button
            class="btn-primary"
            @click="requestClubAccountTopUp"
          >
            Nur im Gutscheinkonto buchen
          </button>
        </div>
      </div>
      <div class="table-container">
        <table
          v-if="clubAccount.entries.length"
          class="vouchers-table"
        >
          <thead>
            <tr>
              <th>Datum</th>
              <th>Betrag</th>
              <th>Grund</th>
              <th>Benutzer</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="entry in clubAccount.entries"
              :key="entry.id"
            >
              <td>{{ formatDate(entry.created_at) }}</td>
              <td>{{ formatCurrency(entry.amount_cents) }}</td>
              <td>{{ entry.reason }}</td>
              <td>{{ entry.user_name || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div
      v-if="showEditModal"
      class="modal-overlay"
    >
      <div class="modal-card">
        <h3>🎫 Gutschein bearbeiten</h3>
        <div class="form-group">
          <label>Wert (€)</label>
          <input
            v-model="editForm.valueDisplay"
            type="number"
            min="0.01"
            step="0.01"
          >
        </div>
        <div
          v-if="editingVoucher?.voucher_type === 'GIFT'"
          class="form-group"
        >
          <label>Grund</label>
          <select v-model="editForm.reason">
            <option value="DYP_SIEGER">
              DYP-Sieger
            </option>
            <option value="PROMOTION">
              Promotion
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>Beschreibung</label>
          <input
            v-model="editForm.description"
            type="text"
            maxlength="255"
          >
        </div>
        <div
          v-if="editError"
          class="error-message"
        >
          ❌ {{ editError }}
        </div>
        <div class="button-row">
          <button
            class="btn-primary"
            :disabled="updatingVoucher"
            @click="saveVoucherEdit"
          >
            {{ updatingVoucher ? '⏳ Speichert...' : '✓ Speichern' }}
          </button>
          <button
            class="btn-secondary"
            @click="closeEditVoucher"
          >
            Abbrechen / Zurück
          </button>
        </div>
      </div>
    </div>
    <div
      v-if="showCreatedVoucherModal && createdVoucherModalData"
      class="modal-overlay"
    >
      <div class="modal-card created-voucher-modal">
        <h3>{{ createdVoucherModalData.title }}</h3>
        <p class="info-text">
          {{ createdVoucherModalData.subtitle }}
        </p>
        <div class="created-voucher-box">
          <div
            v-for="voucherNumber in createdVoucherModalData.numbers"
            :key="voucherNumber"
            class="created-voucher-number"
          >
            {{ voucherNumber }}
          </div>
        </div>
        <div class="created-voucher-alert">
          <p class="created-voucher-note">
            {{ createdVoucherModalData.note }}
          </p>
        </div>
        <div class="button-row created-voucher-actions">
          <button
            v-if="createdVoucherModalData.showClubAccountButton"
            class="btn-secondary"
            @click="openClubAccountFromModal"
          >
            🏦 Gutscheinkonto öffnen
          </button>
          <button
            class="btn-secondary"
            @click="closeCreatedVoucherModal"
          >
            Schließen
          </button>
        </div>
      </div>
    </div>
    <CredentialConfirmModal
      :show="showPasswordModal"
      :title="passwordModalTitle"
      message="Optional können hier die Zugangsdaten des Top-Admin zur Freigabe verwendet werden."
      :username="authStore.user?.username || ''"
      allow-username-edit
      confirm-label="Bestätigen"
      @close="showPasswordModal = false"
      @confirm="handlePasswordConfirmed"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import apiService from '@/services/api'
import CredentialConfirmModal from '@/components/CredentialConfirmModal.vue'

// Active sub-tab
const activeSubTab = ref('create')
const authStore = useAuthStore()

// Form data
const giftForm = ref({
  valueCents: 500,
  reason: 'DYP_SIEGER',
  valueDisplay: '5.00',
})

const prepaidForm = ref({
  valueCents: 1000,
  valueDisplay: '10.00',
  quantity: 1,
})

const reasonLabels = {
  DYP_SIEGER: 'DYP-Sieger',
  PROMOTION: 'Promotion',
}

// Handle value input changes
const syncVoucherValue = (form) => {
  const euroValue = parseFloat(form.valueDisplay)

  if (Number.isNaN(euroValue) || euroValue <= 0) {
    form.valueCents = 0
    return
  }

  form.valueCents = Math.round(euroValue * 100)
}

const formatVoucherValue = (form) => {
  if (!form.valueDisplay) {
    form.valueCents = 0
    return
  }

  const euroValue = parseFloat(form.valueDisplay)
  if (Number.isNaN(euroValue) || euroValue <= 0) {
    form.valueCents = 0
    form.valueDisplay = ''
    return
  }

  form.valueCents = Math.round(euroValue * 100)
  form.valueDisplay = euroValue.toFixed(2)
}

const handleGiftValueInput = () => {
  syncVoucherValue(giftForm.value)
}

const handlePrepaidValueInput = () => {
  syncVoucherValue(prepaidForm.value)
}

const formatGiftValue = () => {
  formatVoucherValue(giftForm.value)
}

const formatPrepaidValue = () => {
  formatVoucherValue(prepaidForm.value)
}

// States
const creatingGift = ref(false)
const creatingPrepaid = ref(false)
const createdGiftVoucher = ref(null)
const createdPrepaidBatch = ref(null)
const showCreatedVoucherModal = ref(false)
const createError = ref(null)
const showPasswordModal = ref(false)
const pendingVoucherAction = ref(null)
const clubAccount = ref({ balance_cents: 0, entries: [] })
const clubAccountTopUp = ref('')
const showEditModal = ref(false)
const editingVoucher = ref(null)
const updatingVoucher = ref(false)
const editError = ref(null)
const editForm = ref({
  valueDisplay: '',
  reason: 'DYP_SIEGER',
  description: '',
})

// Manage section
const vouchers = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const totalVouchers = ref(0)

const filters = ref({
  type: '',
  status: '',
})

const getVoucherCode = (voucher) => {
  if (!voucher) return '-'
  if (voucher.voucher_code && String(voucher.voucher_code).trim()) return voucher.voucher_code
  if (voucher.voucher_number === undefined || voucher.voucher_number === null) return '-'

  const year = voucher.created_at
    ? new Date(voucher.created_at).getFullYear()
    : new Date().getFullYear()
  return `V-${year}-${String(voucher.voucher_number).padStart(3, '0')}`
}

const createdVoucherModalData = computed(() => {
  if (createdPrepaidBatch.value?.vouchers?.length) {
    const numbers = createdPrepaidBatch.value.vouchers.map(getVoucherCode)
    return {
      title: '💳 Verzehrkarten erstellt',
      subtitle: createdPrepaidBatch.value.product_name || 'Die folgenden Verzehrkarten wurden angelegt.',
      numbers,
      note: 'Nummer auf der Verzehrkarte notieren - Einlösung ohne Nummer nicht möglich',
      showClubAccountButton: false,
    }
  }

  if (createdGiftVoucher.value) {
    const voucherNumber = getVoucherCode(createdGiftVoucher.value)
    return {
      title: '🎁 Gutschein erstellt',
      subtitle: 'Der Gutschein wurde erfolgreich angelegt.',
      numbers: [voucherNumber],
      note: 'Nummer auf dem Gutschein notieren - Einlösung ohne Nummer nicht möglich',
      showClubAccountButton: authStore.isAdmin,
    }
  }

  return null
})

// Methods
const passwordModalTitle = computed(() => pendingVoucherAction.value === 'gift'
  ? 'Gutschein erstellen'
  : pendingVoucherAction.value === 'account'
    ? 'Gutscheinkonto aufladen'
    : 'Verzehrkarte erstellen')

const createGiftVoucher = async () => {
  pendingVoucherAction.value = 'gift'
  showPasswordModal.value = true
}

const submitGiftVoucher = async ({ username, password }) => {
  creatingGift.value = true
  createError.value = null
  createdGiftVoucher.value = null

  try {
    console.log('[Vouchers] Creating GIFT voucher with:', {
      value_cents: giftForm.value.valueCents,
      reason: giftForm.value.reason,
    })
    const response = await apiService.post('/admin/vouchers/gift/', {
      value_cents: giftForm.value.valueCents,
      reason: giftForm.value.reason,
      auth_username: username,
      auth_password: password,
    })
    const payload = response.data
    console.log('[Vouchers] Create GIFT response received:')
    console.log('[Vouchers]   Full response:', JSON.stringify(response, null, 2))
    console.log('[Vouchers]   response.id:', payload?.id)
    console.log('[Vouchers]   response.voucher_code:', payload?.voucher_code)
    console.log('[Vouchers]   response.voucher_type:', payload?.voucher_type)
    console.log('[Vouchers]   response.status:', payload?.status)
    
    createdGiftVoucher.value = payload
    showCreatedVoucherModal.value = true
    giftForm.value = { valueCents: 500, reason: 'DYP_SIEGER', valueDisplay: '5.00' }
    await loadClubAccount()
  } catch (error) {
    console.error('[Vouchers] Error creating GIFT voucher:', error)
    console.error('[Vouchers]   Status:', error?.response?.status)
    console.error('[Vouchers]   Message:', error?.response?.data?.detail || error.message)
    createError.value = error.response?.data?.detail || error.message || 'Fehler beim Erstellen'
  } finally {
    creatingGift.value = false
  }
}

const createPrepaidVoucher = async () => {
  pendingVoucherAction.value = 'prepaid'
  showPasswordModal.value = true
}

const submitPrepaidVoucher = async ({ username, password }) => {
  creatingPrepaid.value = true
  createError.value = null
  createdPrepaidBatch.value = null

  try {
    const response = await apiService.post('/admin/vouchers/prepaid/', {
      value_cents: prepaidForm.value.valueCents,
      quantity: prepaidForm.value.quantity,
      auth_username: username,
      auth_password: password,
    })
    const payload = response.data
    createdPrepaidBatch.value = payload
    showCreatedVoucherModal.value = true
    prepaidForm.value = { valueCents: 1000, valueDisplay: '10.00', quantity: 1 }
    await loadVouchers()
  } catch (error) {
    console.error('[Vouchers] Error creating PREPAID voucher:', error)
    createError.value = error.response?.data?.detail || error.message || 'Fehler beim Erstellen'
  } finally {
    creatingPrepaid.value = false
  }
}

const handlePasswordConfirmed = async (credentials) => {
  showPasswordModal.value = false
  if (pendingVoucherAction.value === 'gift') {
    await submitGiftVoucher(credentials)
  } else if (pendingVoucherAction.value === 'prepaid') {
    await submitPrepaidVoucher(credentials)
  } else if (pendingVoucherAction.value === 'account') {
    await apiService.post('/admin/vouchers/club-account/topup', {
      amount_cents: Math.round(Number(clubAccountTopUp.value) * 100),
      auth_username: credentials.username,
      auth_password: credentials.password,
    })
    clubAccountTopUp.value = ''
    await loadClubAccount()
  }
  pendingVoucherAction.value = null
}

const requestClubAccountTopUp = () => {
  if (!clubAccountTopUp.value || Number(clubAccountTopUp.value) <= 0) {
    return
  }
  pendingVoucherAction.value = 'account'
  showPasswordModal.value = true
}

const openClubAccountTab = async () => {
  activeSubTab.value = 'club-account'
  await loadClubAccount()
}

const closeCreatedVoucherModal = () => {
  showCreatedVoucherModal.value = false
  createdGiftVoucher.value = null
  createdPrepaidBatch.value = null
}

const openClubAccountFromModal = async () => {
  closeCreatedVoucherModal()
  await openClubAccountTab()
}

const loadVouchers = async () => {
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
    }

    if (filters.value.type) {
      params.type_filter = filters.value.type
    }
    if (filters.value.status) {
      params.status_filter = filters.value.status
    }

    console.log('[Vouchers] ======================================')
    console.log('[Vouchers] Loading vouchers with params:', params)
    const response = await apiService.get('/admin/vouchers/', { params })
    const payload = response.data
    console.log('[Vouchers] Raw API response:', payload)
    console.log('[Vouchers] Response type:', typeof payload)
    console.log('[Vouchers] Response keys:', Object.keys(payload || {}))
    
    // Try multiple possible response structures
    let loadedVouchers = []
    let loadedTotal = 0
    
    if (payload && payload.vouchers && Array.isArray(payload.vouchers)) {
      loadedVouchers = payload.vouchers
      loadedTotal = payload.total || 0
      console.log('[Vouchers] ✓ Found payload.vouchers (array)', loadedVouchers.length)
    } else if (Array.isArray(payload)) {
      loadedVouchers = payload
      loadedTotal = payload.length
      console.log('[Vouchers] ✓ Payload is array directly', loadedVouchers.length)
    } else {
      console.warn('[Vouchers] ⚠️  Could not find vouchers in response')
      console.log('[Vouchers] Full response object:', JSON.stringify(payload, null, 2))
    }
    
    vouchers.value = loadedVouchers
    totalVouchers.value = loadedTotal
    console.log('[Vouchers] Updated state: vouchers.length =', vouchers.value.length, 'total =', totalVouchers.value)
    
    // Log first voucher with all details
    if (loadedVouchers.length > 0) {
      console.log('[Vouchers] First voucher (full object):')
      console.log('[Vouchers]   id:', loadedVouchers[0].id)
      console.log('[Vouchers]   voucher_code:', loadedVouchers[0].voucher_code)
      console.log('[Vouchers]   voucher_type:', loadedVouchers[0].voucher_type)
      console.log('[Vouchers]   value_cents:', loadedVouchers[0].value_cents)
      console.log('[Vouchers]   status:', loadedVouchers[0].status)
      console.log('[Vouchers]   Full JSON:', JSON.stringify(loadedVouchers[0], null, 2))
    } else {
      console.warn('[Vouchers] No vouchers in response (empty array)')
    }
    console.log('[Vouchers] ======================================')
  } catch (error) {
    console.error('[Vouchers] ❌ Error loading vouchers:', error)
    console.error('[Vouchers] Error message:', error.message)
    console.error('[Vouchers] Error status:', error.response?.status)
    console.error('[Vouchers] Error details:', error.response?.data)
    console.error('[Vouchers] Full error object:', error)
  }
}

const loadClubAccount = async () => {
  if (!authStore.isAdmin) return
  const response = await apiService.get('/admin/vouchers/club-account')
  clubAccount.value = response.data
}

const applyFilters = () => {
  currentPage.value = 1
  loadVouchers()
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('de-DE')
}

const formatCurrency = (amountCents) => `${(amountCents / 100).toFixed(2)}€`

const formatReason = (reason) => {
  if (!reason) return '-'
  return reasonLabels[reason] || reason
}

const getVoucherStatusPresentation = (voucher) => {
  if (voucher.voucher_type === 'PREPAID' && !voucher.sold_at) {
    return { key: 'CREATED', label: '🟣 Erstellt', className: 'created' }
  }
  if (voucher.status === 'CREATED') {
    return { key: 'ACTIVATED', label: '🔵 Aktiviert', className: 'activated' }
  }
  if (voucher.status === 'PARTIALLY_REDEEMED') {
    return { key: 'PARTIALLY_REDEEMED', label: '🟡 Teilweise eingelöst', className: 'partially-redeemed' }
  }
  if (voucher.status === 'REDEEMED') {
    return { key: 'REDEEMED', label: '⚫ Verbraucht', className: 'redeemed' }
  }
  return { key: voucher.status, label: `⚪ ${voucher.status}`, className: 'unknown' }
}

const formatVoucherCreator = (voucher) => {
  return voucher.created_by_username || `#${voucher.created_by_user_id}`
}

const openEditVoucher = (voucher) => {
  editingVoucher.value = voucher
  editForm.value = {
    valueDisplay: (voucher.value_cents / 100).toFixed(2),
    reason: voucher.reason || 'PROMOTION',
    description: voucher.description || '',
  }
  editError.value = null
  showEditModal.value = true
}

const closeEditVoucher = () => {
  showEditModal.value = false
  editingVoucher.value = null
  editError.value = null
}

const saveVoucherEdit = async () => {
  if (!editingVoucher.value) return

  updatingVoucher.value = true
  editError.value = null

  try {
    const response = await apiService.put(`/admin/vouchers/${editingVoucher.value.id}`, {
      value_cents: Math.round(parseFloat(editForm.value.valueDisplay || '0') * 100),
      reason: editingVoucher.value.voucher_type === 'GIFT' ? editForm.value.reason : null,
      description: editForm.value.description || null,
    })

    const updatedVoucher = response.data
    const index = vouchers.value.findIndex(voucher => voucher.id === updatedVoucher.id)
    if (index !== -1) {
      vouchers.value[index] = updatedVoucher
    }

    closeEditVoucher()
  } catch (error) {
    editError.value = error.response?.data?.detail || error.message || 'Fehler beim Speichern'
  } finally {
    updatingVoucher.value = false
  }
}

const exportAsCSV = () => {
  if (vouchers.value.length === 0) return

  const headers = ['Nummer', 'Typ', 'Wert (€)', 'Status', 'Grund', 'Erstellt von', 'Erstellt', 'Eingelöst']
  const rows = vouchers.value.map((v) => [
    getVoucherCode(v),
    v.voucher_type,
    (v.value_cents / 100).toFixed(2),
    v.status,
    formatReason(v.reason),
    formatVoucherCreator(v),
    formatDate(v.created_at),
    v.redeemed_at ? formatDate(v.redeemed_at) : '',
  ])

  const csvContent = [
    headers.join(','),
    ...rows.map((r) => r.map((cell) => `"${cell}"`).join(',')),
  ].join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `Gutscheine-${new Date().toISOString().split('T')[0]}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// Computed
const filteredVouchers = computed(() => vouchers.value)
const totalPages = computed(() => Math.ceil(totalVouchers.value / pageSize.value))

// Watchers
import { watch } from 'vue'

watch(currentPage, () => {
  loadVouchers()
})

watch(() => activeSubTab.value, (newTab) => {
  if (newTab === 'manage') {
    loadVouchers()
  } else if (newTab === 'club-account') {
    loadClubAccount()
  }
})

// Lifecycle
onMounted(() => {
  if (authStore.isAdmin) {
    loadClubAccount()
  }
})
</script>

<style scoped lang="scss">
.vouchers-container {
  padding: 1.25rem;
  background: #cfd3d8;
  min-height: 100%;

  h2 {
    color: #333;
    margin-bottom: 1rem;
  }
}

.voucher-subtabs {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  padding: 0.35rem 0 0.7rem;
  border-bottom: 1px solid #aeb5be;
  background: #cfd3d8;
}

.subtab-button {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 0.9rem;
  background: color-mix(in srgb, var(--app-banner-color) 14%, white);
  border: 1px solid color-mix(in srgb, var(--app-banner-color) 70%, #000 25%);
  border-radius: 8px;
  color: #334155;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: var(--app-highlight-color);
    border-color: var(--app-highlight-color);
    color: var(--app-highlight-contrast);
  }

  &.active {
    background: var(--app-highlight-color);
    border-color: var(--app-highlight-color);
    color: var(--app-highlight-contrast);
  }
}

.create-section {
  animation: fadeIn 0.2s;
}

@media (max-width: 700px) {
  .vouchers-container {
    padding: 1rem;
  }
}

.manage-section {
  animation: fadeIn 0.2s;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
}

.form-card {
  border: 1px solid #9ca4ae;
  border-radius: 8px;
  padding: 1.5rem;
  background: #dde2e8;

  h3 {
    color: #333;
    margin-bottom: 0.5rem;
  }

  .form-description {
    color: #666;
    font-size: 0.85rem;
    margin-bottom: 1.5rem;
  }

  .form-help {
    color: #555;
    font-size: 0.85rem;
    margin-bottom: 1rem;
  }
}

.form-group {
  margin-bottom: 1rem;

  label {
    display: block;
    color: #333;
    font-weight: 500;
    margin-bottom: 0.5rem;
  }

  input,
  select {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 1rem;

    &:focus {
      outline: none;
      border-color: #0275d8;
      box-shadow: 0 0 0 3px rgba(2, 117, 216, 0.1);
    }
  }

  .info-text {
    color: #666;
    font-size: 0.85rem;
    margin: 0;
  }
}

.success-message {
  background: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 4px;
  padding: 1rem;
  margin-top: 1.5rem;
  color: #155724;

  p {
    margin: 0.25rem 0;
  }

  .voucher-number {
    font-family: monospace;
    font-size: 1.1rem;
    font-weight: bold;
    color: #155724;
  }
}

.error-message {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  padding: 1rem;
  margin-top: 1rem;
  color: #721c24;
}

.filter-section {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  align-items: flex-end;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;

  label {
    color: #333;
    font-weight: 500;
    font-size: 0.9rem;
  }

  select {
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 0.9rem;
    min-width: 150px;
  }
}

.table-container {
  overflow-x: auto;
  border: 1px solid #9ca4ae;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.vouchers-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;

  thead {
    background: #d8dde3;
  }

  th,
  td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #ddd;
  }

  th {
    color: #333;
    font-weight: 600;
  }

  tr:hover {
    background: #dde2e8;
  }

  .voucher-number {
    font-family: monospace;
    font-weight: bold;
  }

  .type-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 500;

    &.gift {
      background: #fff3cd;
      color: #856404;
    }

    &.prepaid {
      background: #cfe2ff;
      color: #084298;
    }
  }

  .status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 500;

    &.created {
      background: #ede9fe;
      color: #6d28d9;
    }

    &.activated {
      background: #dbeafe;
      color: #1d4ed8;
    }

    &.redeemed {
      background: #e5e7eb;
      color: #374151;
    }

    &.partially-redeemed {
      background: #fff3cd;
      color: #856404;
    }

    &.unknown {
      background: #f3f4f6;
      color: #4b5563;
    }
  }

  .currency {
    font-weight: 500;

    small {
      display: block;
      margin-top: 0.15rem;
      color: #666;
      font-size: 0.8rem;
      font-weight: 400;
    }
  }

  .date {
    color: #666;
    font-size: 0.9rem;
  }

}

.text-right {
  text-align: right;
}

.no-data {
  padding: 2rem;
  text-align: center;
  color: #999;
  background: #f9f9f9;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;

  span {
    color: #666;
  }
}

.btn-primary,
.btn-secondary,
.btn-small {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: all 0.2s;

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.btn-primary {
  width: 100%;
  background: #0275d8;
  color: white;

  &:hover:not(:disabled) {
    background: #025aa5;
  }
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;

  &:hover:not(:disabled) {
    background: #e2e8f0;
  }
}

.btn-small {
  padding: 0.3rem 0.6rem;
  background: #0275d8;
  color: white;
  font-size: 0.8rem;

  &:hover {
    background: #025aa5;
  }
}

.btn-edit {
  background: #ff6b35;
}

.action-cell {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.35rem;
  flex-wrap: wrap;
  width: 100%;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(20, 24, 30, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  width: min(480px, calc(100vw - 2rem));
  background: #dde2e8;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 16px 40px rgba(15, 20, 28, 0.22);
}

.button-row {
  display: flex;
  gap: 0.75rem;
}

@media (max-width: 768px) {
  .action-cell {
    flex-direction: column;
  }

  .btn-small {
    width: 100%;
  }
}

.created-voucher-modal {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.created-voucher-box {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  border-radius: 10px;
  background: linear-gradient(135deg, #dcfce7, #bbf7d0);
  border: 1px solid #22c55e;
}

.created-voucher-number {
  font-family: monospace;
  font-size: 1.25rem;
  font-weight: 800;
  color: #166534;
  text-align: center;
}

.created-voucher-note {
  margin: 0;
  color: #991b1b;
  font-weight: 700;
}

.created-voucher-alert {
  padding: 0.9rem 1rem;
  border-radius: 10px;
  border: 2px solid #ef4444;
  background: linear-gradient(135deg, #fef2f2, #fee2e2);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.45) inset;
}

.created-voucher-actions {
  flex-wrap: wrap;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
