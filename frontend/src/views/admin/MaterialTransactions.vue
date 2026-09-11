<template>
  <div class="material-transactions">
    <div class="page-header">
      <div class="title-row">
        <h2>Verbrauchsmaterial</h2>
        <span class="title-sep">|</span>
        <span class="page-subtitle">Transaktionsliste aller intern gebuchten Materialartikel.</span>
      </div>
      <div class="header-actions">
        <select
          v-model="typeFilter"
          class="filter-input"
          aria-label="Buchungstyp filtern"
        >
          <option value="">
            Alle Buchungen
          </option>
          <option value="SALE">
            Verkäufe
          </option>
          <option value="STORNO">
            Stornos
          </option>
        </select>
        <input v-model="dateFrom" class="filter-input" type="date" aria-label="Von Datum">
        <input v-model="dateTo" class="filter-input" type="date" aria-label="Bis Datum">
        <input
          v-model="search"
          class="filter-input search-input"
          type="search"
          placeholder="Artikel, Notiz, Beleg …"
        >
      </div>
    </div>

    <div class="summary-grid">
      <div class="summary-card">
        <span>Artikel gesamt</span><strong>{{ account.total_quantity }}</strong>
      </div>
      <div class="summary-card">
        <span>Buchungen</span><strong>{{ account.total }}</strong>
      </div>
      <div class="summary-card">
        <span>Wert der Auswahl</span><strong>{{ formatPrice(account.total_value_cents) }}</strong>
      </div>
    </div>

    <div
      v-if="isLoading"
      class="state"
    >
      <span class="spinner" />Daten werden geladen …
    </div>
    <div
      v-else-if="loadError"
      class="state state-error"
    >
      <span>{{ loadError }}</span>
      <button class="retry-button" type="button" @click="loadEntries">Erneut laden</button>
    </div>
    <div
      v-else-if="account.entries.length === 0"
      class="state"
    >
      Keine passenden Materialbuchungen vorhanden.
    </div>

    <div
      v-else
      class="table-wrapper"
    >
      <table>
        <thead>
          <tr>
            <th>Datum</th>
            <th>Zeit</th>
            <th>Artikel</th>
            <th>Menge</th>
            <th>Wert</th>
            <th>Notiz</th>
            <th>Mitglied / Konto</th>
            <th>Beleg</th>
            <th>Typ</th>
            <th>Benutzer</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="entry in account.entries"
            :key="entry.id"
          >
            <td class="date-cell">
              {{ formatDate(entry.created_at) }}
            </td>
            <td>{{ formatTime(entry.created_at) }}</td>
            <td class="product-cell">
              {{ entry.product_name || entry.reason || '—' }}
            </td>
            <td>{{ signedQuantity(entry) }}</td>
            <td
              class="amount"
              :class="{ negative: entry.amount_cents < 0 }"
            >
              {{ formatPrice(entry.amount_cents) }}
            </td>
            <td class="note-cell">
              {{ entry.note || '—' }}
            </td>
            <td>{{ entry.transaction?.member_name || 'Gast / intern' }}</td>
            <td>{{ entry.receipt_number ? `#${entry.receipt_number}` : '—' }}</td>
            <td><span :class="['type-badge', entry.entry_type.toLowerCase()]">{{ entry.entry_type_label }}</span></td>
            <td>{{ entry.user_name || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="!isLoading && !loadError && account.total > 0" class="pagination">
      <span>{{ account.total }} Buchungen · Seite {{ currentPage }} von {{ account.total_pages || 1 }}</span>
      <div>
        <button type="button" :disabled="currentPage <= 1" @click="currentPage--">Zurück</button>
        <button type="button" :disabled="currentPage >= account.total_pages" @click="currentPage++">Weiter</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import apiService from '@/services/api'
import { formatPrice } from '@/services/utils'
import { useNotificationStore } from '@/stores/notification'

const notificationStore = useNotificationStore()
const isLoading = ref(false)
const account = ref({ total_quantity: 0, total_value_cents: 0, total: 0, total_pages: 0, entries: [] })
const search = ref('')
const typeFilter = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const loadError = ref('')
const currentPage = ref(1)
const pageSize = 50
let searchTimer = null
let requestSequence = 0

const parseDate = (value) => value ? new Date(value) : null
const formatDate = (value) => parseDate(value)?.toLocaleDateString('de-DE') || '—'
const formatTime = (value) => parseDate(value)?.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) || '—'
const signedQuantity = (entry) => {
  if (entry.quantity === null || entry.quantity === undefined) return '—'
  return entry.entry_type === 'STORNO' ? `-${entry.quantity}` : `+${entry.quantity}`
}

const loadEntries = async () => {
  const requestId = ++requestSequence
  isLoading.value = true
  loadError.value = ''
  try {
    const response = await apiService.get('/admin/vouchers/material-transactions', { params: {
      page: currentPage.value,
      page_size: pageSize,
      entry_type: typeFilter.value || undefined,
      search: search.value.trim() || undefined,
      date_from: dateFrom.value ? `${dateFrom.value}T00:00:00` : undefined,
      date_to: dateTo.value ? `${dateTo.value}T23:59:59.999999` : undefined,
    } })
    if (requestId !== requestSequence) return
    account.value = response.data
  } catch (error) {
    if (requestId !== requestSequence) return
    loadError.value = error.response?.data?.detail || 'Materialtransaktionen konnten nicht geladen werden.'
    notificationStore.error(loadError.value)
  } finally {
    if (requestId === requestSequence) isLoading.value = false
  }
}

const resetPageAndLoad = () => {
  if (currentPage.value !== 1) currentPage.value = 1
  else loadEntries()
}

watch([typeFilter, dateFrom, dateTo], resetPageAndLoad)
watch(currentPage, loadEntries)
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(resetPageAndLoad, 300)
})
onMounted(loadEntries)
</script>

<style scoped lang="scss">
.material-transactions {
  padding: 0.85rem 1rem 1rem;
  border-radius: 8px;
  background: #fff;
}

.page-header, .title-row, .header-actions {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.page-header { justify-content: space-between; flex-wrap: wrap; margin-bottom: 1rem; }
.title-row { flex-wrap: wrap; }
.title-row h2 { margin: 0; color: #1e293b; font-size: 1.25rem; }
.title-sep { color: #94a3b8; }
.page-subtitle { color: #64748b; font-size: 0.85rem; }
.header-actions { flex-wrap: wrap; }

.filter-input {
  min-height: 38px;
  padding: 0.45rem 0.7rem;
  border: 1px solid #cbd5e1;
  border-radius: 7px;
  background: #fff;
  color: #334155;
}
.search-input { width: 240px; }

.summary-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.75rem; margin-bottom: 1rem; }
.summary-card { padding: 0.8rem 1rem; border: 1px solid #dbe3ea; border-radius: 9px; background: #f8fafc; }
.summary-card span { display: block; color: #64748b; font-size: 0.75rem; text-transform: uppercase; }
.summary-card strong { display: block; margin-top: 0.2rem; color: #0f172a; font-size: 1.2rem; }

.table-wrapper { overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 8px; }
table { width: 100%; border-collapse: collapse; font-size: 0.84rem; background: #fff; }
th { padding: 0.65rem 0.7rem; text-align: left; white-space: nowrap; color: #64748b; background: #f8fafc; font-size: 0.75rem; text-transform: uppercase; }
td { padding: 0.6rem 0.7rem; border-top: 1px solid #edf2f7; color: #334155; vertical-align: top; }
tbody tr:hover { background: #f8fafc; }
.date-cell, .amount { white-space: nowrap; }
.product-cell, .amount { font-weight: 700; }
.amount { text-align: right; color: #166534; }
.amount.negative { color: #b91c1c; }
.note-cell { min-width: 160px; max-width: 280px; white-space: normal; }
.type-badge { display: inline-block; padding: 0.18rem 0.5rem; border-radius: 999px; font-weight: 700; font-size: 0.72rem; color: #166534; background: #dcfce7; }
.type-badge.storno { color: #991b1b; background: #fee2e2; }
.state { min-height: 220px; display: flex; align-items: center; justify-content: center; gap: 0.7rem; color: #64748b; }
.state-error { flex-direction: column; color: #b91c1c; }
.retry-button, .pagination button { padding: .45rem .75rem; border: 1px solid #cbd5e1; border-radius: 6px; background: #fff; cursor: pointer; }
.pagination { display: flex; justify-content: space-between; align-items: center; gap: .75rem; margin-top: .8rem; color: #64748b; font-size: .85rem; }
.pagination div { display: flex; gap: .5rem; }
.pagination button:disabled { opacity: .45; cursor: default; }
.spinner { width: 24px; height: 24px; border: 3px solid #e2e8f0; border-top-color: var(--app-highlight-color); border-radius: 50%; animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 800px) {
  .summary-grid { grid-template-columns: 1fr; }
  .header-actions, .filter-input { width: 100%; }
  .search-input { width: 100%; }
}
</style>
