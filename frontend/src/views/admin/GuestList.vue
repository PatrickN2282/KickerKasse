<template>
  <div class="admin-guestlist">
    <div class="page-header">
      <div class="title-row">
        <h2>Gästeliste</h2>
        <span class="title-sep">|</span>
        <span class="page-subtitle">Chronologische Übersicht aller eingetragenen Gäste.</span>
      </div>
      <div class="page-header-actions">
        <select
          v-model="productFilter"
          class="filter-input"
          aria-label="Produkt filtern"
        >
          <option value="">
            Alle Produkte
          </option>
          <option
            v-for="product in products"
            :key="product.id"
            :value="String(product.id)"
          >
            {{ product.name }}
          </option>
        </select>
        <input v-model="dateFrom" type="date" class="filter-input" aria-label="Von Datum">
        <input v-model="dateTo" type="date" class="filter-input" aria-label="Bis Datum">
        <input
          v-model="search"
          type="search"
          placeholder="Gast, Gastgeber oder Produkt suchen …"
          class="filter-input search-input"
        >
      </div>
    </div>

    <div
      v-if="isLoading"
      class="state"
    >
      <span class="spinner" />
      Daten werden geladen …
    </div>
    <div v-else-if="loadError" class="state state-error">
      <span>{{ loadError }}</span>
      <button class="retry-button" type="button" @click="loadEntries">Erneut laden</button>
    </div>
    <div
      v-else-if="entries.length === 0"
      class="state"
    >
      Keine passenden Einträge vorhanden.
    </div>

    <div
      v-else
      class="entries-table-wrapper"
    >
      <table class="entries-table">
        <thead>
          <tr>
            <th>Datum</th>
            <th>Zeit</th>
            <th>Name des Gastes</th>
            <th>Gast von</th>
            <th>Produkt / Anlass</th>
            <th>Beleg</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="entry in entries"
            :key="entry.id"
          >
            <td class="date-cell">
              {{ formatDate(entry.created_at) }}
            </td>
            <td class="time-cell">
              {{ formatTime(entry.created_at) }}
            </td>
            <td class="guest-name">
              {{ getGuestFullName(entry) }}
            </td>
            <td>{{ entry.member_name || '—' }}</td>
            <td><span class="product-badge">{{ entry.product_name || '—' }}</span></td>
            <td>{{ entry.receipt_number ? `#${entry.receipt_number}` : '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="!isLoading && !loadError && total > 0" class="pagination">
      <span>{{ total }} Einträge · Seite {{ currentPage }} von {{ totalPages || 1 }}</span>
      <div>
        <button type="button" :disabled="currentPage <= 1" @click="currentPage--">Zurück</button>
        <button type="button" :disabled="currentPage >= totalPages" @click="currentPage++">Weiter</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import apiService from '@/services/api'
import { useNotificationStore } from '@/stores/notification'

const notificationStore = useNotificationStore()
const isLoading = ref(false)
const entries = ref([])
const products = ref([])
const search = ref('')
const productFilter = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const loadError = ref('')
const currentPage = ref(1)
const pageSize = 50
const total = ref(0)
const totalPages = ref(0)
let searchTimer = null
let requestSequence = 0

const getGuestFullName = (entry) => {
  const structuredName = `${entry.guest_first_name || ''} ${entry.guest_last_name || ''}`.trim()
  return structuredName || entry.guest_name || '—'
}

const parseDate = (value) => value ? new Date(value) : null
const formatDate = (value) => parseDate(value)?.toLocaleDateString('de-DE') || '—'
const formatTime = (value) => parseDate(value)?.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) || '—'

const loadEntries = async () => {
  const requestId = ++requestSequence
  isLoading.value = true
  loadError.value = ''
  try {
    const response = await apiService.get('/guest-list/entries-page', { params: {
      page: currentPage.value,
      page_size: pageSize,
      product_id: productFilter.value || undefined,
      search: search.value.trim() || undefined,
      date_from: dateFrom.value ? `${dateFrom.value}T00:00:00` : undefined,
      date_to: dateTo.value ? `${dateTo.value}T23:59:59.999999` : undefined,
    } })
    if (requestId !== requestSequence) return
    entries.value = response.data.entries
    total.value = response.data.total
    totalPages.value = response.data.total_pages
  } catch (error) {
    if (requestId !== requestSequence) return
    loadError.value = error.response?.data?.detail || 'Gästeliste konnte nicht geladen werden.'
    notificationStore.error(loadError.value)
  } finally {
    if (requestId === requestSequence) isLoading.value = false
  }
}

const resetPageAndLoad = () => {
  if (currentPage.value !== 1) currentPage.value = 1
  else loadEntries()
}

watch([productFilter, dateFrom, dateTo], resetPageAndLoad)
watch(currentPage, loadEntries)
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(resetPageAndLoad, 300)
})

onMounted(async () => {
  try {
    const response = await apiService.get('/guest-list/products')
    products.value = response.data
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Produktfilter konnte nicht geladen werden.')
  }
  await loadEntries()
})
</script>

<style scoped lang="scss">
.admin-guestlist { padding: 0.85rem 1rem 1rem; border-radius: 8px; background: #fff; }
.page-header, .title-row, .page-header-actions { display: flex; align-items: center; gap: 0.65rem; }
.page-header { justify-content: space-between; flex-wrap: wrap; margin-bottom: 1rem; }
.title-row { flex-wrap: wrap; }
.title-row h2 { margin: 0; color: #1e293b; font-size: 1.25rem; }
.title-sep { color: #94a3b8; }
.page-subtitle { color: #64748b; font-size: 0.85rem; }
.page-header-actions { flex-wrap: wrap; }
.filter-input { min-height: 38px; padding: 0.45rem 0.7rem; border: 1px solid #cbd5e1; border-radius: 7px; background: #fff; color: #334155; }
.search-input { width: 300px; }
.entries-table-wrapper { overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 8px; }
.entries-table { width: 100%; border-collapse: collapse; background: #fff; font-size: 0.86rem; }
.entries-table th { padding: 0.65rem 0.75rem; text-align: left; white-space: nowrap; color: #64748b; background: #f8fafc; font-size: 0.75rem; text-transform: uppercase; letter-spacing: .03em; }
.entries-table td { padding: 0.65rem 0.75rem; border-top: 1px solid #edf2f7; color: #334155; }
.entries-table tbody tr:hover { background: #f8fafc; }
.date-cell, .time-cell { white-space: nowrap; }
.date-cell, .guest-name { font-weight: 700; }
.time-cell { color: #64748b; }
.product-badge { display: inline-block; padding: 0.18rem 0.5rem; border-radius: 999px; color: #1d4ed8; background: #dbeafe; font-size: 0.75rem; font-weight: 700; white-space: nowrap; }
.state { min-height: 240px; display: flex; align-items: center; justify-content: center; gap: 0.7rem; color: #64748b; }
.state-error { flex-direction: column; color: #b91c1c; }
.retry-button, .pagination button { padding: .45rem .75rem; border: 1px solid #cbd5e1; border-radius: 6px; background: #fff; cursor: pointer; }
.pagination { display: flex; justify-content: space-between; align-items: center; gap: .75rem; margin-top: .8rem; color: #64748b; font-size: .85rem; }
.pagination div { display: flex; gap: .5rem; }
.pagination button:disabled { opacity: .45; cursor: default; }
.spinner { width: 26px; height: 26px; border: 3px solid #e2e8f0; border-top-color: var(--app-highlight-color); border-radius: 50%; animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 760px) {
  .page-header-actions, .filter-input { width: 100%; }
  .search-input { width: 100%; }
}
</style>
