<template>
  <div class="admin-products">
    <h2>Produktverwaltung</h2>

    <button @click="showForm = !showForm" class="btn btn-primary">
      {{ showForm ? 'Abbrechen / Zurück' : 'Neues Produkt' }}
    </button>

    <form v-if="showForm" @submit.prevent="handleSaveProduct" class="form-section">
      <h3>{{ editingId ? 'Produkt bearbeiten' : 'Neues Produkt' }}</h3>
      <div class="form-group">
        <label for="name">Name*:</label>
        <input v-model="formData.name" id="name" type="text" class="form-input" required />
      </div>
      <div class="form-group">
        <label for="price">Preis (€)*:</label>
        <input v-model.number="formData.price" id="price" type="number" step="0.01" class="form-input" required />
      </div>
      <div class="form-group">
        <label for="member-price">Mitgliedspreis (€):</label>
        <input v-model.number="formData.memberPrice" id="member-price" type="number" step="0.01" class="form-input" />
      </div>
      <div class="form-group">
        <label for="stock">Lagerbestand*:</label>
        <input v-model.number="formData.stock" id="stock" type="number" min="0" class="form-input" required />
      </div>
      <div class="form-group">
        <label for="image">Bild:</label>
        <input @change="handleImageUpload" id="image" type="file" accept="image/*" class="form-input" />
        <div v-if="imagePreview" class="image-preview">
          <img :src="imagePreview" :alt="formData.name" style="max-width: 150px; max-height: 150px;" />
        </div>
      </div>
      <div class="form-group">
        <label for="discountable">
          <input v-model="formData.discountable" id="discountable" type="checkbox" />
          Rabattfähig
        </label>
      </div>
      <button type="submit" class="btn btn-success">Speichern</button>
    </form>

    <div v-if="productStore.isLoading" class="loading">Läuft...</div>
    <div v-else class="products-table">
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
          <tr v-for="product in productStore.products" :key="product.id">
            <td class="product-image-cell">
              <img v-if="product.image_path" :src="`/api/products/${product.id}/image`" :alt="product.name" class="product-thumb" />
              <span v-else class="no-image">Kein Bild</span>
            </td>
            <td>{{ product.name }}</td>
            <td>{{ formatPrice(product.price_cents) }}</td>
            <td>{{ product.member_price_cents ? formatPrice(product.member_price_cents) : '-' }}</td>
            <td>{{ product.stock_quantity }}</td>
            <td>
              <button @click="editProduct(product)" class="btn-small">Bearbeiten</button>
              <button @click="deleteProduct(product.id)" class="btn-small btn-danger">
                Löschen
              </button>
            </td>
          </tr>
        </tbody>
      </table>
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

const showForm = ref(false)
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
  showForm.value = false
}

const editProduct = (product) => {
  editingId.value = product.id
  formData.name = product.name
  formData.price = product.price_cents / 100
  formData.memberPrice = product.member_price_cents ? product.member_price_cents / 100 : null
  formData.stock = product.stock_quantity
  formData.discountable = product.is_discountable
  if (product.image) {
    imagePreview.value = 'data:image/jpeg;base64,' + product.image
  }
  showForm.value = true
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
    // API call would go here
    notificationStore.success('Produkt gelöscht')
    await productStore.getProducts()
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

.form-section {
  background: #f5f5f5;
  padding: 1.5rem;
  border-radius: 4px;
  margin: 1rem 0;
}

.form-group {
  margin-bottom: 1rem;

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

.loading {
  text-align: center;
  padding: 2rem;
  color: #999;
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
