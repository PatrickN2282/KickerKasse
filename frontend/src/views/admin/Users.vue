<template>
  <div class="admin-users">
    <h2>Benutzerverwaltung</h2>

    <button
      class="btn btn-primary"
      @click="showForm = !showForm"
    >
      {{ showForm ? 'Abbrechen / Zurück' : 'Neuen Benutzer' }}
    </button>

    <form
      v-if="showForm"
      class="form-section"
      @submit.prevent="handleSaveUser"
    >
      <div class="form-group">
        <label for="username">Benutzername*:</label>
        <input
          id="username"
          v-model="formData.username"
          type="text"
          class="form-input"
          required
        >
      </div>
      <div class="form-group">
        <label for="email">Email:</label>
        <input
          id="email"
          v-model="formData.email"
          type="email"
          class="form-input"
        >
      </div>
      <div class="form-group">
        <label for="password">Passwort*:</label>
        <input
          id="password"
          v-model="formData.password"
          type="password"
          class="form-input"
          required
        >
      </div>
      <div class="form-group">
        <label for="role">Rolle*:</label>
        <select
          id="role"
          v-model="formData.role"
          class="form-input"
          required
        >
          <option value="VERKAUF">
            Verkauf
          </option>
          <option value="MANAGER">
            Manager
          </option>
          <option value="ADMIN">
            Admin
          </option>
        </select>
      </div>
      <button
        type="submit"
        class="btn btn-success"
      >
        Speichern
      </button>
    </form>

    <div class="users-table">
      <table>
        <thead>
          <tr>
            <th>Typ</th>
            <th>Benutzername</th>
            <th>Email</th>
            <th>Rolle</th>
            <th>Aktionen</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="user in displayedUsers"
            :key="user.id"
          >
            <td>{{ user.entryType }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.email || '-' }}</td>
            <td>{{ roleLabel(user.role) }}</td>
            <td>
              <button
                v-if="user.deletable"
                class="btn-small btn-danger"
                @click="deleteUser(user.id)"
              >
                Löschen
              </button>
              <span v-else>-</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useNotificationStore } from '@/stores/notification'
import { getMemberFullName, getRoleLabel } from '@/services/member'
import apiService from '@/services/api'

const notificationStore = useNotificationStore()

const showForm = ref(false)
const users = ref([])
const membersWithRoles = ref([])
const formData = reactive({
  username: '',
  email: '',
  password: '',
  role: 'VERKAUF',
})

const roleLabel = getRoleLabel

const templateUsers = computed(() => [
  { id: 'template-admin', username: 'Admin', email: '-', role: 'ADMIN', entryType: 'Vorlage', deletable: false },
  { id: 'template-verkauf', username: 'Verkauf', email: '-', role: 'VERKAUF', entryType: 'Vorlage', deletable: false },
  { id: 'template-manager', username: 'Manager', email: '-', role: 'MANAGER', entryType: 'Vorlage', deletable: false },
])

const displayedUsers = computed(() => [
  ...templateUsers.value,
  ...users.value.map(user => ({
    ...user,
    entryType: 'Benutzer',
    deletable: true,
  })),
  ...membersWithRoles.value,
])

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
    formData.role = 'VERKAUF'
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
  } catch {
    notificationStore.error('Fehler beim Laden der Benutzer')
  }
}

const loadRoleMembers = async () => {
  try {
    const response = await apiService.get('/members')
    membersWithRoles.value = response.data
      .filter(member => member.role)
      .map(member => ({
        id: `member-${member.id}`,
        username: getMemberFullName(member),
        email: member.email || '-',
        role: member.role,
        entryType: 'Mitglied',
        deletable: false,
      }))
  } catch {
    notificationStore.error('Fehler beim Laden der Mitglieder mit Rolle')
  }
}

onMounted(async () => {
  await Promise.all([loadUsers(), loadRoleMembers()])
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
