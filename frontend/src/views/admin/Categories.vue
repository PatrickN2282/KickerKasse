<template>
  <div class="admin-categories">
    <div class="page-header">
      <div class="title-row">
        <h2>Kategorieverwaltung</h2>
        <span class="title-sep">|</span>
        <span class="page-subtitle">Kategorien verwalten und Artikel den Bereichen im Layout der Mitgliederverwaltung zuordnen.</span>
      </div>
      <div class="page-header-actions">
        <button class="btn btn-primary" @click="openCreateModal">
          <span class="icon">+</span> Neue Kategorie
        </button>
      </div>
    </div>

    <div class="categories-table-wrapper">
      <table v-if="categories.length > 0" class="categories-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Beschreibung</th>
            <th>Farbe</th>
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
            <td>
              <div
                v-if="category.color"
                class="color-swatch-display"
                :style="{ background: category.color }"
                :title="category.color"
              ></div>
              <span v-else class="small-muted">–</span>
            </td>
            <td>{{ category.display_order }}</td>
            <td>
              <span v-if="category.is_active_in_kasse" class="badge badge-success">✓ Ja</span>
              <span v-else class="badge badge-light">✗ Nein</span>
            </td>
            <td>
              <div class="product-count-cell">
                <span class="product-count-badge">{{ assignedProducts(category.id).length }}</span>
                <button class="btn-action" @click="openAssignModal(category)">Verwalten</button>
              </div>
            </td>
            <td class="text-right">
              <div class="action-cell">
                <button
                  class="btn-action"
                  :disabled="category.is_fixed"
                  :title="category.is_fixed ? 'Feste Kategorie kann nicht bearbeitet werden' : ''"
                  @click="editCategory(category)"
                >
                  Bearbeiten
                </button>
                <button
                  class="btn-action btn-action-danger"
                  :disabled="category.is_fixed"
                  :title="category.is_fixed ? 'Feste Kategorie kann nicht gelöscht werden' : ''"
                  @click="deleteCategory(category.id)"
                >
                  Löschen
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-else class="empty-state">
        <p>Noch keine Kategorien vorhanden.</p>
      </div>
    </div>

    <CategoryFormModal
      :show="showCategoryModal"
      :editing-id="editingId"
      :pastel-colors="pastelColors"
      v-model:form-data="formData"
      @close="closeCategoryModal"
      @save="submitForm"
    />

    <CategoryAssignmentModal
      :show="showAssignModal"
      :category="assignModalCategory"
      :assigned-products="assignModalCategory ? assignedProducts(assignModalCategory.id) : []"
      :unassigned-products="assignModalCategory ? unassignedProducts(assignModalCategory.id) : []"
      @close="closeAssignModal"
      @assign-product="assignProductDirect(assignModalCategory.id, $event)"
      @remove-product="removeProduct(assignModalCategory.id, $event)"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import CategoryAssignmentModal from '@/views/admin/modal/CategoryAssignmentModal.vue'
import CategoryFormModal from '@/views/admin/modal/CategoryFormModal.vue'
import { useNotificationStore } from '@/stores/notification'
import apiService from '@/services/api'

const notificationStore = useNotificationStore()

const categories = ref([])
const products = ref([])
const editingId = ref(null)
const showCategoryModal = ref(false)
const showAssignModal = ref(false)
const assignModalCategory = ref(null)
const formData = ref({
  name: '',
  description: '',
  color: null,
  display_order: 0,
  is_active_in_kasse: true,
})

const pastelColors = [
  { value: '#FFB3B3', label: 'Rosé' },
  { value: '#FFCBA4', label: 'Pfirsich' },
  { value: '#FFF2A8', label: 'Gelb' },
  { value: '#B5EAD7', label: 'Mint' },
  { value: '#B5D5FF', label: 'Hellblau' },
  { value: '#C3B1E1', label: 'Lavendel' },
  { value: '#FFD1DC', label: 'Pink' },
  { value: '#D7E8BA', label: 'Limette' },
  { value: '#FFF8E1', label: 'Creme' },
  { value: '#E0F2F1', label: 'Türkis' },
  { value: '#FFE4C4', label: 'Bisque' },
  { value: '#F0E6FF', label: 'Flieder' },
]

const resetForm = () => {
  formData.value = {
    name: '',
    description: '',
    color: null,
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

const assignProductDirect = async (categoryId, productId) => {
  try {
    await apiService.post(`/categories/${categoryId}/products`, [productId])
    await loadProducts()
    notificationStore.success('Artikel zur Kategorie hinzugefügt')
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Zuordnung fehlgeschlagen')
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
    color: category.color || null,
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

const openAssignModal = (category) => {
  assignModalCategory.value = category
  showAssignModal.value = true
}

const closeAssignModal = () => {
  showAssignModal.value = false
  assignModalCategory.value = null
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
  padding: 0.75rem 1rem;
  background: var(--app-background-color);
  min-height: 100%;
}

.page-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--app-background-color);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: -0.75rem -1rem 0.75rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.13);

  h2 {
    font-size: 1.25rem;
    color: #333;
    margin: 0;
  }
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

.page-header-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.page-subtitle,
.modal-subtitle {
  color: #64748b;
  margin: 0;
}

.categories-table-wrapper {
  background: color-mix(in srgb, var(--app-background-color) 30%, white);
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--app-background-color) 65%, #777);
  overflow-x: auto;
  overflow-y: hidden;
}

.categories-table {
  width: 100%;
  min-width: 1080px;
  border-collapse: collapse;
  font-size: 0.88rem;

  thead {
    background: color-mix(in srgb, var(--app-background-color) 75%, white);
  }

  th {
    padding: 0.5rem 0.75rem;
    color: #475569;
    font-weight: 600;
    font-size: 0.8rem;
    text-align: left;
  }

  td {
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
  }

  tr:hover td {
    background: color-mix(in srgb, var(--app-background-color) 60%, white);
  }

  tr:last-child td {
    border-bottom: none;
  }
}

.color-swatch-display {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  display: inline-block;
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
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
  flex-wrap: wrap;
  white-space: nowrap;
  width: 100%;
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

/* ── Color picker ─────────────────────────────────── */
.color-picker-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.color-picker-hint {
  font-size: 0.82rem;
  color: #64748b;
  margin: 0;
}

.color-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  align-items: center;
}

.color-option {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: transform 0.12s, border-color 0.12s;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;

  &:hover {
    transform: scale(1.12);
  }

  &.selected {
    border-color: #1e293b;
    box-shadow: 0 0 0 2px white inset;
  }
}

.color-option-none {
  background: #f1f5f9;
  border: 2px dashed #cbd5e1;
  color: #94a3b8;

  &.selected {
    border-color: #1e293b;
    border-style: solid;
  }
}

.no-color-icon {
  font-size: 0.7rem;
  font-weight: 700;
}

.color-option-custom {
  background: #f8fafc;
  border: 2px dashed #94a3b8;
  cursor: pointer;
  overflow: visible;

  &.selected {
    border-style: solid;
    border-color: #1e293b;
  }

  input[type="color"] {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    opacity: 0;
    cursor: pointer;
    padding: 0;
    border: none;
  }
}

.custom-color-preview {
  width: 100%;
  height: 100%;
  display: block;
  border-radius: 6px;
  position: absolute;
  inset: 0;
}

.custom-color-icon {
  font-size: 1rem;
  pointer-events: none;
}

.color-preview-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-top: 0.25rem;
}

.color-preview-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.7rem;
  border-radius: 999px;
  border: 2px solid;
  font-size: 0.8rem;
  font-weight: 600;
}

.color-preview-card {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.7rem;
  border-radius: 8px;
  border: 2px solid;
  font-size: 0.8rem;
  background: white;
}

.btn-clear-color {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.8rem;
  color: #64748b;
  text-decoration: underline;
  padding: 0;

  &:hover {
    color: #b91c1c;
  }
}

/* ── Modal ────────────────────────────────────────── */
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
  max-height: 650px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.modal-compact {
  max-width: 650px;
}

.modal-header {
  padding: 0.9rem 1.2rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  background: linear-gradient(90deg, #0f766e 0%, #0ea5e9 100%);

  h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #ffffff;
  }

  .modal-subtitle {
    margin: 0.15rem 0 0;
    font-size: 0.85rem;
    color: rgba(255,255,255,0.9);
  }
}

.modal-compact-layout {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-scroller {
  padding: 1rem 1.2rem;
  overflow-y: auto;
  max-height: calc(650px - 110px);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-section {
  margin-bottom: 0;

  h4 {
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.35rem;
    margin-bottom: 0.65rem;
  }

  &.highlight {
    background: #f0f7ff;
    padding: 0.65rem 0.9rem;
    border-radius: 12px;
    border: 1px solid #bae6fd;
  }
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.form-group {
  margin-bottom: 0.6rem;

  label {
    display: block;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 0.25rem;
    color: #334155;
  }

  input,
  textarea {
    width: 100%;
    padding: 0.5rem 0.7rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.9rem;
    color: #0f172a;

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
  padding: 0.6rem 0.8rem;
  background: white;
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  align-items: center;
  min-height: 44px;
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
  padding: 0.55rem 1.1rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-size: 0.9rem;
  min-height: 40px;
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

.btn-action {
  border: 1px solid var(--border);
  background: white;
  color: #334155;
  padding: 0.45rem 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;

  &:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }
}

.btn-action-danger {
  border-color: #fecaca;
  color: #b91c1c;
}

.close-btn {
  width: 34px; height: 34px; border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.45);
  background: rgba(255,255,255,0.18);
  color: #ffffff; font-size: 1.1rem; cursor: pointer;
  display: grid; place-items: center; flex-shrink: 0;
  &:hover { background: rgba(255,255,255,0.3); }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 0.75rem 1.2rem;
  border-top: 1px solid var(--border);
  background: #f8fafc;
}

@media (max-width: 600px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .action-cell {
    flex-direction: column;
  }

  .btn,
  .btn-compact,
  .btn-action {
    width: 100%;
  }
}

// ── Product count cell and assignment modal ──────────
.product-count-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  white-space: nowrap;
}

.product-count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.6rem;
  padding: 0.15rem 0.5rem;
  background: #e2e8f0;
  color: #0f172a;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
}

.assign-modal-body {
  padding: 1rem 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.assign-add-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.assign-select {
  flex: 1;
  padding: 0.5rem 0.7rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 0.9rem;

  &:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
}

.assign-product-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  max-height: 280px;
  overflow-y: auto;
}

.assign-product-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.4rem 0.7rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #f8fafc;
  font-size: 0.88rem;
}

.assign-product-name {
  font-weight: 500;
  color: #1e293b;
}

.btn-tag-remove {
  border: none;
  background: transparent;
  cursor: pointer;
  color: #b91c1c;
  font-size: 1.1rem;
  line-height: 1;
  padding: 0 0.2rem;

  &:hover {
    color: #7f1d1d;
  }
}

.assign-empty {
  text-align: center;
  color: #64748b;
  font-size: 0.88rem;
  padding: 1rem 0;
}

.assign-add-section {
  margin-bottom: 1rem;
}

.assign-section-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #475569;
  margin: 0 0 0.5rem;
}

.product-pick-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.4rem;
}

.product-pick-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.45rem 0.6rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  text-align: left;
  width: 100%;
  &:hover { background: #f0f9ff; border-color: #0ea5e9; }
}

.product-pick-img {
  width: 28px;
  height: 28px;
  border-radius: 5px;
  object-fit: cover;
  flex-shrink: 0;
}

.product-pick-img-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e2e8f0;
  font-size: 0.9rem;
}

.product-pick-name {
  font-size: 0.9rem;
  color: #1e293b;
}

.assign-product-thumb {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  object-fit: cover;
  flex-shrink: 0;
}

.assign-product-thumb-placeholder {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #e2e8f0;
  font-size: 0.75rem;
}
</style>
