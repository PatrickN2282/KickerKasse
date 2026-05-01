<template>
  <div v-if="show" class="member-modal modal-overlay" @click.self="$emit('close')">
    <div class="modal-card">
      <header class="modal-header">
        <div>
          <h3>{{ editingId ? 'Mitglied bearbeiten' : 'Neues Mitglied anlegen' }}</h3>
          <p class="modal-subtitle">Stammdaten und Berechtigungen im Admin-Layout verwalten.</p>
        </div>
        <button class="modal-close" @click="$emit('close')">×</button>
      </header>

      <form class="modal-body-layout" @submit.prevent="handleSubmit">
        <aside class="modal-sidebar">
          <div class="photo-uploader">
            <div class="avatar-display" @click="$refs.fileInput.click()">
              <img v-if="photoPreview" :src="photoPreview" class="profile-img">
              <div v-else class="photo-placeholder">
                <span>Bild hochladen</span>
              </div>
              <div class="hover-overlay">Ändern</div>
            </div>
            <input ref="fileInput" type="file" hidden accept="image/*" @change="handlePhotoUpload">
          </div>

          <div class="sidebar-info-box">
            <label class="checkbox-card">
              <input v-model="localForm.has_discount" type="checkbox">
              <div class="checkbox-content">
                <span class="label">Rabattberechtigt</span>
                <span class="desc">Darf Mitgliederpreise an der Kasse nutzen.</span>
              </div>
            </label>

            <div v-if="editingId" class="summary-card balance-card">
              <span class="label">Aktuelles Guthaben</span>
              <span class="value">{{ formatBalance(currentMemberBalance || 0) }}</span>
              <div class="recharge-trigger">
                <input v-model.number="localRechargeAmount" type="number" step="0.01" placeholder="0,00€">
                <button type="button" class="btn-recharge" :disabled="!localRechargeAmount" @click="$emit('openRecharge')">Laden</button>
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
                <input v-model="localForm.first_name" type="text" required>
              </div>
              <div class="form-group">
                <label>Nachname*</label>
                <input v-model="localForm.last_name" type="text" required>
              </div>
            </div>
            <div class="form-group">
              <label>Mitgliedsnummer (Extern)</label>
              <input v-model="localForm.membership_number" type="text" placeholder="Optional">
            </div>
          </section>

          <section v-if="isTopAdmin" class="form-section highlight-box">
            <h4>System-Zugang &amp; Berechtigungen</h4>
            <div class="form-row">
              <div class="form-group">
                <label>E-Mail Adresse</label>
                <input v-model="localForm.email" type="email" placeholder="mail@beispiel.de">
              </div>
              <div class="form-group">
                <label>Rolle im System</label>
                <select v-model="localForm.role">
                  <option value="">Keine Berechtigung (Nur Mitglied)</option>
                  <option value="VERKAUF">Verkaufspersonal</option>
                  <option value="MANAGER">Manager</option>
                  <option value="ADMIN">Administrator</option>
                </select>
              </div>
            </div>

            <div v-if="localForm.role" class="password-box">
              <div class="form-group">
                <label>{{ hasExistingUserAccount ? 'Passwort überschreiben' : 'Initial-Passwort festlegen*' }}</label>
                <input
                  v-model="localForm.account_password"
                  type="password"
                  :required="!hasExistingUserAccount"
                  minlength="8"
                >
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
              <textarea v-model="localForm.notes" rows="3" placeholder="Interne Bemerkungen..."></textarea>
            </div>
          </section>
        </main>

        <footer class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="$emit('close')">Abbrechen</button>
          <button type="submit" class="btn btn-success">
            {{ editingId ? 'Änderungen speichern' : 'Mitglied anlegen' }}
          </button>
        </footer>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { formatBalance } from '@/services/utils'

const props = defineProps({
  show: { type: Boolean, required: true },
  editingId: { type: Number, default: null },
  initialFormData: { type: Object, default: () => ({}) },
  photoPreview: { type: String, default: null },
  currentMemberBalance: { type: Number, default: null },
  hasExistingUserAccount: { type: Boolean, default: false },
  rechargeAmount: { type: Number, default: null },
  isTopAdmin: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'save', 'photoUpload', 'openRecharge', 'update:rechargeAmount'])

const defaultForm = () => ({
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

const localForm = ref(defaultForm())
const localRechargeAmount = ref(null)

watch(() => props.initialFormData, (val) => {
  if (val) localForm.value = { ...defaultForm(), ...val }
}, { immediate: true, deep: true })

watch(() => props.rechargeAmount, (val) => {
  localRechargeAmount.value = val
}, { immediate: true })

watch(localRechargeAmount, (val) => {
  emit('update:rechargeAmount', val)
})

const handlePhotoUpload = (event) => {
  const file = event.target.files[0]
  if (file) emit('photoUpload', file)
}

const handleSubmit = () => {
  emit('save', { ...localForm.value })
}
</script>

<style scoped lang="scss">
.member-modal {
  --primary: #3b82f6;
  --success: #10b981;
  --bg-main: #f8fafc;
  --border: #e2e8f0;
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
  overflow: hidden;
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;

  h3 {
    margin: 0;
    font-size: 1.25rem;
  }
}

.modal-subtitle {
  color: #64748b;
  margin-top: 0.25rem;
  font-size: 0.875rem;
}

.modal-body-layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  overflow: hidden;
  height: 100%;
}

.modal-sidebar {
  padding: 1.5rem;
  background: var(--bg-main);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.modal-form-content {
  padding: 1.5rem;
  overflow-y: auto;
  max-height: calc(90vh - 160px);
}

.avatar-display {
  width: 150px;
  height: 150px;
  margin: 0 auto;
  border-radius: 20px;
  background: #fff;
  border: 2px dashed #cbd5e1;
  position: relative;
  overflow: hidden;
  cursor: pointer;

  &:hover .hover-overlay {
    opacity: 1;
  }
}

.profile-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 0.8rem;
}

.hover-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: 0.2s;
}

.summary-card {
  padding: 1rem;
  border-radius: 10px;
  border: 1px solid #a7f3d0;
  background: #ecfdf5;

  .label {
    font-size: 0.7rem;
    text-transform: uppercase;
    color: #065f46;
    font-weight: 700;
  }

  .value {
    display: block;
    font-size: 1.3rem;
    font-weight: 700;
    color: #047857;
    margin-top: 0.25rem;
  }
}

.recharge-trigger {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;

  input {
    width: 100%;
    padding: 0.4rem;
    border: 1px solid #a7f3d0;
    border-radius: 6px;
    font-size: 0.9rem;
  }

  .btn-recharge {
    background: #059669;
    color: white;
    border: none;
    padding: 0.4rem 0.75rem;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}

.checkbox-card {
  display: flex;
  gap: 0.75rem;
  padding: 0.9rem 1rem;
  background: white;
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;

  .label {
    font-weight: 600;
    font-size: 0.9rem;
  }

  .desc {
    font-size: 0.75rem;
    color: #64748b;
    display: block;
  }
}

.form-section {
  margin-bottom: 2rem;

  h4 {
    font-size: 0.875rem;
    text-transform: uppercase;
    color: #64748b;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
  }

  &.highlight-box {
    background: #f0f7ff;
    padding: 1.25rem;
    border-radius: 12px;
    border: 1px solid #bae6fd;
  }
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
  select,
  textarea {
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

.password-box {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px dashed #bae6fd;
}

.help-text {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.4rem;
}

.modal-footer {
  grid-column: 1 / -1;
  padding: 1.5rem;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  background: white;
}

.btn {
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  min-width: 120px;
}

.btn-success {
  background: var(--success);
  color: white;
}

.btn-secondary {
  background: #e2e8f0;
  color: #475569;
}

.modal-close {
  border: none;
  background: transparent;
  font-size: 1.6rem;
  cursor: pointer;
  color: #6b7280;
}

@media (max-width: 768px) {
  .modal-body-layout,
  .form-row {
    grid-template-columns: 1fr;
  }

  .modal-sidebar {
    border-right: none;
    border-bottom: 1px solid var(--border);
  }
}
</style>
