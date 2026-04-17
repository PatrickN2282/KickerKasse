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
    </div>

    <!-- CREATE TAB -->
    <div v-if="activeSubTab === 'create'" class="create-section">
      <div class="form-grid">
        <!-- GIFT Voucher Form -->
        <div class="form-card">
          <h3>🎁 Geschenk-Gutschein</h3>
          <p class="form-description">Kostenlos erstellt, wird bei Einlösung als Verlust verbucht</p>

          <form @submit.prevent="createGiftVoucher">
            <div class="form-group">
              <label>Wert (€)</label>
              <input
                type="number"
                min="0.01"
                step="0.01"
                placeholder="z.B. 10.00"
                v-model="giftForm.valueDisplay"
                @input="handleGiftValueInput"
                @blur="formatGiftValue"
                required
              />
            </div>

            <div class="form-group">
              <label>Grund</label>
              <select v-model="giftForm.reason" required>
                <option value="DYP_SIEGER">Dyp-Sieger</option>
                <option value="PROMOTION">Promotion</option>
              </select>
            </div>

            <button type="submit" class="btn-primary" :disabled="creatingGift">
              {{ creatingGift ? '⏳ Wird erstellt...' : '✓ Erstellen' }}
            </button>
          </form>

          <div v-if="createdGiftVoucher" class="success-message">
            <p>✅ Gutschein erstellt!</p>
            <p class="voucher-number">{{ getVoucherCode(createdGiftVoucher) }}</p>
            <button @click="copyToClipboard(getVoucherCode(createdGiftVoucher))" class="btn-secondary">
              📋 Kopieren
            </button>
          </div>
        </div>

        <!-- PREPAID Voucher Form -->
        <div class="form-card">
          <h3>💳 Guthaben-Gutschein</h3>
          <p class="form-description">Sofort bezahlt, wird später - eingelöst</p>

          <form @submit.prevent="createPrepaidVoucher">
            <div class="form-group">
              <label>Wert (€)</label>
              <input
                type="number"
                min="0.01"
                step="0.01"
                placeholder="z.B. 20.00"
                v-model="prepaidForm.valueDisplay"
                @input="handlePrepaidValueInput"
                @blur="formatPrepaidValue"
                required
              />
            </div>

            <button type="submit" class="btn-primary" :disabled="creatingPrepaid">
              {{ creatingPrepaid ? '⏳ Wird erstellt...' : '✓ Erstellen' }}
            </button>
          </form>

          <div v-if="createdPrepaidVoucher" class="success-message">
            <p>✅ Gutschein erstellt!</p>
            <p class="voucher-number">{{ getVoucherCode(createdPrepaidVoucher) }}</p>
            <button @click="copyToClipboard(getVoucherCode(createdPrepaidVoucher))" class="btn-secondary">
              📋 Kopieren
            </button>
          </div>
        </div>
      </div>

      <!-- Error messages -->
      <div v-if="createError" class="error-message">
        ❌ {{ createError }}
      </div>
    </div>

    <!-- MANAGE TAB -->
    <div v-if="activeSubTab === 'manage'" class="manage-section">
      <!-- Filters -->
      <div class="filter-section">
        <div class="filter-group">
          <label>Typ</label>
          <select v-model="filters.type">
            <option value="">Alle</option>
            <option value="GIFT">🎁 Geschenk</option>
            <option value="PREPAID">💳 Guthaben</option>
          </select>
        </div>

        <div class="filter-group">
          <label>Status</label>
          <select v-model="filters.status">
            <option value="">Alle</option>
            <option value="CREATED">Erstellt</option>
            <option value="REDEEMED">Eingelöst</option>
          </select>
        </div>

        <button @click="applyFilters" class="btn-secondary">
          🔍 Filtern
        </button>

        <button @click="exportAsCSV" class="btn-secondary">
          📥 CSV Export
        </button>
      </div>

      <!-- Vouchers Table -->
      <div class="table-container">
        <table v-if="filteredVouchers.length > 0" class="vouchers-table">
          <thead>
            <tr>
              <th>Nummer</th>
              <th>Typ</th>
              <th>Wert</th>
              <th>Status</th>
              <th>Grund</th>
              <th>Erstellt</th>
              <th>Eingelöst</th>
              <th>Aktionen</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="voucher in filteredVouchers" :key="voucher.id">
              <td class="voucher-number">{{ getVoucherCode(voucher) }}</td>
              <td>
                <span :class="['type-badge', voucher.voucher_type.toLowerCase()]">
                  {{ voucher.voucher_type === 'GIFT' ? '🎁 Geschenk' : '💳 Guthaben' }}
                </span>
              </td>
              <td class="currency">{{ (voucher.value_cents / 100).toFixed(2) }}€</td>
              <td>
                <span :class="['status-badge', voucher.status.toLowerCase()]">
                  {{ voucher.status === 'CREATED' ? '✅ Erstellt' : '✓ Eingelöst' }}
                </span>
              </td>
              <td>{{ formatReason(voucher.reason) }}</td>
              <td class="date">{{ formatDate(voucher.created_at) }}</td>
              <td class="date">{{ voucher.redeemed_at ? formatDate(voucher.redeemed_at) : '-' }}</td>
              <td class="actions">
                <button
                  v-if="voucher.status === 'CREATED'"
                  @click="openEditVoucher(voucher)"
                  class="btn-small btn-edit"
                >
                  ✏️
                </button>
                <button @click="copyToClipboard(getVoucherCode(voucher))" class="btn-small">
                  📋
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-else class="no-data">
          Keine Gutscheine gefunden
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="pagination">
        <button
          @click="currentPage--"
          :disabled="currentPage === 1"
          class="btn-secondary"
        >
          ◀ Zurück
        </button>
        <span>Seite {{ currentPage }} von {{ totalPages }}</span>
        <button
          @click="currentPage++"
          :disabled="currentPage === totalPages"
          class="btn-secondary"
        >
          Weiter ▶
        </button>
      </div>
    </div>

    <div v-if="showEditModal" class="modal-overlay">
      <div class="modal-card">
        <h3>🎫 Gutschein bearbeiten</h3>
        <div class="form-group">
          <label>Wert (€)</label>
          <input v-model="editForm.valueDisplay" type="number" min="0.01" step="0.01" />
        </div>
        <div v-if="editingVoucher?.voucher_type === 'GIFT'" class="form-group">
          <label>Grund</label>
          <select v-model="editForm.reason">
            <option value="DYP_SIEGER">Dyp-Sieger</option>
            <option value="PROMOTION">Promotion</option>
          </select>
        </div>
        <div class="form-group">
          <label>Beschreibung</label>
          <input v-model="editForm.description" type="text" maxlength="255" />
        </div>
        <div v-if="editError" class="error-message">
          ❌ {{ editError }}
        </div>
        <div class="button-row">
          <button @click="saveVoucherEdit" class="btn-primary" :disabled="updatingVoucher">
            {{ updatingVoucher ? '⏳ Speichert...' : '✓ Speichern' }}
          </button>
          <button @click="closeEditVoucher" class="btn-secondary">
            Abbrechen
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import apiService from '@/services/api'

// Active sub-tab
const activeSubTab = ref('create')

// Form data
const giftForm = ref({
  valueCents: 1000, // 10€ default
  reason: 'PROMOTION',
  valueDisplay: '10.00',
})

const prepaidForm = ref({
  valueCents: 2000, // 20€ default
  valueDisplay: '20.00',
})

const reasonLabels = {
  DYP_SIEGER: 'Dyp-Sieger',
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
const createdPrepaidVoucher = ref(null)
const createError = ref(null)
const showEditModal = ref(false)
const editingVoucher = ref(null)
const updatingVoucher = ref(false)
const editError = ref(null)
const editForm = ref({
  valueDisplay: '',
  reason: 'PROMOTION',
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

// Methods
const createGiftVoucher = async () => {
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
    })
    const payload = response.data
    console.log('[Vouchers] Create GIFT response received:')
    console.log('[Vouchers]   Full response:', JSON.stringify(response, null, 2))
    console.log('[Vouchers]   response.id:', payload?.id)
    console.log('[Vouchers]   response.voucher_code:', payload?.voucher_code)
    console.log('[Vouchers]   response.voucher_type:', payload?.voucher_type)
    console.log('[Vouchers]   response.status:', payload?.status)
    
    createdGiftVoucher.value = payload
    giftForm.value = { valueCents: 1000, reason: 'PROMOTION', valueDisplay: '10.00' }
    // Always refresh list after creating a voucher
    console.log('[Vouchers] Refreshing voucher list...')
    await loadVouchers()
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
  creatingPrepaid.value = true
  createError.value = null
  createdPrepaidVoucher.value = null

  try {
    const response = await apiService.post('/admin/vouchers/prepaid/', {
      value_cents: prepaidForm.value.valueCents,
    })
    const payload = response.data
    console.log('[Vouchers] Create PREPAID response:', JSON.stringify(payload, null, 2))
    createdPrepaidVoucher.value = payload
    prepaidForm.value = { valueCents: 2000, valueDisplay: '20.00' }
    // Always refresh list after creating a voucher
    await loadVouchers()
  } catch (error) {
    console.error('[Vouchers] Error creating PREPAID voucher:', error)
    createError.value = error.response?.data?.detail || error.message || 'Fehler beim Erstellen'
  } finally {
    creatingPrepaid.value = false
  }
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

const applyFilters = () => {
  currentPage.value = 1
  loadVouchers()
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('de-DE')
}

const formatReason = (reason) => {
  if (!reason) return '-'
  return reasonLabels[reason] || reason
}

const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text)
  // Could add a toast notification here
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

  const headers = ['Nummer', 'Typ', 'Wert (€)', 'Status', 'Grund', 'Erstellt', 'Eingelöst']
  const rows = vouchers.value.map((v) => [
    getVoucherCode(v),
    v.voucher_type,
    (v.value_cents / 100).toFixed(2),
    v.status,
    formatReason(v.reason),
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
  }
})

// Lifecycle
onMounted(() => {
  // Don't load initially, load when manage tab is clicked
})
</script>

<style scoped lang="scss">
.vouchers-container {
  padding: 2rem;
  background: #cfd3d8;
  min-height: 100%;

  h2 {
    color: #333;
    margin-bottom: 1.5rem;
  }
}

.voucher-subtabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  border-bottom: 2px solid #aeb5be;
}

.subtab-button {
  padding: 0.75rem 1.25rem;
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  color: #666;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    color: #0275d8;
  }

  &.active {
    color: #0275d8;
    border-bottom-color: #0275d8;
  }
}

.create-section {
  animation: fadeIn 0.2s;
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
    border-radius: 4px;
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
      background: #d1ecf1;
      color: #0c5460;
    }

    &.redeemed {
      background: #d4edda;
      color: #155724;
    }
  }

  .currency {
    font-weight: 500;
  }

  .date {
    color: #666;
    font-size: 0.9rem;
  }

  .actions {
    white-space: nowrap;
  }
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
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s;

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.btn-primary {
  width: 100%;
  background: #0275d8;
  color: white;
  font-weight: 500;

  &:hover:not(:disabled) {
    background: #025aa5;
  }
}

.btn-secondary {
  background: #6c757d;
  color: white;

  &:hover:not(:disabled) {
    background: #5a6268;
  }
}

.btn-small {
  padding: 0.25rem 0.5rem;
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

.actions {
  display: flex;
  gap: 0.35rem;
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

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
