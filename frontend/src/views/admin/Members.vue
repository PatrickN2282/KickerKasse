<template>
  <div class="admin-members">
    <div class="page-header">
      <div>
        <h2>Mitgliederverwaltung</h2>
        <p class="page-subtitle">Stammdaten, Guthaben und System-Zugänge zentral pflegen.</p>
      </div>
      <button class="btn btn-primary" @click="openCreateModal">
        <span class="icon">+</span> Neues Mitglied
      </button>
    </div>

    <div v-if="memberStore.isLoading" class="loading-state">
      <div class="spinner"></div>
      <p>Daten werden geladen...</p>
    </div>

    <div v-else>
      <div class="table-toolbar">
        <input
          v-model="memberSearch"
          type="text"
          placeholder="Nach Name oder Nummer suchen..."
          class="search-input"
        >
      </div>
      <div class="members-table-wrapper">
        <table class="members-table">
          <thead>
            <tr>
              <th>Foto</th>
              <th>Nr.</th>
              <th>Mitgliedsnummer</th>
              <th>Name</th>
              <th>Rabatt</th>
              <th v-if="authStore.isTopAdmin">Rolle</th>
              <th v-if="authStore.isTopAdmin">Kontakt</th>
              <th>Guthaben</th>
              <th class="text-right">Aktionen</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="member in filteredMembers" :key="member.id">
              <td class="photo-cell">
                <div class="member-thumb-frame">
                  <img
                    v-if="member.photo_path"
                    :src="`/api/members/${member.id}/photo`"
                    :alt="getMemberFullName(member)"
                    class="member-thumb"
                  >
                  <span v-else class="member-thumb-placeholder">
                    {{ member.first_name[0] }}{{ member.last_name[0] }}
                  </span>
                </div>
              </td>
              <td>{{ member.member_number }}</td>
              <td><code class="member-code">{{ member.membership_number || '-' }}</code></td>
              <td class="font-bold">{{ getMemberFullName(member) }}</td>
              <td>
                <span :class="['badge', member.has_discount ? 'badge-success' : 'badge-light']">
                  {{ member.has_discount ? 'Berechtigt' : 'Kein Rabatt' }}
                </span>
              </td>
              <td v-if="authStore.isTopAdmin">
                <span class="role-tag">{{ getRoleLabel(member.role) }}</span>
              </td>
              <td v-if="authStore.isTopAdmin" class="contact-cell">
                <div class="small-text">{{ member.email || '-' }}</div>
                <div class="small-text text-muted">{{ member.phone || '' }}</div>
              </td>
              <td class="balance-cell font-bold">{{ formatBalance(member.balance_cents) }}</td>
              <td class="text-right action-cell">
                <button class="btn-action" @click="editMember(member)">Bearbeiten</button>
                <button 
                  class="btn-action btn-action-danger" 
                  :disabled="!authStore.isAdmin" 
                  @click="deleteMember(member.id)"
                >Löschen</button>
              </td>
            </tr>
            <tr v-if="filteredMembers.length === 0">
              <td :colspan="authStore.isTopAdmin ? 9 : 7" class="empty-state-cell">Keine Mitglieder gefunden</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="showMemberModal" class="modal-overlay" @click.self="closeMemberModal">
      <div class="modal-card">
        <header class="modal-header">
          <div>
            <h3>{{ editingId ? 'Mitglied bearbeiten' : 'Neues Mitglied anlegen' }}</h3>
            <p class="modal-subtitle">Stammdaten und Berechtigungen im Admin-Layout verwalten.</p>
          </div>
          <button class="modal-close" @click="closeMemberModal">×</button>
        </header>

        <form class="modal-body-layout" @submit.prevent="handleSaveMember">
          <aside class="modal-sidebar">
            <div class="photo-uploader">
              <div class="avatar-display" @click="$refs.fileInput.click()">
                <img v-if="photoPreview" :src="photoPreview" class="profile-img">
                <div v-else class="photo-placeholder">
                  <span>Bild hochladen</span>
                </div>
                <div class="hover-overlay">Ändern</div>
              </div>
              <input type="file" ref="fileInput" hidden @change="handlePhotoUpload" accept="image/*">
            </div>

            <div class="sidebar-info-box">
              <label class="checkbox-card">
                <input v-model="formData.has_discount" type="checkbox">
                <div class="checkbox-content">
                  <span class="label">Rabattberechtigt</span>
                  <span class="desc">Darf Mitgliederpreise an der Kasse nutzen.</span>
                </div>
              </label>

              <div v-if="editingId" class="summary-card balance-card">
                <span class="label">Aktuelles Guthaben</span>
                <span class="value">{{ formatBalance(currentMemberBalance || 0) }}</span>
                <div class="recharge-trigger">
                  <input v-model.number="rechargeAmount" type="number" step="0.01" placeholder="0,00€">
                  <button type="button" class="btn-recharge" @click="openRechargeModal" :disabled="!rechargeAmount">Laden</button>
                </div>
              </div>
            </div>
          </aside>

          <main class="modal-form-content">
            <section class="form-section">
              <h4>Stammdaten</h4>
              <div class="form-row">
                <div class="form-group">
                  <label>Vorname*</label>
                  <input v-model="formData.first_name" type="text" required>
                </div>
                <div class="form-group">
                  <label>Nachname*</label>
                  <input v-model="formData.last_name" type="text" required>
                </div>
              </div>
              <div class="form-group">
                <label>Mitgliedsnummer (Extern)</label>
                <input v-model="formData.membership_number" type="text" placeholder="Optional">
              </div>
            </section>

            <section v-if="authStore.isTopAdmin" class="form-section highlight-box">
              <h4>System-Zugang & Berechtigungen</h4>
              <div class="form-row">
                <div class="form-group">
                  <label>E-Mail Adresse</label>
                  <input v-model="formData.email" type="email" placeholder="mail@beispiel.de">
                </div>
                <div class="form-group">
                  <label>Rolle im System</label>
                  <select v-model="formData.role">
                    <option value="">Keine Berechtigung (Nur Mitglied)</option>
                    <option value="VERKAUF">Verkaufspersonal</option>
                    <option value="MANAGER">Manager</option>
                    <option value="ADMIN">Administrator</option>
                  </select>
                </div>
              </div>
              
              <div v-if="formData.role" class="password-box">
                <div class="form-group">
                  <label>{{ hasExistingUserAccount ? 'Passwort überschreiben' : 'Initial-Passwort festlegen*' }}</label>
                  <input v-model="formData.account_password" type="password" 
                         :required="!hasExistingUserAccount" minlength="8">
                </div>
                <p class="help-text">
                  {{ hasExistingUserAccount ? 'Nur ausfüllen, wenn das Passwort neu gesetzt werden soll.' : 'Erforderlich für den ersten System-Login.' }}
                </p>
              </div>
            </section>

            <section class="form-section">
              <h4>Zusatzangaben</h4>
              <div class="form-group">
                <label>Interne Notizen</label>
                <textarea v-model="formData.notes" rows="3" placeholder="Interne Bemerkungen..."></textarea>
              </div>
            </section>
          </main>

          <footer class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeMemberModal">Abbrechen</button>
            <button type="submit" class="btn btn-success">
              {{ editingId ? 'Änderungen speichern' : 'Mitglied anlegen' }}
            </button>
          </footer>
        </form>
      </div>
    </div>

    <PasswordConfirmModal
      :show="showRechargeModal"
      title="Guthaben aufladen"
      :message="rechargeModalMessage"
      :username="authStore.user?.username || ''"
      confirm-label="Jetzt aufladen"
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
import { getMemberFullName, getMemberSearchText, getRoleLabel } from '@/services/member'
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
const hasExistingUserAccount = ref(false)
const memberSearch = ref('')

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

const rechargeModalMessage = computed(() => {
  const amountCents = Math.round(Number(rechargeAmount.value || 0) * 100)
  const current = Number(currentMemberBalance.value || 0)
  return `Möchtest du ${formatBalance(amountCents)} aufladen?\nNeuer Kontostand: ${formatBalance(current + amountCents)}`
})

const filteredMembers = computed(() => {
  const search = memberSearch.value.trim().toLowerCase()

  if (!search) {
    return memberStore.members
  }

  return memberStore.members.filter(member => getMemberSearchText(member).includes(search))
})

const openCreateModal = () => {
  resetForm()
  showMemberModal.value = true
}

const closeMemberModal = () => {
  showMemberModal.value = false
  resetForm()
}

const handlePhotoUpload = (event) => {
  const file = event.target.files[0]
  if (file) {
    if (file.size > 2 * 1024 * 1024) {
      notificationStore.error('Bild ist zu groß (max 2MB)')
      return
    }
    photoFile.value = file
    const reader = new FileReader()
    reader.onload = (e) => photoPreview.value = e.target.result
    reader.readAsDataURL(file)
  }
}

const uploadPhotoToMember = async (memberId) => {
  if (!photoFile.value) return true
  try {
    const fd = new FormData()
    fd.append('file', photoFile.value)
    const response = await fetch(`/api/members/${memberId}/photo`, {
      method: 'POST',
      body: fd,
      credentials: 'include'
    })
    return response.ok
  } catch (e) { return false }
}

const handleSaveMember = async () => {
  const payload = { ...formData }
  if (!authStore.isTopAdmin) {
    ['email', 'phone', 'role', 'account_password'].forEach(key => delete payload[key])
  } else if (!payload.role) {
    payload.role = null
    delete payload.account_password
  }

  if (editingId.value) {
    const success = await memberStore.updateMember(editingId.value, payload)
    if (success) {
      await uploadPhotoToMember(editingId.value)
      notificationStore.success('Mitglied aktualisiert')
      closeMemberModal()
    }
  } else {
    const result = await memberStore.createMember(payload)
    if (result) {
      await uploadPhotoToMember(result.id)
      notificationStore.success('Mitglied erstellt')
      closeMemberModal()
    }
  }
}

const editMember = (member) => {
  editingId.value = member.id
  Object.assign(formData, {
    first_name: member.first_name || '',
    last_name: member.last_name || '',
    membership_number: member.membership_number || '',
    email: member.email || '',
    phone: member.phone || '',
    notes: member.notes || '',
    has_discount: member.has_discount ?? true,
    role: member.role || '',
    account_password: ''
  })
  photoPreview.value = member.photo_path ? `/api/members/${member.id}/photo` : null
  currentMemberBalance.value = member.balance_cents
  hasExistingUserAccount.value = !!member.has_user_account
  showMemberModal.value = true
}

const openRechargeModal = () => { showRechargeModal.value = true }

const handleRecharge = async (password) => {
  showRechargeModal.value = false
  const amountCents = Math.round(rechargeAmount.value * 100)
  const updated = await memberStore.rechargeMember(editingId.value, amountCents, password)
  if (updated) {
    currentMemberBalance.value = updated.balance_cents
    rechargeAmount.value = null
    notificationStore.success('Guthaben aufgeladen')
  }
}

const deleteMember = async (id) => {
  if (confirm('Mitglied wirklich unwiderruflich löschen?')) {
    try {
      await apiService.delete(`/members/${id}`)
      notificationStore.success('Mitglied gelöscht')
      await memberStore.getMembers()
    } catch (e) { notificationStore.error('Fehler beim Löschen') }
  }
}

const resetForm = () => {
  editingId.value = null
  photoFile.value = null
  photoPreview.value = null
  rechargeAmount.value = null
  Object.keys(formData).forEach(key => {
    formData[key] = key === 'has_discount' ? true : ''
  })
}

onMounted(() => memberStore.getMembers())
</script>

<style scoped lang="scss">
.admin-members {
  --primary: #3b82f6;
  --success: #10b981;
  --bg-main: #f8fafc;
  --border: #e2e8f0;
  padding: 1.5rem;
  background: white;
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  h2 { font-size: 1.5rem; color: #1e293b; }
}

.page-subtitle, .modal-subtitle { color: #64748b; margin-top: 0.25rem; }

.table-toolbar {
  margin-bottom: 1rem;
}

.search-input {
  width: 100%;
  padding: 0.85rem 1rem;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 0.95rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;

  &:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
  }
}

/* Tabelle */
.members-table-wrapper {
  background: white;
  border-radius: 12px;
  border: 1px solid var(--border);
  overflow-x: auto;
}

.members-table {
  width: 100%;
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

.photo-cell { width: 74px; }
.member-thumb-frame {
  width: 44px; height: 44px;
  border-radius: 10px;
  overflow: hidden;
  background: #e2e8f0;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid var(--border);
}

.member-thumb { width: 100%; height: 100%; object-fit: cover; }
.member-thumb-placeholder { font-size: 0.8rem; font-weight: bold; color: #64748b; }

.badge {
  display: inline-flex; padding: 0.3rem 0.7rem; border-radius: 999px;
  font-size: 0.8rem; font-weight: 600;
}
.badge-success { background: #dcfce7; color: #166534; }
.badge-light { background: #f1f5f9; color: #475569; }

.role-tag { background: #f1f5f9; color: #475569; padding: 0.25rem 0.6rem; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
.member-code { background: #f8fafc; padding: 0.2rem 0.4rem; border-radius: 4px; border: 1px solid var(--border); font-size: 0.85rem; }

.action-cell { display: flex; justify-content: flex-end; gap: 0.5rem; }
.empty-state-cell { text-align: center; color: #64748b; }

/* Modal Basis */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 1rem;
}

.modal-card {
  background: white; width: 100%; max-width: 900px; max-height: 90vh;
  border-radius: 16px; display: flex; flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

.modal-header {
  padding: 1.5rem; border-bottom: 1px solid var(--border);
  display: flex; justify-content: space-between;
  h3 { margin: 0; font-size: 1.25rem; }
}

/* Modal Body Layout (Grid) */
.modal-body-layout { 
  display: grid; 
  grid-template-columns: 260px 1fr; 
  overflow: hidden;
  height: 100%;
}

.modal-sidebar {
  padding: 1.5rem; background: var(--bg-main);
  border-right: 1px solid var(--border); display: flex; flex-direction: column; gap: 1.5rem;
}

.modal-form-content { 
  padding: 1.5rem; 
  overflow-y: auto; 
  max-height: calc(90vh - 160px); 
}

/* Foto & Sidebar Komponenten */
.avatar-display {
  width: 150px; height: 150px; margin: 0 auto;
  border-radius: 20px; background: #fff; border: 2px dashed #cbd5e1;
  position: relative; overflow: hidden; cursor: pointer;
  &:hover .hover-overlay { opacity: 1; }
}

.profile-img { width: 100%; height: 100%; object-fit: cover; }
.photo-placeholder { height: 100%; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 0.8rem; }
.hover-overlay {
  position: absolute; inset: 0; background: rgba(0,0,0,0.4);
  color: white; display: flex; align-items: center; justify-content: center; opacity: 0; transition: 0.2s;
}

.summary-card {
  padding: 1rem; border-radius: 10px; border: 1px solid #a7f3d0; background: #ecfdf5;
  .label { font-size: 0.7rem; text-transform: uppercase; color: #065f46; font-weight: 700; }
  .value { display: block; font-size: 1.3rem; font-weight: 700; color: #047857; margin-top: 0.25rem; }
}

.recharge-trigger {
  display: flex; gap: 0.5rem; margin-top: 0.75rem;
  input { width: 100%; padding: 0.4rem; border: 1px solid #a7f3d0; border-radius: 6px; font-size: 0.9rem; }
  .btn-recharge { background: #059669; color: white; border: none; padding: 0.4rem 0.75rem; border-radius: 6px; font-weight: 600; cursor: pointer; }
}

.checkbox-card {
  display: flex; gap: 0.75rem; padding: 0.9rem 1rem; background: white; border: 1px solid var(--border); border-radius: 10px; cursor: pointer;
  .label { font-weight: 600; font-size: 0.9rem; }
  .desc { font-size: 0.75rem; color: #64748b; display: block; }
}

/* Formular Sektionen */
.form-section {
  margin-bottom: 2rem;
  h4 { font-size: 0.875rem; text-transform: uppercase; color: #64748b; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin-bottom: 1rem; }
  &.highlight-box { background: #f0f7ff; padding: 1.25rem; border-radius: 12px; border: 1px solid #bae6fd; }
}

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.form-group {
  margin-bottom: 1rem;
  label { display: block; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.4rem; color: #1e293b; }
  input, select, textarea {
    width: 100%; padding: 0.6rem 0.8rem; border: 1px solid var(--border); border-radius: 8px; font-size: 0.95rem;
    &:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }
  }
}

.password-box { margin-top: 1rem; padding-top: 1rem; border-top: 1px dashed #bae6fd; }
.help-text { font-size: 0.75rem; color: #64748b; margin-top: 0.4rem; }

/* Modal Footer - Rechts unten platziert */
.modal-footer { 
  grid-column: 1 / -1; // Spannt über beide Grid-Spalten
  padding: 1.5rem; 
  border-top: 1px solid var(--border); 
  display: flex; 
  justify-content: flex-end; // Schiebt Buttons nach rechts
  gap: 1rem; 
  background: white;
}

/* Button & Action Styles */
.btn { padding: 0.6rem 1.2rem; border-radius: 8px; font-weight: 600; cursor: pointer; border: none; min-width: 120px; }
.btn-primary { background: var(--primary); color: white; }
.btn-success { background: var(--success); color: white; }
.btn-secondary { background: #e2e8f0; color: #475569; }

.btn-action {
  border: 1px solid var(--border); background: white; color: #334155;
  padding: 0.45rem 0.75rem; border-radius: 8px; cursor: pointer; font-weight: 600;
}
.btn-action-danger { border-color: #fecaca; color: #b91c1c; }

.modal-close { border: none; background: transparent; font-size: 1.6rem; cursor: pointer; color: #6b7280; }

.loading-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 3rem; color: #64748b;
}

.spinner {
  width: 2rem; height: 2rem; border-radius: 50%; border: 3px solid #e2e8f0; border-top-color: var(--primary);
  animation: spin 0.8s linear infinite; margin-bottom: 1rem;
}

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .modal-body-layout, .form-row { grid-template-columns: 1fr; }
  .modal-sidebar { border-right: none; border-bottom: 1px solid var(--border); }
}
</style>
