<template>
  <div class="admin-config">
    <!-- Inner section navigation -->
    <div class="section-nav">
      <div class="title-row">
        <span class="section-nav-label">Einstellungen</span>
        <span class="title-sep">|</span>
        <span class="page-subtitle">Konfiguration, Design und Systemeinstellungen.</span>
      </div>
      <div class="section-nav-buttons">
        <button
          :class="['section-tab', { active: activeSection === 'design' }]"
          type="button"
          @click="activeSection = 'design'"
        >
          🎨 Design
        </button>
        <button
          :class="['section-tab', { active: activeSection === 'datamaintenance' }]"
          type="button"
          @click="activeSection = 'datamaintenance'"
        >
          🧹 Datenpflege
        </button>
        <button
          v-if="authStore.isAdmin"
          :class="['section-tab', { active: activeSection === 'importexport' }]"
          type="button"
          @click="activeSection = 'importexport'"
        >
          🔄 Import/Export
        </button>
        <button
          v-if="authStore.isTopAdmin"
          :class="['section-tab', { active: activeSection === 'extsettings' }]"
          type="button"
          @click="activeSection = 'extsettings'"
        >
          ⚙️ Ext. Settings
        </button>
      </div>
    </div>

    <!-- ── Design ─────────────────────────────────────── -->
    <div v-if="activeSection === 'design'" class="section-content">
      <h2>Design &amp; Logo</h2>
      <div class="settings-grid">
        <section class="settings-card">
          <h3>Farben</h3>

          <div class="form-group">
            <label for="appName">App-Überschrift</label>
            <input id="appName" v-model.trim="designForm.app_name" type="text" class="form-input" maxlength="120" />
          </div>

          <!-- Background color -->
          <div class="form-group">
            <label>Hintergrundfarbe</label>
            <div class="color-picker-field">
              <div class="color-options">
                <button
                  v-for="preset in designColors"
                  :key="preset.value"
                  type="button"
                  class="color-option"
                  :class="{ selected: designForm.background_color === preset.value }"
                  :style="{ background: preset.value }"
                  :title="preset.label"
                  @click="designForm.background_color = preset.value"
                ></button>
                <label
                  class="color-option color-option-custom"
                  :class="{ selected: isCustomBackground }"
                  title="Eigene Farbe wählen"
                >
                  <span v-if="isCustomBackground" class="custom-color-preview" :style="{ background: designForm.background_color }"></span>
                  <span v-else class="custom-color-icon">🎨</span>
                  <input
                    type="color"
                    :value="designForm.background_color"
                    @input="designForm.background_color = $event.target.value"
                  >
                </label>
              </div>
              <div class="color-selected-preview" :style="{ background: designForm.background_color }">
                <span :style="{ color: getContrastColor(designForm.background_color) }">{{ designForm.background_color }}</span>
              </div>
            </div>
          </div>

          <!-- Banner color -->
          <div class="form-group">
            <label>Bannerfarbe</label>
            <div class="color-picker-field">
              <div class="color-options">
                <button
                  v-for="preset in designColors"
                  :key="preset.value"
                  type="button"
                  class="color-option"
                  :class="{ selected: designForm.banner_color === preset.value }"
                  :style="{ background: preset.value }"
                  :title="preset.label"
                  @click="designForm.banner_color = preset.value"
                ></button>
                <label
                  class="color-option color-option-custom"
                  :class="{ selected: isCustomBanner }"
                  title="Eigene Farbe wählen"
                >
                  <span v-if="isCustomBanner" class="custom-color-preview" :style="{ background: designForm.banner_color }"></span>
                  <span v-else class="custom-color-icon">🎨</span>
                  <input
                    type="color"
                    :value="designForm.banner_color"
                    @input="designForm.banner_color = $event.target.value"
                  >
                </label>
              </div>
              <div class="color-selected-preview" :style="{ background: designForm.banner_color }">
                <span :style="{ color: getContrastColor(designForm.banner_color) }">{{ designForm.banner_color }}</span>
              </div>
            </div>
          </div>

          <!-- Highlight color -->
          <div class="form-group">
            <label>Highlight-Farbe</label>
            <div class="color-picker-field">
              <div class="color-options">
                <button
                  v-for="preset in designColors"
                  :key="preset.value"
                  type="button"
                  class="color-option"
                  :class="{ selected: designForm.highlight_color === preset.value }"
                  :style="{ background: preset.value }"
                  :title="preset.label"
                  @click="designForm.highlight_color = preset.value"
                ></button>
                <label
                  class="color-option color-option-custom"
                  :class="{ selected: isCustomHighlight }"
                  title="Eigene Farbe wählen"
                >
                  <span v-if="isCustomHighlight" class="custom-color-preview" :style="{ background: designForm.highlight_color }"></span>
                  <span v-else class="custom-color-icon">🎨</span>
                  <input
                    type="color"
                    :value="designForm.highlight_color"
                    @input="designForm.highlight_color = $event.target.value"
                  >
                </label>
              </div>
              <div class="color-selected-preview" :style="{ background: designForm.highlight_color }">
                <span :style="{ color: getContrastColor(designForm.highlight_color) }">{{ designForm.highlight_color }}</span>
              </div>
            </div>
          </div>

          <button class="btn btn-primary" :disabled="appSettingsStore.isSaving" @click="saveDesignSettings">
            Farben speichern
          </button>
        </section>

        <section class="settings-card">
          <h3>Logo</h3>
          <div class="logo-preview">
            <img :src="appSettingsStore.logoUrl" alt="Aktuelles Logo" />
          </div>
          <input type="file" accept="image/*" class="form-input" @change="handleLogoSelection" />
          <button class="btn btn-success" :disabled="!selectedLogo || appSettingsStore.isSaving" @click="uploadLogo">
            Logo hochladen
          </button>
        </section>
      </div>

      <section class="settings-card preview-card">
        <h3>Vorschau</h3>
        <div class="preview-shell" :style="previewStyle">
          <div class="preview-banner">
            <img :src="previewLogoUrl" alt="Logo Vorschau" class="preview-logo" />
            <span class="preview-title">{{ designForm.app_name }}</span>
          </div>
          <div class="preview-highlight">Highlight-Fläche</div>
        </div>
      </section>
    </div>

    <!-- ── Datenpflege ────────────────────────────────── -->
    <div v-if="activeSection === 'datamaintenance'" class="section-content">
      <h2>Datenpflege</h2>
      <div class="warning-box">
        <p>
          Der Hard-Reset entfernt Transaktionen, Benutzer, Mitglieder, Produkte, Statistiken,
          Gutscheine, Verzehrkarten und Kategorien unwiderruflich.
        </p>
        <p v-if="!authStore.isTopAdmin" class="access-note">
          Nur der Top-Admin darf diese Aktion ausführen.
        </p>
      </div>
      <button
        class="btn btn-danger"
        :disabled="!authStore.isTopAdmin"
        @click="showResetModal = true"
      >
        🧨 Hard-Reset starten
      </button>

      <CredentialConfirmModal
        :show="showResetModal"
        title="Hard-Reset bestätigen"
        message="Bitte Top-Admin-Passwort eingeben und zusätzlich RESET bestätigen."
        :username="authStore.user?.username || ''"
        confirm-label="Hard-Reset ausführen"
        confirmation-label="Bestätigung"
        confirmation-placeholder="RESET"
        @close="showResetModal = false"
        @confirm="handleHardReset"
      />
    </div>

    <div v-if="activeSection === 'importexport' && authStore.isAdmin" class="section-content">
      <h2>Import / Export</h2>
      <div class="settings-card">
        <h3>Datenübernahme und Sicherung</h3>
        <p class="section-description">
          Produkte, Mitglieder und Kategorien können gesammelt exportiert oder aus CSV-/ZIP-Dateien wieder importiert werden.
        </p>
        <button class="btn btn-primary" type="button" @click="showImportExportModal = true">
          Import / Export öffnen
        </button>
      </div>
    </div>

    <!-- ── Ext. Settings (TOP_ADMIN only) ─────────────── -->
    <div v-if="activeSection === 'extsettings' && authStore.isTopAdmin" class="section-content ext-settings-section">
      <div class="page-header">
        <div class="title-row">
          <h2>⚙️ Ext. Settings</h2>
          <span class="title-sep">|</span>
          <span class="page-subtitle">Erweiterte Einstellungen – nur für TopAdmin zugänglich.</span>
        </div>
      </div>

      <div class="ext-settings-grid">
        <!-- Business Data Card -->
        <div class="ext-card">
          <div class="ext-card-header">
            <div class="ext-card-icon">🏢</div>
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
        <div class="ext-card">
          <div class="ext-card-header">
            <div class="ext-card-icon">🖥️</div>
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

        <!-- Session Timer Card -->
        <div class="ext-card">
          <div class="ext-card-header">
            <div class="ext-card-icon">⏱️</div>
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
          </form>
          <footer class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showBusinessModal = false">Abbrechen</button>
            <button type="button" class="btn btn-success" @click="saveBusinessData">Speichern</button>
          </footer>
        </div>
      </div>
    </div>

    <ImportExportModal
      :show="showImportExportModal"
      @close="showImportExportModal = false"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import ImportExportModal from '@/components/ImportExportModal.vue'
import { useAppSettingsStore } from '@/stores/appSettings'
import { useNotificationStore } from '@/stores/notification'
import { useAuthStore } from '@/stores/auth'
import { getContrastColor } from '@/services/utils'
import { SESSION_RELOAD_FLAG_KEY } from '@/constants'
import apiService from '@/services/api'
import CredentialConfirmModal from '@/components/CredentialConfirmModal.vue'

const appSettingsStore = useAppSettingsStore()
const notificationStore = useNotificationStore()
const authStore = useAuthStore()

// ── Section navigation ────────────────────────────────
const activeSection = ref('design')

// ── Design ────────────────────────────────────────────
const designColors = [
  { value: '#FFFFFF', label: 'Weiß' },
  { value: '#F5F7FA', label: 'Hellgrau' },
  { value: '#D7DCE2', label: 'Blaugrau' },
  { value: '#E8F4F8', label: 'Eisblau' },
  { value: '#F0FFF4', label: 'Mintgrün' },
  { value: '#FFF7ED', label: 'Creme' },
  { value: '#131820', label: 'Marine' },
  { value: '#1E293B', label: 'Slate' },
  { value: '#374151', label: 'Dunkelgrau' },
  { value: '#1A1A2E', label: 'Mitternacht' },
  { value: '#14532D', label: 'Dunkelgrün' },
  { value: '#7F1D1D', label: 'Dunkelrot' },
  { value: '#5C8F3A', label: 'Grün' },
  { value: '#3B82F6', label: 'Blau' },
  { value: '#8B5CF6', label: 'Violett' },
  { value: '#EC4899', label: 'Pink' },
  { value: '#EF4444', label: 'Rot' },
  { value: '#F97316', label: 'Orange' },
  { value: '#10B981', label: 'Smaragd' },
  { value: '#EAB308', label: 'Gelb' },
]

const designForm = reactive({
  app_name: 'KGB - KickerKasse',
  background_color: '#D7DCE2',
  banner_color: '#131820',
  highlight_color: '#5C8F3A',
})

const selectedLogo = ref(null)
const selectedLogoPreview = ref('')

const isCustomBackground = computed(() => !designColors.some(c => c.value === designForm.background_color))
const isCustomBanner = computed(() => !designColors.some(c => c.value === designForm.banner_color))
const isCustomHighlight = computed(() => !designColors.some(c => c.value === designForm.highlight_color))

const previewStyle = computed(() => ({
  '--preview-background': designForm.background_color,
  '--preview-banner': designForm.banner_color,
  '--preview-highlight': designForm.highlight_color,
  '--preview-banner-contrast': getContrastColor(designForm.banner_color),
  '--preview-highlight-contrast': getContrastColor(designForm.highlight_color),
}))

const previewLogoUrl = computed(() => selectedLogoPreview.value || appSettingsStore.logoUrl)

const syncDesignForm = () => {
  designForm.app_name = appSettingsStore.settings.app_name
  designForm.background_color = appSettingsStore.settings.background_color
  designForm.banner_color = appSettingsStore.settings.banner_color
  designForm.highlight_color = appSettingsStore.settings.highlight_color
}

const handleLogoSelection = (event) => {
  const [file] = event.target.files || []
  if (!file) return
  selectedLogo.value = file
  selectedLogoPreview.value = URL.createObjectURL(file)
}

const saveDesignSettings = async () => {
  try {
    await appSettingsStore.saveAdminSettings({ ...designForm })
    syncDesignForm()
    notificationStore.success('Einstellungen gespeichert')
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Fehler beim Speichern der Einstellungen')
  }
}

const uploadLogo = async () => {
  if (!selectedLogo.value) return
  try {
    await appSettingsStore.uploadLogo(selectedLogo.value)
    selectedLogo.value = null
    selectedLogoPreview.value = ''
    notificationStore.success('Logo erfolgreich aktualisiert')
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Fehler beim Hochladen des Logos')
  }
}

// ── Datenpflege ───────────────────────────────────────
const showResetModal = ref(false)
const showImportExportModal = ref(false)

const handleHardReset = async ({ password, confirmationText }) => {
  showResetModal.value = false
  try {
    await apiService.post('/admin/data-maintenance/hard-reset', {
      auth_password: password,
      confirmation_text: confirmationText,
    })
    notificationStore.success('Hard-Reset erfolgreich durchgeführt')
    await authStore.logout()
    window.location.href = '/login'
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Hard-Reset fehlgeschlagen')
  }
}

// ── Ext. Settings ─────────────────────────────────────
const LAYOUT_STORAGE_KEY = 'kasseLayout'

const showBusinessModal = ref(false)
const sessionTimer = ref({ enabled: false, minutes: 15 })

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

const layoutModules = import.meta.glob('@/views/kasse/Kasse*.vue')

const availableLayouts = computed(() => {
  const layouts = [{ key: 'Kasse', name: 'Standard', icon: '🖥️' }]
  const pattern = /Kasse(\d+)\.vue$/
  Object.keys(layoutModules).forEach((path) => {
    const match = path.match(pattern)
    if (match) {
      const num = match[1]
      layouts.push({ key: `Kasse${num}`, name: `Layout ${num}`, icon: '🎨' })
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
    await appSettingsStore.saveAdminSettings({ kasse_layout: selectedLayout.value })
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
  localStorage.setItem('businessData', JSON.stringify(businessData.value))
  notificationStore.success('Geschäftsdaten gespeichert.')
  showBusinessModal.value = false
}

onMounted(async () => {
  await appSettingsStore.loadAdminSettings()
  syncDesignForm()
  syncSessionTimer()

  const serverLayout = appSettingsStore.settings.kasse_layout
  if (serverLayout) {
    selectedLayout.value = serverLayout
    initialLayout.value = serverLayout
  }

  const saved = localStorage.getItem('businessData')
  if (saved) {
    try {
      Object.assign(businessData.value, JSON.parse(saved))
    } catch {
      // Silently ignore invalid localStorage data; user will see empty defaults
    }
  }
})
</script>

<style scoped lang="scss">
.admin-config {
  background: var(--app-background-color);
  padding: 0.75rem 1rem;
  border-radius: 8px;
  min-height: 100%;
}

// ── Inner section nav ─────────────────────────────────
.section-nav {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--app-background-color);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: -0.75rem -1rem 1rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.13);
  flex-wrap: wrap;
}

.title-row {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.section-nav-label {
  font-size: 1.15rem;
  font-weight: 700;
  color: #333;
  line-height: 1.2;
}

.title-sep {
  color: #aaa;
  font-weight: 300;
}

.page-subtitle {
  font-size: 0.82rem;
  color: #556;
  margin: 0;
}

.section-nav-buttons {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.section-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.35rem 0.85rem;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #475569;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }

  &.active {
    background: var(--app-highlight-color);
    border-color: var(--app-highlight-color);
    color: var(--app-highlight-contrast);
  }
}

// ── Section content ───────────────────────────────────
.section-content {
  h2 {
    font-size: 1.2rem;
    color: #1e293b;
    margin: 0 0 0.75rem;
  }
}

.section-description {
  margin: 0;
  color: #64748b;
  font-size: 0.9rem;
}

// ── Design ────────────────────────────────────────────
.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1rem;
}

.settings-card {
  background: color-mix(in srgb, var(--app-background-color) 55%, white);
  border: 1px solid color-mix(in srgb, var(--app-background-color) 65%, #777);
  padding: 1rem;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;

  h3 {
    margin: 0;
    font-size: 1rem;
    color: #1e293b;
  }
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;

  label {
    font-size: 0.85rem;
    font-weight: 600;
    color: #334155;
  }
}

.form-input {
  width: 100%;
}

// Color picker
.color-picker-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.color-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
}

.color-option {
  width: 30px;
  height: 30px;
  border-radius: 7px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: transform 0.12s, border-color 0.12s;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;

  &:hover {
    transform: scale(1.15);
  }

  &.selected {
    border-color: #1e293b;
    box-shadow: 0 0 0 2px white inset;
  }
}

.color-option-custom {
  background: #f8fafc;
  border: 2px dashed #94a3b8;
  cursor: pointer;
  overflow: visible;

  &.selected {
    border-style: solid;
    border-color: #1e293b;
  }

  input[type="color"] {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    opacity: 0;
    cursor: pointer;
    padding: 0;
    border: none;
  }
}

.custom-color-preview {
  width: 100%;
  height: 100%;
  display: block;
  border-radius: 5px;
  position: absolute;
  inset: 0;
}

.custom-color-icon {
  font-size: 0.9rem;
  pointer-events: none;
}

.color-selected-preview {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  padding: 0 0.75rem;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 600;
  font-family: monospace;
  width: fit-content;
}

// Logo section
.logo-preview {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 160px;
  background: white;
  border-radius: 8px;
  padding: 1rem;

  img {
    max-width: 100%;
    max-height: 130px;
    object-fit: contain;
  }
}

.preview-card {
  margin-top: 1.25rem;
}

.preview-shell {
  background: var(--preview-background);
  border-radius: 12px;
  padding: 1.5rem;
}

.preview-banner {
  background: var(--preview-banner);
  color: var(--preview-banner-contrast);
  border-bottom: 3px solid var(--preview-highlight);
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.preview-logo {
  width: min(320px, 100%);
  height: 84px;
  object-fit: contain;
}

.preview-title {
  font-size: clamp(1.1rem, 1.8vw, 1.5rem);
  font-weight: 700;
}

.preview-highlight {
  margin-top: 1rem;
  background: var(--preview-highlight);
  color: var(--preview-highlight-contrast);
  border-radius: 8px;
  padding: 1rem;
  font-weight: 600;
}

// ── Datenpflege ───────────────────────────────────────
.warning-box {
  margin: 0.75rem 0;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  background: #fff4e5;
  border: 1px solid #f59e0b;
  color: #7c2d12;
}

.access-note {
  font-weight: 700;
}

// ── Ext. Settings ─────────────────────────────────────
.ext-settings-section {
  --ext-primary: #3b82f6;
  --ext-success: #10b981;
  --ext-border: #e2e8f0;
}

.page-header {
  margin-bottom: 0.75rem;

  h2 {
    font-size: 1.2rem;
    color: #333;
    margin: 0;
  }
}

.ext-settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 1rem;
}

.ext-card {
  background: color-mix(in srgb, var(--app-background-color) 55%, white);
  border: 1px solid color-mix(in srgb, var(--app-background-color) 65%, #777);
  border-radius: 14px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.ext-card-header {
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

.ext-card-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

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
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.75rem 0.5rem;
  text-align: center;
  background: white;
  transition: border-color 0.15s, box-shadow 0.15s;

  .layout-option:hover & {
    border-color: var(--ext-primary, #3b82f6);
  }

  .layout-option.selected & {
    border-color: var(--ext-primary, #3b82f6);
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
  background: var(--ext-primary, #3b82f6);
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

  input {
    width: 100%;
    padding: 0.6rem 0.8rem;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 0.95rem;
  }
}

// ── Modal ─────────────────────────────────────────────
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
  max-width: 650px;
  max-height: 650px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

.modal-header {
  padding: 0.9rem 1.2rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  flex-shrink: 0;

  h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #1e293b;
  }
}

.modal-subtitle {
  display: none;
}

.modal-form-content {
  padding: 1rem 1.2rem;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.modal-form-content .form-group {
  margin-bottom: 0.6rem;

  label {
    display: block;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 0.25rem;
    color: #334155;
  }

  input {
    width: 100%;
    padding: 0.5rem 0.7rem;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 0.9rem;
    color: #0f172a;

    &:focus {
      outline: none;
      border-color: var(--ext-primary, #3b82f6);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
  }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 0.75rem 1.2rem;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
  flex-shrink: 0;
  margin-top: auto;
}

.modal-close {
  border: none;
  background: transparent;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: #6b7280;
  padding: 0.25rem;
  min-width: 36px;
  min-height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

// ── Buttons ───────────────────────────────────────────
.btn {
  padding: 0.55rem 1.1rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-size: 0.9rem;
  min-height: 40px;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-success {
  background: #10b981;
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

.btn-danger {
  background: #dc2626;
  color: white;
  padding: 0.75rem 1.5rem;
  font-size: 0.95rem;

  &:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .ext-settings-grid {
    grid-template-columns: 1fr;
  }
}
</style>
