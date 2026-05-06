<template>
  <div class="admin-corrections">
    <div class="page-header">
      <div>
        <h2>Korrektur-Buchungen</h2>
        <p class="page-subtitle">
          Guthaben und Lagerbestände ohne Bargeldfluss revisionssicher korrigieren.
        </p>
        <p class="page-note">
          Korrekturen werden als separate Korrekturbuchungen dokumentiert und direkt im jeweiligen Bereich archiviert.
        </p>
      </div>
    </div>

    <div class="correction-subtabs">
      <button
        v-for="tab in subTabs"
        :key="tab.id"
        :class="['subtab-button', { active: activeTab === tab.id }]"
        type="button"
        @click="activeTab = tab.id"
      >
        <span class="subtab-icon">{{ tab.icon }}</span>
        <span>{{ tab.label }}</span>
      </button>
    </div>

    <div class="correction-content">
      <section
        v-if="activeTab === 'members'"
        class="panel-card"
      >
        <div class="section-header">
          <div>
            <h3>Mitgliedsguthaben korrigieren</h3>
            <p>Korrekturbuchung mit Altbestand, Neubestand, Zeitstempel und ausführendem Benutzer.</p>
          </div>
        </div>

        <div class="form-grid">
          <div class="form-group form-group--full">
            <span>Mitglied auswählen</span>
            <input
              v-model.trim="memberSearch"
              type="text"
              placeholder="Nach Name oder Nummer filtern..."
            >
            <div class="picker-list">
              <button
                v-for="member in filteredMembers"
                :key="member.id"
                type="button"
                :class="['picker-item', { active: selectedMemberId === member.id }]"
                @click="selectedMemberId = member.id"
              >
                <strong>{{ getMemberFullName(member) }}</strong>
                <span>#{{ member.member_number }} · {{ formatBalance(member.balance_cents) }}</span>
              </button>
              <div
                v-if="filteredMembers.length === 0"
                class="picker-empty"
              >
                Keine passenden Mitglieder gefunden
              </div>
            </div>
          </div>

          <label class="form-group">
            <span>Aktueller Bestand</span>
            <input
              :value="selectedMember ? formatBalance(selectedMember.balance_cents) : '—'"
              type="text"
              disabled
            >
          </label>

          <label class="form-group">
            <span>Neuer Bestand (€)</span>
            <input
              v-model.number="memberTargetBalanceEuro"
              type="number"
              min="0"
              step="0.01"
              placeholder="0,00"
            >
          </label>

          <label class="form-group form-group--full">
            <span>Grund der Korrektur</span>
            <input
              v-model.trim="memberCorrectionReason"
              type="text"
              maxlength="255"
              placeholder="z. B. Übertrag aus alter Kasse"
            >
          </label>
        </div>

        <div
          v-if="selectedMember"
          class="preview-card"
        >
          <div>
            <span class="preview-label">Differenz</span>
            <strong>{{ formatBalance(memberDeltaCents) }}</strong>
          </div>
          <div>
            <span class="preview-label">Ausführender Benutzer</span>
            <strong>{{ authStore.user?.username || '—' }}</strong>
          </div>
        </div>

        <div class="action-row">
          <button
            class="btn btn-success"
            type="button"
            :disabled="!canSubmitMemberCorrection || isSubmitting"
            @click="submitMemberCorrection"
          >
            Guthaben korrigieren
          </button>
        </div>

        <div class="history-block">
          <div class="section-header section-header--compact">
            <div>
              <h3>Historie</h3>
              <p>Alle Korrekturbuchungen für Mitglieder.</p>
            </div>
          </div>

          <div class="history-table-wrapper">
            <table class="history-table">
              <thead>
                <tr>
                  <th>Datum</th>
                  <th>Mitglied</th>
                  <th>Altbestand</th>
                  <th>Neubestand</th>
                  <th>Differenz</th>
                  <th>Grund</th>
                  <th>Benutzer</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="log in memberLogs"
                  :key="`member-${log.id}`"
                >
                  <td>{{ formatTimestamp(log.created_at) }}</td>
                  <td>{{ log.member_name }}</td>
                  <td>{{ formatBalance(log.old_balance_cents) }}</td>
                  <td>{{ formatBalance(log.new_balance_cents) }}</td>
                  <td>{{ formatBalance(log.change_cents) }}</td>
                  <td>{{ log.reason }}</td>
                  <td>{{ log.executed_by_username }}</td>
                </tr>
                <tr v-if="memberLogs.length === 0">
                  <td
                    colspan="7"
                    class="empty-state-cell"
                  >
                    Noch keine Guthaben-Korrekturen vorhanden
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section
        v-else
        class="panel-card"
      >
        <div class="section-header">
          <div>
            <h3>Warenbestand korrigieren</h3>
            <p>Bestandskorrektur mit Altbestand, Neubestand, Zeitstempel und ausführendem Benutzer.</p>
          </div>
        </div>

        <div class="form-grid">
          <div class="form-group form-group--full">
            <span>Produkt auswählen</span>
            <input
              v-model.trim="productSearch"
              type="text"
              placeholder="Nach Produktname oder Warengruppe filtern..."
            >
            <div class="picker-list">
              <button
                v-for="product in filteredProducts"
                :key="product.id"
                type="button"
                :class="['picker-item', { active: selectedProductId === product.id }]"
                @click="selectedProductId = product.id"
              >
                <strong>{{ product.name }}</strong>
                <span>{{ getProductMeta(product) }}</span>
              </button>
              <div
                v-if="filteredProducts.length === 0"
                class="picker-empty"
              >
                Keine passenden Produkte gefunden
              </div>
            </div>
          </div>

          <label class="form-group">
            <span>Aktueller Bestand</span>
            <input
              :value="selectedProduct ? formatStockValue(selectedProduct) : '—'"
              type="text"
              disabled
            >
          </label>

          <label class="form-group">
            <span>Neuer Bestand</span>
            <input
              v-model.number="productTargetStock"
              type="number"
              min="0"
              step="1"
              :disabled="selectedProduct?.is_unlimited_stock"
              placeholder="0"
            >
          </label>

          <label class="form-group form-group--full">
            <span>Grund der Korrektur</span>
            <input
              v-model.trim="productCorrectionReason"
              type="text"
              maxlength="255"
              placeholder="z. B. Inventurkorrektur"
            >
          </label>
        </div>

        <div
          v-if="selectedProduct"
          class="preview-card"
        >
          <div>
            <span class="preview-label">Differenz</span>
            <strong>{{ productDelta }}</strong>
          </div>
          <div>
            <span class="preview-label">Ausführender Benutzer</span>
            <strong>{{ authStore.user?.username || '—' }}</strong>
          </div>
        </div>

        <p
          v-if="selectedProduct?.is_unlimited_stock"
          class="inline-hint"
        >
          Produkte mit unendlichem Bestand benötigen keine Korrekturbuchung.
        </p>

        <div class="action-row">
          <button
            class="btn btn-success"
            type="button"
            :disabled="!canSubmitProductCorrection || isSubmitting"
            @click="submitProductCorrection"
          >
            Bestand korrigieren
          </button>
        </div>

        <div class="history-block">
          <div class="section-header section-header--compact">
            <div>
              <h3>Historie</h3>
              <p>Alle Korrekturbuchungen für Produkte.</p>
            </div>
          </div>

          <div class="history-table-wrapper">
            <table class="history-table">
              <thead>
                <tr>
                  <th>Datum</th>
                  <th>Produkt</th>
                  <th>Altbestand</th>
                  <th>Neubestand</th>
                  <th>Differenz</th>
                  <th>Grund</th>
                  <th>Benutzer</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="log in productLogs"
                  :key="`product-${log.id}`"
                >
                  <td>{{ formatTimestamp(log.created_at) }}</td>
                  <td>{{ log.product_name }}</td>
                  <td>{{ log.old_stock_quantity }}</td>
                  <td>{{ log.new_stock_quantity }}</td>
                  <td>{{ formatSignedNumber(log.change_quantity) }}</td>
                  <td>{{ log.reason }}</td>
                  <td>{{ log.executed_by_username }}</td>
                </tr>
                <tr v-if="productLogs.length === 0">
                  <td
                    colspan="7"
                    class="empty-state-cell"
                  >
                    Noch keine Bestands-Korrekturen vorhanden
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import apiService from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useMemberStore } from '@/stores/member'
import { useNotificationStore } from '@/stores/notification'
import { useProductStore } from '@/stores/product'
import { formatBalance } from '@/services/utils'
import { getMemberFullName, getMemberSearchText } from '@/services/member'

const authStore = useAuthStore()
const memberStore = useMemberStore()
const productStore = useProductStore()
const notificationStore = useNotificationStore()

const subTabs = [
  { id: 'members', label: 'Mitglieder', icon: '👥' },
  { id: 'products', label: 'Produkte', icon: '📦' },
]

const activeTab = ref('members')
const selectedMemberId = ref(null)
const selectedProductId = ref(null)
const memberSearch = ref('')
const productSearch = ref('')
const memberTargetBalanceEuro = ref(null)
const productTargetStock = ref(null)
const memberCorrectionReason = ref('')
const productCorrectionReason = ref('')
const memberLogs = ref([])
const productLogs = ref([])
const isSubmitting = ref(false)

const selectedMember = computed(() => (
  memberStore.members.find(member => member.id === Number(selectedMemberId.value)) || null
))

const selectedProduct = computed(() => (
  productStore.products.find(product => product.id === Number(selectedProductId.value)) || null
))

const filteredMembers = computed(() => {
  const search = memberSearch.value.trim().toLowerCase()

  if (!search) {
    return memberStore.members
  }

  return memberStore.members.filter(member => getMemberSearchText(member).includes(search))
})

const buildProductSearchText = (product) => [product?.name, product?.warengruppe]
  .filter(Boolean)
  .join(' ')
  .toLowerCase()

const filteredProducts = computed(() => {
  const search = productSearch.value.trim().toLowerCase()

  if (!search) {
    return productStore.products
  }

  return productStore.products.filter(product => buildProductSearchText(product).includes(search))
})

const memberTargetBalanceCents = computed(() => (
  memberTargetBalanceEuro.value === null || memberTargetBalanceEuro.value === ''
    ? null
    : Math.round(Number(memberTargetBalanceEuro.value) * 100)
))

const memberDeltaCents = computed(() => {
  if (!selectedMember.value || memberTargetBalanceCents.value === null) {
    return 0
  }
  return memberTargetBalanceCents.value - selectedMember.value.balance_cents
})

const productDelta = computed(() => {
  if (!selectedProduct.value || productTargetStock.value === null || selectedProduct.value.is_unlimited_stock) {
    return '—'
  }
  return formatSignedNumber(Number(productTargetStock.value) - Number(selectedProduct.value.stock_quantity))
})

const canSubmitMemberCorrection = computed(() => (
  !!selectedMember.value &&
  memberTargetBalanceCents.value !== null &&
  memberTargetBalanceCents.value >= 0 &&
  memberTargetBalanceCents.value !== selectedMember.value.balance_cents
))

const canSubmitProductCorrection = computed(() => (
  !!selectedProduct.value &&
  !selectedProduct.value.is_unlimited_stock &&
  productTargetStock.value !== null &&
  Number.isInteger(Number(productTargetStock.value)) &&
  Number(productTargetStock.value) >= 0 &&
  Number(productTargetStock.value) !== Number(selectedProduct.value.stock_quantity)
))

const formatTimestamp = (value) => new Date(value).toLocaleString('de-DE', {
  dateStyle: 'short',
  timeStyle: 'medium',
})

const formatSignedNumber = (value) => {
  const numericValue = Number(value || 0)
  return `${numericValue > 0 ? '+' : ''}${numericValue}`
}

const formatStockValue = (product) => (product?.is_unlimited_stock ? '∞' : `${product?.stock_quantity ?? 0}`)

const getProductMeta = (product) => {
  if (!product) return '—'

  const parts = []
  if (product.warengruppe) {
    parts.push(product.warengruppe)
  }
  parts.push(product.is_unlimited_stock ? '∞ Bestand' : `${product.stock_quantity ?? 0} Stück`)
  return parts.join(' · ')
}

const ensureSelections = () => {
  if (!selectedMember.value && memberStore.members.length > 0) {
    selectedMemberId.value = memberStore.members[0].id
  }
  if (!selectedProduct.value && productStore.products.length > 0) {
    selectedProductId.value = productStore.products[0].id
  }
}

const loadLogs = async () => {
  const [memberResponse, productResponse] = await Promise.all([
    apiService.get('/members/balance-corrections'),
    apiService.get('/products/stock-corrections'),
  ])
  memberLogs.value = memberResponse.data
  productLogs.value = productResponse.data
}

const initialize = async () => {
  await Promise.all([
    memberStore.getMembers(),
    productStore.getProducts(),
    loadLogs(),
  ])
  ensureSelections()
}

const submitMemberCorrection = async () => {
  if (!canSubmitMemberCorrection.value) return

  isSubmitting.value = true
  try {
    await apiService.post(`/members/${selectedMember.value.id}/balance-correction`, {
      new_balance_cents: memberTargetBalanceCents.value,
      reason: memberCorrectionReason.value || null,
    })
    await Promise.all([memberStore.getMembers(), loadLogs()])
    ensureSelections()
    memberTargetBalanceEuro.value = selectedMember.value ? selectedMember.value.balance_cents / 100 : null
    memberCorrectionReason.value = ''
    notificationStore.success('Guthaben erfolgreich korrigiert')
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Guthaben-Korrektur fehlgeschlagen')
  } finally {
    isSubmitting.value = false
  }
}

const submitProductCorrection = async () => {
  if (!canSubmitProductCorrection.value) return

  isSubmitting.value = true
  try {
    await apiService.post(`/products/${selectedProduct.value.id}/stock-correction`, {
      new_stock_quantity: Number(productTargetStock.value),
      reason: productCorrectionReason.value || null,
    })
    await Promise.all([productStore.getProducts(), loadLogs()])
    ensureSelections()
    productTargetStock.value = selectedProduct.value ? selectedProduct.value.stock_quantity : null
    productCorrectionReason.value = ''
    notificationStore.success('Bestand erfolgreich korrigiert')
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Bestands-Korrektur fehlgeschlagen')
  } finally {
    isSubmitting.value = false
  }
}

watch(selectedMember, (member) => {
  memberTargetBalanceEuro.value = member ? member.balance_cents / 100 : null
}, { immediate: true })

watch(selectedProduct, (product) => {
  productTargetStock.value = product && !product.is_unlimited_stock ? product.stock_quantity : null
}, { immediate: true })

onMounted(() => {
  initialize().catch(() => {
    notificationStore.error('Korrekturbuchungen konnten nicht geladen werden')
  })
})
</script>

<style scoped lang="scss">
.admin-corrections {
  --border: #e2e8f0;
  padding: 1.25rem;
  background: white;
  min-height: 100%;
}

.page-header {
  margin-bottom: 1rem;

  h2 {
    margin: 0;
    color: #1e293b;
  }
}

.page-subtitle {
  color: #64748b;
  margin-top: 0.25rem;
}

.page-note {
  color: #64748b;
  margin-top: 0.35rem;
  font-size: 0.86rem;
}

.correction-subtabs {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin: 0 0 1rem;
  padding: 0.4rem 0 0.75rem;
  background: white;
  border-bottom: 1px solid var(--border);
}

.subtab-button {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.5rem 0.85rem;
  border: 1px solid color-mix(in srgb, var(--app-banner-color) 70%, #000 25%);
  border-radius: 8px;
  background: color-mix(in srgb, var(--app-banner-color) 14%, white);
  color: #334155;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;

  &.active,
  &:hover {
    background: var(--app-highlight-color);
    border-color: var(--app-highlight-color);
    color: var(--app-highlight-contrast);
  }
}

.subtab-icon {
  font-size: 0.95rem;
}

.correction-content {
  display: grid;
  gap: 1rem;
}

.panel-card {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #fff;
  padding: 1rem;
}

.section-header {
  margin-bottom: 1rem;

  h3 {
    margin: 0;
    color: #1e293b;
  }

  p {
    margin: 0.3rem 0 0;
    color: #64748b;
  }
}

.section-header--compact {
  margin-bottom: 0.75rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.85rem;
}

.form-group--full {
  grid-column: 1 / -1;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  color: #334155;
  font-weight: 600;

  input {
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.75rem 0.9rem;
    font-size: 0.95rem;
  }
}

.picker-list {
  display: grid;
  gap: 0.5rem;
  max-height: 240px;
  overflow-y: auto;
  padding: 0.35rem;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #f8fafc;
}

.picker-item {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  align-items: flex-start;
  padding: 0.75rem 0.85rem;
  border: 1px solid transparent;
  border-radius: 10px;
  background: white;
  color: #1e293b;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;

  span {
    color: #64748b;
    font-size: 0.86rem;
  }

  &:hover,
  &.active {
    border-color: var(--app-highlight-color);
    background: color-mix(in srgb, var(--app-highlight-color) 12%, white);
  }
}

.picker-empty {
  padding: 0.9rem;
  text-align: center;
  color: #64748b;
}

.preview-card {
  margin-top: 1rem;
  padding: 0.85rem 1rem;
  border-radius: 10px;
  background: #f8fafc;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}

.preview-label {
  display: block;
  font-size: 0.8rem;
  color: #64748b;
  margin-bottom: 0.2rem;
}

.inline-hint {
  margin: 1rem 0 0;
  color: #64748b;
}

.action-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 1rem;
}

.history-block {
  margin-top: 1.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--border);
}

.history-table-wrapper {
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: 10px;
}

.history-table {
  width: 100%;
  border-collapse: collapse;

  th,
  td {
    padding: 0.8rem 0.85rem;
    border-bottom: 1px solid var(--border);
    text-align: left;
  }

  th {
    background: #f8fafc;
    color: #64748b;
    font-size: 0.78rem;
    text-transform: uppercase;
  }
}

.empty-state-cell {
  text-align: center !important;
  color: #64748b;
}

@media (max-width: 700px) {
  .admin-corrections {
    padding: 1rem;
  }

  .action-row {
    justify-content: stretch;

    .btn {
      width: 100%;
    }
  }
}
</style>
