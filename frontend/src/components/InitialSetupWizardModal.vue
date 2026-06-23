<template>
  <div v-if="show" class="modal-overlay" @click.self="handleOverlayClick">
    <div class="modal-card wizard-card">
      <header class="modal-header">
        <div>
          <h3>Initial-Setup</h3>
          <p class="modal-subtitle">Richte Top-Admin, Vereinsdaten und den Start der Kasse ein.</p>
        </div>
        <button v-if="dismissible && (step === 0 || step === 4)" class="modal-close" type="button" @click="handleClose">×</button>
      </header>

      <div class="wizard-progress">
        <div
          v-for="(label, index) in stepLabels"
          :key="label"
          :class="['wizard-step', { active: step === index, done: step > index }]"
        >
          <span class="wizard-step__index">{{ index + 1 }}</span>
          <span class="wizard-step__label">{{ label }}</span>
        </div>
      </div>

      <div class="modal-body">
        <section v-if="step === 0" class="panel-stack">
          <div class="info-box">
            <strong>Top-Admin anlegen</strong>
            <p>Dieser Benutzer erhält Vollzugriff auf Einrichtung, Design, E-Mail-Konfiguration und Systemfunktionen.</p>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Benutzername</label>
              <input v-model.trim="topAdmin.username" type="text" class="form-input" placeholder="topadmin" />
            </div>
            <div class="form-group">
              <label>E-Mail</label>
              <input v-model.trim="topAdmin.email" type="email" class="form-input" placeholder="optional" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Passwort</label>
              <input v-model="topAdmin.password" type="password" class="form-input" />
            </div>
            <div class="form-group">
              <label>Passwort wiederholen</label>
              <input v-model="topAdmin.passwordConfirm" type="password" class="form-input" />
            </div>
          </div>
        </section>

        <section v-else-if="step === 1" class="panel-stack">
          <div class="info-box">
            <strong>Vereinsdaten</strong>
            <p>Diese Angaben können später im Top-Admin-Bereich geändert werden und stehen für Berichte bereit.</p>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Vereinsname</label>
              <input v-model.trim="businessData.name" type="text" class="form-input" placeholder="KickerKasse e.V." />
            </div>
            <div class="form-group">
              <label>Steuernummer</label>
              <input v-model.trim="businessData.taxNumber" type="text" class="form-input" placeholder="optional" />
            </div>
          </div>
          <div class="form-group">
            <label>Straße & Hausnummer</label>
            <input v-model.trim="businessData.street" type="text" class="form-input" placeholder="Musterstraße 1" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>PLZ</label>
              <input v-model.trim="businessData.zip" type="text" class="form-input" placeholder="12345" />
            </div>
            <div class="form-group">
              <label>Ort</label>
              <input v-model.trim="businessData.city" type="text" class="form-input" placeholder="Musterstadt" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Telefon</label>
              <input v-model.trim="businessData.phone" type="tel" class="form-input" placeholder="optional" />
            </div>
            <div class="form-group">
              <label>E-Mail</label>
              <input v-model.trim="businessData.email" type="email" class="form-input" placeholder="optional" />
            </div>
          </div>
          <div class="form-group">
            <label>Vereinsregister</label>
            <input v-model.trim="businessData.registrationNumber" type="text" class="form-input" placeholder="optional" />
          </div>
        </section>

        <section v-else-if="step === 2" class="panel-stack">
          <div class="info-box success">
            <strong>Startbestand der Kasse</strong>
            <p>Lege fest, mit welchem Bargeldbestand die Kasse nach Migration oder Reset startet.</p>
          </div>
          <div class="form-group narrow">
            <label>Startbetrag in €</label>
            <input v-model="openingCashInput" type="number" min="0" step="0.01" class="form-input" placeholder="0,00" />
          </div>
          <p class="hint-copy">Der Betrag wird als dokumentierte Einlage im Kassenbestand hinterlegt.</p>
        </section>

        <section v-else-if="step === 3" class="panel-stack">
          <div class="info-box">
            <strong>Sicherung importieren</strong>
            <p>Optional kannst du jetzt Produkte, Mitglieder und Kategorien aus einer vorhandenen Sicherung übernehmen.</p>
          </div>
          <div class="action-row">
            <button type="button" class="btn btn-primary" @click="showImportModal = true">Sicherung auswählen</button>
            <button type="button" class="btn btn-secondary" @click="step = 4">Ohne Import fortfahren</button>
          </div>
          <div v-if="hasImportedBackup" class="info-box success compact">
            <strong>Import abgeschlossen.</strong>
            <p>Die Sicherung wurde übernommen. Du kannst das Setup jetzt abschließen.</p>
          </div>
        </section>

        <section v-else class="panel-stack">
          <div class="info-box success">
            <strong>Fast geschafft</strong>
            <p>Die wichtigsten Startwerte sind gesetzt. Im (Top-)Admin-Bereich findest du weitere Funktionen:</p>
          </div>
          <ul class="feature-list">
            <li><strong>E-Mail-Setup:</strong> SMTP-Zugang, Empfänger und automatische Versandzeit für Kassenberichte.</li>
            <li><strong>Design & Hintergrundbild:</strong> Farben, Logo und Kassenhintergrund im Reiter „Design“.</li>
            <li><strong>Session-Timer & Layout:</strong> automatische Abmeldung und alternative Kassenlayouts.</li>
            <li><strong>Import / Export:</strong> Sicherungen erstellen oder Datenbestände wiederherstellen.</li>
            <li><strong>Audit-Log & Hard-Reset:</strong> nur im Top-Admin-Bereich für Nachvollziehbarkeit und Neuaufsetzung.</li>
          </ul>
        </section>

        <div v-if="errorMessage" class="alert alert-error">{{ errorMessage }}</div>
      </div>

      <footer class="modal-footer">
        <button type="button" class="btn btn-secondary" :disabled="isSubmitting || (!dismissible && step === 0)" @click="handleBack">
          {{ step === 0 ? (dismissible ? 'Später' : 'Bitte Setup abschließen') : 'Zurück' }}
        </button>
        <button type="button" class="btn btn-success" :disabled="isSubmitting" @click="handleNext">
          {{ nextLabel }}
        </button>
      </footer>
    </div>

    <ImportExportModal
      :show="showImportModal"
      initial-tab="import"
      @close="showImportModal = false"
      @imported="handleImported"
    />
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import apiService from '@/services/api'
import ImportExportModal from '@/components/ImportExportModal.vue'
import { useAppSettingsStore } from '@/stores/appSettings'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  dismissible: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['close', 'completed'])

const authStore = useAuthStore()
const appSettingsStore = useAppSettingsStore()
const notificationStore = useNotificationStore()

const stepLabels = ['Top-Admin', 'Vereinsdaten', 'Startbetrag', 'Import', 'Hinweise']
const step = ref(0)
const isSubmitting = ref(false)
const errorMessage = ref('')
const showImportModal = ref(false)
const hasImportedBackup = ref(false)
const openingCashBooked = ref(false)

const topAdmin = reactive({
  username: '',
  email: '',
  password: '',
  passwordConfirm: '',
})

const businessData = reactive({
  name: '',
  street: '',
  zip: '',
  city: '',
  phone: '',
  email: '',
  taxNumber: '',
  registrationNumber: '',
})

const openingCashInput = ref('0.00')

const nextLabel = computed(() => {
  if (isSubmitting.value) return 'Bitte warten...'
  if (step.value === 0) return 'Top-Admin anlegen'
  if (step.value === 4) return 'Setup abschließen'
  if (step.value === 3) return hasImportedBackup.value ? 'Weiter zu den Hinweisen' : 'Weiter'
  return 'Weiter'
})

const resetWizard = () => {
  step.value = 0
  errorMessage.value = ''
  showImportModal.value = false
  hasImportedBackup.value = false
  openingCashBooked.value = false
  topAdmin.username = ''
  topAdmin.email = ''
  topAdmin.password = ''
  topAdmin.passwordConfirm = ''
  businessData.name = ''
  businessData.street = ''
  businessData.zip = ''
  businessData.city = ''
  businessData.phone = ''
  businessData.email = ''
  businessData.taxNumber = ''
  businessData.registrationNumber = ''
  openingCashInput.value = '0.00'
}

watch(() => props.show, (visible) => {
  if (visible) {
    resetWizard()
  }
})

const requireTopAdminFields = () => {
  if (!topAdmin.username || !topAdmin.password || !topAdmin.passwordConfirm) {
    throw new Error('Bitte Benutzername und Passwort für den Top-Admin vollständig eingeben')
  }
  if (topAdmin.password !== topAdmin.passwordConfirm) {
    throw new Error('Die Top-Admin-Passwörter stimmen nicht überein')
  }
}

const persistBusinessAndCash = async () => {
  await appSettingsStore.saveAdminSettings({
    business_name: businessData.name || null,
    business_street: businessData.street || null,
    business_zip: businessData.zip || null,
    business_city: businessData.city || null,
    business_phone: businessData.phone || null,
    business_email: businessData.email || null,
    business_tax_number: businessData.taxNumber || null,
    business_registration_number: businessData.registrationNumber || null,
  })

  const openingCash = Number.parseFloat(openingCashInput.value || '0')
  if (Number.isNaN(openingCash) || openingCash < 0) {
    throw new Error('Bitte einen gültigen Startbetrag ab 0 € eingeben')
  }

  if (!openingCashBooked.value && openingCash > 0) {
    await apiService.post('/transactions/cash/deposit', {
      amount_cents: Math.round(openingCash * 100),
      reason: 'Initiale Kassen-Einlage beim Setup',
    })
    openingCashBooked.value = true
  }
}

const handleBack = () => {
  errorMessage.value = ''
  if (step.value === 0) {
    if (!props.dismissible) {
      return
    }
    emit('close')
    return
  }
  step.value -= 1
}

const handleNext = async () => {
  errorMessage.value = ''
  isSubmitting.value = true
  try {
    if (step.value === 0) {
      requireTopAdminFields()
      const success = await authStore.completeTopAdminSetup({
        username: topAdmin.username,
        password: topAdmin.password,
        email: topAdmin.email,
      })
      if (!success) {
        throw new Error(authStore.error || 'Top-Admin konnte nicht erstellt werden')
      }
      await appSettingsStore.loadAdminSettings()
      step.value = 1
      return
    }

    if (step.value === 1) {
      step.value = 2
      return
    }

    if (step.value === 2) {
      await persistBusinessAndCash()
      notificationStore.success('Grundkonfiguration gespeichert')
      step.value = 3
      return
    }

    if (step.value === 3) {
      step.value = 4
      return
    }

    emit('completed')
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || error.message || 'Setup fehlgeschlagen'
  } finally {
    isSubmitting.value = false
  }
}

const handleImported = () => {
  showImportModal.value = false
  hasImportedBackup.value = true
  step.value = 4
}

const handleClose = () => {
  if (!props.dismissible) {
    return
  }
  emit('close')
}

const handleOverlayClick = () => {
  if (!props.dismissible) {
    return
  }
  handleClose()
}
</script>

<style scoped lang="scss">
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.72);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 900;
  padding: 1rem;
}

.wizard-card {
  width: min(760px, 100%);
  max-height: 92vh;
  background: white;
  border-radius: 18px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header,
.modal-footer {
  padding: 1.25rem 1.5rem;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  border-bottom: 1px solid #e2e8f0;

  h3 {
    margin: 0;
    font-size: 1.35rem;
  }
}

.modal-subtitle {
  margin: 0.35rem 0 0;
  color: #64748b;
}

.modal-close {
  border: none;
  background: transparent;
  font-size: 1.8rem;
  color: #64748b;
  cursor: pointer;
}

.wizard-progress {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.5rem;
  padding: 1rem 1.5rem 0;
}

.wizard-step {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.65rem 0.75rem;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  color: #64748b;
  font-size: 0.82rem;

  &.active {
    border-color: var(--app-highlight-color);
    background: color-mix(in srgb, var(--app-highlight-color) 10%, white);
    color: #1e293b;
  }

  &.done {
    border-color: #bbf7d0;
    background: #f0fdf4;
    color: #166534;
  }
}

.wizard-step__index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: white;
  font-weight: 700;
}

.modal-body {
  padding: 1.25rem 1.5rem;
  overflow-y: auto;
}

.panel-stack {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.info-box {
  padding: 0.9rem 1rem;
  border-radius: 12px;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  color: #1e3a8a;

  &.success {
    border-color: #bbf7d0;
    background: #f0fdf4;
    color: #166534;
  }

  &.compact {
    padding: 0.8rem 0.9rem;
  }

  strong,
  p {
    margin: 0;
  }

  p {
    margin-top: 0.35rem;
  }
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;

  &.narrow {
    max-width: 240px;
  }

  label {
    font-weight: 600;
    color: #1e293b;
  }
}

.form-input {
  width: 100%;
  border: 1px solid #dbe3ee;
  border-radius: 10px;
  padding: 0.75rem 0.85rem;
  font-size: 0.98rem;

  &:focus {
    outline: none;
    border-color: var(--app-highlight-color);
    box-shadow: 0 0 0 3px rgba(92, 143, 58, 0.15);
  }
}

.hint-copy {
  margin: 0;
  color: #64748b;
}

.action-row {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.feature-list {
  margin: 0;
  padding-left: 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  color: #334155;
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  border-top: 1px solid #e2e8f0;
}

.btn {
  border: none;
  border-radius: 10px;
  padding: 0.75rem 1rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-secondary {
  background: #e2e8f0;
  color: #1e293b;
}

.btn-success {
  background: var(--app-highlight-color);
  color: var(--app-highlight-contrast);
}

.alert {
  margin-top: 1rem;
  padding: 0.9rem 1rem;
  border-radius: 12px;
  border: 1px solid #fecaca;
  background: #fef2f2;
  color: #b91c1c;
}

@media (max-width: 720px) {
  .wizard-progress,
  .form-row {
    grid-template-columns: 1fr;
  }

  .modal-footer {
    flex-direction: column-reverse;
  }
}
</style>
