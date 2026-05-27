<template>
  <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card modal-compact">
      <header class="modal-header">
        <div>
          <h3>{{ editingId ? 'Mitglied bearbeiten' : 'Neues Mitglied anlegen' }}</h3>
          <p class="modal-subtitle">Stammdaten und Berechtigungen verwalten.</p>
        </div>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </header>

      <form class="modal-compact-layout" @submit.prevent="$emit('save')">
        <div class="modal-scroller">
          <div class="main-form-grid">
            <div class="image-upload-section">
              <span class="section-label">Foto</span>
              <template v-if="photoPreview && isGif">
                <div class="avatar-display compact-avatar gif-preview-frame">
                  <img :src="photoPreview" :alt="memberPhotoAlt" class="profile-img">
                  <span class="gif-badge">GIF 🎬</span>
                </div>
                <div class="image-action-buttons">
                  <label class="upload-button btn-action">
                    Foto ersetzen
                    <input type="file" hidden accept="image/*" @change="$emit('photo-upload', $event)">
                  </label>
                </div>
              </template>
              <template v-else-if="photoPreview">
                <button
                  type="button"
                  class="image-preview-trigger"
                  aria-label="Foto anpassen"
                  @click="$emit('open-photo-editor')"
                >
                  <div class="avatar-display compact-avatar interactive-image-frame">
                    <img :src="photoPreview" :alt="memberPhotoAlt" class="profile-img">
                    <span class="image-preview-overlay">Anpassen</span>
                  </div>
                </button>
              </template>
              <template v-else>
                <div class="avatar-display compact-avatar">
                  <div class="photo-placeholder">
                    <span>Kein Bild ausgewählt</span>
                  </div>
                </div>
                <div class="image-action-buttons">
                  <label class="upload-button btn-action">
                    Bild auswählen
                    <input type="file" hidden accept="image/*" @change="$emit('photo-upload', $event)">
                  </label>
                </div>
              </template>

              <label class="checkbox-card compact-cb">
                <input v-model="formData.has_discount" type="checkbox">
                <div class="checkbox-content">
                  <span class="label">Rabattberechtigt</span>
                  <span class="desc">Darf Mitgliederpreise nutzen.</span>
                </div>
              </label>
            </div>

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

              <div v-if="editingId" class="summary-card compact-summary balance-card">
                <div class="summary-text-layout">
                  <span class="label">Guthaben</span>
                  <span class="value">{{ currentMemberBalanceDisplay }}</span>
                </div>
                <div class="recharge-trigger">
                  <input v-model.number="rechargeAmount" type="number" step="0.01" placeholder="0,00€">
                  <button type="button" class="btn-recharge" :disabled="!rechargeAmount" @click="$emit('open-recharge')">Laden</button>
                </div>
              </div>
            </div>
          </div>

          <div v-if="authIsTopAdmin" class="options-section highlight-box">
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
                <input
                  v-model="formData.account_password"
                  type="password"
                  :required="!hasExistingUserAccount"
                  minlength="8"
                >
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
defineProps({
  show: { type: Boolean, required: true },
  editingId: { type: [Number, String], default: null },
  authIsTopAdmin: { type: Boolean, default: false },
  hasExistingUserAccount: { type: Boolean, default: false },
  photoPreview: { type: String, default: null },
  isGif: { type: Boolean, default: false },
  memberPhotoAlt: { type: String, default: '' },
  currentMemberBalanceDisplay: { type: String, default: '' },
})

const formData = defineModel('formData', {
  type: Object,
  required: true,
})

const rechargeAmount = defineModel('rechargeAmount', {
  type: [Number, String],
  default: null,
})

defineEmits(['close', 'save', 'open-photo-editor', 'photo-upload', 'open-recharge'])
</script>

<style scoped lang="scss">
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 1rem;
}

.modal-card {
  --primary: #3b82f6;
  --border: #e2e8f0;

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

.gif-preview-frame {
  position: relative;
}

.gif-badge {
  position: absolute;
  bottom: 4px;
  right: 4px;
  z-index: 1;
  font-size: 9px;
  font-weight: 800;
  padding: 2px 5px;
  border-radius: 3px;
  background: #fef3c7;
  color: #92400e;
}

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

  .btn-recharge {
    background: #059669;
    color: white;
    border: none;
    padding: 0.4rem 0.75rem;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }
}

.fields-section {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;

  .form-group { margin-bottom: 0; }
}

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

  &.highlight-box {
    background: #f0f7ff;
    padding: 0.75rem 0.9rem;
    border-radius: 12px;
    border: 1px solid #bae6fd;
  }
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

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }

.form-group {
  margin-bottom: 0.6rem;

  label { display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.25rem; color: #334155; }

  input, select, textarea {
    width: 100%;
    padding: 0.5rem 0.7rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.9rem;
    color: #0f172a;

    &:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
  }
}

.password-box { margin-top: 1rem; padding-top: 1rem; border-top: 1px dashed #bae6fd; }
.help-text { font-size: 0.75rem; color: #64748b; margin-top: 0.4rem; }

.modal-footer {
  padding: 0.75rem 1.2rem;
  border-top: 1px solid var(--border);
  background: #f8fafc;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn { padding: 0.55rem 1.1rem; border-radius: 6px; font-weight: 600; cursor: pointer; border: none; font-size: 0.9rem; min-height: 40px; }
.btn-success { background: #10b981; color: white; }
.btn-secondary { background: #e2e8f0; color: #475569; }

.btn-action {
  border: 1px solid var(--border);
  background: white;
  color: #334155;
  padding: 0.45rem 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.upload-button { overflow: hidden; }

.close-btn {
  width: 34px; height: 34px; border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.45);
  background: rgba(255,255,255,0.18);
  color: #ffffff; font-size: 1.1rem; cursor: pointer;
  display: grid; place-items: center; flex-shrink: 0;

  &:hover { background: rgba(255,255,255,0.3); }
}

@media (max-width: 600px) {
  .main-form-grid { grid-template-columns: 1fr; }
  .form-row { grid-template-columns: 1fr; }
}
</style>
