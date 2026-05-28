<template>
  <div class="admin-config">
    <!-- ═══════════════════════════════════════════════
         SECTION NAVIGATION
         ═══════════════════════════════════════════════ -->
    <div class="section-nav">
      <div class="title-row">
        <span class="section-nav-label">⚙️ Einstellungsverwaltung</span>
        <span class="title-sep">|</span>
        <span class="page-subtitle">Konfiguration, Design und Systemeinstellungen</span>
      </div>
      <div class="section-nav-buttons">
        <button
          :class="['section-tab', { active: activeSection === 'design' }]"
          type="button"
          @click="activeSection = 'design'"
        >
          <span class="tab-icon">🎨</span> Design
        </button>
        <button
          :class="['section-tab', { active: activeSection === 'datamaintenance' }]"
          type="button"
          @click="activeSection = 'datamaintenance'"
        >
          <span class="tab-icon">🧹</span> Datenpflege
        </button>
        <button
          v-if="authStore.isAdmin"
          :class="['section-tab', { active: activeSection === 'importexport' }]"
          type="button"
          @click="activeSection = 'importexport'"
        >
          <span class="tab-icon">🔄</span> Import / Export
        </button>
        <button
          v-if="authStore.isAdmin"
          :class="['section-tab', { active: activeSection === 'extsettings' }]"
          type="button"
          @click="activeSection = 'extsettings'"
        >
          <span class="tab-icon">⚙️</span> Erweitert
        </button>
        <button
          v-if="authStore.isTopAdmin"
          :class="['section-tab', { active: activeSection === 'auditlog' }]"
          type="button"
          @click="activeSection = 'auditlog'"
        >
          <span class="tab-icon">🔍</span> Audit-Log
        </button>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════
         SECTION: DESIGN
         ═══════════════════════════════════════════════ -->
    <div v-if="activeSection === 'design'" class="section-content">
      <div class="section-title">
        <div class="title-icon">🎨</div>
        Design & Logo
      </div>

      <!-- Row 1: Colors + Preview -->
      <div class="grid-2">
        <!-- Card: Farben -->
        <div class="card">
          <div class="card-header">
            <div class="card-icon blue">🎨</div>
            <div>
              <div class="card-title">Farben</div>
              <div class="card-subtitle">App-Farben anpassen</div>
            </div>
          </div>

          <!-- Reset Hint -->
          <div class="info-row">
            <span class="info-icon">↺</span>
            <div class="info-text">
              <strong>Standardfarben wiederherstellen</strong>
              Setzt alle Farben auf die Werkseinstellung zurück.
            </div>
            <button class="btn btn-warning btn-sm" @click="resetDesignColors">Reset</button>
          </div>

          <!-- App Name -->
          <div class="form-group">
            <label class="form-label">App-Überschrift</label>
            <input
              v-model.trim="designForm.app_name"
              type="text"
              class="form-input"
              maxlength="120"
            />
          </div>

          <!-- Hintergrundfarbe -->
          <div class="form-group">
            <label class="form-label">
              Hintergrundfarbe
              <span class="color-hex-display">{{ designForm.background_color }}</span>
            </label>
            <div class="color-presets">
              <button
                v-for="preset in designColors"
                :key="preset.value"
                type="button"
                class="color-preset"
                :class="{ selected: designForm.background_color === preset.value }"
                :style="{ background: preset.value }"
                :title="preset.label"
                @click="designForm.background_color = preset.value"
              />
              <label
                class="color-preset color-custom"
                :class="{ selected: isCustomBackground }"
                title="Eigene Farbe wählen"
              >
                <span
                  v-if="isCustomBackground"
                  class="custom-color-preview"
                  :style="{ background: designForm.background_color }"
                />
                <span v-else class="custom-color-icon">🎨</span>
                <input
                  type="color"
                  :value="designForm.background_color"
                  @input="designForm.background_color = $event.target.value"
                />
              </label>
            </div>
          </div>

          <!-- Bannerfarbe -->
          <div class="form-group">
            <label class="form-label">
              Bannerfarbe
              <span class="color-hex-display">{{ designForm.banner_color }}</span>
            </label>
            <div class="color-presets">
              <button
                v-for="preset in designColors"
                :key="preset.value"
                type="button"
                class="color-preset"
                :class="{ selected: designForm.banner_color === preset.value }"
                :style="{ background: preset.value }"
                :title="preset.label"
                @click="designForm.banner_color = preset.value"
              />
              <label
                class="color-preset color-custom"
                :class="{ selected: isCustomBanner }"
                title="Eigene Farbe wählen"
              >
                <span
                  v-if="isCustomBanner"
                  class="custom-color-preview"
                  :style="{ background: designForm.banner_color }"
                />
                <span v-else class="custom-color-icon">🎨</span>
                <input
                  type="color"
                  :value="designForm.banner_color"
                  @input="designForm.banner_color = $event.target.value"
                />
              </label>
            </div>
          </div>

          <!-- Highlight-Farbe -->
          <div class="form-group">
            <label class="form-label">
              Highlight-Farbe
              <span class="color-hex-display">{{ designForm.highlight_color }}</span>
            </label>
            <div class="color-presets">
              <button
                v-for="preset in designColors"
                :key="preset.value"
                type="button"
                class="color-preset"
                :class="{ selected: designForm.highlight_color === preset.value }"
                :style="{ background: preset.value }"
                :title="preset.label"
                @click="designForm.highlight_color = preset.value"
              />
              <label
                class="color-preset color-custom"
                :class="{ selected: isCustomHighlight }"
                title="Eigene Farbe wählen"
              >
                <span
                  v-if="isCustomHighlight"
                  class="custom-color-preview"
                  :style="{ background: designForm.highlight_color }"
                />
                <span v-else class="custom-color-icon">🎨</span>
                <input
                  type="color"
                  :value="designForm.highlight_color"
                  @input="designForm.highlight_color = $event.target.value"
                />
              </label>
            </div>
          </div>

          <!-- Kassenbereich -->
          <div class="form-group">
            <label class="form-label">
              Kassenbereich
              <span class="color-hex-display">{{ designForm.kasse_area_background_color }}</span>
            </label>
            <div class="color-presets">
              <button
                v-for="preset in designColors"
                :key="preset.value"
                type="button"
                class="color-preset"
                :class="{ selected: designForm.kasse_area_background_color === preset.value }"
                :style="{ background: preset.value }"
                :title="preset.label"
                @click="designForm.kasse_area_background_color = preset.value"
              />
              <label
                class="color-preset color-custom"
                :class="{ selected: isCustomKasseArea }"
                title="Eigene Farbe wählen"
              >
                <span
                  v-if="isCustomKasseArea"
                  class="custom-color-preview"
                  :style="{ background: designForm.kasse_area_background_color }"
                />
                <span v-else class="custom-color-icon">🎨</span>
                <input
                  type="color"
                  :value="designForm.kasse_area_background_color"
                  @input="designForm.kasse_area_background_color = $event.target.value"
                />
              </label>
            </div>
          </div>

          <div class="btn-row">
            <button
              class="btn btn-primary"
              :disabled="appSettingsStore.isSaving"
              @click="saveDesignSettings"
            >
              💾 Farben speichern
            </button>
          </div>
        </div>

        <!-- Card: Live-Vorschau -->
        <div class="card">
          <div class="card-header">
            <div class="card-icon purple">👁️</div>
            <div>
              <div class="card-title">Live-Vorschau</div>
              <div class="card-subtitle">Echtzeit-Vorschau der Änderungen</div>
            </div>
          </div>
          <div class="preview-box" :style="previewStyle">
            <div class="preview-banner">
              <img :src="previewLogoUrl" alt="Logo" class="preview-logo" />
              <span class="preview-title">{{ designForm.app_name }}</span>
            </div>
            <div class="preview-body">
              <div class="preview-highlight">Highlight-Fläche</div>
              <div class="preview-kasse">Kassenbereich</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Row 2: Logo + Kassen-Hintergrund -->
      <div class="grid-2">
        <!-- Card: Logo -->
        <div class="card">
          <div class="card-header">
            <div class="card-icon green">🏷️</div>
            <div>
              <div class="card-title">Logo</div>
              <div class="card-subtitle">App-Logo hochladen</div>
            </div>
          </div>
          <div class="image-preview">
            <img
              v-if="appSettingsStore.logoUrl"
              :src="appSettingsStore.logoUrl"
              alt="Aktuelles Logo"
            />
            <span v-else class="no-image">Kein Logo ausgewählt</span>
          </div>
          <div class="upload-zone" @click="$refs.logoInput.click()">
            <div class="upload-icon">📤</div>
            <div class="upload-text">Logo hier ablegen oder klicken</div>
            <div class="upload-hint">Bilddatei (PNG, JPG, SVG)</div>
          </div>
          <input
            ref="logoInput"
            type="file"
            accept="image/*"
            style="display: none"
            @change="handleLogoSelection"
          />
          <div class="btn-row">
            <button
              class="btn btn-success"
              :disabled="!selectedLogo || appSettingsStore.isSaving"
              @click="uploadLogo"
            >
              ⬆️ Logo hochladen
            </button>
          </div>
        </div>

        <!-- Card: Kassen-Hintergrund -->
        <div class="card">
          <div class="card-header">
            <div class="card-icon orange">🖼️</div>
            <div>
              <div class="card-title">Hintergrundbild Produktbereich</div>
              <div class="card-subtitle">Hintergrund für den Kassenbereich</div>
            </div>
          </div>
          <div class="image-preview">
            <img
              v-if="previewKasseBackgroundUrl"
              :src="previewKasseBackgroundUrl"
              alt="Produktbereich Hintergrund"
            />
            <span v-else class="no-image">Kein Hintergrundbild</span>
          </div>
          <div class="warning-box">
            <span class="warning-icon">⚠️</span>
            <div class="warning-text">
              <strong>Mindestgröße: 700 × 700 Pixel</strong>
              Kleinere Bilder werden abgelehnt.
            </div>
          </div>
          <div class="upload-zone" @click="$refs.bgInput.click()">
            <div class="upload-icon">📤</div>
            <div class="upload-text">Hintergrundbild hier ablegen</div>
            <div class="upload-hint">Mindestens 700×700 px</div>
          </div>
          <input
            ref="bgInput"
            type="file"
            accept="image/*"
            style="display: none"
            @change="handleKasseBackgroundSelection"
          />

          <hr class="divider" />

          <div class="toggle-row">
            <span class="toggle-label-text">Hintergrundbild anzeigen</span>
            <div
              class="toggle-switch"
              :class="{ active: designForm.kasse_products_background_enabled }"
              @click="designForm.kasse_products_background_enabled = !designForm.kasse_products_background_enabled"
            />
          </div>

          <div class="form-group">
            <label class="form-label">
              Deckkraft
              <span class="hint">{{ designForm.kasse_products_background_opacity }}%</span>
            </label>
            <input
              v-model.number="designForm.kasse_products_background_opacity"
              type="range"
              class="form-input"
              min="0"
              max="100"
              step="5"
            />
            <div class="range-labels"><span>0%</span><span>100%</span></div>
          </div>

          <div class="form-group">
            <label class="form-label">
              Skalierung
              <span class="hint">{{ designForm.kasse_products_background_scale }}%</span>
            </label>
            <input
              v-model.number="designForm.kasse_products_background_scale"
              type="range"
              class="form-input"
              min="10"
              max="300"
              step="5"
            />
            <div class="range-labels"><span>10%</span><span>300%</span></div>
          </div>

          <div class="btn-row">
            <button
              class="btn btn-success"
              :disabled="!selectedKasseBackground || appSettingsStore.isSaving"
              @click="uploadKasseBackground"
            >
              ⬆️ Hintergrund hochladen
            </button>
            <button
              class="btn btn-primary"
              :disabled="appSettingsStore.isSaving"
              @click="saveDesignSettings"
            >
              💾 Einstellungen aktualisieren
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════
         SECTION: DATENPFLEGE
         ═══════════════════════════════════════════════ -->
    <div v-if="activeSection === 'datamaintenance'" class="section-content">
      <div class="section-title">
        <div class="title-icon">🧹</div>
        Datenpflege
      </div>

      <div class="grid-2">
        <div class="card">
          <div class="card-header">
            <div class="card-icon red">🧨</div>
            <div>
              <div class="card-title">Hard-Reset</div>
              <div class="card-subtitle">Alle Daten unwiderruflich löschen</div>
            </div>
          </div>
          <div class="warning-box danger">
            <span class="warning-icon">⚠️</span>
            <div class="warning-text">
              <strong>Achtung!</strong>
              Der Hard-Reset entfernt Transaktionen, Benutzer, Mitglieder, Produkte,
              Statistiken, Gutscheine, Verzehrkarten und Kategorien unwiderruflich.
            </div>
          </div>
          <div class="warning-box success">
            <span class="warning-icon">🔒</span>
            <div class="warning-text">
              <strong>Zugriffsbeschränkung</strong>
              Nur der Top-Admin darf diese Aktion ausführen.
            </div>
          </div>
          <div class="btn-row">
            <button
              class="btn btn-danger"
              :disabled="!authStore.isTopAdmin"
              @click="showResetModal = true"
            >
              🧨 Hard-Reset starten
            </button>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-icon gray">📋</div>
            <div>
              <div class="card-title">Daten-Übersicht</div>
              <div class="card-subtitle">Aktueller Datenbestand</div>
            </div>
          </div>
          <div class="data-overview">
            <div class="overview-item">
              <span>Transaktionen</span>
              <span class="overview-value">{{ dataStats.transactions ?? '—' }}</span>
            </div>
            <div class="overview-item">
              <span>Mitglieder</span>
              <span class="overview-value">{{ dataStats.members ?? '—' }}</span>
            </div>
            <div class="overview-item">
              <span>Benutzer</span>
              <span class="overview-value">{{ dataStats.users ?? '—' }}</span>
            </div>
            <div class="overview-item">
              <span>Produkte</span>
              <span class="overview-value">{{ dataStats.products ?? '—' }}</span>
            </div>
            <div class="overview-item">
              <span>Kategorien</span>
              <span class="overview-value">{{ dataStats.categories ?? '—' }}</span>
            </div>
            <div class="overview-item">
              <span>Gutscheine</span>
              <span class="overview-value">{{ dataStats.vouchers ?? '—' }}</span>
            </div>
            <div class="overview-item">
              <span>Audit-Log Einträge</span>
              <span class="overview-value">{{ dataStats.audit_log_entries ?? '—' }}</span>
            </div>
          </div>
          <div class="btn-row">
            <button class="btn btn-outline btn-sm" @click="loadDataStats">🔄 Aktualisieren</button>
          </div>
        </div>
      </div>

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

    <!-- ═══════════════════════════════════════════════
         SECTION: IMPORT / EXPORT
         ═══════════════════════════════════════════════ -->
    <div v-if="activeSection === 'importexport' && authStore.isAdmin" class="section-content">
      <div class="section-title">
        <div class="title-icon">🔄</div>
        Import / Export
      </div>

      <div class="warning-box" style="margin-bottom: 0.75rem;">
        <span class="warning-icon">⚠️</span>
        <div class="warning-text">
          <strong>Hinweis:</strong> Der Import ist ausschließlich für frische oder leere
          Datenbanken vorgesehen. Auf einer bestehenden Datenbank mit Transaktionen kann
          der Import zu Inkonsistenzen führen.
        </div>
      </div>

      <div class="grid-2">
        <div class="card">
          <div class="card-header">
            <div class="card-icon blue">📥</div>
            <div>
              <div class="card-title">Import</div>
              <div class="card-subtitle">CSV oder ZIP-Datei hochladen</div>
            </div>
          </div>
          <div class="hint-box">
            Importiere Produkte, Mitglieder und Kategorien aus einer CSV- oder ZIP-Datei.
          </div>
          <div class="btn-row">
            <button class="btn btn-primary" @click="showImportExportModal = true; importExportInitialTab = 'import'">
              📥 Import öffnen
            </button>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-icon green">📤</div>
            <div>
              <div class="card-title">Export</div>
              <div class="card-subtitle">Daten als CSV oder ZIP exportieren</div>
            </div>
          </div>
          <div class="hint-box">
            Exportiere Produkte, Mitglieder und Kategorien. Einzelne Bereiche als CSV,
            Kombinationen oder mit Medien als ZIP.
          </div>
          <div class="btn-row">
            <button class="btn btn-success" @click="showImportExportModal = true; importExportInitialTab = 'export'">
              📤 Export öffnen
            </button>
          </div>
        </div>
      </div>

      <ImportExportModal
        :show="showImportExportModal"
        :initial-tab="importExportInitialTab"
        @close="showImportExportModal = false"
      />
    </div>

    <!-- ═══════════════════════════════════════════════
         SECTION: AUDIT-LOG
         ═══════════════════════════════════════════════ -->
    <div v-if="activeSection === 'auditlog' && authStore.isTopAdmin" class="section-content">
      <div class="section-title">
        <div class="title-icon">🔍</div>
        Audit-Log
      </div>
      <AuditLogPanel />
    </div>

    <!-- ═══════════════════════════════════════════════
         SECTION: ERWEITERTE EINSTELLUNGEN
         ═══════════════════════════════════════════════ -->
    <div v-if="activeSection === 'extsettings' && authStore.isAdmin" class="section-content">
      <div class="section-title">
        <div class="title-icon">⚙️</div>
        Erweiterte Einstellungen
      </div>

      <div class="grid-2">
        <!-- Geschäftsdaten -->
        <div v-if="authStore.isTopAdmin" class="card">
          <div class="card-header">
            <div class="card-icon blue">🏢</div>
            <div>
              <div class="card-title">Geschäftsdaten</div>
              <div class="card-subtitle">Vereinsname, Anschrift und Kontaktdaten</div>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Firmenname</label>
            <input v-model="businessData.name" type="text" class="form-input" placeholder="z.B. KickerKasse e.V." />
          </div>
          <div class="form-group">
            <label class="form-label">Straße & Hausnr.</label>
            <input v-model="businessData.street" type="text" class="form-input" placeholder="Musterstraße 1" />
          </div>
          <div class="grid-2" style="gap: 0.75rem;">
            <div class="form-group">
              <label class="form-label">PLZ</label>
              <input v-model="businessData.zip" type="text" class="form-input" placeholder="12345" />
            </div>
            <div class="form-group">
              <label class="form-label">Ort</label>
              <input v-model="businessData.city" type="text" class="form-input" placeholder="Musterstadt" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Telefon</label>
            <input v-model="businessData.phone" type="tel" class="form-input" placeholder="+49 123 456789" />
          </div>
          <div class="form-group">
            <label class="form-label">E-Mail</label>
            <input v-model="businessData.email" type="email" class="form-input" placeholder="info@beispiel.de" />
          </div>
          <div class="btn-row">
            <button class="btn btn-primary" @click="saveBusinessData">💾 Geschäftsdaten speichern</button>
          </div>
        </div>

        <!-- Layout-Chooser -->
        <div v-if="authStore.isTopAdmin" class="card">
          <div class="card-header">
            <div class="card-icon purple">🖥️</div>
            <div>
              <div class="card-title">Layout-Chooser</div>
              <div class="card-subtitle">Kassenansicht-Layout auswählen</div>
            </div>
          </div>
          <div class="layout-grid">
            <div
              v-for="layout in availableLayouts"
              :key="layout.key"
              class="layout-card"
              :class="{ selected: selectedLayout === layout.key }"
              @click="selectedLayout = layout.key"
            >
              <div class="layout-icon">{{ layout.icon }}</div>
              <div class="layout-name">{{ layout.name }}</div>
              <div v-if="selectedLayout === layout.key" class="layout-badge">Aktiv</div>
            </div>
          </div>
          <div v-if="layoutChanged" class="layout-changed-hint">
            <span>⚠️ Auswahl geändert. Zum Übernehmen neu laden.</span>
            <button class="btn btn-warning btn-sm" @click="applyLayout">🔄 Jetzt neu laden</button>
          </div>
        </div>

        <!-- Session-Timer -->
        <div v-if="authStore.isTopAdmin" class="card">
          <div class="card-header">
            <div class="card-icon orange">⏱️</div>
            <div>
              <div class="card-title">Session-Timer</div>
              <div class="card-subtitle">Automatischer Logout bei Inaktivität</div>
            </div>
          </div>
          <div class="toggle-row">
            <span class="toggle-label-text">Session-Timer aktivieren</span>
            <div
              class="toggle-switch"
              :class="{ active: sessionTimer.enabled }"
              @click="sessionTimer.enabled = !sessionTimer.enabled"
            />
          </div>
          <div class="timer-display" :class="{ inactive: !sessionTimer.enabled }">
            <div>
              <div class="timer-value">{{ sessionTimer.minutes }}</div>
              <div class="timer-label">Minuten</div>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Automatische Abmeldung nach (Minuten)</label>
            <input
              v-model.number="sessionTimer.minutes"
              type="number"
              class="form-input"
              min="1"
              step="1"
              inputmode="numeric"
              :disabled="!sessionTimer.enabled"
            />
          </div>
          <div class="btn-row">
            <button
              class="btn btn-primary"
              :disabled="appSettingsStore.isSaving"
              @click="saveSessionTimer"
            >
              💾 Session-Timer speichern
            </button>
          </div>
        </div>

        <!-- Deckel-Funktion -->
        <div v-if="authStore.isAdmin" class="card">
          <div class="card-header">
            <div class="card-icon green">🧾</div>
            <div>
              <div class="card-title">Deckel-Funktion</div>
              <div class="card-subtitle">Deckel-Button im Kassenbereich</div>
            </div>
          </div>
          <div class="toggle-row">
            <span class="toggle-label-text">Deckel-Funktion aktivieren</span>
            <div
              class="toggle-switch"
              :class="{ active: deckelEnabled }"
              @click="deckelEnabled = !deckelEnabled"
            />
          </div>
          <div class="hint-box">
            Wenn aktiviert, wird der Deckel-Button im Kassenbereich angezeigt und kann zur
            Verwaltung von Deckeln verwendet werden.
          </div>
          <div class="btn-row">
            <button
              class="btn btn-primary"
              :disabled="appSettingsStore.isSaving"
              @click="saveDeckelSettings"
            >
              💾 Deckel-Einstellungen speichern
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

// ── Design Colors ─────────────────────────────────────
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

const previewStyle = computed(() => {
  const bgImage = previewKasseBackgroundUrl.value
    ? `url(${previewKasseBackgroundUrl.value})`
    : 'none'
  return {
    '--preview-background': designForm.background_color,
    '--preview-banner': designForm.banner_color,
    '--preview-highlight': designForm.highlight_color,
    '--preview-kasse-area': designForm.kasse_area_background_color,
    '--preview-banner-contrast': getContrastColor(designForm.banner_color),
    '--preview-highlight-contrast': getContrastColor(designForm.highlight_color),
    '--preview-kasse-area-contrast': getContrastColor(designForm.kasse_area_background_color),
    '--preview-bg-image': designForm.kasse_products_background_enabled ? bgImage : 'none',
  }
})

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
const dataStats = ref({})

const loadDataStats = async () => {
  try {
    const response = await apiService.get('/admin/data-maintenance/stats')
    dataStats.value = response.data
  } catch (e) {
    console.error('Daten-Übersicht konnte nicht geladen werden:', e)
  }
}

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

// ── Import / Export ───────────────────────────────────
const importExportInitialTab = ref('import')

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
  loadDataStats()

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
// ═══════════════════════════════════════════════════════
// CSS VARIABLES
// ═══════════════════════════════════════════════════════
.admin-config {
  --bg: #f1f5f9;
  --card-bg: #ffffff;
  --text: #1e293b;
  --muted: #64748b;
  --border: #e2e8f0;
  --primary: #3b82f6;
  --primary-light: #eff6ff;
  --danger: #ef4444;
  --danger-bg: #fef2f2;
  --warning: #f59e0b;
  --warning-bg: #fffbeb;
  --success: #10b981;
  --success-bg: #f0fdf4;
  --radius: 14px;
  --shadow: 0 1px 3px rgba(0,0,0,0.07), 0 4px 12px rgba(0,0,0,0.05);
  --shadow-hover: 0 4px 12px rgba(0,0,0,0.1), 0 8px 24px rgba(0,0,0,0.06);
  --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

  background: var(--app-background-color);
  padding: 0.35rem 1rem 0.75rem;
  border-radius: 8px;
  min-height: 100%;
}

// ═══════════════════════════════════════════════════════
// SECTION NAVIGATION
// ═══════════════════════════════════════════════════════
.section-nav {
  position: sticky;
  top: 0;
  z-index: 100;
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
  padding: 0.4rem 0.9rem;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #475569;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition);
  white-space: nowrap;

  &:hover {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }

  &.active {
    background: var(--app-highlight-color);
    border-color: var(--app-highlight-color);
    color: var(--app-highlight-contrast);
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }

  .tab-icon { font-size: 1rem; }
}

// ═══════════════════════════════════════════════════════
// SECTION CONTENT & TITLE
// ═══════════════════════════════════════════════════════
.section-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.section-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  .title-icon {
    width: 28px; height: 28px;
    background: var(--primary-light);
    color: var(--primary);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.9rem;
  }
}

// ═══════════════════════════════════════════════════════
// GRID SYSTEM
// ═══════════════════════════════════════════════════════
.grid-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

@media (max-width: 900px) {
  .grid-2, .grid-3 { grid-template-columns: 1fr; }
}

// ═══════════════════════════════════════════════════════
// CARDS
// ═══════════════════════════════════════════════════════
.card {
  background: color-mix(in srgb, var(--app-background-color) 55%, white);
  border: 1px solid color-mix(in srgb, var(--app-background-color) 65%, #777);
  border-radius: var(--radius);
  padding: 0.85rem;
  box-shadow: var(--shadow);
  transition: var(--transition);
  display: flex;
  flex-direction: column;
  gap: 0.65rem;

  &:hover {
    box-shadow: var(--shadow-hover);
    transform: translateY(-1px);
  }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border);
}

.card-icon {
  width: 34px; height: 34px;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem;
  flex-shrink: 0;

  &.blue { background: #eff6ff; }
  &.green { background: #f0fdf4; }
  &.orange { background: #fff7ed; }
  &.purple { background: #faf5ff; }
  &.red { background: #fef2f2; }
  &.gray { background: #f8fafc; }
}

.card-title { font-size: 0.95rem; font-weight: 700; color: var(--text); }
.card-subtitle { font-size: 0.8rem; color: var(--muted); margin-top: 0.15rem; }

// ═══════════════════════════════════════════════════════
// FORM ELEMENTS
// ═══════════════════════════════════════════════════════
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.form-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text);
  display: flex;
  align-items: center;
  justify-content: space-between;

  .hint {
    font-weight: 400;
    color: var(--muted);
    font-size: 0.75rem;
  }
}

.form-input, .form-select {
  width: 100%;
  padding: 0.6rem 0.85rem;
  border: 1.5px solid var(--border);
  border-radius: 8px;
  font-size: 0.9rem;
  color: var(--text);
  background: var(--card-bg);
  transition: var(--transition);

  &:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    background: var(--bg);
  }
}

.form-input[type="range"] {
  padding: 0;
  accent-color: var(--primary);
}

// ═══════════════════════════════════════════════════════
// COLOR PRESETS
// ═══════════════════════════════════════════════════════
.color-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.color-preset {
  width: 28px; height: 28px;
  border-radius: 8px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: var(--transition);
  position: relative;
  padding: 0;

  &:hover { transform: scale(1.15); }

  &.selected {
    border-color: var(--text);
    box-shadow: 0 0 0 2px white inset, 0 2px 8px rgba(0,0,0,0.15);
  }
}

.color-custom {
  background: #f8fafc;
  border: 2px dashed #94a3b8;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.8rem;
  overflow: hidden;

  &.selected { border-style: solid; border-color: var(--text); }

  input[type="color"] {
    position: absolute; inset: 0;
    width: 100%; height: 100%;
    opacity: 0; cursor: pointer;
    padding: 0; border: none;
  }
}

.custom-color-preview {
  width: 100%; height: 100%;
  display: block; border-radius: 6px;
  position: absolute; inset: 0;
}

.custom-color-icon { pointer-events: none; }

.color-hex-display {
  font-family: 'SF Mono', monospace;
  font-size: 0.72rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  border: 1px solid var(--border);
  background: var(--bg);
}

// ═══════════════════════════════════════════════════════
// PREVIEW BOX
// ═══════════════════════════════════════════════════════
.preview-box {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--border);
  min-height: 150px;
  display: flex;
  flex-direction: column;
  background: var(--preview-background);
}

.preview-banner {
  background: var(--preview-banner);
  color: var(--preview-banner-contrast);
  border-bottom: 2px solid var(--preview-highlight);
  padding: 0.75rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  justify-content: center;

  img {
    height: 32px;
    object-fit: contain;
  }

  span {
    font-weight: 700;
    font-size: 0.9rem;
  }
}

.preview-body {
  flex: 1;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.preview-highlight {
  background: var(--preview-highlight);
  color: var(--preview-highlight-contrast);
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.8rem;
  text-align: center;
}

.preview-kasse {
  flex: 1;
  background: var(--preview-kasse-area);
  background-image: var(--preview-bg-image);
  background-size: cover;
  background-position: center;
  color: var(--preview-kasse-area-contrast);
  border-radius: 6px;
  padding: 0.75rem;
  font-weight: 600;
  font-size: 0.8rem;
  text-align: center;
  border: 1px dashed rgba(0,0,0,0.1);
  display: flex; align-items: center; justify-content: center;
}

// ═══════════════════════════════════════════════════════
// MEDIA UPLOAD
// ═══════════════════════════════════════════════════════
.upload-zone {
  border: 2px dashed var(--border);
  border-radius: 10px;
  padding: 0.85rem;
  text-align: center;
  cursor: pointer;
  transition: var(--transition);
  background: var(--bg);

  &:hover {
    border-color: var(--primary);
    background: var(--primary-light);
  }

  .upload-icon { font-size: 1.5rem; margin-bottom: 0.25rem; }
  .upload-text { font-size: 0.8rem; color: var(--muted); }
  .upload-hint { font-size: 0.7rem; color: var(--muted); margin-top: 0.2rem; }
}

.image-preview {
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg);
  display: flex; align-items: center; justify-content: center;
  min-height: 70px;

  img { max-width: 100%; max-height: 80px; object-fit: contain; }

  .no-image { color: var(--muted); font-size: 0.8rem; }
}

// ═══════════════════════════════════════════════════════
// TOGGLE SWITCH
// ═══════════════════════════════════════════════════════
.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.toggle-switch {
  position: relative;
  width: 48px; height: 26px;
  background: #cbd5e1;
  border-radius: 13px;
  cursor: pointer;
  transition: var(--transition);
  flex-shrink: 0;

  &::after {
    content: '';
    position: absolute;
    top: 3px; left: 3px;
    width: 20px; height: 20px;
    background: white;
    border-radius: 50%;
    transition: var(--transition);
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  }

  &.active {
    background: var(--success);
    &::after { left: 25px; }
  }
}

.toggle-label-text { font-size: 0.85rem; font-weight: 500; }

// ═══════════════════════════════════════════════════════
// RANGE WITH LABELS
// ═══════════════════════════════════════════════════════
.range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.7rem;
  color: var(--muted);
}

// ═══════════════════════════════════════════════════════
// WARNING / INFO BOXES
// ═══════════════════════════════════════════════════════
.warning-box {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  background: var(--warning-bg);
  border: 1px solid #fde68a;
  border-radius: 10px;
  padding: 0.75rem 1rem;

  &.danger {
    background: var(--danger-bg);
    border-color: #fecaca;
    color: #991b1b;
  }

  &.success {
    background: var(--success-bg);
    border-color: #86efac;
    color: #166534;
  }

  .warning-icon { font-size: 1.2rem; flex-shrink: 0; }
  .warning-text {
    font-size: 0.85rem;
    strong { display: block; margin-bottom: 0.2rem; }
  }
}

.info-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--primary-light);
  border-radius: 8px;
  border: 1px solid #bfdbfe;

  .info-icon { font-size: 1.2rem; }
  .info-text {
    font-size: 0.8rem;
    color: #1e40af;
    strong { display: block; color: #1e3a8a; }
  }
}

.hint-box {
  padding: 0.75rem;
  background: var(--bg);
  border-radius: 8px;
  border: 1px solid var(--border);
  font-size: 0.8rem;
  color: var(--muted);
}

// ═══════════════════════════════════════════════════════
// DIVIDER
// ═══════════════════════════════════════════════════════
.divider {
  border: none;
  border-top: 1px solid var(--border);
  margin: 0.5rem 0;
}

// ═══════════════════════════════════════════════════════
// DATA OVERVIEW
// ═══════════════════════════════════════════════════════
.data-overview {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.overview-item {
  display: flex;
  justify-content: space-between;
  padding: 0.6rem 0.75rem;
  background: var(--bg);
  border-radius: 8px;
  font-size: 0.85rem;

  .overview-value { font-weight: 700; }
}

// ═══════════════════════════════════════════════════════
// LAYOUT CHOOSER
// ═══════════════════════════════════════════════════════
.layout-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

@media (max-width: 500px) {
  .layout-grid { grid-template-columns: repeat(2, 1fr); }
}

.layout-card {
  border: 2px solid var(--border);
  border-radius: 10px;
  padding: 1rem 0.5rem;
  text-align: center;
  cursor: pointer;
  transition: var(--transition);
  position: relative;
  background: var(--card-bg);

  &:hover { border-color: var(--primary); }

  &.selected {
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
  }

  .layout-icon { font-size: 1.8rem; margin-bottom: 0.4rem; }
  .layout-name { font-size: 0.8rem; font-weight: 600; }
  .layout-badge {
    position: absolute;
    top: -6px; right: -6px;
    background: var(--primary);
    color: white;
    font-size: 0.62rem;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 999px;
  }
}

.layout-changed-hint {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--warning-bg);
  border: 1px solid #fde68a;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #92400e;
  flex-wrap: wrap;
}

// ═══════════════════════════════════════════════════════
// TIMER DISPLAY
// ═══════════════════════════════════════════════════════
.timer-display {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--bg);
  border-radius: 8px;
  border: 1px solid var(--border);
  transition: var(--transition);

  &.inactive { opacity: 0.4; }

  .timer-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary);
    font-variant-numeric: tabular-nums;
  }
  .timer-label { font-size: 0.8rem; color: var(--muted); }
}

// ═══════════════════════════════════════════════════════
// ACTION CARDS (Import/Export)
// ═══════════════════════════════════════════════════════
.action-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.75rem;
  padding: 1.5rem;
  border: 2px dashed var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: var(--transition);
  background: var(--card-bg);

  &:hover {
    border-color: var(--primary);
    background: var(--primary-light);
  }

  .action-icon { font-size: 2.5rem; }
  .action-title { font-weight: 700; font-size: 0.95rem; }
  .action-desc { font-size: 0.8rem; color: var(--muted); }
}

// ═══════════════════════════════════════════════════════
// BUTTONS
// ═══════════════════════════════════════════════════════
.btn-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-top: auto;
  padding-top: 0.5rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  border: none;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition);
  white-space: nowrap;
  min-height: 38px;

  &:hover { filter: brightness(1.08); transform: translateY(-1px); }
  &:active { transform: translateY(0); }
  &:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
}

.btn-primary   { background: var(--primary); color: white; }
.btn-success   { background: var(--success); color: white; }
.btn-secondary { background: var(--border); color: var(--text); }
.btn-warning   { background: var(--warning); color: white; }
.btn-danger    { background: var(--danger); color: white; }
.btn-outline   { background: transparent; border: 1.5px solid var(--border); color: var(--text); }
.btn-outline:hover { border-color: var(--primary); color: var(--primary); }
.btn-sm { padding: 0.4rem 0.8rem; font-size: 0.8rem; }

// ═══════════════════════════════════════════════════════
// RESPONSIVE
// ═══════════════════════════════════════════════════════
@media (max-width: 640px) {
  .card { padding: 1rem; }
  .section-nav { padding: 0.5rem; }
  .section-tab { padding: 0.35rem 0.6rem; font-size: 0.8rem; }
}
</style>
