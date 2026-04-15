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
                v-model.number="giftForm.valueCents"
                type="number"
                min="0.01"
                step="0.01"
                placeholder="z.B. 10.00"
                :value="(giftForm.valueCents / 100).toFixed(2)"
                @input="giftForm.valueCents = Math.round($event.target.value * 100)"
                required
              />
            </div>

            <div class="form-group">
              <label>Grund</label>
              <select v-model="giftForm.reason" required>
                <option value="COURTESY">Kulanz</option>
                <option value="PROMOTIONAL">Aktion/Werbung</option>
                <option value="STAFF_BENEFIT">Mitarbeitervorteil</option>
                <option value="OTHER">Sonstig</option>
              </select>
            </div>

            <button type="submit" class="btn-primary" :disabled="creatingGift">
              {{ creatingGift ? '⏳ Wird erstellt...' : '✓ Erstellen' }}
            </button>
          </form>

          <div v-if="createdGiftVoucher" class="success-message">
            <p>✅ Gutschein erstellt!</p>
            <p class="voucher-number">{{ createdGiftVoucher.voucher_number }}</p>
            <button @click="copyToClipboard(createdGiftVoucher.voucher_number)" class="btn-secondary">
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
                v-model.number="prepaidForm.valueCents"
                type="number"
                min="0.01"
                step="0.01"
                placeholder="z.B. 20.00"
                :value="(prepaidForm.valueCents / 100).toFixed(2)"
                @input="prepaidForm.valueCents = Math.round($event.target.value * 100)"
                required
              />
            </div>

            <div class="form-group">
              <label>Höchster Preis</label>
              <p class="info-text">Der Gutschein wird zum angegebenen Wert verkauft</p>
            </div>

            <button type="submit" class="btn-primary" :disabled="creatingPrepaid">
              {{ creatingPrepaid ? '⏳ Wird erstellt...' : '✓ Erstellen' }}
            </button>
          </form>

          <div v-if="createdPrepaidVoucher" class="success-message">
            <p>✅ Gutschein erstellt!</p>
            <p class="voucher-number">{{ createdPrepaidVoucher.voucher_number }}</p>
            <button @click="copyToClipboard(createdPrepaidVoucher.voucher_number)" class="btn-secondary">
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
              <td class="voucher-number">{{ voucher.voucher_number }}</td>
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
              <td>{{ voucher.reason || '-' }}</td>
              <td class="date">{{ formatDate(voucher.created_at) }}</td>
              <td class="date">{{ voucher.redeemed_at ? formatDate(voucher.redeemed_at) : '-' }}</td>
              <td class="actions">
                <button @click="copyToClipboard(voucher.voucher_number)" class="btn-small">
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
  reason: 'COURTESY',
})

const prepaidForm = ref({
  valueCents: 2000, // 20€ default
})

// States
const creatingGift = ref(false)
const creatingPrepaid = ref(false)
const createdGiftVoucher = ref(null)
const createdPrepaidVoucher = ref(null)
const createError = ref(null)

// Manage section
const vouchers = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const totalVouchers = ref(0)

const filters = ref({
  type: '',
  status: '',
})

// Methods
const createGiftVoucher = async () => {
  creatingGift.value = true
  createError.value = null
  createdGiftVoucher.value = null

  try {
    const response = await apiService.post('/admin/vouchers/gift/', {
      value_cents: giftForm.value.valueCents,
      reason: giftForm.value.reason,
    })
    createdGiftVoucher.value = response
    giftForm.value = { valueCents: 1000, reason: 'COURTESY' }
    // Refresh list if manage tab was visited
    if (vouchers.value.length > 0) {
      await loadVouchers()
    }
  } catch (error) {
    createError.value = error.response?.data?.detail || 'Fehler beim Erstellen'
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
    createdPrepaidVoucher.value = response
    prepaidForm.value = { valueCents: 2000 }
    // Refresh list if manage tab was visited
    if (vouchers.value.length > 0) {
      await loadVouchers()
    }
  } catch (error) {
    createError.value = error.response?.data?.detail || 'Fehler beim Erstellen'
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

    const response = await apiService.get('/admin/vouchers/', { params })
    vouchers.value = response.vouchers
    totalVouchers.value = response.total
  } catch (error) {
    console.error('Error loading vouchers:', error)
  }
}

const applyFilters = () => {
  currentPage.value = 1
  loadVouchers()
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('de-DE')
}

const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text)
  // Could add a toast notification here
}

const exportAsCSV = () => {
  if (vouchers.value.length === 0) return

  const headers = ['Nummer', 'Typ', 'Wert (€)', 'Status', 'Grund', 'Erstellt', 'Eingelöst']
  const rows = vouchers.value.map((v) => [
    v.voucher_number,
    v.voucher_type,
    (v.value_cents / 100).toFixed(2),
    v.status,
    v.reason || '',
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
  if (newTab === 'manage' && vouchers.value.length === 0) {
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

  h2 {
    color: #333;
    margin-bottom: 1.5rem;
  }
}

.voucher-subtabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  border-bottom: 2px solid #f0f0f0;
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
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1.5rem;
  background: #f9f9f9;

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
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.vouchers-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;

  thead {
    background: #f5f5f5;
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
    background: #f9f9f9;
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

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
