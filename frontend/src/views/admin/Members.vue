<template>
  <div class="admin-members">
    <div class="page-header">
      <h2>Mitgliederverwaltung</h2>
      <button
        class="btn btn-primary"
        @click="openCreateModal"
      >
        Neues Mitglied
      </button>
    </div>

    <div
      v-if="memberStore.isLoading"
      class="loading"
    >
      Läuft...
    </div>
    <div
      v-else
      class="members-table"
    >
      <table>
        <thead>
          <tr>
            <th style="width: 60px;">
              Foto
            </th>
            <th>Nr.</th>
            <th>Mitgliedsnummer</th>
            <th>Name</th>
            <th>Rabatt</th>
            <th v-if="authStore.isTopAdmin">Rolle</th>
            <th v-if="authStore.isTopAdmin">E-Mail</th>
            <th v-if="authStore.isTopAdmin">Telefon</th>
            <th>Guthaben</th>
            <th>Aktionen</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="member in memberStore.members"
            :key="member.id"
          >
            <td class="photo-cell">
              <img
                v-if="member.photo_path"
                :src="`/api/members/${member.id}/photo`"
                :alt="getMemberFullName(member)"
                class="member-thumb"
              >
              <span
                v-else
                class="no-photo"
              >-</span>
            </td>
            <td>{{ member.member_number }}</td>
            <td>{{ member.membership_number || '-' }}</td>
            <td>{{ getMemberFullName(member) }}</td>
            <td>{{ member.has_discount ? 'Ja' : 'Nein' }}</td>
            <td v-if="authStore.isTopAdmin">{{ getRoleLabel(member.role) }}</td>
            <td v-if="authStore.isTopAdmin">{{ member.email || '-' }}</td>
            <td v-if="authStore.isTopAdmin">{{ member.phone || '-' }}</td>
            <td class="balance">
              {{ formatBalance(member.balance_cents) }}
            </td>
            <td>
              <button
                class="btn-small"
                @click="editMember(member)"
              >
                Bearbeiten
              </button>
              <button
                class="btn-small btn-danger"
                :disabled="!authStore.isAdmin"
                @click="deleteMember(member.id)"
              >
                Löschen
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      v-if="showMemberModal"
      class="modal-overlay"
      @click.self="closeMemberModal"
    >
      <div class="modal-card">
        <div class="modal-header">
          <div>
            <h3>{{ editingId ? 'Mitglied bearbeiten' : 'Neues Mitglied anlegen' }}</h3>
            <p class="modal-subtitle">
              Mitglied anlegen oder aktualisieren und alle relevanten Angaben gesammelt pflegen.
            </p>
          </div>
          <button
            class="modal-close"
            @click="closeMemberModal"
          >
            ×
          </button>
        </div>

        <form
          class="modal-form"
          @submit.prevent="handleSaveMember"
        >
          <section class="modal-section">
            <h4 class="modal-section-title">
              Basisdaten
            </h4>
            <div class="form-group">
              <label for="first_name">Vorname*</label>
              <input
                id="first_name"
                v-model="formData.first_name"
                type="text"
                class="form-input"
                required
              >
            </div>
            <div class="form-group">
              <label for="last_name">Nachname*</label>
              <input
                id="last_name"
                v-model="formData.last_name"
                type="text"
                class="form-input"
                required
              >
            </div>
            <div class="form-group">
              <label for="membership_number">Mitgliedsnummer</label>
              <input
                id="membership_number"
                v-model="formData.membership_number"
                type="text"
                class="form-input"
              >
            </div>
            <label class="checkbox-row">
              <input
                v-model="formData.has_discount"
                type="checkbox"
              >
              Rabatt
            </label>
          </section>

          <section
            v-if="showContactFields || authStore.isTopAdmin"
            class="modal-section"
          >
            <h4 class="modal-section-title">
              Zugang & Kontakt
            </h4>
            <div
              v-if="showContactFields"
              class="form-group"
            >
              <label for="email">E-Mail</label>
              <input
                id="email"
                v-model="formData.email"
                type="email"
                class="form-input"
              >
            </div>
            <div
              v-if="showContactFields"
              class="form-group"
            >
              <label for="phone">Telefon</label>
              <input
                id="phone"
                v-model="formData.phone"
                type="text"
                class="form-input"
              >
            </div>
            <div
              v-if="authStore.isTopAdmin"
              class="form-group"
            >
              <label for="role">Rolle</label>
              <select
                id="role"
                v-model="formData.role"
                class="form-input"
              >
                <option value="">
                  Keine Rolle
                </option>
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
          </section>

          <section
            v-if="showAccountPasswordSection"
            class="modal-section role-account-box"
          >
            <h4 class="modal-section-title">
              Benutzerkonto
            </h4>
            <div
              v-if="currentAccountUsername"
              class="form-group"
            >
              <label>Loginname</label>
              <input
                :value="currentAccountUsername"
                type="text"
                class="form-input"
                readonly
              >
            </div>
            <div class="form-group">
              <label for="account_password">
                {{ hasExistingUserAccount ? 'Neues Passwort (optional)' : 'Passwort für Benutzerkonto*' }}
              </label>
              <input
                id="account_password"
                v-model="formData.account_password"
                type="password"
                class="form-input"
                :required="!hasExistingUserAccount"
                minlength="8"
                placeholder="Mindestens 8 Zeichen"
              >
            </div>
            <small class="form-help">
              {{ hasExistingUserAccount
                ? 'Bei bestehenden Benutzerkonten können Admin und Top-Admin hier ein neues Passwort setzen.'
                : 'Sobald eine Rolle vergeben wird, wird ein Benutzerkonto angelegt und ein Passwort benötigt.' }}
            </small>
          </section>
          <section class="modal-section">
            <h4 class="modal-section-title">
              Zusätzliche Angaben
            </h4>
            <div class="form-group">
              <label for="notes">Notizen</label>
              <textarea
                id="notes"
                v-model="formData.notes"
                class="form-input notes-input"
                rows="3"
              />
            </div>
          </section>

          <div
            v-if="editingId"
            class="modal-section recharge-section"
          >
            <h4 class="modal-section-title">
              Guthaben
            </h4>
            <label for="recharge">Guthaben aufladen</label>
            <small class="form-help">
              Aufzuladenden Wert eintragen, Passwort des angemeldeten Benutzers eintragen, Bestätigen
            </small>
            <div class="recharge-input-group">
              <input
                id="recharge"
                v-model.number="rechargeAmount"
                type="number"
                placeholder="0.00"
                step="0.01"
                min="0"
                class="form-input"
              >
              <button
                type="button"
                class="btn btn-info"
                :disabled="!rechargeAmount || rechargeAmount <= 0"
                @click="openRechargeModal"
              >
                + Aufladen
              </button>
            </div>
            <small v-if="editingId && currentMemberBalance !== null">
              Aktuelles Guthaben: {{ formatBalance(currentMemberBalance) }}
            </small>
          </div>

          <section class="modal-section">
            <h4 class="modal-section-title">
              Foto
            </h4>
            <div class="form-group">
              <label for="photo">Foto</label>
              <input
                id="photo"
                type="file"
                accept="image/*"
                class="form-input"
                @change="handlePhotoUpload"
              >
              <div
                v-if="photoPreview"
                class="photo-preview"
              >
                <img
                  :src="photoPreview"
                  :alt="fullFormName"
                  style="max-width: 150px; max-height: 150px;"
                >
              </div>
            </div>
          </section>

          <div class="form-buttons">
            <button
              type="submit"
              class="btn btn-success"
            >
              {{ editingId ? 'Aktualisieren' : 'Erstellen' }}
            </button>
            <button
              type="button"
              class="btn btn-secondary"
              @click="closeMemberModal"
            >
              Abbrechen / Zurück
            </button>
          </div>
        </form>
      </div>
    </div>
    <PasswordConfirmModal
      :show="showRechargeModal"
      title="Mitgliedsguthaben aufladen"
      :message="rechargeModalMessage"
      :username="authStore.user?.username || ''"
      confirm-label="Aufladen"
      @close="showRechargeModal = false"
      @confirm="handleRecharge"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useMemberStore } from '@/stores/member'
import { useNotificationStore } from '@/stores/notification'
import { formatBalance } from '@/services/utils'
import { getMemberFullName, getRoleLabel } from '@/services/member'
import PasswordConfirmModal from '@/components/PasswordConfirmModal.vue'
import apiService from '@/services/api'

const authStore = useAuthStore()
const memberStore = useMemberStore()
const notificationStore = useNotificationStore()

const showMemberModal = ref(false)
const editingId = ref(null)
const photoFile = ref(null)
const photoPreview = ref(null)
const rechargeAmount = ref(null)
const currentMemberBalance = ref(null)
const showRechargeModal = ref(false)
const currentAccountUsername = ref('')
const hasExistingUserAccount = ref(false)
const formData = reactive({
  first_name: '',
  last_name: '',
  membership_number: '',
  email: '',
  phone: '',
  notes: '',
  has_discount: true,
  role: '',
  account_password: '',
})

const openCreateModal = () => {
  resetForm()
  showMemberModal.value = true
}

const closeMemberModal = () => {
  showRechargeModal.value = false
  showMemberModal.value = false
  resetForm()
}

const fullFormName = computed(() => [formData.first_name, formData.last_name].filter(Boolean).join(' '))
const showContactFields = computed(() => authStore.isTopAdmin)
const showAccountPasswordSection = computed(() => authStore.isTopAdmin && !!formData.role)
const rechargeModalMessage = computed(() => {
  const amountCents = Math.max(Math.round(Number(rechargeAmount.value || 0) * 100), 0)
  const currentBalance = Number(currentMemberBalance.value || 0)
  const nextBalance = currentBalance + amountCents

  return [
    'Bitte Zugangsdaten des aktuell angemeldeten Benutzers bestätigen.',
    amountCents > 0 ? `Aufzuladender Wert: ${formatBalance(amountCents)}` : null,
    `Neuer Gesamtwert: ${formatBalance(nextBalance)}`,
  ].filter(Boolean).join('\n')
})

const handlePhotoUpload = (event) => {
  const file = event.target.files[0]
  if (file) {
    photoFile.value = file
    const reader = new FileReader()
    reader.onload = (e) => {
      photoPreview.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

const uploadPhotoToMember = async (memberId) => {
  if (!photoFile.value) return true

  try {
    const formDataUpload = new FormData()
    formDataUpload.append('file', photoFile.value)

    const response = await fetch(`/api/members/${memberId}/photo`, {
      method: 'POST',
      body: formDataUpload,
      credentials: 'include',
    })

    if (response.ok) {
      photoFile.value = null
      return true
    }

    notificationStore.error('Foto-Upload fehlgeschlagen')
    return false
  } catch (error) {
    console.error('Photo upload error:', error)
    notificationStore.error('Fehler beim Foto-Upload')
    return false
  }
}

const handleSaveMember = async () => {
  const payload = { ...formData }
  if (!authStore.isAdmin) {
    delete payload.email
    delete payload.phone
    delete payload.role
    delete payload.account_password
  } else if (!authStore.isTopAdmin) {
    delete payload.email
    delete payload.phone
    delete payload.role
    delete payload.account_password
  } else if (!payload.role) {
    payload.role = null
    delete payload.account_password
  } else if (!payload.account_password) {
    delete payload.account_password
  }

  if (authStore.isTopAdmin && payload.role && !hasExistingUserAccount.value && !formData.account_password) {
    notificationStore.error('Bitte ein Passwort für das Benutzerkonto vergeben')
    return
  }

  if (editingId.value) {
    const photoUploadSuccess = await uploadPhotoToMember(editingId.value)
    if (!photoUploadSuccess && photoFile.value) {
      return
    }

    const result = await memberStore.updateMember(editingId.value, payload)
    if (result) {
      notificationStore.success('Mitglied aktualisiert')
      resetForm()
    } else {
      notificationStore.error(memberStore.error)
    }
  } else {
    const result = await memberStore.createMember(payload)
    if (result) {
      if (photoFile.value) {
        const photoUploadSuccess = await uploadPhotoToMember(result.id)
        if (!photoUploadSuccess) {
          notificationStore.warning('Mitglied erstellt, aber Foto-Upload fehlgeschlagen')
        } else {
          notificationStore.success('Mitglied mit Foto erstellt')
        }
      } else {
        notificationStore.success('Mitglied erstellt')
      }
      resetForm()
    } else {
      notificationStore.error(memberStore.error)
    }
  }
}

const resetForm = () => {
  formData.first_name = ''
  formData.last_name = ''
  formData.membership_number = ''
  formData.email = ''
  formData.phone = ''
  formData.notes = ''
  formData.has_discount = true
  formData.role = ''
  formData.account_password = ''
  photoFile.value = null
  photoPreview.value = null
  rechargeAmount.value = null
  currentMemberBalance.value = null
  currentAccountUsername.value = ''
  hasExistingUserAccount.value = false
  editingId.value = null
  showMemberModal.value = false
}

const editMember = (member) => {
  editingId.value = member.id
  formData.first_name = member.first_name || ''
  formData.last_name = member.last_name || ''
  formData.membership_number = member.membership_number || ''
  formData.email = member.email || ''
  formData.phone = member.phone || ''
  formData.notes = member.notes || ''
  formData.has_discount = member.has_discount ?? true
  formData.role = member.role || ''
  formData.account_password = ''
  photoFile.value = null
  photoPreview.value = member.photo_path ? `/api/members/${member.id}/photo` : null
  currentMemberBalance.value = member.balance_cents
  currentAccountUsername.value = member.account_username || ''
  hasExistingUserAccount.value = !!member.has_user_account
  rechargeAmount.value = null
  showMemberModal.value = true
}

const openRechargeModal = () => {
  if (!editingId.value || !rechargeAmount.value || rechargeAmount.value <= 0) {
    notificationStore.error('Bitte einen gültigen Betrag eingeben')
    return
  }

  showRechargeModal.value = true
}

const handleRecharge = async (password) => {
  showRechargeModal.value = false

  try {
    const amountCents = Math.round(rechargeAmount.value * 100)
    const updatedMember = await memberStore.rechargeMember(editingId.value, amountCents, password)

    if (updatedMember) {
      currentMemberBalance.value = updatedMember.balance_cents
      rechargeAmount.value = null
      notificationStore.success(`Guthaben aufgeladen! Neuer Betrag: ${formatBalance(updatedMember.balance_cents)}`)
    } else {
      notificationStore.error(memberStore.error || 'Fehler beim Aufladen')
    }
  } catch (error) {
    console.error('[Members] Recharge error:', error)
    notificationStore.error('Fehler beim Aufladen: ' + (error.message || 'Unbekannter Fehler'))
  }
}

const deleteMember = async (memberId) => {
  if (!authStore.isAdmin) {
    notificationStore.error('Nur Admins dürfen Mitglieder löschen')
    return
  }

  if (confirm('Wirklich löschen?')) {
    try {
      await apiService.delete(`/members/${memberId}`)
      notificationStore.success('Mitglied gelöscht')
      await memberStore.getMembers()
    } catch (error) {
      notificationStore.error(error.response?.data?.detail || 'Fehler beim Löschen')
    }
  }
}

onMounted(async () => {
  await memberStore.getMembers()
})
</script>

<style scoped lang="scss">
.admin-members {
  background: white;
  padding: 2rem;
  border-radius: 8px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.modal-subtitle,
.modal-section-title,
.form-help {
  color: #6b7280;
}

.modal-subtitle {
  margin-top: 0.35rem;
}

.modal-form {
  display: grid;
  gap: 1rem;
}

.modal-section {
  display: grid;
  gap: 0.9rem;
  padding: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #f8fafc;
}

.modal-section-title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.form-group {
  display: grid;
  gap: 0.5rem;

  label {
    display: block;
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

  .notes-input {
    resize: vertical;
  }
}

.form-help {
  display: block;
}

.form-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.role-account-box {
  margin-bottom: 1rem;
  padding: 1rem;
  border-radius: 8px;
  background: #eef4ea;
  border: 1px solid rgba(92, 143, 58, 0.2);
}

.recharge-input-group {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.75rem;
}

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-weight: 600;
}

.members-table {
  overflow-x: auto;
  margin-top: 2rem;
}

.photo-cell,
.balance {
  font-weight: 600;
}

.member-thumb {
  width: 44px;
  height: 44px;
  object-fit: cover;
  border-radius: 50%;
}

.btn,
.btn-small {
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}

.btn {
  padding: 0.75rem 1.5rem;
}

.btn-small {
  padding: 0.4rem 0.8rem;
  margin-right: 0.5rem;
}

.btn-primary,
.btn-info {
  background: var(--app-highlight-color);
  color: white;
}

.btn-success {
  background: var(--app-banner-color);
  color: white;
}

.btn-danger {
  background: #f44336;
  color: white;
}

.btn-secondary {
  background: #6b7280;
  color: white;
}

table {
  width: 100%;
  border-collapse: collapse;

  th,
  td {
    padding: 1rem;
    border-bottom: 1px solid #ddd;
    text-align: left;
  }

  th {
    background: #f0f0f0;
  }
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 1000;
}

.modal-card {
  width: min(100%, 560px);
  max-height: calc(100vh - 2rem);
  overflow-y: auto;
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.22);
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

@media (max-width: 640px) {
  .page-header {
    flex-direction: column;
  }

  .form-buttons {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }

  .recharge-input-group {
    grid-template-columns: 1fr;
  }
}
</style>
