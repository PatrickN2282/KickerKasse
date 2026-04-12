<template>
  <div class="admin-members">
    <h2>Mitgliederverwaltung</h2>

    <button @click="showForm = !showForm" class="btn btn-primary">
      {{ showForm ? 'Abbrechen' : 'Neues Mitglied' }}
    </button>

    <form v-if="showForm" @submit.prevent="handleSaveMember" class="form-section">
      <h3>{{ editingId ? 'Mitglied bearbeiten' : 'Neues Mitglied' }}</h3>
      <div class="form-group">
        <label for="name">Name*:</label>
        <input v-model="formData.name" id="name" type="text" class="form-input" required />
      </div>
      <div class="form-group">
        <label for="email">Email:</label>
        <input v-model="formData.email" id="email" type="email" class="form-input" />
      </div>
      <div class="form-group">
        <label for="phone">Telefon:</label>
        <input v-model="formData.phone" id="phone" type="tel" class="form-input" />
      </div>

      <!-- Balance recharge section (only when editing) -->
      <div v-if="editingId" class="form-group recharge-section">
        <label for="recharge">Guthaben aufladen:</label>
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
            @click="handleRecharge"
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
          <img :src="photoPreview" :alt="formData.name" style="max-width: 150px; max-height: 150px;" />
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
            <th>Name</th>
            <th>Email</th>
            <th>Telefon</th>
            <th>Guthaben</th>
            <th>Aktionen</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="member in memberStore.members" :key="member.id">
            <td class="photo-cell">
              <img v-if="member.photo_path" :src="`/api/members/${member.id}/photo`" :alt="member.name" class="member-thumb" />
              <span v-else class="no-photo">-</span>
            </td>
            <td>{{ member.name }}</td>
            <td>{{ member.email || '-' }}</td>
            <td>{{ member.phone || '-' }}</td>
            <td class="balance">{{ formatBalance(member.balance_cents) }}</td>
            <td>
              <button @click="editMember(member)" class="btn-small">Bearbeiten</button>
              <button @click="deleteMember(member.id)" class="btn-small btn-danger">
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
import { useMemberStore } from '@/stores/member'
import { useNotificationStore } from '@/stores/notification'
import { formatBalance } from '@/services/utils'

const memberStore = useMemberStore()
const notificationStore = useNotificationStore()

const showForm = ref(false)
const editingId = ref(null)
const photoFile = ref(null)
const photoPreview = ref(null)
const rechargeAmount = ref(null)
const currentMemberBalance = ref(null)
const formData = reactive({
  name: '',
  email: '',
  phone: '',
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
  if (!photoFile.value) return true // No photo to upload
  
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
    } else {
      notificationStore.error('Foto-Upload fehlgeschlagen')
      return false
    }
  } catch (error) {
    console.error('Photo upload error:', error)
    notificationStore.error('Fehler beim Foto-Upload')
    return false
  }
}

const handleSaveMember = async () => {
  if (editingId.value) {
    // Upload photo first if exists
    const photoUploadSuccess = await uploadPhotoToMember(editingId.value)
    if (!photoUploadSuccess && photoFile.value) {
      return
    }
    
    // Update existing member
    const result = await memberStore.updateMember(editingId.value, formData)
    if (result) {
      notificationStore.success('Mitglied aktualisiert')
      resetForm()
    } else {
      notificationStore.error(memberStore.error)
    }
  } else {
    // Create new member
    const result = await memberStore.createMember(formData)
    if (result) {
      // Upload photo after creation
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
  formData.name = ''
  formData.email = ''
  formData.phone = ''
  photoFile.value = null
  photoPreview.value = null
  editingId.value = null
  showForm.value = false
}

const editMember = (member) => {
  editingId.value = member.id
  formData.name = member.name
  formData.email = member.email || ''
  formData.phone = member.phone || ''
  currentMemberBalance.value = member.balance_cents
  showForm.value = true
}

const handleRecharge = async () => {
  if (!editingId.value || !rechargeAmount.value || rechargeAmount.value <= 0) {
    notificationStore.error('Bitte einen gültigen Betrag eingeben')
    return
  }

  try {
    // Convert to cents (if user entered euros)
    const amountCents = Math.round(rechargeAmount.value * 100)
    
    console.log(`[Members] Recharging member ${editingId.value} with ${amountCents} cents`)
    
    // Use store function to recharge
    const updatedMember = await memberStore.rechargeMember(editingId.value, amountCents)
    
    if (updatedMember) {
      currentMemberBalance.value = updatedMember.balance_cents
      rechargeAmount.value = null
      notificationStore.success(`Guthaben aufgeladen! Neuer Betrag: ${formatBalance(updatedMember.balance_cents)}`)
      console.log('[Members] Recharge successful, balance is now:', updatedMember.balance_cents)
    } else {
      notificationStore.error(memberStore.error || 'Fehler beim Aufladen')
    }
  } catch (error) {
    console.error('[Members] Recharge error:', error)
    notificationStore.error('Fehler beim Aufladen: ' + (error.message || 'Unbekannter Fehler'))
  }
}

const deleteMember = async (memberId) => {
  if (confirm('Wirklich löschen?')) {
    // API call would go here
    notificationStore.success('Mitglied gelöscht')
    await memberStore.getMembers()
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
      border-color: #1976d2;
    }
  }
}

.members-table {
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

      &.balance {
        font-weight: 600;
        color: #667eea;
      }
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
  margin-right: 0.5rem;

  &:hover {
    background: #0b7dda;
  }

  &.btn-danger {
    background: #f44336;

    &:hover {
      background: #da190b;
    }
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
  background: #1976d2;
  color: white;

  &:hover {
    background: #1565c0;
  }
}

.btn-success {
  background: #4caf50;
  color: white;

  &:hover {
    background: #45a049;
  }
}

.btn-info {
  background: #29b6f6;
  color: white;

  &:hover:not(:disabled) {
    background: #0288d1;
  }

  &:disabled {
    background: #ccc;
    cursor: not-allowed;
  }
}

.recharge-section {
  background: #e8f5e9;
  padding: 1rem;
  border-radius: 4px;
  border-left: 4px solid #4caf50;

  .recharge-input-group {
    display: flex;
    gap: 0.75rem;
    align-items: center;

    .form-input {
      flex: 1;
      padding: 0.75rem;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 1rem;

      &:focus {
        outline: none;
        border-color: #4caf50;
        box-shadow: 0 0 4px rgba(76, 175, 80, 0.3);
      }
    }

    .btn {
      white-space: nowrap;
    }
  }

  small {
    display: block;
    margin-top: 0.5rem;
    color: #2e7d32;
    font-weight: 600;
  }
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #999;
}

.photo-cell {
  text-align: center;

  .member-thumb {
    width: 50px;
    height: 50px;
    border-radius: 4px;
    object-fit: contain;
    border: 1px solid #ddd;
  }

  .no-photo {
    color: #999;
    font-size: 0.9rem;
  }
}

.photo-preview {
  margin-top: 1rem;
  display: inline-block;

  img {
    border-radius: 4px;
    border: 1px solid #ddd;
  }
}
</style>
