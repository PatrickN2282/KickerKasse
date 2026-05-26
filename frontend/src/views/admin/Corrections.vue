<template>
  <div class="admin-corrections">
    <div class="page-header">
      <div class="page-header-title">
        <div class="title-row">
          <h2>Korrektur-Buchungen</h2>
          <span class="title-sep">|</span>
          <span class="page-subtitle">
            Guthaben und Lagerbestände ohne Bargeldfluss revisionssicher korrigieren.
          </span>
        </div>
        <p class="page-note">
          Korrekturen werden als separate Korrekturbuchungen dokumentiert und direkt im jeweiligen Bereich archiviert.
        </p>
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
    </div>

    <div class="correction-content">
      <!-- ── Mitglieder ──────────────────────────────── -->
      <section
        v-if="activeTab === 'members'"
        class="panel-card"
      >
        <div class="section-header">
          <div>
            <h3>Mitgliedsguthaben korrigieren</h3>
            <p>Zeile anklicken um eine Korrekturbuchung mit Altbestand, Neubestand und Zeitstempel zu erfassen.</p>
          </div>
        </div>

        <div class="table-toolbar">
          <input
            v-model.trim="memberSearch"
            type="text"
            placeholder="Nach Name oder Nummer filtern..."
            class="search-input"
          >
        </div>

        <div class="correction-table-wrapper">
          <table class="correction-slim-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Nr.</th>
                <th>Guthaben</th>
                <th class="text-right">Korrektur</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="member in filteredMembers"
                :key="member.id"
              >
                <td class="font-medium">{{ getMemberFullName(member) }}</td>
                <td class="text-muted">#{{ member.member_number }}</td>
                <td class="font-medium">{{ formatBalance(member.balance_cents) }}</td>
                <td class="text-right">
                  <button
                    class="btn-small btn-edit-inline"
                    type="button"
                    @click="openMemberCorrectionModal(member.id)"
                  >
                    ✏️
                  </button>
                </td>
              </tr>
              <tr v-if="filteredMembers.length === 0">
                <td
                  colspan="4"
                  class="empty-state-cell"
                >
                  Keine passenden Mitglieder gefunden
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="history-block">
          <div class="section-header section-header--compact">
            <div>
              <h3>Historie</h3>
              <p>Alle Korrekturbuchungen für Mitglieder.</p>
            </div>
          </div>

          <div class="correction-table-wrapper">
            <table class="correction-slim-table">
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

      <!-- ── Produkte ────────────────────────────────── -->
      <section
        v-else-if="activeTab === 'products'"
        class="panel-card"
      >
        <div class="section-header">
          <div>
            <h3>Warenbestand korrigieren</h3>
            <p>Zeile anklicken um eine Bestandskorrektur mit Altbestand, Neubestand und Zeitstempel zu erfassen.</p>
          </div>
        </div>

        <div class="table-toolbar">
          <input
            v-model.trim="productSearch"
            type="text"
            placeholder="Nach Produktname oder Warengruppe filtern..."
            class="search-input"
          >
        </div>

        <div class="correction-table-wrapper">
          <table class="correction-slim-table">
            <thead>
              <tr>
                <th>Produkt</th>
                <th>Warengruppe</th>
                <th>Bestand</th>
                <th class="text-right">Korrektur</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="product in filteredProducts"
                :key="product.id"
              >
                <td class="font-medium">{{ product.name }}</td>
                <td class="text-muted">{{ product.warengruppe || '—' }}</td>
                <td>
                  <span
                    v-if="product.is_unlimited_stock"
                    class="badge-unlimited"
                  >∞</span>
                  <span v-else>{{ product.stock_quantity }}</span>
                </td>
                <td class="text-right">
                  <button
                    class="btn-small btn-edit-inline"
                    type="button"
                    :disabled="product.is_unlimited_stock"
                    :title="product.is_unlimited_stock ? 'Kein Bestand für unbegrenzte Artikel' : ''"
                    @click="openProductCorrectionModal(product.id)"
                  >
                    ✏️
                  </button>
                </td>
              </tr>
              <tr v-if="filteredProducts.length === 0">
                <td
                  colspan="4"
                  class="empty-state-cell"
                >
                  Keine passenden Produkte gefunden
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="history-block">
          <div class="section-header section-header--compact">
            <div>
              <h3>Historie</h3>
              <p>Alle Korrekturbuchungen für Produkte.</p>
            </div>
          </div>

          <div class="correction-table-wrapper">
            <table class="correction-slim-table">
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

    <CorrectionModal
      :show="showCorrectionModal"
      :active-tab="activeTab"
      :selected-member="selectedMember"
      :selected-product="selectedProduct"
      :product-meta="getProductMeta(selectedProduct)"
      :member-target-balance-euro="memberTargetBalanceEuro"
      :product-target-stock="productTargetStock"
      :member-correction-reason="memberCorrectionReason"
      :product-correction-reason="productCorrectionReason"
      :member-delta-cents="memberDeltaCents"
      :product-delta="productDelta"
      :username="authStore.user?.username || ''"
      :is-submitting="isSubmitting"
      :can-submit-member-correction="canSubmitMemberCorrection"
      :can-submit-product-correction="canSubmitProductCorrection"
      @close="closeCorrectionModal"
      @update:member-target-balance-euro="memberTargetBalanceEuro = $event"
      @update:product-target-stock="productTargetStock = $event"
      @update:member-correction-reason="memberCorrectionReason = $event"
      @update:product-correction-reason="productCorrectionReason = $event"
      @submit-member="submitMemberCorrection"
      @submit-product="submitProductCorrection"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import CorrectionModal from '@/views/admin/modal/CorrectionModal.vue'
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

const getProductMeta = (product) => {
  if (!product) return '—'

  const parts = []
  if (product.warengruppe) {
    parts.push(product.warengruppe)
  }
  parts.push(product.is_unlimited_stock ? '∞ Bestand' : `${product.stock_quantity ?? 0} Stück`)
  return parts.join(' · ')
}

const showCorrectionModal = ref(false)

const openMemberCorrectionModal = (memberId) => {
  selectedMemberId.value = memberId
  showCorrectionModal.value = true
}

const openProductCorrectionModal = (productId) => {
  selectedProductId.value = productId
  showCorrectionModal.value = true
}

const closeCorrectionModal = () => {
  showCorrectionModal.value = false
  memberTargetBalanceEuro.value = selectedMember.value ? selectedMember.value.balance_cents / 100 : null
  memberCorrectionReason.value = ''
  productTargetStock.value = selectedProduct.value?.is_unlimited_stock === false
    ? (selectedProduct.value?.stock_quantity ?? null)
    : null
  productCorrectionReason.value = ''
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
    memberCorrectionReason.value = ''
    showCorrectionModal.value = false
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
    productCorrectionReason.value = ''
    showCorrectionModal.value = false
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
  padding: 0 1rem 0.75rem;
  background: var(--app-background-color);
  min-height: 100%;
}

.page-header {
  position: sticky;
  top: var(--finance-sticky-offset, 0px);
  z-index: 9;
  background: var(--app-background-color);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin: 0 -1rem 0.6rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.13);

  h2 {
    margin: 0;
    color: #333;
    font-size: 1.25rem;
  }
}

.page-header-title {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.title-row {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.title-sep {
  color: #aaa;
  font-weight: 300;
}

.page-subtitle {
  color: #64748b;
  margin: 0;
}

.page-note {
  color: #64748b;
  margin: 0;
  font-size: 0.86rem;
}

.correction-subtabs {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.subtab-button {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.5rem 0.85rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f1f5f9;
  color: #94a3b8;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: color-mix(in srgb, var(--app-banner-color) 14%, white);
    border-color: color-mix(in srgb, var(--app-banner-color) 70%, #000 25%);
    color: #334155;
  }

  &.active {
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
  border: 1px solid color-mix(in srgb, var(--app-background-color) 65%, #777);
  border-radius: 12px;
  background: color-mix(in srgb, var(--app-background-color) 55%, white);
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

.table-toolbar {
  margin-bottom: 0.6rem;
}

.search-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 0.9rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;

  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
  }
}

.correction-table-wrapper {
  background: color-mix(in srgb, var(--app-background-color) 30%, white);
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--app-background-color) 65%, #777);
  overflow-x: auto;
}

.correction-slim-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;

  thead {
    background: color-mix(in srgb, var(--app-background-color) 75%, white);
  }

  th,
  td {
    padding: 0.5rem 0.75rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }

  th {
    color: #475569;
    font-weight: 600;
    font-size: 0.8rem;
  }

  tr:last-child td {
    border-bottom: none;
  }

  tr:hover td {
    background: color-mix(in srgb, var(--app-background-color) 60%, white);
  }
}

.text-right {
  text-align: right !important;
}

.text-muted {
  color: #64748b;
}

.font-medium {
  font-weight: 600;
}

.badge-unlimited {
  background: #e2e8f0;
  color: #0f172a;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.88rem;
  font-weight: 600;
}

.btn-small {
  padding: 0.3rem 0.55rem;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 0.85rem;
  transition: background 0.15s;

  &:hover:not(:disabled) {
    background: #f1f5f9;
  }

  &:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }
}

.btn-edit-inline {
  border-color: #cbd5e1;
}

.history-block {
  margin-top: 1.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--border);
}

.empty-state-cell {
  text-align: center !important;
  color: #64748b;
  padding: 2rem 1rem !important;
}

@media (max-width: 700px) {
  .admin-corrections {
    padding: 0 1rem 1rem;
  }

  .action-row {
    justify-content: stretch;

    .btn {
      width: 100%;
    }
  }
}

</style>
