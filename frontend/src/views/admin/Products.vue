<template>
  <div class="admin-products">
    <div class="page-header">
      <div>
        <h2>Produktverwaltung</h2>
        <p class="page-subtitle">Produkte, Preise und Lagerbestände im gleichen Layout wie die Mitgliederverwaltung pflegen.</p>
      </div>
      <button class="btn btn-primary" @click="openCreateModal">
        <span class="icon">+</span> Neues Produkt
      </button>
    </div>

    <div v-if="productStore.isLoading" class="loading-state">
      <div class="spinner"></div>
      <p>Daten werden geladen...</p>
    </div>

    <div v-else>
      <div class="table-toolbar">
        <input
          v-model="productSearch"
          type="text"
          placeholder="Nach Produktname suchen..."
          class="search-input"
        >
      </div>
      <div class="products-table-wrapper">
        <table class="products-table">
          <thead>
            <tr>
              <th>Bild</th>
              <th>Name</th>
              <th>Warengruppe</th>
              <th>Preis</th>
              <th>Mitgliedspreis</th>
              <th>Lager</th>
              <th class="text-right">Aktionen</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="product in filteredProducts" :key="product.id">
              <td class="product-image-cell">
                <div class="product-thumb-frame">
                  <img
                    v-if="product.image_path"
                    :src="`/api/products/${product.id}/image`"
                    :alt="product.name"
                    class="product-thumb"
                  >
                  <span v-else class="product-thumb-placeholder">Bild</span>
                </div>
              </td>
              <td>
                <div class="product-name-cell">
                  <span class="font-bold">{{ product.name }}</span>
                  <div class="product-badges">
                    <span v-if="hasMemberPrice(product)" class="badge badge-info">Rabatt</span>
                    <span v-if="product.is_unlimited_stock" class="badge badge-dark">∞</span>
                  </div>
                </div>
              </td>
              <td>{{ product.warengruppe || '—' }}</td>
              <td>{{ formatPrice(product.price_cents) }}</td>
              <td>
                <span :class="['badge', hasMemberPrice(product) ? 'badge-success' : 'badge-light']">
                  {{ hasMemberPrice(product) ? formatPrice(product.member_price_cents) : 'Kein Sonderpreis' }}
                </span>
              </td>
              <td>
                <span :class="['badge', product.is_unlimited_stock ? 'badge-dark' : (product.stock_quantity > 0 ? 'badge-success' : 'badge-danger')]">
                  {{ product.is_unlimited_stock ? '∞' : product.stock_quantity }}
                </span>
              </td>
              <td class="text-right">
                <div class="action-cell">
                  <button class="btn-action" @click="editProduct(product)">Bearbeiten</button>
                  <button class="btn-action btn-action-danger" @click="deleteProduct(product.id)">Löschen</button>
                </div>
              </td>
            </tr>
            <tr v-if="filteredProducts.length === 0">
              <td colspan="7" class="empty-state-cell">Keine Produkte gefunden</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <ProductModal
      :show="showProductModal"
      :editing-id="editingId"
      :editing-product="editingProduct"
      :warengruppe-options="warengruppeOptions"
      @close="closeProductModal"
      @save="onProductSave"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useProductStore } from '@/stores/product'
import { useNotificationStore } from '@/stores/notification'
import { formatPrice } from '@/services/utils'
import ProductModal from './modal/ProductModal.vue'

const productStore = useProductStore()
const notificationStore = useNotificationStore()

const showProductModal = ref(false)
const editingId = ref(null)
const editingProduct = ref(null)
const productSearch = ref('')

const hasMemberPrice = (product) => product.member_price_cents !== null && product.member_price_cents !== undefined

const getProductSearchText = (product) => [
  product?.name,
  product?.warengruppe,
  product?.description,
  product?.stock_quantity,
  product?.price_cents,
  product?.member_price_cents,
]
  .filter(value => value !== null && value !== undefined && value !== '')
  .join(' ')
  .toLowerCase()

const filteredProducts = computed(() => {
  const search = productSearch.value.trim().toLowerCase()

  if (!search) {
    return productStore.products
  }

  return productStore.products.filter(product => getProductSearchText(product).includes(search))
})

const warengruppeOptions = computed(() => (
  [...new Set(
    productStore.products
      .map(product => product?.warengruppe?.trim())
      .filter(Boolean),
  )].sort((left, right) => left.localeCompare(right, 'de'))
))

const deleteProduct = async (productId) => {
  if (confirm('Wirklich löschen?')) {
    const result = await productStore.deleteProduct(productId)

    if (result) {
      if (editingId.value === productId) {
        closeProductModal()
      }
      notificationStore.success('Produkt gelöscht')
    } else {
      notificationStore.error(productStore.error || 'Fehler beim Löschen')
    }
  }
}

const openCreateModal = () => {
  editingId.value = null
  editingProduct.value = null
  showProductModal.value = true
}

const closeProductModal = () => {
  showProductModal.value = false
  editingId.value = null
  editingProduct.value = null
}

const editProduct = (product) => {
  editingId.value = product.id
  editingProduct.value = product
  showProductModal.value = true
}

const onProductSave = async (payload) => {
  if (editingId.value) {
    const imageUploadSuccess = await uploadImagePayload(editingId.value, payload)
    if (!imageUploadSuccess && payload.imageFile) return

    const result = await productStore.updateProduct(editingId.value, {
      name: payload.name,
      warengruppe: payload.warengruppe || null,
      price_cents: payload.price_cents,
      member_price_cents: payload.member_price_cents,
      stock_quantity: payload.stock_quantity,
      is_unlimited_stock: payload.is_unlimited_stock,
      is_variable_price: payload.is_variable_price,
    })

    if (result) {
      notificationStore.success('Produkt aktualisiert')
      closeProductModal()
    } else {
      notificationStore.error(productStore.error)
    }
  } else {
    const result = await productStore.createProduct({
      name: payload.name,
      warengruppe: payload.warengruppe || null,
      price_cents: payload.price_cents,
      member_price_cents: payload.member_price_cents,
      stock_quantity: payload.stock_quantity,
      is_unlimited_stock: payload.is_unlimited_stock,
      is_variable_price: payload.is_variable_price,
    })

    if (result) {
      if (payload.imageFile) {
        const imageUploadSuccess = await uploadImagePayload(result.id, payload)
        if (!imageUploadSuccess) {
          notificationStore.warning('Produkt erstellt, aber Bild-Upload fehlgeschlagen')
        } else {
          notificationStore.success('Produkt mit Bild erstellt')
        }
      } else {
        notificationStore.success('Produkt erstellt')
      }
      closeProductModal()
    } else {
      notificationStore.error(productStore.error)
    }
  }
}

const uploadImagePayload = async (productId, payload) => {
  if (!payload.imageFile) return true

  if (payload.cropIsNewUpload && payload.originalImageFile) {
    try {
      const origFormData = new FormData()
      origFormData.append('file', payload.originalImageFile)
      await fetch(`/api/products/${productId}/original-image`, {
        method: 'POST',
        body: origFormData,
        credentials: 'include',
      })
    } catch (err) {
      console.error('Original image upload error:', err)
    }
  }

  try {
    const formDataUpload = new FormData()
    formDataUpload.append('file', payload.imageFile)
    const response = await fetch(`/api/products/${productId}/image`, {
      method: 'POST',
      body: formDataUpload,
      credentials: 'include',
    })
    if (response.ok) return true
    notificationStore.error('Bild-Upload fehlgeschlagen')
    return false
  } catch (error) {
    console.error('Image upload error:', error)
    notificationStore.error('Fehler beim Bild-Upload')
    return false
  }
}

onMounted(async () => {
  await productStore.getProducts()
})
</script>

<style scoped lang="scss">
.admin-products {
  --primary: #3b82f6;
  --success: #10b981;
  --bg-main: #f8fafc;
  --border: #e2e8f0;
  padding: 1.5rem;
  background: white;
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;

  h2 {
    font-size: 1.5rem;
    color: #1e293b;
  }
}

.page-subtitle,
.modal-subtitle {
  color: #64748b;
}

.page-subtitle {
  margin-top: 0.25rem;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 3rem 1rem;
  color: #64748b;
}

.spinner {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  border: 3px solid #e2e8f0;
  border-top-color: var(--primary);
  animation: spin 0.8s linear infinite;
}

.table-toolbar {
  margin-bottom: 1rem;
}

.search-input {
  width: 100%;
  padding: 0.85rem 1rem;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 0.95rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;

  &:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
  }
}

.products-table-wrapper {
  background: white;
  border-radius: 12px;
  border: 1px solid var(--border);
  overflow-x: auto;
  overflow-y: hidden;
}

.products-table {
  width: 100%;
  min-width: 760px;
  border-collapse: collapse;

  th {
    background: #f1f5f9;
    padding: 1rem;
    font-size: 0.8rem;
    text-transform: uppercase;
    color: #64748b;
    text-align: left;
  }

  td {
    padding: 1rem;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
  }
}

.text-right {
  text-align: right;
}

.empty-state-cell {
  text-align: center;
  color: #64748b;
}

.action-cell {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
  flex-wrap: wrap;
  white-space: nowrap;
  width: 100%;
}

.font-bold {
  font-weight: 600;
}

.product-name-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.product-badges {
  display: inline-flex;
  gap: 0.35rem;
}

.product-image-cell {
  width: 84px;
}

.product-thumb-frame {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  overflow: hidden;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
}

.product-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-thumb-placeholder {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 600;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.3rem 0.7rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
}

.badge-success {
  background: #dcfce7;
  color: #166534;
}

.badge-light {
  background: #f1f5f9;
  color: #475569;
}

.badge-info {
  background: #dbeafe;
  color: #1d4ed8;
}

.badge-danger {
  background: #fee2e2;
  color: #b91c1c;
}

.badge-dark {
  background: #e2e8f0;
  color: #0f172a;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-card {
  background: white;
  width: 100%;
  max-width: 1050px;
  max-height: 90vh;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  gap: 1rem;

  h3 {
    margin: 0;
    font-size: 1.25rem;
  }
}

.modal-body-layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  overflow: hidden;
}

.modal-sidebar {
  padding: 1.5rem;
  background: var(--bg-main);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  overflow-y: auto;
}

.product-image-panel,
.sidebar-info-box {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.modal-form-content {
  padding: 1.5rem;
  overflow-y: auto;
  max-height: calc(90vh - 160px);
}

.avatar-display {
  width: 150px;
  height: 150px;
  margin: 0 auto;
  border-radius: 20px;
  background: #fff;
  border: 2px dashed #cbd5e1;
  overflow: hidden;
}

.profile-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 1rem;
  font-size: 0.8rem;
  color: #94a3b8;
}

.upload-button {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  padding: 0.65rem 1rem;
  border-radius: 8px;
  background: white;
  border: 1px solid var(--border);
  cursor: pointer;
  font-weight: 600;
  color: #334155;
}

.checkbox-card,
.summary-card {
  padding: 0.9rem 1rem;
  background: white;
  border: 1px solid var(--border);
  border-radius: 10px;
}

.checkbox-card {
  display: flex;
  gap: 0.75rem;
  cursor: pointer;
}

.checkbox-content {
  display: flex;
  flex-direction: column;

  .label {
    font-weight: 600;
    font-size: 0.9rem;
  }

  .desc {
    font-size: 0.75rem;
    color: #64748b;
  }
}

.summary-card {
  background: #ecfdf5;
  border-color: #a7f3d0;

  .label {
    font-size: 0.7rem;
    text-transform: uppercase;
    color: #065f46;
    font-weight: 700;
  }

  .value {
    display: block;
    margin-top: 0.35rem;
    font-size: 1.3rem;
    font-weight: 700;
    color: #047857;
  }
}

.form-section {
  margin-bottom: 2rem;

  h4 {
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
  }
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  margin-bottom: 1rem;

  label {
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    margin-bottom: 0.4rem;
    color: #1e293b;
  }

  input {
    width: 100%;
    padding: 0.6rem 0.8rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.95rem;

    &:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
  }
}

.btn {
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-success {
  background: var(--success);
  color: white;
}

.btn-secondary {
  background: #e2e8f0;
  color: #475569;
}

.btn-action {
  border: 1px solid var(--border);
  background: white;
  color: #334155;
  padding: 0.45rem 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.btn-action-danger {
  border-color: #fecaca;
  color: #b91c1c;
}

.modal-close {
  border: none;
  background: transparent;
  font-size: 1.6rem;
  line-height: 1;
  cursor: pointer;
  color: #6b7280;
}

.modal-footer {
  grid-column: 1 / -1;
  padding: 1.5rem;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

@media (max-width: 768px) {
  .modal-body-layout,
  .form-row {
    grid-template-columns: 1fr;
  }

  .modal-sidebar {
    border-right: none;
    border-bottom: 1px solid var(--border);
  }
}

@media (max-width: 640px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .modal-footer,
  .action-cell {
    flex-direction: column;
  }

  .btn,
  .btn-action {
    width: 100%;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

// ── Crop editor & card preview ────────────────────────────────────────────────
.image-editor-label {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
  margin: 0;
}

.image-editor-hint {
  font-size: 0.72rem;
  color: #94a3b8;
  margin: -0.4rem 0 0;
}

.preview-label {
  margin-top: 0.5rem;
}

// The crop frame: fixed size, clips the image
.crop-frame {
  width: 320px;
  height: 213px;
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  border: 2px solid var(--primary);
  background: #e2e8f0;
  flex-shrink: 0;
  touch-action: none;
  user-select: none;
}

.crop-source-img {
  display: block;
  max-width: none;
  max-height: none;
}

.crop-zoom-row {
  display: flex;
  align-items: center;
  gap: 6px;

  .zoom-icon {
    font-size: 1rem;
    color: #64748b;
    font-weight: 700;
    line-height: 1;
    cursor: default;
    user-select: none;
  }

  .zoom-pct {
    font-size: 0.72rem;
    color: #64748b;
    min-width: 2.6rem;
    text-align: right;
  }
}

.zoom-slider {
  flex: 1;
  cursor: pointer;
  accent-color: var(--primary);
}

.btn-crop-reset {
  align-self: flex-start;
  padding: 0.3rem 0.75rem;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: white;
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
  cursor: pointer;

  &:hover {
    background: #f1f5f9;
  }
}

.btn-crop-restore {
  border-color: #fcd34d;
  color: #92400e;
  background: #fffbeb;

  &:hover {
    background: #fef3c7;
  }
}

.crop-action-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  align-self: flex-start;
}

// Card preview mimics .product-btn from Kasse.vue
.kasse-card-preview {
  width: 180px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.07);

  .card-img {
    height: 62px;
    overflow: hidden;
    background: #eef1f7;
    flex-shrink: 0;
    position: relative;
  }

  .preview-crop-img {
    display: block;
    max-width: none;
    max-height: none;
  }

  .card-badge {
    position: absolute;
    top: 3px;
    left: 3px;
    z-index: 1;
    font-size: 9px;
    font-weight: 800;
    padding: 2px 4px;
    border-radius: 3px;
    letter-spacing: 0.04em;
    line-height: 1.4;

    &.discount-badge {
      background: #fffbeb;
      color: #d97706;
    }
  }

  .card-body {
    padding: 5px 6px 6px;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .card-name {
    font-size: .72rem;
    font-weight: 700;
    line-height: 1.2;
    color: #111827;
  }

  .card-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: auto;
  }

  .card-price {
    font-size: .82rem;
    font-weight: 800;
    color: var(--primary);
    letter-spacing: -0.02em;
  }

  .card-stock {
    font-size: .64rem;
    color: #64748b;
    font-weight: 500;
  }
}

.crop-file-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.crop-sidebar-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.btn-crop-open {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  padding: 0.65rem 1rem;
  border-radius: 8px;
  background: var(--primary);
  border: none;
  cursor: pointer;
  font-weight: 600;
  color: white;
  font-size: 0.9rem;

  &:hover {
    background: #2563eb;
  }
}

// Crop sub-modal
.crop-modal-overlay {
  z-index: 1001;
}

.crop-modal-card {
  --success: #10b981;
  --border: #e2e8f0;
  --primary: #3b82f6;
  background: white;
  width: 100%;
  max-width: 480px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.35);
}

.crop-modal-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.crop-modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
}
</style>
