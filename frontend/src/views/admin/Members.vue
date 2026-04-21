<template>
  <div class="admin-members">
    <h2>Mitgliederverwaltung</h2>

    <button @click="showForm = !showForm" class="btn btn-primary">
      {{ showForm ? 'Abbrechen / Zurück' : 'Neues Mitglied' }}
    </button>

    <form v-if="showForm" @submit.prevent="handleSaveMember" class="form-section">
      <h3>{{ editingId ? 'Mitglied bearbeiten' : 'Neues Mitglied' }}</h3>
      <div class="form-grid">
        <div class="form-group">
          <label for="first_name">Vorname*:</label>
          <input v-model="formData.first_name" id="first_name" type="text" class="form-input" required />
        </div>
        <div class="form-group">
          <label for="last_name">Nachname*:</label>
          <input v-model="formData.last_name" id="last_name" type="text" class="form-input" required />
        </div>
      </div>
      <div class="form-group">
        <label for="membership_number">Mitgliedsnummer:</label>
        <input v-model="formData.membership_number" id="membership_number" type="text" class="form-input" />
      </div>
      <div class="form-grid">
        <label class="checkbox-row">
          <input v-model="formData.has_discount" type="checkbox" />
          Rabatt
        </label>
        <div v-if="authStore.isAdmin" class="form-group">
          <label for="role">Rolle:</label>
          <select v-model="formData.role" id="role" class="form-input">
            <option value="">Keine Rolle</option>
            <option value="CASHIER">Verkauf</option>
            <option value="KASSENMITGLIED">VerkaufAdmin</option>
            <option value="ADMIN">Admin</option>
          </select>
        </div>
      </div>

      <div v-if="editingId" class="form-group recharge-section">
        <label for="recharge">Guthaben aufladen:</label>
        <small class="form-help">
          Aufzuladenden Wert eintragen, Passwort des angemeldeten Benutzers eintragen, Bestätigen
        </small>
        <div class="recharge-input-group">
          <input
            v-model.number="rechargeAmount"
            id="recharge"
            type="number"
            placeholder="0.00"
            step="0.01"
            min="0"
            class="form-input"
          />
          <button
            @click="openRechargeModal"
            type="button"
            class="btn btn-info"
            :disabled="!rechargeAmount || rechargeAmount <= 0"
          >
            + Aufladen
          </button>
        </div>
        <small v-if="editingId && currentMemberBalance !== null">
          Aktuelles Guthaben: {{ formatBalance(currentMemberBalance) }}
        </small>
      </div>

      <div class="form-group">
        <label for="photo">Foto:</label>
        <input @change="handlePhotoUpload" id="photo" type="file" accept="image/*" class="form-input" />
        <div v-if="photoPreview" class="photo-preview">
          <img :src="photoPreview" :alt="fullFormName" style="max-width: 150px; max-height: 150px;" />
        </div>
      </div>
      <button type="submit" class="btn btn-success">Speichern</button>
    </form>

    <div v-if="memberStore.isLoading" class="loading">Läuft...</div>
    <div v-else class="members-table">
      <table>
        <thead>
          <tr>
            <th style="width: 60px;">Foto</th>
            <th>Nr.</th>
            <th>Mitgliedsnummer</th>
            <th>Name</th>
            <th>Rabatt</th>
            <th>Rolle</th>
            <th>Guthaben</th>
            <th>Aktionen</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="member in memberStore.members" :key="member.id">
            <td class="photo-cell">
              <img v-if="member.photo_path" :src="`/api/members/${member.id}/photo`" :alt="getMemberFullName(member)" class="member-thumb" />
              <span v-else class="no-photo">-</span>
            </td>
            <td>{{ member.member_number }}</td>
            <td>{{ member.membership_number || '-' }}</td>
            <td>{{ getMemberShortName(member) }}</td>
            <td>{{ member.has_discount ? 'Ja' : 'Nein' }}</td>
            <td>{{ getRoleLabel(member.role) }}</td>
            <td class="balance">{{ formatBalance(member.balance_cents) }}</td>
            <td>
              <button @click="editMember(member)" class="btn-small">Bearbeiten</button>
              <button @click="deleteMember(member.id)" class="btn-small btn-danger" :disabled="!authStore.isAdmin">
                Löschen
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <PasswordConfirmModal
      :show="showRechargeModal"
      title="Mitgliedsguthaben aufladen"
      message="Bitte Zugangsdaten des aktuell angemeldeten Benutzers bestätigen."
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
import { getMemberFullName, getMemberShortName, getRoleLabel } from '@/services/member'
import PasswordConfirmModal from '@/components/PasswordConfirmModal.vue'
import apiService from '@/services/api'

const authStore = useAuthStore()
const memberStore = useMemberStore()
const notificationStore = useNotificationStore()

const showForm = ref(false)
const editingId = ref(null)
const photoFile = ref(null)
const photoPreview = ref(null)
const rechargeAmount = ref(null)
const currentMemberBalance = ref(null)
const showRechargeModal = ref(false)
const formData = reactive({
  first_name: '',
  last_name: '',
  membership_number: '',
  email: '',
  phone: '',
  has_discount: true,
  role: '',
})

const fullFormName = computed(() => [formData.first_name, formData.last_name].filter(Boolean).join(' '))

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
  const payload = {
    ...formData,
    role: authStore.isAdmin ? formData.role || null : undefined,
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
  formData.has_discount = true
  formData.role = ''
  photoFile.value = null
  photoPreview.value = null
  rechargeAmount.value = null
  currentMemberBalance.value = null
  editingId.value = null
  showForm.value = false
}

const editMember = (member) => {
  editingId.value = member.id
  formData.first_name = member.first_name || ''
  formData.last_name = member.last_name || ''
  formData.membership_number = member.membership_number || ''
  formData.email = member.email || ''
  formData.phone = member.phone || ''
  formData.has_discount = member.has_discount ?? true
  formData.role = member.role || ''
  currentMemberBalance.value = member.balance_cents
  rechargeAmount.value = null
  showForm.value = true
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

.form-section {
  background: #f5f5f5;
  padding: 1.5rem;
  border-radius: 4px;
  margin: 1rem 0;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
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

.form-help {
  display: block;
  margin-bottom: 0.5rem;
  color: #666;
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
  margin-top: 2rem;
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
</style>
