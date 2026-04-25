<template>
  <div class="categories-container">
    <div class="page-header">
      <div>
        <h2>Kategorieverwaltung</h2>
        <p class="page-subtitle">Kategorien verwalten und Artikel den Bereichen zuordnen.</p>
      </div>
      <button class="btn btn-primary" @click="openCreateModal">
        + Neue Kategorie
      </button>
    </div>

    <div class="list-section">
      <div class="list-header">
        <h3>Kategorien</h3>
      </div>

      <table v-if="categories.length > 0" class="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Beschreibung</th>
            <th>Reihenfolge</th>
            <th>In Kasse aktiv</th>
            <th>Artikel zuordnen</th>
            <th>Aktionen</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="category in categories" :key="category.id">
            <td>
              <strong>{{ category.name }}</strong>
              <span v-if="category.is_fixed" class="badge badge-info">Fest</span>
            </td>
            <td>{{ category.description || '-' }}</td>
            <td>{{ category.display_order }}</td>
            <td>
              <span v-if="category.is_active_in_kasse" class="badge badge-success">✓ Ja</span>
              <span v-else class="badge badge-secondary">✗ Nein</span>
            </td>
            <td>
              <div class="assignment-cell">
                <select v-model="selectedProductByCategory[category.id]" class="form-input compact">
                  <option value="">Artikel wählen...</option>
                  <option
                    v-for="product in unassignedProducts(category.id)"
                    :key="`assign-${category.id}-${product.id}`"
                    :value="product.id"
                  >
                    {{ product.name }}
                  </option>
                </select>
                <button
                  @click="assignProduct(category.id)"
                  :disabled="!selectedProductByCategory[category.id]"
                  class="btn btn-sm btn-primary"
                >
                  Hinzufügen
                </button>

                <div v-if="assignedProducts(category.id).length > 0" class="product-tags">
                  <span
                    v-for="product in assignedProducts(category.id)"
                    :key="`tag-${category.id}-${product.id}`"
                    class="product-tag"
                  >
                    {{ product.name }}
                    <button
                      @click="removeProduct(category.id, product.id)"
                      class="tag-remove"
                      title="Zuordnung entfernen"
                    >
                      ×
                    </button>
                  </span>
                </div>
                <div v-else class="small-muted">Noch kein Artikel zugeordnet</div>
              </div>
            </td>
            <td class="actions">
              <button
                @click="editCategory(category)"
                class="btn btn-sm btn-info"
                :disabled="category.is_fixed"
                :title="category.is_fixed ? 'Feste Kategorie kann nicht bearbeitet werden' : ''"
              >
                Bearbeiten
              </button>
              <button
                @click="deleteCategory(category.id)"
                class="btn btn-sm btn-danger"
                :disabled="category.is_fixed"
                :title="category.is_fixed ? 'Feste Kategorie kann nicht gelöscht werden' : ''"
              >
                Löschen
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-else class="empty-message">
        Noch keine Kategorien vorhanden.
      </div>
    </div>

    <div v-if="showCategoryModal" class="modal-overlay" @click.self="closeCategoryModal">
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ editingId ? 'Kategorie bearbeiten' : 'Neue Kategorie anlegen' }}</h3>
          <button class="modal-close" @click="closeCategoryModal">×</button>
        </div>

        <form @submit.prevent="submitForm" class="form-group">
          <div class="form-field">
            <label for="name">Name:</label>
            <input
              v-model="formData.name"
              id="name"
              type="text"
              required
              class="form-input"
            />
          </div>

          <div class="form-field">
            <label for="description">Beschreibung:</label>
            <textarea
              v-model="formData.description"
              id="description"
              class="form-input"
              rows="3"
            ></textarea>
          </div>

          <div class="form-field">
            <label for="display_order">Anzeigereihenfolge:</label>
            <input
              v-model.number="formData.display_order"
              id="display_order"
              type="number"
              class="form-input"
            />
          </div>

          <div class="form-field checkbox">
            <input
              v-model="formData.is_active_in_kasse"
              id="is_active"
              type="checkbox"
              class="form-checkbox"
            />
            <label for="is_active">In Kassenansicht sichtbar</label>
          </div>

          <div class="form-buttons">
            <button type="submit" class="btn btn-primary">
              {{ editingId ? 'Aktualisieren' : 'Erstellen' }}
            </button>
            <button type="button" @click="closeCategoryModal" class="btn btn-secondary">
              Abbrechen / Zurück
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useNotificationStore } from '@/stores/notification'
import apiService from '@/services/api'

const notificationStore = useNotificationStore()

const categories = ref([])
const products = ref([])
const editingId = ref(null)
const showCategoryModal = ref(false)
const selectedProductByCategory = ref({})
const formData = ref({
  name: '',
  description: '',
  display_order: 0,
  is_active_in_kasse: true,
})

const resetForm = () => {
  formData.value = {
    name: '',
    description: '',
    display_order: 0,
    is_active_in_kasse: true,
  }
  editingId.value = null
}

const openCreateModal = () => {
  resetForm()
  showCategoryModal.value = true
}

const closeCategoryModal = () => {
  showCategoryModal.value = false
  resetForm()
}

const loadCategories = async () => {
  try {
    const response = await apiService.get('/categories')
    categories.value = response.data
    categories.value.forEach((category) => {
      if (selectedProductByCategory.value[category.id] === undefined) {
        selectedProductByCategory.value[category.id] = ''
      }
    })
  } catch (error) {
    console.error('Error loading categories:', error)
    notificationStore.error('Fehler beim Laden der Kategorien')
  }
}

const loadProducts = async () => {
  try {
    const response = await apiService.get('/products')
    products.value = response.data
  } catch (error) {
    console.error('Error loading products:', error)
    notificationStore.error('Fehler beim Laden der Artikel')
  }
}

const assignedProducts = (categoryId) => {
  return products.value.filter((product) =>
    (product.categories || []).some((category) => category.id === categoryId)
  )
}

const unassignedProducts = (categoryId) => {
  return products.value.filter(
    (product) => !(product.categories || []).some((category) => category.id === categoryId)
  )
}

const assignProduct = async (categoryId) => {
  const productId = Number(selectedProductByCategory.value[categoryId])
  if (!productId) return

  try {
    await apiService.post(`/categories/${categoryId}/products`, [productId])
    selectedProductByCategory.value[categoryId] = ''
    await loadProducts()
    notificationStore.success('Artikel zur Kategorie hinzugefügt')
  } catch (error) {
    console.error('Error assigning product:', error)
    notificationStore.error(error.response?.data?.detail || 'Zuordnung fehlgeschlagen')
  }
}

const removeProduct = async (categoryId, productId) => {
  try {
    await apiService.delete(`/categories/${categoryId}/products/${productId}`)
    await loadProducts()
    notificationStore.success('Artikelzuordnung entfernt')
  } catch (error) {
    console.error('Error removing product assignment:', error)
    notificationStore.error(error.response?.data?.detail || 'Entfernen fehlgeschlagen')
  }
}

const submitForm = async () => {
  try {
    if (editingId.value) {
      await apiService.put(`/categories/${editingId.value}`, formData.value)
    } else {
      await apiService.post('/categories', formData.value)
    }
    notificationStore.success(editingId.value ? 'Kategorie aktualisiert' : 'Kategorie erstellt')
    closeCategoryModal()
    await loadCategories()
  } catch (error) {
    console.error('Error submitting form:', error)
    notificationStore.error(error.response?.data?.detail || 'Fehler beim Speichern')
  }
}

const editCategory = (category) => {
  editingId.value = category.id
  formData.value = {
    name: category.name,
    description: category.description,
    display_order: category.display_order,
    is_active_in_kasse: category.is_active_in_kasse,
  }
  showCategoryModal.value = true
}

const deleteCategory = async (categoryId) => {
  if (!confirm('Soll diese Kategorie wirklich gelöscht werden?')) {
    return
  }

  try {
    await apiService.delete(`/categories/${categoryId}`)
    notificationStore.success('Kategorie gelöscht')
    await loadCategories()
  } catch (error) {
    console.error('Error deleting category:', error)
    notificationStore.error('Fehler beim Löschen')
  }
}

onMounted(() => {
  loadCategories()
  loadProducts()
})
</script>

<style scoped lang="scss">
.categories-container {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;

  h2 {
    color: #333;
    margin-bottom: 0.35rem;
  }

  h3 {
    color: #555;
    margin: 0;
  }
}

.page-header,
.list-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.page-header {
  margin-bottom: 1.5rem;
}

.page-subtitle {
  color: #6b7280;
}

.form-group {
  display: grid;
  gap: 1rem;
}

.form-field {
  display: flex;
  flex-direction: column;

  label {
    font-weight: 500;
    margin-bottom: 0.5rem;
    color: #333;
  }

  &.checkbox {
    flex-direction: row;
    align-items: center;

    label {
      margin: 0 0 0 0.5rem;
    }
  }
}

.form-input {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.95rem;
  font-family: inherit;

  &:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
  }
}

.form-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.form-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    transform: translateY(-2px);
  }

  &.btn-primary {
    background: #007bff;
    color: white;

    &:hover {
      background: #0056b3;
    }
  }

  &.btn-secondary {
    background: #6c757d;
    color: white;

    &:hover {
      background: #545b62;
    }
  }

  &.btn-info {
    background: #17a2b8;
    color: white;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;

    &:hover {
      background: #138496;
    }
  }

  &.btn-danger {
    background: #dc3545;
    color: white;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;

    &:hover {
      background: #bb2d3b;
    }
  }

  &.btn-sm {
    padding: 0.5rem 0.75rem;
    font-size: 0.85rem;
  }
}

.list-section {
  background: white;
  padding: 1.5rem;
  border-radius: 16px;
  border: 1px solid #eee;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;

  thead {
    background: #f5f5f5;
  }

  th, td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #eee;
  }

  th {
    font-weight: 600;
    color: #333;
  }

  tbody tr:hover {
    background: #f9f9f9;
  }
}

.assignment-cell {
  min-width: 260px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-input.compact {
  padding: 0.5rem;
  font-size: 0.85rem;
}

.product-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.product-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: #e8f4ff;
  border: 1px solid #c5ddff;
  color: #0f4b8f;
  border-radius: 999px;
  padding: 0.15rem 0.45rem;
  font-size: 0.75rem;
}

.tag-remove {
  border: none;
  background: transparent;
  cursor: pointer;
  color: #0f4b8f;
  font-size: 0.9rem;
  line-height: 1;
}

.small-muted {
  color: #808080;
  font-size: 0.8rem;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
  margin-left: 0.5rem;

  &.badge-success {
    background: #d4edda;
    color: #155724;
  }

  &.badge-secondary {
    background: #e2e3e5;
    color: #383d41;
  }

  &.badge-info {
    background: #dbeafe;
    color: #1d4ed8;
  }
}

.actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.empty-message {
  padding: 2rem;
  text-align: center;
  color: #666;
  background: #f9f9f9;
  border-radius: 4px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: grid;
  place-items: center;
  padding: 1.5rem;
  z-index: 1500;
}

.modal-card {
  width: min(100%, 560px);
  background: white;
  border-radius: 18px;
  padding: 1.5rem;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.24);
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
  font-size: 1.75rem;
  line-height: 1;
  cursor: pointer;
  color: #475569;
}
</style>
