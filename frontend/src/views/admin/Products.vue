<template>
  <div class="admin-products">
    <div class="page-header">
      <h2>Produktverwaltung</h2>
      <button
        class="btn btn-primary"
        @click="openCreateModal"
      >
        Neues Produkt
      </button>
    </div>

    <div
      v-if="productStore.isLoading"
      class="loading"
    >
      Läuft...
    </div>
    <div
      v-else
      class="products-table"
    >
      <table>
        <thead>
          <tr>
            <th>Bild</th>
            <th>Name</th>
            <th>Preis</th>
            <th>Mitgliedspreis</th>
            <th>Lager</th>
            <th>Aktionen</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="product in productStore.products"
            :key="product.id"
          >
            <td class="product-image-cell">
              <img
                v-if="product.image_path"
                :src="`/api/products/${product.id}/image`"
                :alt="product.name"
                class="product-thumb"
              >
              <span
                v-else
                class="no-image"
              >Kein Bild</span>
            </td>
            <td>{{ product.name }}</td>
            <td>{{ formatPrice(product.price_cents) }}</td>
            <td>{{ product.member_price_cents ? formatPrice(product.member_price_cents) : '-' }}</td>
            <td>{{ product.stock_quantity }}</td>
            <td>
              <button
                class="btn-small"
                @click="editProduct(product)"
              >
                Bearbeiten
              </button>
              <button
                class="btn-small btn-danger"
                @click="deleteProduct(product.id)"
              >
                Löschen
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      v-if="showProductModal"
      class="modal-overlay"
      @click.self="closeProductModal"
    >
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ editingId ? 'Produkt bearbeiten' : 'Neues Produkt anlegen' }}</h3>
          <button
            class="modal-close"
            @click="closeProductModal"
          >
            ×
          </button>
        </div>

        <form
          class="form-section"
          @submit.prevent="handleSaveProduct"
        >
          <div class="form-group">
            <label for="name">Name*:</label>
            <input
              id="name"
              v-model="formData.name"
              type="text"
              class="form-input"
              required
            >
          </div>
          <div class="form-group">
            <label for="price">Preis (€)*:</label>
            <input
              id="price"
              v-model.number="formData.price"
              type="number"
              step="0.01"
              class="form-input"
              required
            >
          </div>
          <div class="form-group">
            <label for="member-price">Mitgliedspreis (€):</label>
            <input
              id="member-price"
              v-model.number="formData.memberPrice"
              type="number"
              step="0.01"
              class="form-input"
            >
          </div>
          <div class="form-group">
            <label for="stock">Lagerbestand*:</label>
            <input
              id="stock"
              v-model.number="formData.stock"
              type="number"
              min="0"
              class="form-input"
              required
            >
          </div>
          <div class="form-group">
            <label for="image">Bild:</label>
            <input
              id="image"
              type="file"
              accept="image/*"
              class="form-input"
              @change="handleImageUpload"
            >
            <div
              v-if="imagePreview"
              class="image-preview"
            >
              <img
                :src="imagePreview"
                :alt="formData.name"
                style="max-width: 150px; max-height: 150px;"
              >
            </div>
          </div>
          <div class="form-group">
            <label for="discountable">
              <input
                id="discountable"
                v-model="formData.discountable"
                type="checkbox"
              >
              Rabattfähig
            </label>
          </div>
          <div class="form-buttons">
            <button
              type="submit"
              class="btn btn-success"
            >
              {{ editingId ? 'Aktualisieren' : 'Erstellen' }}
            </button>
            <button
              type="button"
              class="btn btn-secondary"
              @click="closeProductModal"
            >
              Abbrechen / Zurück
            </button>
          </div>
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
    // Upload image first if exists
    const imageUploadSuccess = await uploadImageToProduct(editingId.value)
    if (!imageUploadSuccess && imageFile.value) {
      return
    }
    
    // Update existing product
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
    // Create new product
    const result = await productStore.createProduct({
      name: formData.name,
      price_cents: Math.round(formData.price * 100),
      member_price_cents: formData.memberPrice ? Math.round(formData.memberPrice * 100) : null,
      stock_quantity: formData.stock,
      is_discountable: formData.discountable,
    })

    if (result) {
      // Upload image after creation
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
  if (!imageFile.value) return true // No image to upload
  
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
  imagePreview.value = product.image ? 'data:image/jpeg;base64,' + product.image : null
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
.admin-products {
  background: white;
  padding: 2rem;
  border-radius: 8px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.form-section {
  display: grid;
  gap: 1rem;
}

.form-group {
  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
  }

  .form-input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;

    &:focus {
      outline: none;
      border-color: #1976d2;
    }
  }

  input[type="checkbox"] {
    margin-right: 0.5rem;
  }
}

.form-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
}

.products-table {
  overflow-x: auto;
  margin-top: 2rem;

  table {
    width: 100%;
    border-collapse: collapse;

    th {
      background: #f0f0f0;
      padding: 1rem;
      text-align: left;
      font-weight: 600;
      border-bottom: 2px solid #ddd;
    }

    td {
      padding: 1rem;
      border-bottom: 1px solid #ddd;
    }

    tr:hover {
      background: #fafafa;
    }
  }
}

.btn-small {
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
  background: #2196f3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 0.5rem;

  &:hover {
    background: #0b7dda;
  }

  &.btn-danger {
    background: #f44336;

    &:hover {
      background: #da190b;
    }
  }
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}

.btn-primary {
  background: #1976d2;
  color: white;

  &:hover {
    background: #1565c0;
  }
}

.btn-success {
  background: #4caf50;
  color: white;

  &:hover {
    background: #45a049;
  }
}

.btn-secondary {
  background: #6b7280;
  color: white;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #999;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 1000;
}

.modal-card {
  width: min(100%, 520px);
  max-height: calc(100vh - 2rem);
  overflow-y: auto;
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.22);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.modal-close {
  border: none;
  background: transparent;
  font-size: 1.6rem;
  line-height: 1;
  cursor: pointer;
  color: #6b7280;
}

.product-image-cell {
  padding: 0.5rem 1rem !important;
  text-align: center;

  .product-thumb {
    width: 50px;
    height: 50px;
    object-fit: contain;
    border-radius: 4px;
    border: 1px solid #ddd;
  }

  .no-image {
    font-size: 0.85rem;
    color: #999;
  }
}
</style>
