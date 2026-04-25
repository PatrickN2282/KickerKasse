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

    <div v-else class="products-table-wrapper">
      <table class="products-table">
        <thead>
          <tr>
            <th>Bild</th>
            <th>Name</th>
            <th>Preis</th>
            <th>Mitgliedspreis</th>
            <th>Lager</th>
            <th class="text-right">Aktionen</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in productStore.products" :key="product.id">
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
            <td class="font-bold">{{ product.name }}</td>
            <td>{{ formatPrice(product.price_cents) }}</td>
            <td>
              <span :class="['badge', product.member_price_cents ? 'badge-success' : 'badge-light']">
                {{ product.member_price_cents ? formatPrice(product.member_price_cents) : 'Kein Sonderpreis' }}
              </span>
            </td>
            <td>
              <span :class="['badge', product.stock_quantity > 0 ? 'badge-success' : 'badge-danger']">
                {{ product.stock_quantity }}
              </span>
            </td>
            <td class="text-right action-cell">
              <button class="btn-icon" @click="editProduct(product)" title="Bearbeiten">✏️</button>
              <button class="btn-icon btn-icon-danger" @click="deleteProduct(product.id)" title="Löschen">🗑️</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showProductModal" class="modal-overlay" @click.self="closeProductModal">
      <div class="modal-card">
        <header class="modal-header">
          <div>
            <h3>{{ editingId ? 'Produkt bearbeiten' : 'Neues Produkt anlegen' }}</h3>
            <p class="modal-subtitle">Pflichtangaben, Preise und Bild im angepassten Admin-Layout verwalten.</p>
          </div>
          <button class="modal-close" @click="closeProductModal">×</button>
        </header>

        <form class="modal-body-layout" @submit.prevent="handleSaveProduct">
          <aside class="modal-sidebar">
            <div class="product-image-panel">
              <div class="avatar-display">
                <img v-if="imagePreview" :src="imagePreview" :alt="formData.name || 'Produktbild'" class="profile-img">
                <div v-else class="photo-placeholder">
                  <span>Bild hochladen</span>
                </div>
              </div>

              <label class="upload-button">
                Bild auswählen
                <input id="image" type="file" accept="image/*" hidden @change="handleImageUpload">
              </label>
            </div>

            <div class="sidebar-info-box">
              <label class="checkbox-card">
                <input id="discountable" v-model="formData.discountable" type="checkbox">
                <div class="checkbox-content">
                  <span class="label">Rabattfähig</span>
                  <span class="desc">Mitgliederpreis kann an der Kasse verwendet werden.</span>
                </div>
              </label>

              <div class="summary-card">
                <span class="label">Lagerbestand</span>
                <span class="value">{{ formData.stock }}</span>
              </div>
            </div>
          </aside>

          <main class="modal-form-content">
            <section class="form-section">
              <h4>Allgemeine Informationen</h4>
              <div class="form-row">
                <div class="form-group">
                  <label for="name">Name*</label>
                  <input id="name" v-model="formData.name" type="text" required>
                </div>
                <div class="form-group">
                  <label for="stock">Lagerbestand*</label>
                  <input id="stock" v-model.number="formData.stock" type="number" min="0" required>
                </div>
              </div>
            </section>

            <section class="form-section">
              <h4>Preisgestaltung</h4>
              <div class="form-row">
                <div class="form-group">
                  <label for="price">Preis (€)*</label>
                  <input id="price" v-model.number="formData.price" type="number" step="0.01" required>
                </div>
                <div class="form-group">
                  <label for="member-price">Mitgliedspreis (€)</label>
                  <input id="member-price" v-model.number="formData.memberPrice" type="number" step="0.01">
                </div>
              </div>
            </section>
          </main>

          <footer class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeProductModal">Abbrechen</button>
            <button type="submit" class="btn btn-success">
              {{ editingId ? 'Änderungen speichern' : 'Produkt anlegen' }}
            </button>
          </footer>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useProductStore } from '@/stores/product'
import { useNotificationStore } from '@/stores/notification'
import { formatPrice } from '@/services/utils'

const productStore = useProductStore()
const notificationStore = useNotificationStore()

const showProductModal = ref(false)
const editingId = ref(null)
const imagePreview = ref(null)
const imageFile = ref(null)
const formData = reactive({
  name: '',
  price: 0,
  memberPrice: null,
  stock: 0,
  discountable: true,
})

const openCreateModal = () => {
  resetForm()
  showProductModal.value = true
}

const closeProductModal = () => {
  showProductModal.value = false
  resetForm()
}

const handleSaveProduct = async () => {
  if (editingId.value) {
    const imageUploadSuccess = await uploadImageToProduct(editingId.value)
    if (!imageUploadSuccess && imageFile.value) {
      return
    }

    const result = await productStore.updateProduct(editingId.value, {
      name: formData.name,
      price_cents: Math.round(formData.price * 100),
      member_price_cents: formData.memberPrice ? Math.round(formData.memberPrice * 100) : null,
      stock_quantity: formData.stock,
      is_discountable: formData.discountable,
    })

    if (result) {
      notificationStore.success('Produkt aktualisiert')
      resetForm()
    } else {
      notificationStore.error(productStore.error)
    }
  } else {
    const result = await productStore.createProduct({
      name: formData.name,
      price_cents: Math.round(formData.price * 100),
      member_price_cents: formData.memberPrice ? Math.round(formData.memberPrice * 100) : null,
      stock_quantity: formData.stock,
      is_discountable: formData.discountable,
    })

    if (result) {
      if (imageFile.value) {
        const imageUploadSuccess = await uploadImageToProduct(result.id)
        if (!imageUploadSuccess) {
          notificationStore.warning('Produkt erstellt, aber Bild-Upload fehlgeschlagen')
        } else {
          notificationStore.success('Produkt mit Bild erstellt')
        }
      } else {
        notificationStore.success('Produkt erstellt')
      }
      resetForm()
    } else {
      notificationStore.error(productStore.error)
    }
  }
}

const uploadImageToProduct = async (productId) => {
  if (!imageFile.value) return true

  try {
    const formDataUpload = new FormData()
    formDataUpload.append('file', imageFile.value)

    const response = await fetch(`/api/products/${productId}/image`, {
      method: 'POST',
      body: formDataUpload,
      credentials: 'include',
    })

    if (response.ok) {
      imageFile.value = null
      return true
    } else {
      notificationStore.error('Bild-Upload fehlgeschlagen')
      return false
    }
  } catch (error) {
    console.error('Image upload error:', error)
    notificationStore.error('Fehler beim Bild-Upload')
    return false
  }
}

const resetForm = () => {
  formData.name = ''
  formData.price = 0
  formData.memberPrice = null
  formData.stock = 0
  formData.discountable = true
  imageFile.value = null
  imagePreview.value = null
  editingId.value = null
  showProductModal.value = false
}

const editProduct = (product) => {
  editingId.value = product.id
  formData.name = product.name
  formData.price = product.price_cents / 100
  formData.memberPrice = product.member_price_cents ? product.member_price_cents / 100 : null
  formData.stock = product.stock_quantity
  formData.discountable = product.is_discountable
  imageFile.value = null
  imagePreview.value = product.image_path ? `/api/products/${product.id}/image` : null
  showProductModal.value = true
}

const handleImageUpload = (event) => {
  const file = event.target.files[0]
  if (file) {
    imageFile.value = file
    const reader = new FileReader()
    reader.onload = (e) => {
      imagePreview.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

const deleteProduct = async (productId) => {
  if (confirm('Wirklich löschen?')) {
    const result = await productStore.deleteProduct(productId)

    if (result) {
      if (editingId.value === productId) {
        resetForm()
      }
      notificationStore.success('Produkt gelöscht')
    } else {
      notificationStore.error(productStore.error || 'Fehler beim Löschen')
    }
  }
}

onMounted(async () => {
  await productStore.getProducts()
})
</script>

<style scoped lang="scss">
:root {
  --primary: #3b82f6;
  --success: #10b981;
  --danger: #ef4444;
  --bg-main: #f8fafc;
  --border: #e2e8f0;
}

.admin-products {
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

.action-cell {
  white-space: nowrap;
}

.font-bold {
  font-weight: 600;
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

.badge-danger {
  background: #fee2e2;
  color: #b91c1c;
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
  max-width: 900px;
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

.btn-icon {
  background: none;
  border: none;
  padding: 0.4rem;
  cursor: pointer;
  border-radius: 4px;

  &:hover {
    background: #f1f5f9;
  }

  &.btn-icon-danger:hover {
    background: #fee2e2;
  }
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

  .modal-footer {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
