<template>
  <div class="categories-container">
    <h2>Kategorieverwaltung</h2>

    <!-- Create Form -->
    <div class="form-section">
      <h3>{{ editingId ? 'Kategorie bearbeiten' : 'Neue Kategorie hinzufügen' }}</h3>
      
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
          <button type="button" @click="resetForm" class="btn btn-secondary">
            Abbrechen
          </button>
        </div>
      </form>
    </div>

    <!-- Categories List -->
    <div class="list-section">
      <h3>Kategorien</h3>
      
      <table v-if="categories.length > 0" class="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Beschreibung</th>
            <th>Reihenfolge</th>
            <th>In Kasse aktiv</th>
            <th>Aktionen</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="category in categories" :key="category.id">
            <td><strong>{{ category.name }}</strong></td>
            <td>{{ category.description || '-' }}</td>
            <td>{{ category.display_order }}</td>
            <td>
              <span v-if="category.is_active_in_kasse" class="badge badge-success">✓ Ja</span>
              <span v-else class="badge badge-secondary">✗ Nein</span>
            </td>
            <td class="actions">
              <button @click="editCategory(category)" class="btn btn-sm btn-info">Bearbeiten</button>
              <button @click="deleteCategory(category.id)" class="btn btn-sm btn-danger">Löschen</button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-else class="empty-message">
        Noch keine Kategorien vorhanden.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useNotificationStore } from '@/stores/notification'

const notificationStore = useNotificationStore()

const categories = ref([])
const editingId = ref(null)
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

const loadCategories = async () => {
  try {
    const response = await fetch('/api/categories', {
      credentials: 'include',
    })
    if (response.ok) {
      categories.value = await response.json()
    } else {
      notificationStore.error('Fehler beim Laden der Kategorien')
    }
  } catch (error) {
    console.error('Error loading categories:', error)
    notificationStore.error('Fehler beim Laden der Kategorien')
  }
}

const submitForm = async () => {
  try {
    const url = editingId.value 
      ? `/api/categories/${editingId.value}`
      : '/api/categories'
    
    const method = editingId.value ? 'PUT' : 'POST'

    const response = await fetch(url, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData.value),
      credentials: 'include',
    })

    if (response.ok) {
      notificationStore.success(
        editingId.value ? 'Kategorie aktualisiert' : 'Kategorie erstellt'
      )
      resetForm()
      loadCategories()
    } else {
      const error = await response.json()
      notificationStore.error(error.detail || 'Fehler beim Speichern')
    }
  } catch (error) {
    console.error('Error submitting form:', error)
    notificationStore.error('Fehler beim Speichern')
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
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const deleteCategory = async (categoryId) => {
  if (!confirm('Soll diese Kategorie wirklich gelöscht werden?')) {
    return
  }

  try {
    const response = await fetch(`/api/categories/${categoryId}`, {
      method: 'DELETE',
      credentials: 'include',
    })

    if (response.ok) {
      notificationStore.success('Kategorie gelöscht')
      loadCategories()
    } else {
      notificationStore.error('Fehler beim Löschen')
    }
  } catch (error) {
    console.error('Error deleting category:', error)
    notificationStore.error('Fehler beim Löschen')
  }
}

onMounted(() => {
  loadCategories()
})
</script>

<style scoped lang="scss">
.categories-container {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;

  h2 {
    color: #333;
    margin-bottom: 1.5rem;
    border-bottom: 2px solid #007bff;
    padding-bottom: 0.5rem;
  }

  h3 {
    color: #555;
    margin: 1.5rem 0 1rem;
  }
}

.form-section {
  background: #f9f9f9;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  border: 1px solid #eee;
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
  margin-top: 1rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
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
  border-radius: 8px;
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

.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;

  &.badge-success {
    background: #d4edda;
    color: #155724;
  }

  &.badge-secondary {
    background: #e2e3e5;
    color: #383d41;
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
</style>
