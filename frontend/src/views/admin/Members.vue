<template>
  <div class="admin-members">
    <div class="page-header">
      <div class="title-row">
        <h2>Mitgliederverwaltung</h2>
        <span class="title-sep">|</span>
        <span class="page-subtitle">Stammdaten, Guthaben und System-Zugänge zentral pflegen.</span>
      </div>
      <div class="page-header-actions">
        <button class="btn btn-primary" @click="openCreateModal">
          <span class="icon">+</span> Neues Mitglied
        </button>
      </div>
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
              <td class="text-right">
                <div class="action-cell">
                  <button class="btn-action" @click="editMember(member)">Bearbeiten</button>
                  <button
                    class="btn-action btn-action-danger"
                    :disabled="!authStore.isAdmin"
                    @click="deleteMember(member.id)"
                  >Löschen</button>
                </div>
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
      <div class="modal-card modal-compact">
        <header class="modal-header">
          <div>
            <h3>{{ editingId ? 'Mitglied bearbeiten' : 'Neues Mitglied anlegen' }}</h3>
            <p class="modal-subtitle">Stammdaten und Berechtigungen verwalten.</p>
          </div>
          <button class="close-btn" @click="closeMemberModal">✕</button>
        </header>

        <form class="modal-compact-layout" @submit.prevent="handleSaveMember">
          <div class="modal-scroller">

            <div class="main-form-grid">
              <!-- LINKE SEITE: Foto & Rabatt-Checkbox -->
              <div class="image-upload-section">
                <span class="section-label">Foto</span>
                <button
                  v-if="photoPreview"
                  type="button"
                  class="image-preview-trigger"
                  aria-label="Foto anpassen"
                  @click="openPhotoEditor"
                >
                  <div class="avatar-display compact-avatar interactive-image-frame">
                    <img :src="photoPreview" :alt="memberPhotoAlt" class="profile-img">
                    <span class="image-preview-overlay">Anpassen</span>
                  </div>
                </button>
                <div v-else class="avatar-display compact-avatar">
                  <div class="photo-placeholder">
                    <span>Kein Bild ausgewählt</span>
                  </div>
                </div>
                <div v-if="!photoPreview" class="image-action-buttons">
                  <label class="upload-button btn-action">
                    Bild auswählen
                    <input ref="fileInput" type="file" hidden @change="handlePhotoUpload" accept="image/*">
                  </label>
                </div>

                <!-- Hierher verschoben: Rabattberechtigt-Checkbox -->
                <label class="checkbox-card compact-cb">
                  <input v-model="formData.has_discount" type="checkbox">
                  <div class="checkbox-content">
                    <span class="label">Rabattberechtigt</span>
                    <span class="desc">Darf Mitgliederpreise nutzen.</span>
                  </div>
                </label>
              </div>

              <!-- RECHTE SEITE: Eingabefelder & Guthaben aufladen -->
              <div class="fields-section">
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

                <!-- Hierher verschoben: Guthaben aufbuchen (Hat jetzt volle Breite für Input + Button) -->
                <div v-if="editingId" class="summary-card compact-summary balance-card">
                  <div class="summary-text-layout">
                    <span class="label">Guthaben</span>
                    <span class="value">{{ formatBalance(currentMemberBalance || 0) }}</span>
                  </div>
                  <div class="recharge-trigger">
                    <input v-model.number="rechargeAmount" type="number" step="0.01" placeholder="0,00€">
                    <button type="button" class="btn-recharge" @click="openRechargeModal" :disabled="!rechargeAmount">Laden</button>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="authStore.isTopAdmin" class="options-section highlight-box">
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
                  <label> {{ hasExistingUserAccount ? 'Passwort überfragen' : 'Initial-Passwort festlegen*' }}</label>
                  <input v-model="formData.account_password" type="password"
                         :required="!hasExistingUserAccount" minlength="8">
                </div>
                <p class="help-text">
                  {{ hasExistingUserAccount ? 'Nur ausfüllen, wenn das Passwort neu gesetzt werden soll.' : 'Erforderlich für den ersten System-Login.' }}
                </p>
              </div>
            </div>

            <div class="options-section">
              <h4>Zusatzangaben</h4>
              <div class="form-group">
                <label>Interne Notizen</label>
                <textarea v-model="formData.notes" rows="2" placeholder="Interne Bemerkungen..."></textarea>
              </div>
            </div>

          </div>

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
    <ImageEditorModal
      :show="showPhotoCropModal"
      :image-src="photoCropSource"
      :restore-source="photoRestoreSrc"
      title="Mitgliederbild bearbeiten"
      subtitle="Verschieben und zoomen, um den gewünschten Bildausschnitt festzulegen."
      :aspect-ratio="1"
      :frame-width="280"
      :output-width="560"
      :can-restore="Boolean(photoRestoreSrc)"
      restore-label="Ausgangsbild wiederherstellen"
      :can-delete="Boolean(photoPreview || persistedPhotoExists)"
      delete-label="Foto löschen"
      @close="closePhotoEditor"
      @apply="handlePhotoCropApply"
      @delete="handlePhotoDelete"
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
import ImageEditorModal from '@/components/ImageEditorModal.vue'
import PasswordConfirmModal from '@/components/PasswordConfirmModal.vue'
import apiService from '@/services/api'

const authStore = useAuthStore()
const memberStore = useMemberStore()
const notificationStore = useNotificationStore()

const showMemberModal = ref(false)
const editingId = ref(null)
const photoFile = ref(null)
const photoPreview = ref(null)
const photoOriginalSrc = ref(null)
const photoCropSource = ref(null)
const pendingPhotoOriginalSrc = ref(null)
const showPhotoCropModal = ref(false)
const photoDeleteRequested = ref(false)
const photoPendingOriginalUpload = ref(false)
const persistedPhotoExists = ref(false)
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

const memberPhotoAlt = computed(() => {
  const fullName = [formData.first_name, formData.last_name].filter(Boolean).join(' ').trim()
  return fullName ? `Foto von ${fullName}` : 'Mitgliederfoto-Vorschau'
})

const photoRestoreSrc = computed(() => pendingPhotoOriginalSrc.value || photoOriginalSrc.value)

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

const readFileAsDataUrl = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (event) => resolve(event.target.result)
    reader.onerror = () => reject(new Error('Datei konnte nicht gelesen werden'))
    reader.readAsDataURL(file)
  })
}

const checkImageExists = async (url) => {
  try {
    const response = await fetch(url, { credentials: 'include' })
    return response.ok
  } catch {
    return false
  }
}

const withCacheBust = (url, token = Date.now()) => `${url}?t=${token}`

const handlePhotoUpload = async (event) => {
  const [file] = event.target.files || []
  event.target.value = ''
  if (!file) return
  if (file.size > 5 * 1024 * 1024) {
    notificationStore.error('Bild ist zu groß (max 5MB)')
    return
  }

  try {
    const dataUrl = await readFileAsDataUrl(file)
    photoCropSource.value = dataUrl
    pendingPhotoOriginalSrc.value = dataUrl
    showPhotoCropModal.value = true
  } catch (error) {
    console.error('Member image file read error:', error)
    notificationStore.error('Das ausgewählte Bild konnte nicht gelesen werden')
  }
}

const openPhotoEditor = () => {
  if (!photoPreview.value) return
  photoCropSource.value = photoPreview.value
  pendingPhotoOriginalSrc.value = null
  showPhotoCropModal.value = true
}

const closePhotoEditor = () => {
  showPhotoCropModal.value = false
  photoCropSource.value = null
  pendingPhotoOriginalSrc.value = null
}

const handlePhotoCropApply = ({ blob, dataUrl }) => {
  photoFile.value = new File([blob], 'member-photo.jpg', { type: 'image/jpeg' })
  photoPreview.value = dataUrl
  photoOriginalSrc.value = pendingPhotoOriginalSrc.value || photoOriginalSrc.value
  photoPendingOriginalUpload.value = Boolean(pendingPhotoOriginalSrc.value)
  photoDeleteRequested.value = false
  showPhotoCropModal.value = false
  photoCropSource.value = null
  pendingPhotoOriginalSrc.value = null
}

const requestPhotoRemoval = () => {
  photoPreview.value = null
  photoFile.value = null
  photoOriginalSrc.value = null
  photoCropSource.value = null
  pendingPhotoOriginalSrc.value = null
  showPhotoCropModal.value = false
  photoPendingOriginalUpload.value = false
  photoDeleteRequested.value = Boolean(editingId.value && persistedPhotoExists.value)
}

const handlePhotoDelete = () => {
  requestPhotoRemoval()
  closePhotoEditor()
}

const syncMemberPhoto = async (memberId) => {
  if (photoDeleteRequested.value) {
    try {
      await apiService.delete(`/members/${memberId}/photo`)
      photoDeleteRequested.value = false
      persistedPhotoExists.value = false
    } catch (error) {
      console.error('Member photo delete error:', error)
      notificationStore.error('Vorhandenes Mitgliederbild konnte nicht gelöscht werden')
      return false
    }
  }

  if (!photoFile.value) return true

  if (photoPendingOriginalUpload.value && photoOriginalSrc.value) {
    try {
      const originalBlob = await dataUrlToBlob(photoOriginalSrc.value)
      const originalFormData = new FormData()
      originalFormData.append('file', new File([originalBlob], 'original.jpg', { type: 'image/jpeg' }))
      await fetch(`/api/members/${memberId}/original-photo`, {
        method: 'POST',
        body: originalFormData,
        credentials: 'include'
      })
    } catch (error) {
      console.error('Failed to back up original member photo raw payload:', error)
    }
  }

  try {
    const fd = new FormData()
    fd.append('file', photoFile.value)
    const response = await fetch(`/api/members/${memberId}/photo`, {
      method: 'POST',
      body: fd,
      credentials: 'include'
    })
    if (response.ok) {
      photoFile.value = null
      photoPendingOriginalUpload.value = false
      persistedPhotoExists.value = true
      return true
    }
    notificationStore.error('Bild-Upload fehlgeschlagen')
    return false
  } catch (e) {
    console.error('Member photo upload error:', e)
    notificationStore.error('Fehler beim Übertragen des Bildes')
    return false
  }
}

const dataUrlToBlob = (dataUrl) => {
  return new Promise((resolve, reject) => {
    const parts = dataUrl.split(',')
    const mimeMatch = parts[0].match(/:(.*?);/)
    if (!mimeMatch) {
      reject(new Error('Invalid data URL'))
      return
    }
    const mime = mimeMatch[1]
    const bStr = atob(parts[1])
    let n = bStr.length
    const u8arr = new Uint8Array(n)
    while (n--) {
      u8arr[n] = bStr.charCodeAt(n)
    }
    resolve(new Blob([u8arr], { type: mime }))
  })
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
      const photoSynced = await syncMemberPhoto(editingId.value)
      if (!photoSynced) return
      notificationStore.success('Mitglied aktualisiert')
      closeMemberModal()
    }
  } else {
    const result = await memberStore.createMember(payload)
    if (result) {
      const photoSynced = await syncMemberPhoto(result.id)
      if (!photoSynced && photoFile.value) {
        notificationStore.warning('Mitglied wurde erstellt, aber der Bild-Upload ist fehlgeschlagen.')
      } else if (!photoSynced && photoPreview.value) {
        notificationStore.warning('Mitglied wurde erstellt, aber das bisherige Bild konnte nicht übernommen werden.')
      }
      notificationStore.success('Mitglied erstellt')
      closeMemberModal()
    }
  }
}

const editMember = async (member) => {
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
  const cacheBust = Date.now()
  photoPreview.value = member.photo_path ? withCacheBust(`/api/members/${member.id}/photo`, cacheBust) : null
  photoOriginalSrc.value = null
  photoPendingOriginalUpload.value = false
  photoCropSource.value = null
  pendingPhotoOriginalSrc.value = null
  photoFile.value = null
  photoDeleteRequested.value = false
  persistedPhotoExists.value = !!member.photo_path
  currentMemberBalance.value = member.balance_cents
  hasExistingUserAccount.value = !!member.has_user_account
  showMemberModal.value = true

  if (member.photo_path) {
    const originalUrl = withCacheBust(`/api/members/${member.id}/original-photo`, cacheBust)
    if (await checkImageExists(originalUrl)) {
      photoOriginalSrc.value = originalUrl
    } else {
      photoOriginalSrc.value = null
    }
  }
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
    } catch (error) {
      console.error('Member delete error:', error)
      notificationStore.error('Fehler beim Löschen')
    }
  }
}

const resetForm = () => {
  editingId.value = null
  photoFile.value = null
  photoPreview.value = null
  photoOriginalSrc.value = null
  photoCropSource.value = null
  pendingPhotoOriginalSrc.value = null
  showPhotoCropModal.value = false
  photoDeleteRequested.value = false
  photoPendingOriginalUpload.value = false
  persistedPhotoExists.value = false
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
  padding: 0.75rem 1rem;
  background: var(--app-background-color);
  min-height: 100%;
}

.page-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--app-background-color);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: -0.75rem -1rem 0.75rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.13);
}

.title-row {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  flex-wrap: wrap;

  h2 { font-size: 1.25rem; color: #333; margin: 0; }
}

.title-sep {
  color: #aaa;
  font-weight: 300;
}

.page-header-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.page-subtitle, .modal-subtitle { color: #64748b; margin: 0; }

.table-toolbar {
  margin-bottom: 0.6rem;
}

.search-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 0.9rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;

  &:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
  }
}

/* Tabelle */
.members-table-wrapper {
  background: color-mix(in srgb, var(--app-background-color) 30%, white);
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--app-background-color) 65%, #777);
  overflow-x: auto;
}

.members-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;

  thead {
    background: color-mix(in srgb, var(--app-background-color) 75%, white);
  }

  th {
    padding: 0.5rem 0.75rem;
    color: #475569;
    font-weight: 600;
    font-size: 0.8rem;
    text-align: left;
  }

  td {
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
  }

  tr:hover td {
    background: color-mix(in srgb, var(--app-background-color) 60%, white);
  }

  tr:last-child td {
    border-bottom: none;
  }
}

.photo-cell { width: 60px; }
.member-thumb-frame {
  width: 36px; height: 36px;
  border-radius: 8px;
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

.action-cell {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
  flex-wrap: wrap;
  width: 100%;
}
.empty-state-cell { text-align: center; color: #64748b; }

/* Modal Basis */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 1rem;
}

.modal-card {
  background: white;
  width: 100%;
  max-height: 650px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.modal-compact {
  max-width: 650px;
}

.modal-header {
  padding: 0.9rem 1.2rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  background: linear-gradient(90deg, #0f766e 0%, #0ea5e9 100%);
  h3 { margin: 0; font-size: 1.1rem; font-weight: 600; color: #ffffff; }
  .modal-subtitle { margin: 0.35rem 0 0; color: rgba(255,255,255,0.9); font-size: 0.85rem; }
}

.modal-compact-layout {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-scroller {
  padding: 1rem 1.2rem;
  overflow-y: auto;
  max-height: calc(650px - 110px);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Bild + Kernfelder nebeneinander */
.main-form-grid {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 1rem;
  align-items: start;
}

.section-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #64748b;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.image-upload-section {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0.5rem;
}

.image-action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;

  .btn-action {
    flex: 1 1 100%;
    justify-content: center;
    text-align: center;
  }
}

.image-preview-trigger {
  display: block;
  width: 100%;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
}

.interactive-image-frame {
  position: relative;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}

.image-preview-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.58);
  color: #fff;
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.image-preview-trigger:hover .interactive-image-frame,
.image-preview-trigger:focus-visible .interactive-image-frame {
  transform: translateY(-1px);
  border-color: #93c5fd;
  box-shadow: 0 8px 18px rgba(14, 165, 233, 0.18);
}

.image-preview-trigger:hover .image-preview-overlay,
.image-preview-trigger:focus-visible .image-preview-overlay {
  opacity: 1;
}

.image-preview-trigger:focus-visible {
  outline: 2px solid #38bdf8;
  outline-offset: 4px;
  border-radius: 12px;
}

.avatar-display {
  width: 100%;
  height: 120px;
  border-radius: 14px;
  background: #fff;
  border: 2px dashed #cbd5e1;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.compact-avatar {
  height: 120px;
}

.profile-img { width: 100%; height: 100%; object-fit: cover; }
.photo-placeholder { height: 100%; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 0.8rem; text-align: center; }

.compact-summary {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  justify-content: center;

  .summary-text-layout {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }

  .label {
    font-size: 0.7rem;
    text-transform: uppercase;
    color: #065f46;
    font-weight: 700;
    letter-spacing: 0.02em;
  }

  .value {
    font-size: 1.3rem;
    font-weight: 800;
    color: #047857;
    margin: 0;
    line-height: 1;
  }
}

.recharge-trigger {
  display: flex; gap: 0.5rem; margin-top: 0.5rem;
  input { width: 100%; padding: 0.4rem; border: 1px solid #a7f3d0; border-radius: 6px; font-size: 0.9rem; }
  .btn-recharge { background: #059669; color: white; border: none; padding: 0.4rem 0.75rem; border-radius: 6px; font-weight: 600; cursor: pointer; white-space: nowrap; }
}

.fields-section {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  .form-group { margin-bottom: 0; }
}

/* Optionale Sektionen unterhalb des Haupt-Grids */
.options-section {
  border-top: 1px dashed var(--border);
  padding-top: 0.9rem;
  h4 {
    font-size: 0.875rem;
    text-transform: uppercase;
    color: #64748b;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.35rem;
    margin-bottom: 0.65rem;
  }
  &.highlight-box { background: #f0f7ff; padding: 0.75rem 0.9rem; border-radius: 12px; border: 1px solid #bae6fd; }
}

.compact-cb {
  display: flex;
  gap: 0.6rem;
  padding: 0.6rem 0.8rem;
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  align-items: center;
  min-height: 44px;
  transition: background-color 0.15s ease, border-color 0.15s ease;
  &:hover { background: #f1f5f9; border-color: #cbd5e1; }
  input { margin-top: 0; }
  .label { display: block; font-size: 0.85rem; font-weight: 600; color: #1e293b; }
  .desc { display: block; font-size: 0.72rem; color: #64748b; line-height: 1.3; margin-top: 0.05rem; }
}

/* Formular */
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.form-group {
  margin-bottom: 0.6rem;
  label { display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.25rem; color: #334155; }
  input, select, textarea {
    width: 100%; padding: 0.5rem 0.7rem; border: 1px solid var(--border); border-radius: 8px; font-size: 0.9rem; color: #0f172a;
    &:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }
  }
}

.password-box { margin-top: 1rem; padding-top: 1rem; border-top: 1px dashed #bae6fd; }
.help-text { font-size: 0.75rem; color: #64748b; margin-top: 0.4rem; }

/* Modal Footer */
.modal-footer {
  padding: 0.75rem 1.2rem;
  border-top: 1px solid var(--border);
  background: #f8fafc;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

/* Button & Action Styles */
.btn { padding: 0.55rem 1.1rem; border-radius: 6px; font-weight: 600; cursor: pointer; border: none; font-size: 0.9rem; min-height: 40px; }
.btn-primary { background: var(--primary); color: white; }
.btn-success { background: var(--success); color: white; }
.btn-secondary { background: #e2e8f0; color: #475569; }

.btn-action {
  border: 1px solid var(--border); background: white; color: #334155;
  padding: 0.45rem 0.75rem; border-radius: 8px; cursor: pointer; font-weight: 600;
  display: inline-flex; align-items: center; justify-content: center;
}
.btn-action-danger { border-color: #fecaca; color: #b91c1c; }
.upload-button { overflow: hidden; }

.close-btn {
  width: 34px; height: 34px; border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.45);
  background: rgba(255,255,255,0.18);
  color: #ffffff; font-size: 1.1rem; cursor: pointer;
  display: grid; place-items: center; flex-shrink: 0;
  &:hover { background: rgba(255,255,255,0.3); }
}

.loading-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 3rem; color: #64748b;
}

.spinner {
  width: 2rem; height: 2rem; border-radius: 50%; border: 3px solid #e2e8f0; border-top-color: var(--primary);
  animation: spin 0.8s linear infinite; margin-bottom: 1rem;
}

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 600px) {
  .main-form-grid { grid-template-columns: 1fr; }
  .form-row { grid-template-columns: 1fr; }
}
</style>
