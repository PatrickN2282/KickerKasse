<template>
  <div class="admin-categories">
    <div class="page-header">
      <div>
        <h2>Kategorieverwaltung</h2>
        <p class="page-subtitle">Kategorien verwalten und Artikel den Bereichen im Layout der Mitgliederverwaltung zuordnen.</p>
      </div>
      <button class="btn btn-primary" @click="openCreateModal">
        <span class="icon">+</span> Neue Kategorie
      </button>
    </div>

    <div class="categories-table-wrapper">
      <table v-if="categories.length > 0" class="categories-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Beschreibung</th>
            <th>Reihenfolge</th>
            <th>In Kasse aktiv</th>
            <th>Artikel zuordnen</th>
            <th class="text-right">Aktionen</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="category in categories" :key="category.id">
            <td>
              <div class="category-name-cell">
                <strong>{{ category.name }}</strong>
                <span v-if="category.is_fixed" class="badge badge-info">Fest</span>
              </div>
            </td>
            <td>{{ category.description || '-' }}</td>
            <td>{{ category.display_order }}</td>
            <td>
              <span v-if="category.is_active_in_kasse" class="badge badge-success">✓ Ja</span>
              <span v-else class="badge badge-light">✗ Nein</span>
            </td>
            <td>
              <div class="assignment-cell">
                <div class="assignment-controls">
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
                  <button class="btn btn-primary btn-compact" :disabled="!selectedProductByCategory[category.id]" @click="assignProduct(category.id)">
                    Hinzufügen
                  </button>
                </div>

                <div v-if="assignedProducts(category.id).length > 0" class="product-tags">
                  <span
                    v-for="product in assignedProducts(category.id)"
                    :key="`tag-${category.id}-${product.id}`"
                    class="product-tag"
                  >
                    {{ product.name }}
                    <button class="tag-remove" title="Zuordnung entfernen" @click="removeProduct(category.id, product.id)">
                      ×
                    </button>
                  </span>
                </div>
                <div v-else class="small-muted">Noch kein Artikel zugeordnet</div>
              </div>
            </td>
            <td class="text-right action-cell">
              <button
                class="btn-icon"
                :disabled="category.is_fixed"
                :title="category.is_fixed ? 'Feste Kategorie kann nicht bearbeitet werden' : 'Bearbeiten'"
                :aria-label="category.is_fixed ? 'Kategorie kann nicht bearbeitet werden' : 'Kategorie bearbeiten'"
                @click="editCategory(category)"
              >
                ✏️
              </button>
              <button
                class="btn-icon btn-icon-danger"
                :disabled="category.is_fixed"
                :title="category.is_fixed ? 'Feste Kategorie kann nicht gelöscht werden' : 'Löschen'"
                :aria-label="category.is_fixed ? 'Kategorie kann nicht gelöscht werden' : 'Kategorie löschen'"
                @click="deleteCategory(category.id)"
              >
                🗑️
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-else class="empty-state">
        <p>Noch keine Kategorien vorhanden.</p>
      </div>
    </div>

    <div v-if="showCategoryModal" class="modal-overlay" @click.self="closeCategoryModal">
      <div class="modal-card modal-card-form">
        <header class="modal-header">
          <div>
            <h3>{{ editingId ? 'Kategorie bearbeiten' : 'Neue Kategorie anlegen' }}</h3>
            <p class="modal-subtitle">Kategorie mit Namen, Beschreibung und Anzeigeeinstellungen kompakt verwalten.</p>
          </div>
          <button class="modal-close" @click="closeCategoryModal">×</button>
        </header>

        <form class="modal-form-content" @submit.prevent="submitForm">
          <section class="form-section">
            <h4>Stammdaten</h4>
            <div class="form-row">
              <div class="form-group">
                <label for="name">Name</label>
                <input id="name" v-model="formData.name" type="text" required>
              </div>
              <div class="form-group">
                <label for="display_order">Anzeigereihenfolge</label>
                <input id="display_order" v-model.number="formData.display_order" type="number">
              </div>
            </div>
            <div class="form-group">
              <label for="description">Beschreibung</label>
              <textarea id="description" v-model="formData.description" rows="3"></textarea>
            </div>
          </section>

          <section class="form-section highlight">
            <h4>Darstellung</h4>
            <label class="checkbox-card">
              <input id="is_active" v-model="formData.is_active_in_kasse" type="checkbox">
              <div class="checkbox-content">
                <span class="label">In Kassenansicht sichtbar</span>
                <span class="desc">Die Kategorie wird direkt in der Kasse als auswählbarer Bereich angezeigt.</span>
              </div>
            </label>
          </section>

          <footer class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeCategoryModal">Abbrechen</button>
            <button type="submit" class="btn btn-success">
              {{ editingId ? 'Änderungen speichern' : 'Kategorie anlegen' }}
            </button>
          </footer>
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
.admin-categories {
  --primary: #3b82f6;
  --success: #10b981;
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

.categories-table-wrapper {
  background: white;
  border-radius: 12px;
  border: 1px solid var(--border);
  overflow-x: auto;
  overflow-y: hidden;
}

.categories-table {
  width: 100%;
  min-width: 980px;
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
    vertical-align: top;
  }
}

.category-name-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.text-right {
  text-align: right;
}

.action-cell {
  white-space: nowrap;
}

.assignment-cell {
  min-width: 320px;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.assignment-controls {
  display: flex;
  gap: 0.75rem;
}

.form-input {
  width: 100%;
  padding: 0.6rem 0.8rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 0.95rem;
  background: white;

  &:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
}

.form-input.compact {
  padding: 0.55rem 0.75rem;
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
  padding: 0.25rem 0.55rem;
  font-size: 0.75rem;
}

.tag-remove {
  border: none;
  background: transparent;
  cursor: pointer;
  color: #0f4b8f;
  font-size: 0.95rem;
  line-height: 1;
}

.small-muted {
  color: #808080;
  font-size: 0.8rem;
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

.empty-state {
  padding: 3rem 1rem;
  text-align: center;
  color: #64748b;
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

.modal-card-form {
  max-width: 760px;
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

.modal-form-content {
  padding: 1.5rem;
  overflow-y: auto;
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

  &.highlight {
    background: #f0f7ff;
    padding: 1rem;
    border-radius: 12px;
    border: 1px solid #bae6fd;
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

  input,
  textarea {
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

.checkbox-card {
  display: flex;
  gap: 0.75rem;
  padding: 0.9rem 1rem;
  background: white;
  border: 1px solid var(--border);
  border-radius: 10px;
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

.btn-compact {
  white-space: nowrap;
}

.btn-icon {
  background: none;
  border: none;
  padding: 0.4rem;
  cursor: pointer;
  border-radius: 4px;

  &:hover:not(:disabled) {
    background: #f1f5f9;
  }

  &.btn-icon-danger:hover:not(:disabled) {
    background: #fee2e2;
  }

  &:disabled {
    opacity: 0.45;
    cursor: not-allowed;
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
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

@media (max-width: 900px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .assignment-controls,
  .modal-footer {
    flex-direction: column;
  }

  .btn,
  .btn-compact {
    width: 100%;
  }
}
</style>
