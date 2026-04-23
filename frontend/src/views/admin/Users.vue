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
                  class="btn-small"
                  @click="openPasswordReset(user)"
                >
                  Passwort setzen
                </button>
                <button
                  v-if="user.deletable"
                  class="btn-small btn-danger"
                  @click="deleteUser(user.id)"
                >
                  Löschen
                </button>
              </td>
            </tr>
        </tbody>
      </table>
    </div>

    <div v-if="resettingPasswordFor" class="modal-overlay">
      <div class="modal-card">
        <h3>Passwort neu vergeben</h3>
        <p class="modal-help">
          Neues Passwort für <strong>{{ resettingPasswordFor.username }}</strong> festlegen.
        </p>
        <div class="form-group">
          <label for="reset-password">Neues Passwort</label>
          <input
            id="reset-password"
            v-model="passwordResetData.password"
            type="password"
            minlength="8"
            class="form-input"
          >
        </div>
        <div class="modal-actions">
          <button class="btn btn-success" :disabled="passwordResetData.password.length < 8" @click="submitPasswordReset">
            Speichern
          </button>
          <button class="btn btn-danger" @click="closePasswordReset">
            Abbrechen / Zurück
          </button>
        </div>
      </div>
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
const resettingPasswordFor = ref(null)
const formData = reactive({
  username: '',
  email: '',
  password: '',
  role: 'VERKAUF',
})
const passwordResetData = reactive({
  password: '',
})

const roleLabel = getRoleLabel

const displayedUsers = computed(() => [
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
    users.value = response.data.filter(user => !user.member_id)
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
        memberId: member.id,
        username: member.account_username || getMemberFullName(member),
        email: member.email || '-',
        role: member.role,
        hasUserAccount: member.has_user_account,
        entryType: member.has_user_account ? 'Mitgliedskonto' : 'Mitglied',
        deletable: false,
      }))
  } catch {
    notificationStore.error('Fehler beim Laden der Mitglieder mit Rolle')
  }
}

const openPasswordReset = (user) => {
  if (user.entryType === 'Mitglied' && !user.hasUserAccount) {
    notificationStore.error('Für dieses Mitglied existiert kein Benutzerkonto')
    return
  }
  resettingPasswordFor.value = user
  passwordResetData.password = ''
}

const closePasswordReset = () => {
  resettingPasswordFor.value = null
  passwordResetData.password = ''
}

const submitPasswordReset = async () => {
  try {
    if (resettingPasswordFor.value.memberId) {
      await apiService.put(`/members/${resettingPasswordFor.value.memberId}`, {
        account_password: passwordResetData.password,
      })
    } else {
      await apiService.put(`/users/${resettingPasswordFor.value.id}`, {
        password: passwordResetData.password,
      })
    }
    notificationStore.success('Passwort neu vergeben')
    closePasswordReset()
    await Promise.all([loadUsers(), loadRoleMembers()])
  } catch (err) {
    notificationStore.error(err.response?.data?.detail || 'Fehler beim Speichern des Passworts')
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

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 30;
}

.modal-card {
  width: min(420px, calc(100vw - 2rem));
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
}

.modal-help {
  margin-bottom: 1rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
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
