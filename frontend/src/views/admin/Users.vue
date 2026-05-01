<template>
  <div class="admin-users">
    <div class="page-header">
      <div>
        <h2>Benutzerverwaltung</h2>
        <p class="page-subtitle">Direkte Benutzerkonten verwalten und Mitgliedskonten separat im gleichen Admin-Layout einsehen.</p>
      </div>

      <button class="btn btn-primary" @click="openCreateModal">
        <span class="icon">+</span> Neuer Benutzer
      </button>
    </div>

    <div class="users-table-wrapper">
      <table class="users-table">
        <thead>
          <tr>
            <th>Typ</th>
            <th>Benutzername</th>
            <th>E-Mail</th>
            <th>Rolle</th>
            <th class="text-right">Aktionen</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in displayedUsers" :key="user.id">
            <td>
              <span :class="['badge', user.entryType === 'Benutzer' ? 'badge-success' : 'badge-light']">
                {{ user.entryType }}
              </span>
            </td>
            <td class="font-bold">{{ user.username }}</td>
            <td>{{ user.email || '-' }}</td>
            <td>
              <span :class="['role-tag', roleClass(user.role)]">{{ roleLabel(user.role) }}</span>
            </td>
            <td class="text-right action-cell">
              <button v-if="user.deletable" class="btn-action" @click="openEditModal(user)">Bearbeiten</button>
              <button v-if="user.canResetPassword" class="btn-action" @click="openPasswordReset(user)">Passwort setzen</button>
              <button v-if="user.deletable" class="btn-action btn-action-danger" @click="deleteUser(user.id)">Löschen</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <UserModal
      :show="showUserModal"
      :editing-user-id="editingUserId"
      :initial-form-data="formData"
      @close="closeUserModal"
      @save="handleSaveUser"
    />

    <UserPasswordResetModal
      :resetting-password-for="resettingPasswordFor"
      @close="closePasswordReset"
      @save="submitPasswordReset"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useNotificationStore } from '@/stores/notification'
import { getMemberFullName, getRoleLabel } from '@/services/member'
import apiService from '@/services/api'
import UserModal from './modal/UserModal.vue'
import UserPasswordResetModal from './modal/UserPasswordResetModal.vue'

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

const roleLabel = getRoleLabel
const roleClass = (role) => ({
  TOP_ADMIN: 'role-tag-top-admin',
  ADMIN: 'role-tag-admin',
  MANAGER: 'role-tag-manager',
  VERKAUF: 'role-tag-verkauf',
}[role] || 'role-tag-default')

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

const handleSaveUser = async (data) => {
  const payload = {
    username: data.username.trim(),
    email: data.email?.trim() || null,
    role: data.role,
  }

  if (data.password) {
    payload.password = data.password
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
}

const closePasswordReset = () => {
  resettingPasswordFor.value = null
}

const submitPasswordReset = async (password) => {
  try {
    if (resettingPasswordFor.value.memberId) {
      await apiService.put(`/members/${resettingPasswordFor.value.memberId}`, {
        account_password: password,
      })
    } else {
      await apiService.put(`/users/${resettingPasswordFor.value.id}`, {
        password,
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
  --primary: #3b82f6;
  --success: #10b981;
  --border: #e2e8f0;
  padding: 1.5rem;
  background: white;
  min-height: 100%;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 2rem;

  h2 {
    font-size: 1.5rem;
    color: #1e293b;
  }
}

.page-subtitle,
.modal-subtitle,
.help-text {
  color: #64748b;
}

.page-subtitle {
  margin-top: 0.25rem;
}

.users-table-wrapper {
  background: white;
  border-radius: 12px;
  border: 1px solid var(--border);
  overflow-x: auto;
  overflow-y: hidden;
}

.users-table {
  width: 100%;
  min-width: 720px;
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
    vertical-align: middle;
  }
}

.text-right {
  text-align: right;
}

.action-cell {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
  flex-wrap: wrap;
  width: 100%;
}

.font-bold {
  font-weight: 600;
}

.badge,
.role-tag {
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

.badge-light,
.role-tag-default {
  background: #f1f5f9;
  color: #475569;
}

.role-tag-top-admin {
  background: #fee2e2;
  color: #b91c1c;
}

.role-tag-admin {
  background: #ede9fe;
  color: #6d28d9;
}

.role-tag-manager {
  background: #dbeafe;
  color: #1d4ed8;
}

.role-tag-verkauf {
  background: #dcfce7;
  color: #15803d;
}

.btn-action {
  border: 1px solid var(--border);
  background: white;
  color: #334155;
  padding: 0.45rem 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
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

.modal-card-compact {
  max-width: 520px;
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
}

.compact-section {
  margin-bottom: 1rem;
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
  select {
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

.help-text {
  display: block;
  margin-top: 0.4rem;
  font-size: 0.75rem;
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

.btn-action-danger {
  border-color: #fecaca;
  color: #b91c1c;
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

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .form-row,
  .modal-footer,
  .action-cell {
    grid-template-columns: 1fr;
    flex-direction: column;
  }

  .btn,
  .btn-action {
    width: 100%;
  }
}
</style>
