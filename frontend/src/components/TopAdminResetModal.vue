<template>
  <div v-if="show" class="modal-overlay">
    <div class="modal-dialog">
      <div class="modal-header">
        <div>
          <h3>Passwort zurücksetzen</h3>
          <p class="subtitle">TopAdmin-Zugang</p>
        </div>
        <!-- Anforderung 1: Modal darf nur über den expliziten X-Button/"Abbrechen" schließen,
             nicht per Klick außerhalb (siehe globale Modal-Konvention, Anforderung 4). -->
        <button class="close-btn" @click="close">✕</button>
      </div>

      <div class="modal-body">
        <template v-if="!submitted">
          <p class="message">
            Bitte gib die für diesen Account hinterlegte E-Mail-Adresse ein, um einen
            Link zum Zurücksetzen des Passworts zu erhalten.
          </p>
          <p v-if="!resetEmailChannelConfigured" class="warning-message">
            Hinweis: Aktuell ist kein E-Mail-Server für den Versand konfiguriert
            (SMTP/E-Mail deaktiviert oder unvollständig). Ein Reset-Link kann erst
            zugestellt werden, wenn die E-Mail-Einstellungen durch den TopAdmin
            vollständig eingerichtet wurden.
          </p>
          <div class="form-group">
            <label>Hinterlegte E-Mail-Adresse</label>
            <input
              ref="emailInput"
              v-model.trim="email"
              type="email"
              class="form-input"
              :class="{ 'form-input-error': error }"
              placeholder="admin@verein.de"
              @keyup.enter="submit"
            />
            <p v-if="error" class="field-error">{{ error }}</p>
          </div>
        </template>
        <template v-else>
          <p class="message success-message">
            Falls die E-Mail-Adresse hinterlegt ist, wurde soeben ein Link zum Zurücksetzen
            des Passworts an diese Adresse versendet. Wiederholte Anfragen innerhalb einer Minute
            versenden keine weitere E-Mail. Der Link ist 60 Minuten gültig und
            kann nur einmal verwendet werden.
          </p>
        </template>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="close">{{ submitted ? 'Schließen' : 'Abbrechen' }}</button>
        <button v-if="!submitted" class="btn btn-primary" :disabled="!email || isSubmitting" @click="submit">
          {{ isSubmitting ? 'Wird gesendet…' : 'Link anfordern' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import apiService from '@/services/api'

const props = defineProps({
  show: { type: Boolean, required: true },
})

const emit = defineEmits(['close'])

const email = ref('')
const error = ref('')
const isSubmitting = ref(false)
const submitted = ref(false)
const emailInput = ref(null)
const resetEmailChannelConfigured = ref(true)

const reset = () => {
  email.value = ''
  error.value = ''
  isSubmitting.value = false
  submitted.value = false
}

const close = () => {
  reset()
  emit('close')
}

const submit = async () => {
  if (!email.value) return
  isSubmitting.value = true
  error.value = ''
  try {
    await apiService.post('/auth/password-reset/request', { email: email.value })
    submitted.value = true
  } catch (err) {
    error.value = err.response?.data?.detail || 'Anfrage konnte nicht gesendet werden. Bitte später erneut versuchen.'
  } finally {
    isSubmitting.value = false
  }
}

watch(() => props.show, async (show) => {
  if (!show) {
    reset()
    return
  }
  try {
    const { data } = await apiService.get('/auth/setup-status')
    resetEmailChannelConfigured.value = Boolean(data?.top_admin_reset_email_channel_configured)
  } catch {
    resetEmailChannelConfigured.value = true
  }
  await nextTick()
  emailInput.value?.focus()
})
</script>

<style scoped lang="scss">
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.25rem;
  z-index: 3000;
}

.modal-dialog {
  background: #ffffff;
  border-radius: 16px;
  width: 100%;
  max-width: 440px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  overflow: hidden;
}

.modal-header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: linear-gradient(90deg, #0f766e 0%, #0ea5e9 100%);

  h3 { margin: 0; color: #ffffff; font-size: 1.1rem; }
  .subtitle { margin: 0.35rem 0 0; color: rgba(255, 255, 255, 0.9); font-size: 0.85rem; }
}

.close-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.45);
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
  font-size: 1.1rem;
  cursor: pointer;
  display: grid;
  place-items: center;
  flex-shrink: 0;

  &:hover { background: rgba(255, 255, 255, 0.3); }
}

.modal-body {
  padding: 1rem 1.25rem;
}

.modal-footer {
  padding: 0.95rem 1.25rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  background: #ffffff;
}

.message {
  margin: 0 0 1rem;
  font-size: 0.92rem;
  line-height: 1.5;
  color: #334155;
}

.success-message {
  color: #166534;
}

.warning-message {
  margin: 0 0 1rem;
  font-size: 0.86rem;
  line-height: 1.45;
  color: #9a3412;
  background: #ffedd5;
  border: 1px solid #fdba74;
  border-radius: 10px;
  padding: 0.55rem 0.7rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  box-sizing: border-box;
}

.form-input-error {
  border-color: #c62828 !important;
  box-shadow: 0 0 0 3px rgba(198, 40, 40, 0.12);
}

.field-error {
  margin: 0.4rem 0 0;
  color: #c62828;
  font-size: 0.82rem;
  font-weight: 600;
}

.btn {
  border: none;
  border-radius: 8px;
  padding: 0.65rem 1rem;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;

  &:disabled { opacity: 0.55; cursor: not-allowed; }
}

.btn-secondary { background: #f8fafc; color: #475569; border: 1px solid #cbd5e1; }
.btn-primary { background: var(--app-highlight-color, #209529); color: var(--app-highlight-contrast, #fff); }
</style>
