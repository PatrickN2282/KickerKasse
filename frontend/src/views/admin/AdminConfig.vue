<template>
  <div class="admin-config">
    <!-- Inner section navigation -->
    <div class="section-nav">
      <div class="title-row">
        <span class="section-nav-label">Einstellungsverwaltung</span>
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
          v-if="authStore.isAdmin"
          :class="['section-tab', { active: activeSection === 'extsettings' }]"
          type="button"
          @click="activeSection = 'extsettings'"
        >
          ⚙️ Ext. Settings
        </button>
        <button
          v-if="authStore.isTopAdmin"
          :class="['section-tab', { active: activeSection === 'auditlog' }]"
          type="button"
          @click="activeSection = 'auditlog'"
        >
          🔍 Audit-Log
        </button>
      </div>
    </div>

    <!-- ── Design ─────────────────────────────────────── -->
    <div v-if="activeSection === 'design'" class="section-content">
      <h2>Design &amp; Logo</h2>

      <div class="design-grid">

        <!-- Spalte 1: Farben -->
        <section class="settings-card colors-card">
          <div class="card-row-header">
            <h3>Farben</h3>
          </div>

          <!-- Reset-Hinweis-Box -->
          <div class="reset-hint-box">
            <div class="reset-hint-text">
              <span class="reset-hint-icon">↺</span>
              <div>
                <strong>Standardfarben wiederherstellen</strong>
                <span class="reset-hint-sub">Setzt alle Farben auf die Werkseinstellung zurück.</span>
              </div>
            </div>
            <button
              class="btn btn-reset"
              type="button"
              title="Farben auf Standard zurücksetzen"
              aria-label="Farben zurücksetzen"
              @click="resetDesignColors"
            >
              Reset
            </button>
          </div>

          <div class="form-group">
            <label for="appName">App-Überschrift</label>
            <input id="appName" v-model.trim="designForm.app_name" type="text" class="form-input" maxlength="120" />
          </div>

          <div class="color-row">
            <span class="color-row-label">Hintergrundfarbe</span>
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
                <input type="color" :value="designForm.background_color" @input="designForm.background_color = $event.target.value">
              </label>
            </div>
            <code class="color-hex" :style="{ background: designForm.background_color, color: getContrastColor(designForm.background_color) }">{{ designForm.background_color }}</code>
          </div>

          <div class="color-row">
            <span class="color-row-label">Bannerfarbe</span>
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
                <input type="color" :value="designForm.banner_color" @input="designForm.banner_color = $event.target.value">
              </label>
            </div>
            <code class="color-hex" :style="{ background: designForm.banner_color, color: getContrastColor(designForm.banner_color) }">{{ designForm.banner_color }}</code>
          </div>

          <div class="color-row">
            <span class="color-row-label">Highlight-Farbe</span>
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
                <input type="color" :value="designForm.highlight_color" @input="designForm.highlight_color = $event.target.value">
              </label>
            </div>
            <code class="color-hex" :style="{ background: designForm.highlight_color, color: getContrastColor(designForm.highlight_color) }">{{ designForm.highlight_color }}</code>
          </div>

          <div class="color-row">
            <span class="color-row-label">Kassenbereich</span>
            <div class="color-options">
              <button
                v-for="preset in designColors"
                :key="preset.value"
                type="button"
                class="color-option"
                :class="{ selected: designForm.kasse_area_background_color === preset.value }"
                :style="{ background: preset.value }"
                :title="preset.label"
                @click="designForm.kasse_area_background_color = preset.value"
              ></button>
              <label
                class="color-option color-option-custom"
                :class="{ selected: isCustomKasseArea }"
                title="Eigene Farbe wählen"
              >
                <span v-if="isCustomKasseArea" class="custom-color-preview" :style="{ background: designForm.kasse_area_background_color }"></span>
                <span v-else class="custom-color-icon">🎨</span>
                <input type="color" :value="designForm.kasse_area_background_color" @input="designForm.kasse_area_background_color = $event.target.value">
              </label>
            </div>
            <code class="color-hex" :style="{ background: designForm.kasse_area_background_color, color: getContrastColor(designForm.kasse_area_background_color) }">{{ designForm.kasse_area_background_color }}</code>
          </div>

          <button class="btn btn-primary" :disabled="appSettingsStore.isSaving" @click="saveDesignSettings">
            Farben speichern
          </button>
        </section>

        <!-- Spalte 2: Live-Vorschau -->
        <section class="settings-card preview-card">
          <h3>Vorschau</h3>
          <div class="preview-shell" :style="previewStyle">
            <div class="preview-banner">
              <img :src="previewLogoUrl" alt="Logo Vorschau" class="preview-logo" />
              <span class="preview-title">{{ designForm.app_name }}</span>
            </div>
            <div class="preview-highlight">Highlight-Fläche</div>
            <div class="preview-kasse-area">Kassenbereich</div>
          </div>
        </section>

        <!-- Spalte 3: Logo + Kassen-Hintergrund -->
        <section class="settings-card media-card">

          <!-- Logo -->
          <h3>Logo</h3>
          <div class="logo-preview logo-preview--sm">
            <img :src="appSettingsStore.logoUrl" alt="Aktuelles Logo" />
          </div>
          <input type="file" accept="image/*" class="form-input" @change="handleLogoSelection" />
          <button class="btn btn-success" :disabled="!selectedLogo || appSettingsStore.isSaving" @click="uploadLogo">
            Logo hochladen
          </button>

          <div class="divider"></div>

          <!-- Kassen-Hintergrund -->
          <h3>Hintergrundbild Produktbereich</h3>
          <div class="logo-preview logo-preview--sm">
            <img v-if="previewKasseBackgroundUrl" :src="previewKasseBackgroundUrl" alt="Produktbereich Hintergrund" />
            <span v-else class="no-image-hint">Kein Hintergrundbild</span>
          </div>
          <p class="upload-hint">⚠️ Mindestgröße: <strong>700 × 700 Pixel</strong>. Kleinere Bilder werden abgelehnt.</p>
          <input type="file" accept="image/*" class="form-input" @change="handleKasseBackgroundSelection" />
          <button class="btn btn-success" :disabled="!selectedKasseBackground || appSettingsStore.isSaving" @click="uploadKasseBackground">
            Hintergrundbild hochladen
          </button>

          <div class="kasse-bg-controls">
            <label class="checkbox-label" for="kasse-bg-enabled">
              <input
                id="kasse-bg-enabled"
                v-model="designForm.kasse_products_background_enabled"
                type="checkbox"
                class="form-checkbox"
              />
              Hintergrundbild anzeigen
            </label>
            <div class="form-group">
              <label for="kasse-bg-opacity">Deckkraft ({{ designForm.kasse_products_background_opacity }}%)</label>
              <input
                id="kasse-bg-opacity"
                v-model.number="designForm.kasse_products_background_opacity"
                type="range" min="0" max="100" step="5" class="form-input"
              >
              <div class="range-labels"><span>0%</span><span>100%</span></div>
            </div>
            <div class="form-group">
              <label for="kasse-bg-scale">Skalierung ({{ designForm.kasse_products_background_scale }}%)</label>
              <input
                id="kasse-bg-scale"
                v-model.number="designForm.kasse_products_background_scale"
                type="range" min="10" max="300" step="5" class="form-input"
              >
            </div>
          </div>

          <button class="btn btn-primary" :disabled="appSettingsStore.isSaving" @click="saveDesignSettings">
            Einstellungen aktualisieren
          </button>
        </section>

      </div>
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
        <div class="import-warning-box">
          <span class="import-warning-icon">⚠️</span>
          <div>
            <strong>Hinweis:</strong> Der Import ist ausschließlich für frische oder leere Datenbanken vorgesehen.
            Auf einer bestehenden Datenbank mit Transaktionen kann der Import zu Inkonsistenzen führen.
          </div>
        </div>
        <p class="section-description">
          Produkte, Mitglieder und Kategorien können gesammelt exportiert oder aus CSV-/ZIP-Dateien wieder importiert werden.
        </p>
        <button class="btn btn-primary" type="button" @click="showImportExportModal = true">
          Import / Export öffnen
        </button>
      </div>
    </div>

    <div v-if="activeSection === 'auditlog' && authStore.isTopAdmin" class="section-content">
      <h2>Audit-Log</h2>
      <AuditLogPanel />
    </div>

    <!-- ── Ext. Settings ──────────────────────────────── -->
    <div v-if="activeSection === 'extsettings' && authStore.isAdmin" class="section-content ext-settings-section">
      <div class="page-header">
        <div class="title-row">
          <h2>Erweiterte Einstellungen</h2>
          <span class="title-sep">|</span>
          <span class="page-subtitle">Bereich sichtbar für Admin und TopAdmin; erweiterte Systemkarten nur für TopAdmin.</span>
        </div>
      </div>

      <div class="ext-settings-grid">
        <div v-if="authStore.isTopAdmin" class="ext-card">
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

        <div v-if="authStore.isTopAdmin" class="ext-card">
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
                <input v-model="selectedLayout" type="radio" :value="layout.key" class="layout-radio">
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

        <div v-if="authStore.isTopAdmin" class="ext-card">
          <div class="ext-card-header">
            <div class="ext-card-icon">⏱️</div>
            <div>
              <h3>Session-Timer</h3>
              <p>Automatischer Logout nach Inaktivität mit Rückkehr zum Login-Screen.</p>
            </div>
          </div>
          <div class="ext-card-controls">
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
                type="number" min="1" step="1" inputmode="numeric"
              >
            </div>
            <button class="btn btn-primary" type="button" :disabled="appSettingsStore.isSaving" @click="saveSessionTimer">
              Session-Timer speichern
            </button>
          </div>
        </div>

        <div v-if="authStore.isAdmin" class="ext-card">
          <div class="ext-card-header">
            <div class="ext-card-icon">🧾</div>
            <div>
              <h3>Deckel-Funktion</h3>
              <p>Steuert, ob der Deckel-Button im Kassenbereich angezeigt wird.</p>
            </div>
          </div>
          <div class="ext-card-controls">
            <label class="toggle-label" for="deckel-enabled">
              <input id="deckel-enabled" v-model="deckelEnabled" type="checkbox" class="toggle-checkbox">
              <span>Deckel-Funktion aktivieren</span>
            </label>
            <button class="btn btn-primary" type="button" :disabled="appSettingsStore.isSaving" @click="saveDeckelSettings">
              Deckel-Funktion speichern
            </button>
          </div>
        </div>
      </div>

      <BusinessDataModal
        :show="showBusinessModal"
        v-model:business-data="businessData"
        @close="showBusinessModal = false"
        @save="saveBusinessData"
      />
    </div>

    <ImportExportModal
      :show="showImportExportModal"
      @close="showImportExportModal = false"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import AuditLogPanel from '@/components/admin/AuditLogPanel.vue'
import ImportExportModal from '@/components/ImportExportModal.vue'
import { useAppSettingsStore } from '@/stores/appSettings'
import { useNotificationStore } from '@/stores/notification'
import { useAuthStore } from '@/stores/auth'
import { getContrastColor } from '@/services/utils'
import { SESSION_RELOAD_FLAG_KEY } from '@/constants'
import apiService from '@/services/api'
import CredentialConfirmModal from '@/components/CredentialConfirmModal.vue'
import BusinessDataModal from '@/views/admin/modal/BusinessDataModal.vue'

const appSettingsStore = useAppSettingsStore()
const notificationStore = useNotificationStore()
const authStore = useAuthStore()

const activeSection = ref('design')

const designColors = [
  { value: '#FFFFFF', label: 'Weiß' },
  { value: '#D7DCE2', label: 'Blaugrau' },
  { value: '#131820', label: 'Marine' },
  { value: '#5C8F3A', label: 'Grün' },
  { value: '#3B82F6', label: 'Blau' },
  { value: '#F97316', label: 'Orange' },
  { value: '#111827', label: 'Anthrazit' },
]

const designForm = reactive({
  app_name: 'KGB - KickerKasse',
  background_color: '#D7DCE2',
  banner_color: '#131820',
  highlight_color: '#5C8F3A',
  kasse_area_background_color: '#FFFFFF',
  kasse_products_background_scale: 100,
  kasse_products_background_opacity: 100,
  kasse_products_background_enabled: true,
})

const selectedLogo = ref(null)
const selectedLogoPreview = ref('')
const selectedKasseBackground = ref(null)
const selectedKasseBackgroundPreview = ref('')

const isCustomBackground = computed(() => !designColors.some(c => c.value === designForm.background_color))
const isCustomBanner = computed(() => !designColors.some(c => c.value === designForm.banner_color))
const isCustomHighlight = computed(() => !designColors.some(c => c.value === designForm.highlight_color))
const isCustomKasseArea = computed(() => !designColors.some(c => c.value === designForm.kasse_area_background_color))

const previewStyle = computed(() => ({
  '--preview-background': designForm.background_color,
  '--preview-banner': designForm.banner_color,
  '--preview-highlight': designForm.highlight_color,
  '--preview-kasse-area': designForm.kasse_area_background_color,
  '--preview-banner-contrast': getContrastColor(designForm.banner_color),
  '--preview-highlight-contrast': getContrastColor(designForm.highlight_color),
  '--preview-kasse-area-contrast': getContrastColor(designForm.kasse_area_background_color),
}))

const previewLogoUrl = computed(() => selectedLogoPreview.value || appSettingsStore.logoUrl)
const previewKasseBackgroundUrl = computed(() => (
  selectedKasseBackgroundPreview.value
  || (appSettingsStore.settings.kasse_products_background_url
    ? `${appSettingsStore.settings.kasse_products_background_url}?v=${appSettingsStore.settings.asset_version}`
    : '')
))

const syncDesignForm = () => {
  designForm.app_name = appSettingsStore.settings.app_name
  designForm.background_color = appSettingsStore.settings.background_color
  designForm.banner_color = appSettingsStore.settings.banner_color
  designForm.highlight_color = appSettingsStore.settings.highlight_color
  designForm.kasse_area_background_color = appSettingsStore.settings.kasse_area_background_color || '#FFFFFF'
  designForm.kasse_products_background_scale = appSettingsStore.settings.kasse_products_background_scale || 100
  designForm.kasse_products_background_opacity = appSettingsStore.settings.kasse_products_background_opacity ?? 100
  designForm.kasse_products_background_enabled = appSettingsStore.settings.kasse_products_background_enabled !== false
}

const DESIGN_COLOR_DEFAULTS = {
  background_color: '#D7DCE2',
  banner_color: '#131820',
  highlight_color: '#209529',
  kasse_area_background_color: '#FFFFFF',
}

const resetDesignColors = () => {
  designForm.background_color = DESIGN_COLOR_DEFAULTS.background_color
  designForm.banner_color = DESIGN_COLOR_DEFAULTS.banner_color
  designForm.highlight_color = DESIGN_COLOR_DEFAULTS.highlight_color
  designForm.kasse_area_background_color = DESIGN_COLOR_DEFAULTS.kasse_area_background_color
}

const handleLogoSelection = (event) => {
  const [file] = event.target.files || []
  if (!file) return
  selectedLogo.value = file
  selectedLogoPreview.value = URL.createObjectURL(file)
}

const handleKasseBackgroundSelection = (event) => {
  const [file] = event.target.files || []
  if (!file) return
  const objectUrl = URL.createObjectURL(file)
  const img = new Image()
  img.onload = () => {
    if (img.width < 700 || img.height < 700) {
      notificationStore.error(`Das Bild ist zu klein (${img.width}×${img.height}px). Mindestgröße: 700×700 Pixel.`)
      event.target.value = ''
      URL.revokeObjectURL(objectUrl)
      return
    }
    selectedKasseBackground.value = file
    selectedKasseBackgroundPreview.value = objectUrl
  }
  img.src = objectUrl
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

const uploadKasseBackground = async () => {
  if (!selectedKasseBackground.value) return
  try {
    await appSettingsStore.uploadKasseProductsBackground(selectedKasseBackground.value)
    selectedKasseBackground.value = null
    selectedKasseBackgroundPreview.value = ''
    notificationStore.success('Produktbereich-Hintergrund erfolgreich aktualisiert')
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Fehler beim Hochladen des Produktbereich-Hintergrunds')
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
const deckelEnabled = ref(false)

const businessData = ref({
  name: '', street: '', zip: '', city: '',
  phone: '', email: '', taxNumber: '', registrationNumber: '',
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

const syncDeckelSetting = () => {
  deckelEnabled.value = !!appSettingsStore.settings.deckel_enabled
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

const saveDeckelSettings = async () => {
  try {
    await appSettingsStore.saveAdminSettings({ deckel_enabled: deckelEnabled.value })
    notificationStore.success('Deckel-Funktion gespeichert')
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Deckel-Funktion konnte nicht gespeichert werden')
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
  syncDeckelSetting()

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
      // Silently ignore invalid localStorage data
    }
  }
})
</script>

<style scoped lang="scss">
.admin-config {
  background: var(--app-background-color);
  padding: 0.35rem 1rem 0.75rem;
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
  margin: -0.35rem -1rem 1rem;
  padding: 0.35rem 1rem 0.75rem;
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
  font-size: 1.25rem;
  font-weight: 700;
  color: #333;
  line-height: 1.2;
}

.title-sep { color: #aaa; font-weight: 300; }

.page-subtitle { color: #64748b; margin: 0; }

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

  &:hover { background: #f1f5f9; border-color: #cbd5e1; }
  &.active {
    background: var(--app-highlight-color);
    border-color: var(--app-highlight-color);
    color: var(--app-highlight-contrast);
  }
}

// ── Section content ───────────────────────────────────
.section-content {
  h2 {
    font-size: 1.25rem;
    color: #1e293b;
    margin: 0 0 0.75rem;
  }
}

.section-description {
  margin: 0;
  color: #64748b;
  font-size: 0.9rem;
}

.import-warning-box {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  background: #fff7ed;
  border: 1px solid #fdba74;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  font-size: 0.9rem;
  color: #92400e;

  .import-warning-icon { font-size: 1.1rem; flex-shrink: 0; margin-top: 0.05rem; }
}

// ── Design grid: 3 columns ────────────────────────────
.design-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr) minmax(0, 1.1fr);
  gap: 0.9rem;
  align-items: start;

  @media (max-width: 900px) {
    grid-template-columns: 1fr 1fr;
  }
  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
}

// ── Settings cards ────────────────────────────────────
.settings-card {
  background: color-mix(in srgb, var(--app-background-color) 55%, white);
  border: 1px solid color-mix(in srgb, var(--app-background-color) 65%, #777);
  padding: 0.85rem;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;

  h3 {
    margin: 0;
    font-size: 0.9rem;
    font-weight: 700;
    color: #1e293b;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
}

.card-row-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;

  h3 { margin: 0; }
}

// ── Reset hint box ────────────────────────────────────
.reset-hint-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  background: #fffbeb;
  border: 1.5px solid #f59e0b;
  border-radius: 8px;
  padding: 0.6rem 0.75rem;
}

.reset-hint-text {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  min-width: 0;

  strong {
    display: block;
    font-size: 0.8rem;
    color: #78350f;
    font-weight: 700;
    line-height: 1.2;
  }
}

.reset-hint-icon {
  font-size: 1.3rem;
  flex-shrink: 0;
  color: #b45309;
}

.reset-hint-sub {
  display: block;
  font-size: 0.72rem;
  color: #92400e;
  margin-top: 1px;
}

.btn-reset {
  flex-shrink: 0;
  padding: 0.35rem 0.8rem;
  border-radius: 6px;
  border: 1px solid #d97706;
  background: #f59e0b;
  color: #fff;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  transition: filter 0.15s;
  white-space: nowrap;

  &:hover { filter: brightness(1.08); }
  &:active { filter: brightness(0.95); }
}

// ── Form ──────────────────────────────────────────────
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;

  label {
    font-size: 0.8rem;
    font-weight: 600;
    color: #334155;
  }
}

.form-input { width: 100%; }

// ── Color pickers ─────────────────────────────────────
.color-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;

  .color-row-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: #334155;
    min-width: 105px;
    flex-shrink: 0;
  }

  .color-options {
    flex: 1;
    flex-wrap: wrap;
    min-width: 0;
  }
}

.color-hex {
  font-size: 0.68rem;
  font-family: monospace;
  padding: 2px 6px;
  border-radius: 4px;
  flex-shrink: 0;
  white-space: nowrap;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.color-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  align-items: center;
}

.color-option {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: transform 0.12s, border-color 0.12s;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;

  &:hover { transform: scale(1.15); }
  &.selected { border-color: #1e293b; box-shadow: 0 0 0 2px white inset; }
}

.color-option-custom {
  background: #f8fafc;
  border: 2px dashed #94a3b8;
  cursor: pointer;
  overflow: visible;

  &.selected { border-style: solid; border-color: #1e293b; }

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
  border-radius: 4px;
  position: absolute;
  inset: 0;
}

.custom-color-icon {
  font-size: 0.85rem;
  pointer-events: none;
}

// ── Vorschau card ─────────────────────────────────────
.preview-card {
  .preview-shell {
    background: var(--preview-background);
    border-radius: 8px;
    padding: 0.5rem;
    flex: 1;
  }

  .preview-banner {
    background: var(--preview-banner);
    color: var(--preview-banner-contrast);
    border-bottom: 2px solid var(--preview-highlight);
    border-radius: 5px;
    padding: 0.4rem 0.65rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    justify-content: center;
    flex-wrap: wrap;
  }

  .preview-logo {
    width: min(90px, 100%);
    height: 30px;
    object-fit: contain;
  }

  .preview-title {
    font-size: 0.8rem;
    font-weight: 700;
  }

  .preview-highlight {
    margin-top: 0.35rem;
    background: var(--preview-highlight);
    color: var(--preview-highlight-contrast);
    border-radius: 5px;
    padding: 0.3rem 0.5rem;
    font-weight: 600;
    font-size: 0.74rem;
  }

  .preview-kasse-area {
    margin-top: 0.35rem;
    background: var(--preview-kasse-area);
    color: var(--preview-kasse-area-contrast);
    border-radius: 5px;
    padding: 0.5rem 0.65rem;
    font-weight: 600;
    font-size: 0.8rem;
    border: 1px solid color-mix(in srgb, var(--preview-banner) 20%, transparent);
  }
}

// ── Media card (Logo + Kasse BG) ──────────────────────
.media-card {
  .logo-preview--sm {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 90px;
    background: white;
    border-radius: 8px;
    padding: 0.65rem;

    img {
      max-width: 100%;
      max-height: 80px;
      object-fit: contain;
    }
  }

  .no-image-hint {
    font-size: 0.78rem;
    color: #94a3b8;
  }
}

.divider {
  border-top: 1px solid color-mix(in srgb, var(--app-background-color) 65%, #aaa);
  margin: 0.1rem 0;
}

.kasse-bg-controls {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.upload-hint {
  font-size: 0.78rem;
  color: #92400e;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 6px;
  padding: 0.35rem 0.6rem;
  margin: 0;
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

.access-note { font-weight: 700; }

// ── Ext. Settings ─────────────────────────────────────
.ext-settings-section {
  --ext-primary: #3b82f6;
  --ext-success: #10b981;
  --ext-border: #e2e8f0;
}

.page-header {
  margin-bottom: 0.75rem;
  h2 { font-size: 1.25rem; color: #333; margin: 0; }
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

  h3 { margin: 0 0 0.25rem; font-size: 1.05rem; color: #1e293b; }
  p { margin: 0; font-size: 0.85rem; color: #64748b; }
}

.ext-card-icon { font-size: 2rem; flex-shrink: 0; }

.layout-options { display: flex; flex-wrap: wrap; gap: 0.75rem; }

.layout-option {
  cursor: pointer;
  .layout-radio { display: none; }
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

  .layout-option:hover & { border-color: var(--ext-primary, #3b82f6); }
  .layout-option.selected & {
    border-color: var(--ext-primary, #3b82f6);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  }
}

.layout-preview-icon { font-size: 1.8rem; margin-bottom: 0.3rem; }
.layout-preview-name { font-size: 0.78rem; font-weight: 600; color: #334155; }

.layout-active-badge {
  position: absolute;
  top: -8px; right: -8px;
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

.ext-card-controls {
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

.toggle-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-weight: 500;
}

.toggle-checkbox { width: 1.1rem; height: 1.1rem; cursor: pointer; }

// ── Buttons ───────────────────────────────────────────
.btn {
  padding: 0.55rem 1.1rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-size: 0.9rem;
  min-height: 38px;
  transition: filter 0.15s;

  &:disabled { opacity: 0.55; cursor: not-allowed; }
  &:not(:disabled):hover { filter: brightness(1.07); }
}

.btn-primary   { background: #3b82f6; color: white; }
.btn-success   { background: #10b981; color: white; }
.btn-secondary { background: #e2e8f0; color: #475569; }
.btn-warning   { background: #f59e0b; color: white; }
.btn-danger {
  background: #dc2626;
  color: white;
  padding: 0.75rem 1.5rem;
  font-size: 0.95rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  font-size: 0.85rem;
}

.form-checkbox {
  width: 1rem;
  height: 1rem;
  accent-color: var(--app-highlight-color, #5C8F3A);
  cursor: pointer;
}

.range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.72rem;
  color: #64748b;
  margin-top: 0.15rem;
}

@media (max-width: 640px) {
  .ext-settings-grid { grid-template-columns: 1fr; }
}
</style>
