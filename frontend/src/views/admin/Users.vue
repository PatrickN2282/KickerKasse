<template>
  <div class="admin-users">
    <h2>Benutzerverwaltung</h2>

    <button @click="showForm = !showForm" class="btn btn-primary">
      {{ showForm ? 'Abbrechen' : 'Neuen Benutzer' }}
    </button>

    <form v-if="showForm" @submit.prevent="handleSaveUser" class="form-section">
      <div class="form-group">
        <label for="username">Benutzername*:</label>
        <input v-model="formData.username" id="username" type="text" class="form-input" required />
      </div>
      <div class="form-group">
        <label for="email">Email:</label>
        <input v-model="formData.email" id="email" type="email" class="form-input" />
      </div>
      <div class="form-group">
        <label for="password">Passwort*:</label>
        <input v-model="formData.password" id="password" type="password" class="form-input" required />
      </div>
      <div class="form-group">
        <label for="role">Rolle*:</label>
        <select v-model="formData.role" id="role" class="form-input" required>
          <option value="CASHIER">Verkauf</option>
          <option value="KASSENMITGLIED">VerkaufAdmin</option>
          <option value="ADMIN">Admin</option>
        </select>
      </div>
      <button type="submit" class="btn btn-success">Speichern</button>
    </form>

    <div class="users-table">
      <table>
        <thead>
          <tr>
            <th>Benutzername</th>
            <th>Email</th>
            <th>Rolle</th>
            <th>Aktionen</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.username }}</td>
            <td>{{ user.email || '-' }}</td>
            <td>{{ roleLabel(user.role) }}</td>
            <td>
              <button @click="deleteUser(user.id)" class="btn-small btn-danger">
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
import { useNotificationStore } from '@/stores/notification'
import apiService from '@/services/api'

const notificationStore = useNotificationStore()

const showForm = ref(false)
const users = ref([])
const formData = reactive({
  username: '',
  email: '',
  password: '',
  role: 'CASHIER',
})

const roleLabel = (role) => ({
  ADMIN: 'Admin',
  CASHIER: 'Verkauf',
  KASSENMITGLIED: 'VerkaufAdmin',
}[role] || role)

const handleSaveUser = async () => {
  try {
    await apiService.post('/users', {
      ...formData,
      email: formData.email?.trim() || null,
    })
    notificationStore.success('Benutzer erstellt')
    formData.username = ''
    formData.email = ''
    formData.password = ''
    formData.role = 'CASHIER'
    showForm.value = false
    await loadUsers()
  } catch (err) {
    notificationStore.error(err.response?.data?.detail || 'Fehler beim Erstellen')
  }
}

const deleteUser = async (userId) => {
  if (confirm('Wirklich löschen?')) {
    try {
      await apiService.delete(`/users/${userId}`)
      notificationStore.success('Benutzer gelöscht')
      await loadUsers()
    } catch (err) {
      notificationStore.error(err.response?.data?.detail || 'Fehler beim Löschen')
    }
  }
}

const loadUsers = async () => {
  try {
    const response = await apiService.get('/users')
    users.value = response.data
  } catch (err) {
    notificationStore.error('Fehler beim Laden der Benutzer')
  }
}

onMounted(async () => {
  await loadUsers()
})
</script>

<style scoped lang="scss">
.admin-users {
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
      border-color: var(--app-highlight-color);
    }
  }
}

.users-table {
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

  &.btn-danger {
    background: #f44336;
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
  background: var(--app-highlight-color);
  color: white;
}

.btn-success {
  background: var(--app-banner-color);
  color: white;
}
</style>
