<template>
  <div class="admin-users">
    <div class="page-header">
      <div>
        <h2>Benutzerverwaltung</h2>
        <p class="page-subtitle">
          Direkte Benutzerkonten verwalten und Mitgliedskonten separat einsehen.
        </p>
      </div>

      <button
        class="btn btn-primary"
        @click="openCreateModal"
      >
        Neuer Benutzer
      </button>
    </div>

    <div class="users-table">
      <table>
        <thead>
          <tr>
            <th>Typ</th>
            <th>Benutzername</th>
            <th>E-Mail</th>
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
            <td class="action-cell">
              <button
                v-if="user.deletable"
                class="btn-small"
                @click="openEditModal(user)"
              >
                Bearbeiten
              </button>
              <button
                v-if="user.canResetPassword"
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

    <div
      v-if="showUserModal"
      class="modal-overlay"
      @click.self="closeUserModal"
    >
      <div class="modal-card user-modal-card modal-card-horizontal">
        <div class="modal-header">
          <div>
            <h3>{{ editingUserId ? 'Benutzer bearbeiten' : 'Neuen Benutzer anlegen' }}</h3>
            <p class="modal-subtitle">
              Direkte Benutzerkonten nutzen eigene Zugangsdaten und sind nicht an ein Mitglied gebunden.
            </p>
          </div>
          <button
            class="modal-close"
            @click="closeUserModal"
          >
            ×
          </button>
        </div>

        <form
          class="modal-form modal-form-horizontal"
          @submit.prevent="handleSaveUser"
        >
          <div class="form-group">
            <label for="username">Benutzername*</label>
            <input
              id="username"
              v-model="formData.username"
              type="text"
              class="form-input"
              required
            >
          </div>

          <div class="form-group">
            <label for="email">E-Mail</label>
            <input
              id="email"
              v-model="formData.email"
              type="email"
              class="form-input"
            >
          </div>

          <div class="form-group">
            <label for="role">Rolle*</label>
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

          <div class="form-group form-group-wide">
            <label for="password">
              {{ editingUserId ? 'Neues Passwort' : 'Passwort*' }}
            </label>
            <input
              id="password"
              v-model="formData.password"
              type="password"
              minlength="8"
              class="form-input"
              :required="!editingUserId"
              placeholder="Mindestens 8 Zeichen"
            >
            <small class="form-help">
              {{ editingUserId
                ? 'Leer lassen, wenn das bestehende Passwort unverändert bleiben soll.'
                : 'Passwort wird für den ersten Login benötigt.' }}
            </small>
          </div>

          <div class="form-buttons">
            <button
              type="submit"
              class="btn btn-success"
            >
              {{ editingUserId ? 'Aktualisieren' : 'Erstellen' }}
            </button>
            <button
              type="button"
              class="btn btn-secondary"
              @click="closeUserModal"
            >
              Abbrechen / Zurück
            </button>
          </div>
        </form>
      </div>
    </div>

    <div
      v-if="resettingPasswordFor"
      class="modal-overlay"
      @click.self="closePasswordReset"
    >
      <div class="modal-card password-modal-card">
        <div class="modal-header">
          <div>
            <h3>Passwort neu vergeben</h3>
            <p class="modal-subtitle">
              Neues Passwort für <strong>{{ resettingPasswordFor.username }}</strong> festlegen.
            </p>
          </div>
          <button
            class="modal-close"
            @click="closePasswordReset"
          >
            ×
          </button>
        </div>

        <div class="form-group">
          <label for="reset-password">Neues Passwort</label>
          <input
            id="reset-password"
            v-model="passwordResetData.password"
            type="password"
            minlength="8"
            class="form-input"
            placeholder="Mindestens 8 Zeichen"
          >
        </div>

        <div class="form-buttons">
          <button
            class="btn btn-success"
            :disabled="passwordResetData.password.length < 8"
            @click="submitPasswordReset"
          >
            Speichern
          </button>
          <button
            class="btn btn-secondary"
            @click="closePasswordReset"
          >
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

const users = ref([])
const membersWithRoles = ref([])
const showUserModal = ref(false)
const editingUserId = ref(null)
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
    canResetPassword: false,
  })),
  ...membersWithRoles.value,
])

const resetForm = () => {
  formData.username = ''
  formData.email = ''
  formData.password = ''
  formData.role = 'VERKAUF'
  editingUserId.value = null
}

const openCreateModal = () => {
  resetForm()
  showUserModal.value = true
}

const openEditModal = (user) => {
  editingUserId.value = user.id
  formData.username = user.username || ''
  formData.email = user.email || ''
  formData.password = ''
  formData.role = user.role || 'VERKAUF'
  showUserModal.value = true
}

const closeUserModal = () => {
  showUserModal.value = false
  resetForm()
}

const handleSaveUser = async () => {
  const payload = {
    username: formData.username.trim(),
    email: formData.email?.trim() || null,
    role: formData.role,
  }

  if (formData.password) {
    payload.password = formData.password
  }

  try {
    if (editingUserId.value) {
      await apiService.put(`/users/${editingUserId.value}`, payload)
      notificationStore.success('Benutzer aktualisiert')
    } else {
      await apiService.post('/users', payload)
      notificationStore.success('Benutzer erstellt')
    }

    closeUserModal()
    await loadUsers()
  } catch (err) {
    notificationStore.error(err.response?.data?.detail || 'Fehler beim Speichern')
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
        canResetPassword: true,
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

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.page-subtitle,
.modal-subtitle,
.form-help {
  color: #6b7280;
}

.page-subtitle {
  margin-top: 0.35rem;
}

.modal-subtitle {
  margin-top: 0.35rem;
}

.users-table {
  overflow-x: auto;

  table {
    width: 100%;
    border-collapse: collapse;
  }

  th,
  td {
    padding: 1rem;
    border-bottom: 1px solid #ddd;
    text-align: left;
  }

  th {
    background: #f0f0f0;
    font-weight: 600;
  }

  tr:hover {
    background: #fafafa;
  }
}

.action-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 30;
}

.modal-card {
  width: min(100%, 460px);
  max-height: calc(100vh - 2rem);
  overflow-y: auto;
  background: white;
  border-radius: 14px;
  padding: 1.25rem;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.22);
}

.modal-card-horizontal {
  width: min(100%, 720px);
  padding: 1.15rem 1.25rem 1.25rem;
}

.modal-header {
  display: flex;
  align-items: flex-start;
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

.modal-form {
  display: grid;
  gap: 1rem;
}

.modal-form-horizontal {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem;
  align-items: start;
}

.form-group-wide,
.form-buttons {
  grid-column: 1 / -1;
}

.form-group {
  display: grid;
  gap: 0.5rem;

  label {
    font-weight: 500;
  }
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;

  &:focus {
    outline: none;
    border-color: var(--app-highlight-color);
    box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.12);
  }
}

.form-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 0.25rem;
  justify-content: flex-end;
}

.btn,
.btn-small {
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.btn {
  padding: 0.75rem 1.25rem;
}

.btn-small {
  padding: 0.45rem 0.8rem;
  font-size: 0.85rem;
  background: #2196f3;
  color: white;

  &.btn-danger {
    background: #f44336;
  }
}

.btn-primary {
  background: var(--app-highlight-color);
  color: white;
}

.btn-success {
  background: var(--app-banner-color);
  color: white;
}

.btn-secondary {
  background: #6b7280;
  color: white;
}

@media (max-width: 640px) {
  .page-header {
    flex-direction: column;
  }

  .modal-form-horizontal {
    grid-template-columns: 1fr;
  }

  .btn,
  .btn-small {
    width: 100%;
    justify-content: center;
  }

  .form-buttons,
  .action-cell {
    flex-direction: column;
  }
}
</style>
