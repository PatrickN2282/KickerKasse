<template>
  <div class="admin-finance">
    <h2>Finanzstatistik</h2>

    <div class="finance-tabs">
      <button
        v-for="tab in tabs"
        :key="tab"
        @click="activeTab = tab"
        :class="{ active: activeTab === tab }"
        class="tab-btn"
      >
        {{ tabLabels[tab] }}
      </button>
    </div>

    <!-- Z-BON / Tagesabrechnung -->
    <div v-if="activeTab === 'zbon'" class="tab-content">
      <h3>Z-Bon (Tagesabrechnung)</h3>
      
      <div class="date-picker">
        <label>Datum:</label>
        <input v-model="selectedDate" type="date" class="form-input" />
      </div>

      <div v-if="loading" class="loading">Läuft...</div>
      <div v-else class="zbon-summary">
        <div class="summary-grid">
          <div class="summary-card">
            <div class="card-label">Umsatz (BAR)</div>
            <div class="card-value">{{ formatPrice(dailyStats.cash_total) }}</div>
          </div>
          <div class="summary-card">
            <div class="card-label">Umsatz (Guthaben)</div>
            <div class="card-value">{{ formatPrice(dailyStats.balance_total) }}</div>
          </div>
          <div class="summary-card highlight">
            <div class="card-label">Umsatz GESAMT</div>
            <div class="card-value">{{ formatPrice(dailyStats.total_amount) }}</div>
          </div>
          <div class="summary-card">
            <div class="card-label">Anzahl Transaktionen</div>
            <div class="card-value">{{ dailyStats.transaction_count }}</div>
          </div>
        </div>

        <div class="daily-transactions">
          <h4>Transaktionen am {{ formatDateDE(selectedDate) }}</h4>
          <div v-if="dailyStats.transactions.length === 0" class="empty">
            Keine Transaktionen für diesen Tag
          </div>
          <table v-else class="transactions-table">
            <thead>
              <tr>
                <th>Zeit</th>
                <th>Belegnummer</th>
                <th>Mitglied</th>
                <th>Betrag</th>
                <th>Zahlungsart</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="transaction in dailyStats.transactions" :key="transaction.id">
                <tr class="transaction-row" @click="toggleTransaction(transaction.id)" style="cursor: pointer;">
                  <td>{{ formatTime(transaction.created_at) }}</td>
                  <td><strong>{{ transaction.receipt_number }}</strong></td>
                  <td>{{ transaction.member?.name || 'Gast' }}</td>
                  <td class="amount">{{ formatPrice(transaction.total_amount_cents) }}</td>
                  <td>
                    <span v-if="transaction.type === 'RECHARGE'" class="payment-badge recharge">
                      ⬆️ Aufladen
                    </span>
                    <span v-else :class="['payment-badge', transaction.payment_method.toLowerCase()]">
                      {{ transaction.payment_method === 'CASH' ? '💰 BAR' : '💳 Guthaben' }}
                    </span>
                  </td>
                </tr>
                <tr v-if="expandedTransactions.has(transaction.id)" class="items-row">
                  <td colspan="5" class="items-cell">
                    <div class="items-list">
                      <div v-if="transaction.items && transaction.items.length > 0">
                        <div v-for="item in transaction.items" :key="item.id" class="item-detail">
                          <span class="item-name">{{ item.product?.name || item.id }}: </span>
                          <span class="item-qty">{{ item.quantity }}×</span>
                          <span class="item-price">{{ formatPrice(item.unit_price_cents) }}</span>
                          <span class="item-total">= {{ formatPrice(item.total_price_cents) }}</span>
                        </div>
                      </div>
                      <div v-else class="no-items">
                        Keine Artikel
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>

        <div class="zbon-actions">
          <button @click="downloadZBon" class="btn btn-primary">
            📄 Z-Bon drucken
          </button>
          <button @click="askForCashCount" class="btn btn-info">
            📧 Z-Bon per Email
          </button>
          <button @click="openCashCounterModal" class="btn btn-secondary">
            💰 Kasse zählen
          </button>
        </div>

        <div class="scheduler-section">
          <h4>⏱️ Automatischer Email-Versand</h4>
          <div class="scheduler-status">
            <div class="status-item">
              <span>Status:</span>
              <span v-if="schedulerStatus.running" class="status-badge running">
                ● Läuft
              </span>
              <span v-else class="status-badge stopped">
                ● Gestoppt
              </span>
            </div>
            <div v-if="schedulerStatus.next_run" class="status-item">
              <span>Nächster Versand:</span>
              <span class="next-run">{{ formatTime(schedulerStatus.next_run) }}</span>
            </div>
          </div>
          <p class="scheduler-info">
            Der automatische Z-Bon-Versand muss in der .env-Datei konfiguriert werden:
          </p>
          <ul class="config-list">
            <li><code>SCHEDULED_ZBON_ENABLED=true</code></li>
            <li><code>SCHEDULED_ZBON_TIME=23:59</code> (HH:MM Format)</li>
            <li><code>SCHEDULED_ZBON_REPORT_TYPE=zbon</code> (oder "daily-report")</li>
            <li><code>EMAIL_ENABLED=true</code></li>
            <li>SMTP-Einstellungen konfigurieren</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Transaktionshistorie -->
    <div v-if="activeTab === 'history'" class="tab-content">
      <h3>Transaktionshistorie</h3>

      <div class="filter-section">
        <div class="filter-group">
          <label>Von Datum:</label>
          <input v-model="filterStartDate" type="date" class="form-input" />
        </div>
        <div class="filter-group">
          <label>Bis Datum:</label>
          <input v-model="filterEndDate" type="date" class="form-input" />
        </div>
        <div class="filter-group">
          <label>Zahlungsart:</label>
          <select v-model="filterPaymentMethod" class="form-input">
            <option value="">Alle</option>
            <option value="CASH">BAR</option>
            <option value="BALANCE">Guthaben</option>
          </select>
        </div>
        <button @click="applyFilters" class="btn btn-info">Filter anwenden</button>
      </div>

      <div v-if="loadingHistory" class="loading">Läuft...</div>
      <div v-else>
        <div class="history-summary">
          <div class="summary-item">
            <span>Umsatz gesamt:</span>
            <span class="amount">{{ formatPrice(filteredStats.total) }}</span>
          </div>
          <div class="summary-item">
            <span>Anzahl Transaktionen:</span>
            <span>{{ filteredTransactions.length }}</span>
          </div>
        </div>

        <table v-if="filteredTransactions.length > 0" class="transactions-table">
          <thead>
            <tr>
              <th>Datum</th>
              <th>Zeit</th>
              <th>Belegnummer</th>
              <th>Mitglied</th>
              <th>Betrag</th>
              <th>Zahlungsart</th>
              <th>Benutzer</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="transaction in filteredTransactions" :key="transaction.id">
              <td>{{ formatDate(transaction.created_at) }}</td>
              <td>{{ formatTime(transaction.created_at) }}</td>
              <td><strong>{{ transaction.receipt_number }}</strong></td>
              <td>{{ transaction.member?.name || 'Gast' }}</td>
              <td class="amount">{{ formatPrice(transaction.total_amount_cents) }}</td>
              <td>
                <span v-if="transaction.type === 'RECHARGE'" class="payment-badge recharge">
                  ⬆️ Aufladen
                </span>
                <span v-else :class="['payment-badge', transaction.payment_method.toLowerCase()]">
                  {{ transaction.payment_method === 'CASH' ? '💰 BAR' : '💳 Guthaben' }}
                </span>
              </td>
              <td>{{ transaction.user?.username || '-' }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty">
          Keine Transaktionen im ausgewählten Zeitraum
        </div>
      </div>
    </div>

    <!-- Umsatzstatistik -->
    <div v-if="activeTab === 'revenue'" class="tab-content">
      <h3>Umsatzstatistik</h3>

      <div class="revenue-overview">
        <div class="revenue-card">
          <div class="card-label">Umsatz diese Woche</div>
          <div class="card-value">{{ formatPrice(revenueStats.week_total) }}</div>
        </div>
        <div class="revenue-card">
          <div class="card-label">Umsatz diesen Monat</div>
          <div class="card-value">{{ formatPrice(revenueStats.month_total) }}</div>
        </div>
        <div class="revenue-card">
          <div class="card-label">Durchschnitt pro Tag</div>
          <div class="card-value">{{ formatPrice(revenueStats.daily_average) }}</div>
        </div>
      </div>

      <div class="payment-stats">
        <h4>Nach Zahlungsart</h4>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-label">💰 Bargeld</div>
            <div class="stat-value">{{ formatPrice(revenueStats.cash_total) }}</div>
            <div class="stat-percent">{{ revenueStats.cash_percent }}%</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">💳 Guthaben</div>
            <div class="stat-value">{{ formatPrice(revenueStats.balance_total) }}</div>
            <div class="stat-percent">{{ revenueStats.balance_percent }}%</div>
          </div>
        </div>
      </div>

      <div class="top-products">
        <h4>Top Produkte (diese Woche)</h4>
        <table v-if="revenueStats.top_products.length > 0" class="products-table">
          <thead>
            <tr>
              <th>Produkt</th>
              <th>Menge</th>
              <th>Umsatz</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="product in revenueStats.top_products" :key="product.id">
              <td>{{ product.name }}</td>
              <td>{{ product.quantity_sold }}</td>
              <td>{{ formatPrice(product.total_revenue) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Member-Statistik -->
    <div v-if="activeTab === 'members'" class="tab-content">
      <h3>Mitglied-Statistik</h3>

      <div class="member-stats-overview">
        <div class="stat-card">
          <div class="stat-label">Gesamte Mitglieder</div>
          <div class="stat-value">{{ memberStats.total_members }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Aktiv diese Woche</div>
          <div class="stat-value">{{ memberStats.active_this_week }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Gesamtes Guthaben</div>
          <div class="stat-value">{{ formatPrice(memberStats.total_balance) }}</div>
        </div>
      </div>

      <h4>Top Mitglieder (nach Ausgaben)</h4>
      <table v-if="memberStats.top_members.length > 0" class="members-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Transaktionen</th>
            <th>Ausgegeben</th>
            <th>Guthaben</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="member in memberStats.top_members" :key="member.id">
            <td>{{ member.name }}</td>
            <td>{{ member.transaction_count }}</td>
            <td>{{ formatPrice(member.total_spent) }}</td>
            <td>{{ formatPrice(member.balance_cents) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Cash Counter Modal -->
    <CashCounterModal
      :show="showCashCounterModal"
      @close="showCashCounterModal = false"
      @confirm="onCashCounterConfirm"
    />

    <div v-if="showCashCountConfirm" class="confirmation-overlay">
      <div class="confirmation-dialog">
        <h3>Kassenzählung erforderlich?</h3>
        <p>Soll die Kasse vor der Z-Bon-Generierung gezählt werden?</p>
        <div class="confirmation-buttons">
          <button @click="proceedWithoutCashCount" class="btn btn-secondary">
            ✕ Nein, ohne Zählung
          </button>
          <button @click="proceedWithCashCount" class="btn btn-primary">
            ✓ Ja, Kasse zählen
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { formatPrice } from '@/services/utils'
import apiService from '@/services/api'
import CashCounterModal from '@/components/CashCounterModal.vue'

const activeTab = ref('zbon')
const loading = ref(false)
const loadingHistory = ref(false)
const selectedDate = ref(new Date().toISOString().split('T')[0])

// Cash counter modal state
const showCashCounterModal = ref(false)
const cashCountData = ref(null)
const reportType = ref('zbon') // 'zbon' or 'daily-report'
// Filters
const filterStartDate = ref(getDateDaysAgo(30))
const filterEndDate = ref(new Date().toISOString().split('T')[0])
const filterPaymentMethod = ref('')

// Pre-dialog for cash counting confirmation
const showCashCountConfirm = ref(false)
// Expanded transactions state
const expandedTransactions = ref(new Set())

// Data
const dailyStats = ref({
  cash_total: 0,
  balance_total: 0,
  total_amount: 0,
  transaction_count: 0,
  transactions: [],
})

const filteredTransactions = ref([])
const filteredStats = ref({ total: 0 })
const revenueStats = ref({
  week_total: 0,
  month_total: 0,
  daily_average: 0,
  cash_total: 0,
  balance_total: 0,
  cash_percent: 0,
  balance_percent: 0,
  top_products: [],
})

const memberStats = ref({
  total_members: 0,
  active_this_week: 0,
  total_balance: 0,
  top_members: [],
})

const tabs = ['zbon', 'history', 'revenue', 'members']
const tabLabels = {
  zbon: '📊 Z-Bon',
  history: '📜 Transaktionen',
  revenue: '📈 Umsatz',
  members: '👥 Mitglieder',
}

// Scheduler configuration
const schedulerStatus = ref({
  enabled: false,
  running: false,
  scheduled_time: '23:59',
})
const schedulerEnabled = ref(false)
const schedulerTime = ref('23:59')
function getDateDaysAgo(days) {
  const date = new Date()
  date.setDate(date.getDate() - days)
  return date.toISOString().split('T')[0]
}

const loadSchedulerStatus = async () => {
  try {
    const response = await apiService.get('/transactions/scheduler/status')
    schedulerStatus.value = response.data
    console.log('Scheduler status loaded:', schedulerStatus.value)
  } catch (error) {
    console.error('Error loading scheduler status:', error)
  }
}
function formatDateDE(dateStr) {
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('de-DE', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('de-DE')
}

function formatTime(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
}

const loadDailyStats = async () => {
  loading.value = true
  try {
    console.log('Loading daily stats for date:', selectedDate.value)
    const data = await apiService.get(`/transactions/daily-stats?date=${selectedDate.value}`)
    console.log('Daily stats loaded:', data.data)
    dailyStats.value = data.data
  } catch (error) {
    console.error('Error loading daily stats:', error)
    dailyStats.value = {
      cash_total: 0,
      balance_total: 0,
      total_amount: 0,
      transaction_count: 0,
      transactions: [],
    }
  } finally {
    loading.value = false
  }
}

const applyFilters = async () => {
  loadingHistory.value = true
  try {
    const params = new URLSearchParams({
      start_date: filterStartDate.value,
      end_date: filterEndDate.value,
    })
    if (filterPaymentMethod.value) {
      params.append('payment_method', filterPaymentMethod.value)
    }

    console.log('Loading filtered transactions:', params.toString())
    const data = await apiService.get(`/transactions/filtered?${params.toString()}`)
    console.log('Filtered transactions loaded:', data.data)
    filteredTransactions.value = data.data.transactions || []
    filteredStats.value = {
      total: data.data.total_amount || 0,
    }
  } catch (error) {
    console.error('Error loading filtered transactions:', error)
    filteredTransactions.value = []
    filteredStats.value = { total: 0 }
  } finally {
    loadingHistory.value = false
  }
}

const loadRevenueStats = async () => {
  try {
    console.log('Loading revenue stats')
    const data = await apiService.get('/transactions/revenue-stats')
    console.log('Revenue stats loaded:', data.data)
    revenueStats.value = data.data
  } catch (error) {
    console.error('Error loading revenue stats:', error)
  }
}

const loadMemberStats = async () => {
  try {
    console.log('Loading member stats')
    const data = await apiService.get('/members/statistics')
    console.log('Member stats loaded:', data.data)
    memberStats.value = data.data
  } catch (error) {
    console.error('Error loading member stats:', error)
  }
}

const toggleTransaction = (transactionId) => {
  if (expandedTransactions.value.has(transactionId)) {
    expandedTransactions.value.delete(transactionId)
  } else {
    expandedTransactions.value.add(transactionId)
  }
}

const openCashCounterModal = () => {
  showCashCounterModal.value = true
}

const askForCashCount = () => {
  showCashCountConfirm.value = true
}

const proceedWithCashCount = () => {
  showCashCountConfirm.value = false
  openCashCounterModal()
}

const proceedWithoutCashCount = () => {
  showCashCountConfirm.value = false
  cashCountData.value = null
  sendZBonEmail()
}
const onCashCounterConfirm = (data) => {
  cashCountData.value = data
  sendZBonEmail()
}

const sendZBonEmail = async () => {
  try {
    // First generate the Z-Bon with optional cash count data
    const generateResponse = await apiService.post('/transactions/zbon/generate', {
      date: selectedDate.value,
      report_type: reportType.value,
      cash_count: cashCountData.value ? {
        coins: Object.fromEntries(Object.entries(cashCountData.value.coins).map(([k, v]) => [parseFloat(k), v])),
        notes: Object.fromEntries(Object.entries(cashCountData.value.notes).map(([k, v]) => [parseInt(k), v]))
      } : null,
    })
    
    // Then send via email
    const emailResponse = await apiService.post('/transactions/zbon/send-email', {
      zbon_content: generateResponse.data.content,
      date: selectedDate.value,
    })
    
    // Show success notification
    alert(`✓ Z-Bon erfolgreich versendet an ${emailResponse.data.recipient}`)
    
    // Reset cash count
    cashCountData.value = null
  } catch (error) {
    console.error('Error sending Z-Bon:', error)
    alert(`✗ Fehler beim Versenden: ${error.response?.data?.detail || error.message}`)
  }
}
const downloadZBon = () => {
  const content = `
╔════════════════════════════════════════════╗
║              Z-BON / TAGESABRECHNUNG       ║
╚════════════════════════════════════════════╝
Datum: ${formatDateDE(selectedDate.value)}

────────────────────────────────────────────
UMSATZ NACH ZAHLUNGSART
────────────────────────────────────────────
💰 Bargeld:              ${formatPrice(dailyStats.value.cash_total).padStart(15)}
💳 Guthaben:            ${formatPrice(dailyStats.value.balance_total).padStart(15)}

GESAMT:                  ${formatPrice(dailyStats.value.total_amount).padStart(15)}

Transaktionen:           ${String(dailyStats.value.transaction_count).padStart(15)}

════════════════════════════════════════════
Generated: ${new Date().toLocaleString('de-DE')}
════════════════════════════════════════════
  `.trim()

  const blob = new Blob([content], { type: 'text/plain' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `Z-Bon_${selectedDate.value}.txt`
  a.click()
  window.URL.revokeObjectURL(url)
}

// Watch für Datumänderungen
watch(selectedDate, () => {
  loadDailyStats()
})

// Watch für Filteränderungen
watch([filterStartDate, filterEndDate, filterPaymentMethod], () => {
  applyFilters()
})

// Watch für Tab-Wechsel
watch(activeTab, (newTab) => {
  console.log('Switched to tab:', newTab)
  if (newTab === 'zbon' && dailyStats.value.transaction_count === 0) {
    loadDailyStats()
  } else if (newTab === 'history' && filteredTransactions.value.length === 0) {
    applyFilters()
  } else if (newTab === 'revenue' && revenueStats.value.week_total === 0) {
    loadRevenueStats()
  } else if (newTab === 'members' && memberStats.value.total_members === 0) {
    loadMemberStats()
  }
})

onMounted(() => {
  console.log('Finance component mounted, loading data...')
  loadDailyStats()
  applyFilters()
  loadRevenueStats()
  loadMemberStats()
  loadSchedulerStatus()
})
</script>

<style scoped lang="scss">
.admin-finance {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  h2 {
    margin-bottom: 2rem;
    color: #333;
  }

  h3 {
    margin-bottom: 1.5rem;
    color: #555;
  }

  h4 {
    margin: 1.5rem 0 1rem 0;
    color: #666;
  }
}

.finance-tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  border-bottom: 2px solid #eee;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 0.75rem 1.5rem;
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  font-weight: 600;
  color: #666;
  transition: all 0.2s;

  &:hover {
    color: #1976d2;
  }

  &.active {
    color: #1976d2;
    border-bottom-color: #1976d2;
  }
}

.tab-content {
  animation: fadeIn 0.2s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.date-picker {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 2rem;

  label {
    font-weight: 600;
  }

  input {
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
  }
}

.filter-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
  padding: 1rem;
  background: #f9f9f9;
  border-radius: 4px;
  align-items: flex-end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;

  label {
    font-weight: 600;
    font-size: 0.9rem;
  }

  input,
  select {
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.summary-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(102, 126, 234, 0.2);

  &.highlight {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  }

  .card-label {
    font-size: 0.9rem;
    opacity: 0.9;
    margin-bottom: 0.5rem;
  }

  .card-value {
    font-size: 1.8rem;
    font-weight: bold;
  }
}

.daily-transactions,
.payment-stats,
.top-products {
  margin: 2rem 0;
}

.transactions-table,
.products-table,
.members-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;

  thead {
    background: #f5f5f5;

    th {
      padding: 1rem;
      text-align: left;
      font-weight: 600;
      border-bottom: 2px solid #ddd;
    }
  }

  tbody {
    tr {
      border-bottom: 1px solid #eee;

      &:hover {
        background: #f9f9f9;
      }

      td {
        padding: 1rem;

        &.amount {
          font-weight: 600;
          color: #667eea;
        }
      }
    }
  }
}

.payment-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  display: inline-block;

  &.cash {
    background: #e8f5e9;
    color: #2e7d32;
  }

  &.balance {
    background: #e3f2fd;
    color: #1565c0;
  }

  &.recharge {
    background: #fff3e0;
    color: #e65100;
  }
}

.empty {
  text-align: center;
  padding: 2rem;
  color: #999;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.history-summary,
.revenue-overview,
.member-stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.summary-item,
.stat-card,
.revenue-card {
  background: #f5f5f5;
  padding: 1.5rem;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;

  span {
    &:first-child {
      font-weight: 600;
    }

    &.amount {
      font-size: 1.3rem;
      font-weight: bold;
      color: #667eea;
    }
  }
}

.stat-card {
  .stat-label {
    font-weight: 600;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
  }

  .stat-value {
    font-size: 2rem;
    font-weight: bold;
    color: #667eea;
  }
}

.revenue-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;

  .card-label {
    font-size: 0.9rem;
    opacity: 0.9;
  }

  .card-value {
    font-size: 1.8rem;
    font-weight: bold;
    margin-top: 0.5rem;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.stat-item {
  background: #f5f5f5;
  padding: 1rem;
  border-radius: 8px;
  text-align: center;

  .stat-label {
    font-weight: 600;
    margin-bottom: 0.5rem;
  }

  .stat-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: #667eea;
    margin-bottom: 0.5rem;
  }

  .stat-percent {
    font-size: 0.9rem;
    color: #999;
  }
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-primary {
  background: #1976d2;
  color: white;

  &:hover {
    background: #1565c0;
  }
}

.btn-info {
  background: #00bcd4;
  color: white;

  &:hover {
    background: #0097a7;
  }
}

.btn-secondary {
  background: #f5f5f5;
  color: #666;
  border: 1px solid #ddd;

  &:hover {
    background: #e0e0e0;
  }
}

.zbon-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
  flex-wrap: wrap;
}
.form-input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.scheduler-section {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 1.5rem;
  margin: 2rem 0;
  border-left: 4px solid #ff9800;
}

.scheduler-status {
  display: flex;
  gap: 2rem;
  margin: 1rem 0;
  flex-wrap: wrap;
}

.status-item {
  display: flex;
  gap: 1rem;
  align-items: center;

  span:first-child {
    font-weight: 600;
    color: #666;
  }
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;

  &.running {
    background: #c8e6c9;
    color: #2e7d32;
  }

  &.stopped {
    background: #ffcccc;
    color: #c62828;
  }
}

.next-run {
  color: #667eea;
  font-weight: 600;
}

.scheduler-info {
  margin: 1rem 0 0.5rem 0;
  color: #666;
  font-size: 0.9rem;
}

.config-list {
  margin: 0.5rem 0 0 1.5rem;
  color: #666;
  font-size: 0.9rem;

  li {
    margin: 0.3rem 0;

    code {
      background: #fff;
      padding: 0.2rem 0.5rem;
      border-radius: 3px;
      font-family: monospace;
      color: #d32f2f;
    }
  }
}
.confirmation-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1500;
}

.confirmation-dialog {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  max-width: 400px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  text-align: center;

  h3 {
    margin: 0 0 0.75rem 0;
    color: #333;
  }

  p {
    margin: 0 0 1.5rem 0;
    color: #666;
  }
}

.confirmation-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
}
.transaction-row {
  &:hover {
    background: #f0f0f0;
  }
}

.items-row {
  background: #f9f9f9;

  td {
    padding: 0 !important;
  }
}

.items-cell {
  background: #f9f9f9 !important;
  padding: 0.5rem 1rem !important;
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.item-detail {
  display: flex;
  gap: 1rem;
  padding: 0.5rem;
  background: white;
  border-radius: 4px;
  border-left: 3px solid #667eea;
  font-size: 0.9rem;

  .item-name {
    font-weight: 600;
    flex: 1;
  }

  .item-qty {
    color: #666;
    min-width: 40px;
  }

  .item-price {
    color: #666;
    min-width: 60px;
    text-align: right;
  }

  .item-total {
    font-weight: 600;
    color: #667eea;
    min-width: 70px;
    text-align: right;
  }
}

.no-items {
  padding: 1rem;
  text-align: center;
  color: #999;
  font-style: italic;
}
</style>
