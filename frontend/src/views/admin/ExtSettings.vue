<template>
  <div class="ext-settings">
    <div class="page-header">
      <div>
        <h2>⚙️ Ext. Settings</h2>
        <p class="page-subtitle">Erweiterte Einstellungen – nur für TopAdmin zugänglich.</p>
      </div>
    </div>

    <div class="settings-grid">
      <!-- Business Data Card -->
      <div class="settings-card">
        <div class="settings-card-header">
          <div class="settings-card-icon">🏢</div>
          <div>
            <h3>Geschäftsdaten</h3>
            <p>Vereinsname, Anschrift und Kontaktdaten hinterlegen.</p>
          </div>
        </div>
        <button class="btn btn-primary" @click="showBusinessModal = true">
          Geschäftsdaten bearbeiten
        </button>
      </div>

      <!-- Layout Chooser Card -->
      <div class="settings-card">
        <div class="settings-card-header">
          <div class="settings-card-icon">🎨</div>
          <div>
            <h3>Layout-Chooser</h3>
            <p>Kassenansicht-Layout auswählen. Die App wird nach der Auswahl neu geladen.</p>
          </div>
        </div>
        <div class="layout-chooser">
          <div class="layout-options">
            <label
              v-for="layout in availableLayouts"
              :key="layout.key"
              class="layout-option"
              :class="{ selected: selectedLayout === layout.key }"
            >
              <input
                v-model="selectedLayout"
                type="radio"
                :value="layout.key"
                class="layout-radio"
              >
              <div class="layout-preview">
                <div class="layout-preview-icon">{{ layout.icon }}</div>
                <div class="layout-preview-name">{{ layout.name }}</div>
                <div v-if="selectedLayout === layout.key" class="layout-active-badge">Aktiv</div>
              </div>
            </label>
          </div>
          <div v-if="layoutChanged" class="layout-changed-hint">
            <span>⚠️ Auswahl geändert. Zum Übernehmen neu laden.</span>
            <button class="btn btn-warning" @click="applyLayout">Jetzt neu laden</button>
          </div>
        </div>
      </div>

      <div class="settings-card">
        <div class="settings-card-header">
          <div class="settings-card-icon">⏱️</div>
          <div>
            <h3>Session-Timer</h3>
            <p>Automatischer Logout nach Inaktivität mit Rückkehr zum Login-Screen.</p>
          </div>
        </div>
        <div class="session-timer-settings">
          <button
            class="btn"
            :class="sessionTimer.enabled ? 'btn-success' : 'btn-secondary'"
            type="button"
            @click="sessionTimer.enabled = !sessionTimer.enabled"
          >
            {{ sessionTimer.enabled ? 'Eingeschaltet' : 'Ausgeschaltet' }}
          </button>

          <div class="form-group">
            <label for="session-timer-minutes">Automatische Abmeldung nach (Minuten)</label>
            <input
              id="session-timer-minutes"
              v-model.number="sessionTimer.minutes"
              type="number"
              min="1"
              step="1"
              inputmode="numeric"
            >
          </div>

          <button class="btn btn-primary" type="button" @click="saveSessionTimer">
            Session-Timer speichern
          </button>
        </div>
      </div>
    </div>

    <!-- Business Data Modal -->
    <div v-if="showBusinessModal" class="modal-overlay" @click.self="showBusinessModal = false">
      <div class="modal-card">
        <header class="modal-header">
          <div>
            <h3>Geschäftsdaten</h3>
            <p class="modal-subtitle">Diese Daten werden für Belege und Berichte verwendet.</p>
          </div>
          <button class="modal-close" @click="showBusinessModal = false">×</button>
        </header>

        <form class="modal-form-content" @submit.prevent="saveBusinessData">
          <div class="form-row">
            <div class="form-group">
              <label for="bd-name">Vereinsname</label>
              <input id="bd-name" v-model="businessData.name" type="text" placeholder="z. B. Tischfußball e.V.">
            </div>
            <div class="form-group">
              <label for="bd-tax">Steuernummer</label>
              <input id="bd-tax" v-model="businessData.taxNumber" type="text" placeholder="z. B. 12/345/67890">
            </div>
          </div>
          <div class="form-group">
            <label for="bd-street">Straße &amp; Hausnummer</label>
            <input id="bd-street" v-model="businessData.street" type="text" placeholder="z. B. Musterstraße 1">
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="bd-zip">PLZ</label>
              <input id="bd-zip" v-model="businessData.zip" type="text" placeholder="z. B. 12345">
            </div>
            <div class="form-group">
              <label for="bd-city">Ort</label>
              <input id="bd-city" v-model="businessData.city" type="text" placeholder="z. B. Musterstadt">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="bd-phone">Telefon</label>
              <input id="bd-phone" v-model="businessData.phone" type="tel" placeholder="z. B. +49 123 456789">
            </div>
            <div class="form-group">
              <label for="bd-email">E-Mail</label>
              <input id="bd-email" v-model="businessData.email" type="email" placeholder="z. B. info@verein.de">
            </div>
          </div>
          <div class="form-group">
            <label for="bd-reg">Vereinsregister (optional)</label>
            <input id="bd-reg" v-model="businessData.registrationNumber" type="text" placeholder="z. B. VR 12345 Amtsgericht Musterstadt">
          </div>

          <footer class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showBusinessModal = false">Abbrechen</button>
            <button type="submit" class="btn btn-success">Speichern</button>
          </footer>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useNotificationStore } from '@/stores/notification'
import { useAppSettingsStore } from '@/stores/appSettings'
import { SESSION_RELOAD_FLAG_KEY } from '@/constants'

const notificationStore = useNotificationStore()
const appSettingsStore = useAppSettingsStore()

const LAYOUT_STORAGE_KEY = 'kasseLayout'

const showBusinessModal = ref(false)
const sessionTimer = ref({
  enabled: false,
  minutes: 15,
})

const businessData = ref({
  name: '',
  street: '',
  zip: '',
  city: '',
  phone: '',
  email: '',
  taxNumber: '',
  registrationNumber: '',
})

// Discover available layouts via Vite's glob import
const layoutModules = import.meta.glob('@/views/kasse/Kasse*.vue')

const availableLayouts = computed(() => {
  const layouts = [{ key: 'Kasse', name: 'Standard', icon: '🖥️' }]
  const pattern = /Kasse(\d+)\.vue$/
  Object.keys(layoutModules).forEach((path) => {
    const match = path.match(pattern)
    if (match) {
      const num = match[1]
      layouts.push({
        key: `Kasse${num}`,
        name: `Layout ${num}`,
        icon: '🎨',
      })
    }
  })
  return layouts
})

const selectedLayout = ref(localStorage.getItem(LAYOUT_STORAGE_KEY) || 'Kasse')
const initialLayout = ref(localStorage.getItem(LAYOUT_STORAGE_KEY) || 'Kasse')

const layoutChanged = computed(() => selectedLayout.value !== initialLayout.value)

const syncSessionTimer = () => {
  sessionTimer.value.enabled = !!appSettingsStore.settings.session_timer_enabled
  sessionTimer.value.minutes = Number(appSettingsStore.settings.session_timer_minutes) || 15
}

const applyLayout = async () => {
  try {
    await appSettingsStore.saveAdminSettings({
      kasse_layout: selectedLayout.value,
    })
  } catch {
    notificationStore.error('Layout konnte nicht gespeichert werden')
    return
  }
  localStorage.setItem(LAYOUT_STORAGE_KEY, selectedLayout.value)
  sessionStorage.setItem(SESSION_RELOAD_FLAG_KEY, '1')
  window.location.reload()
}

const saveSessionTimer = async () => {
  const minutes = Number(sessionTimer.value.minutes)
  if (!Number.isInteger(minutes) || minutes < 1) {
    notificationStore.error('Bitte eine gültige Anzahl Minuten ab 1 eingeben')
    return
  }

  try {
    await appSettingsStore.saveAdminSettings({
      session_timer_enabled: sessionTimer.value.enabled,
      session_timer_minutes: minutes,
    })
    syncSessionTimer()
    notificationStore.success('Session-Timer gespeichert')
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Session-Timer konnte nicht gespeichert werden')
  }
}

const saveBusinessData = () => {
  // Persist data locally for later use
  localStorage.setItem('businessData', JSON.stringify(businessData.value))
  notificationStore.success('Geschäftsdaten gespeichert.')
  showBusinessModal.value = false
}

onMounted(async () => {
  // Pre-fill with any previously saved data
  const saved = localStorage.getItem('businessData')
  if (saved) {
    try {
      Object.assign(businessData.value, JSON.parse(saved))
    } catch {
      // ignore parse errors
    }
  }

  await appSettingsStore.loadAdminSettings()

  // Sync layout from server settings
  const serverLayout = appSettingsStore.settings.kasse_layout
  if (serverLayout) {
    selectedLayout.value = serverLayout
    initialLayout.value = serverLayout
  }

  syncSessionTimer()
})
</script>

<style scoped lang="scss">
.ext-settings {
  --primary: #3b82f6;
  --success: #10b981;
  --border: #e2e8f0;
  padding: 1.5rem;
  background: white;
  min-height: 100%;
}

.page-header {
  margin-bottom: 2rem;

  h2 {
    font-size: 1.5rem;
    color: #1e293b;
  }
}

.page-subtitle {
  color: #64748b;
  margin-top: 0.25rem;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 1.5rem;
}

.settings-card {
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.settings-card-header {
  display: flex;
  gap: 1rem;
  align-items: flex-start;

  h3 {
    margin: 0 0 0.25rem;
    font-size: 1.05rem;
    color: #1e293b;
  }

  p {
    margin: 0;
    font-size: 0.85rem;
    color: #64748b;
  }
}

.settings-card-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

/* ── Layout chooser ─────────────────────────────── */
.layout-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.layout-option {
  cursor: pointer;

  .layout-radio {
    display: none;
  }
}

.layout-preview {
  position: relative;
  width: 100px;
  border: 2px solid var(--border);
  border-radius: 10px;
  padding: 0.75rem 0.5rem;
  text-align: center;
  background: white;
  transition: border-color 0.15s, box-shadow 0.15s;

  .layout-option:hover & {
    border-color: var(--primary);
  }

  .layout-option.selected & {
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  }
}

.layout-preview-icon {
  font-size: 1.8rem;
  margin-bottom: 0.3rem;
}

.layout-preview-name {
  font-size: 0.78rem;
  font-weight: 600;
  color: #334155;
}

.layout-active-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  background: var(--primary);
  color: white;
  font-size: 0.62rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 999px;
}

.layout-changed-hint {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.75rem;
  padding: 0.75rem 1rem;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #92400e;
  flex-wrap: wrap;
}

.session-timer-settings {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* ── Modal ──────────────────────────────────────── */
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
  max-width: 640px;
  max-height: 90vh;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
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

.modal-subtitle {
  color: #64748b;
  margin-top: 0.25rem;
  font-size: 0.875rem;
}

.modal-form-content {
  padding: 1.5rem;
  overflow-y: auto;
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

  input {
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

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding-top: 0.5rem;
}

.modal-close {
  border: none;
  background: transparent;
  font-size: 1.6rem;
  line-height: 1;
  cursor: pointer;
  color: #6b7280;
}

/* ── Buttons ─────────────────────────────────────── */
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

.btn-warning {
  background: #f59e0b;
  color: white;
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
