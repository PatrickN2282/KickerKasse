<template>
  <div class="admin-config">
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
          @click="switchSection('design')"
        >
          <span class="tab-icon">🎨</span> Design
        </button>
        <button
          v-if="authStore.isTopAdmin"
          :class="['section-tab', { active: activeSection === 'datamaintenance' }]"
          type="button"
          @click="switchSection('datamaintenance')"
        >
          <span class="tab-icon">🧹</span> Datenpflege
        </button>
        <button
          v-if="authStore.isAdmin"
          :class="['section-tab', { active: activeSection === 'importexport' }]"
          type="button"
          @click="switchSection('importexport')"
        >
          <span class="tab-icon">🔄</span> Import / Export
        </button>
        <button
          v-if="authStore.isAdmin"
          :class="['section-tab', { active: activeSection === 'extsettings' }]"
          type="button"
          @click="switchSection('extsettings')"
        >
          <span class="tab-icon">⚙️</span> Erweitert
        </button>
        <button
          v-if="authStore.isTopAdmin"
          :class="['section-tab', { active: activeSection === 'emailsettings' }]"
          type="button"
          @click="switchSection('emailsettings')"
        >
          <span class="tab-icon">✉️</span> E-Mail
        </button>
        <button
          v-if="authStore.isTopAdmin"
          :class="['section-tab', { active: activeSection === 'auditlog' }]"
          type="button"
          @click="switchSection('auditlog')"
        >
          <span class="tab-icon">🔍</span> Audit-Log
        </button>
      </div>
    </div>
    <div v-if="appSettingsStore.isSaving || hasUnsavedSettings" class="save-state" role="status">
      {{ appSettingsStore.isSaving ? 'Änderungen werden gespeichert …' : 'Ungespeicherte Änderungen in diesem Bereich' }}
    </div>

    <div v-if="activeSection === 'design'" class="section-content">
      <div class="section-title">
        <div class="title-icon">🎨</div>
        Design & Logo
      </div>

      <div class="grid-layout-design">
        <div class="card design-card">
          <div class="card-header">
            <div class="card-icon blue">🎨</div>
            <div>
              <div class="card-title">Farben</div>
              <div class="card-subtitle">Farbpalette der App</div>
            </div>
            <button
              class="btn btn-warning btn-icon btn-sm ms-auto"
              title="Standard wiederherstellen: Setzt alle Farbanpassungen auf die Standardwerte der Anwendung zurück."
              aria-label="Standard wiederherstellen"
              @click="resetDesignColors"
            >
              ↺
            </button>
          </div>

          <div class="form-group mb-compact">
            <label class="form-label">App-Überschrift</label>
            <input v-model.trim="designForm.app_name" type="text" class="form-input" maxlength="120" />
          </div>

          <div class="color-grid">
            <div class="color-input-group">
              <label>Hintergrund</label>
              <div class="color-control">
                <input type="color" v-model="designForm.background_color" />
                <input type="text" v-model="designForm.background_color" class="hex-input" maxlength="7" />
              </div>
            </div>
            <div class="color-input-group">
              <label>Banner</label>
              <div class="color-control">
                <input type="color" v-model="designForm.banner_color" />
                <input type="text" v-model="designForm.banner_color" class="hex-input" maxlength="7" />
              </div>
            </div>
            <div class="color-input-group">
              <label>Highlight</label>
              <div class="color-control">
                <input type="color" v-model="designForm.highlight_color" />
                <input type="text" v-model="designForm.highlight_color" class="hex-input" maxlength="7" />
              </div>
            </div>
            <div class="color-input-group">
              <label>Kassenbereich</label>
              <div class="color-control">
                <input type="color" v-model="designForm.kasse_area_background_color" />
                <input type="text" v-model="designForm.kasse_area_background_color" class="hex-input" maxlength="7" />
              </div>
            </div>
          </div>

          <div class="btn-row mt-auto">
            <button class="btn btn-primary w-100" :disabled="appSettingsStore.isSaving" @click="saveDesignSettings">
              💾 Farben speichern
            </button>
          </div>
        </div>

        <div class="card design-card flex-col gap-sm">
          <div class="card-header">
            <div class="card-icon green">🖼️</div>
            <div>
              <div class="card-title">Medien</div>
              <div class="card-subtitle">Logo & Hintergrund</div>
            </div>
          </div>

          <div class="compact-upload">
            <div class="upload-preview">
              <img v-if="previewLogoUrl" :src="previewLogoUrl" alt="Logo" />
              <span v-else>Logo</span>
            </div>
            <div class="upload-actions">
              <button class="btn btn-outline btn-sm" @click="$refs.logoInput.click()">Durchsuchen...</button>
              <button class="btn btn-success btn-sm" :disabled="!selectedLogo || appSettingsStore.isSaving" @click="uploadLogo">Upload</button>
            </div>
            <input ref="logoInput" type="file" accept="image/*" class="d-none" @change="handleLogoSelection" />
          </div>

          <hr class="divider compact" />

          <div class="compact-upload">
            <div class="upload-preview bg-preview">
              <img v-if="previewKasseBackgroundUrl" :src="previewKasseBackgroundUrl" alt="Background" />
              <span v-else>Hintergrund</span>
            </div>
            <div class="upload-actions">
              <button class="btn btn-outline btn-sm" @click="$refs.bgInput.click()">Durchsuchen...</button>
              <button class="btn btn-success btn-sm" :disabled="!selectedKasseBackground || appSettingsStore.isSaving" @click="uploadKasseBackground">Upload</button>
            </div>
            <input ref="bgInput" type="file" accept="image/*" class="d-none" @change="handleKasseBackgroundSelection" />
          </div>

          <div class="bg-settings-grid mt-compact">
            <div class="toggle-row compact">
              <span class="toggle-label-text">Hintergrund aktiv</span>
              <button type="button" class="toggle-switch" :class="{ active: designForm.kasse_products_background_enabled }" :aria-pressed="designForm.kasse_products_background_enabled" aria-label="Produkthintergrund ein- oder ausschalten" @click="designForm.kasse_products_background_enabled = !designForm.kasse_products_background_enabled" />
            </div>
            <div class="form-group compact">
              <label class="form-label">Deckkraft <span class="hint">{{ designForm.kasse_products_background_opacity }}%</span></label>
              <input v-model.number="designForm.kasse_products_background_opacity" type="range" class="form-input" min="0" max="100" step="5" />
            </div>
            <div class="form-group compact">
              <label class="form-label">Skalierung <span class="hint">{{ designForm.kasse_products_background_scale }}%</span></label>
              <input v-model.number="designForm.kasse_products_background_scale" type="range" class="form-input" min="10" max="300" step="5" />
            </div>
          </div>
          
          <div class="btn-row mt-auto">
             <button class="btn btn-primary w-100" :disabled="appSettingsStore.isSaving" @click="saveDesignSettings">
                💾 Layout aktualisieren
              </button>
          </div>
        </div>

        <div class="card design-card no-padding bg-transparent shadow-none border-none">
          <div class="preview-box" :style="previewStyle">
            <div class="preview-banner">
              <img :src="previewLogoUrl" alt="Logo" class="preview-logo" />
              <span class="preview-title">{{ designForm.app_name }}</span>
            </div>
            <div class="preview-body">
              <div class="preview-products">
                <div class="preview-highlight-bar">Kategorien</div>
                <div class="preview-kasse">
                  <span class="preview-kasse-label">Produktbereich</span>
                </div>
              </div>
              <div class="preview-sidebar">
                <div class="preview-receipt-item" />
                <div class="preview-receipt-item" />
                <div class="preview-receipt-item preview-receipt-item--wide" />
                <div class="preview-total">Total</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="activeSection === 'datamaintenance' && authStore.isTopAdmin" class="section-content">
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
          <div class="warning-box danger compact-box">
            <span class="warning-icon">⚠️</span>
            <div class="warning-text">
              Transaktionen, Benutzer, Mitglieder, Produkte, Gutscheine etc. werden gelöscht.
            </div>
          </div>
          <div class="btn-row mt-auto">
            <button
              class="btn btn-danger w-100"
              :disabled="!authStore.isTopAdmin"
              @click="showResetModal = true"
            >
              🧨 Hard-Reset starten (Nur Top-Admin)
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
            <button class="btn btn-outline btn-icon btn-sm ms-auto" title="Aktualisieren" @click="loadDataStats">🔄</button>
          </div>
          <div class="data-overview-grid">
            <div class="overview-tile">
              <span class="tile-label">Transaktionen</span>
              <span class="tile-value">{{ dataStats.transactions ?? '—' }}</span>
            </div>
            <div class="overview-tile">
              <span class="tile-label">Mitglieder</span>
              <span class="tile-value">{{ dataStats.members ?? '—' }}</span>
            </div>
            <div class="overview-tile">
              <span class="tile-label">Benutzer</span>
              <span class="tile-value">{{ dataStats.users ?? '—' }}</span>
            </div>
            <div class="overview-tile">
              <span class="tile-label">Produkte</span>
              <span class="tile-value">{{ dataStats.products ?? '—' }}</span>
            </div>
            <div class="overview-tile">
              <span class="tile-label">Kategorien</span>
              <span class="tile-value">{{ dataStats.categories ?? '—' }}</span>
            </div>
            <div class="overview-tile">
              <span class="tile-label">Gutscheine</span>
              <span class="tile-value">{{ dataStats.vouchers ?? '—' }}</span>
            </div>
            <div class="overview-tile w-100">
              <span class="tile-label">Audit-Log Einträge</span>
              <span class="tile-value">{{ dataStats.audit_log_entries ?? '—' }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="grid-2 mt-compact">
        <div class="card">
          <div class="card-header">
            <div class="card-icon blue">🗂️</div>
            <div>
              <div class="card-title">Datenbank-Backup</div>
              <div class="card-subtitle">Vollständige Sicherung herunterladen</div>
            </div>
          </div>
          <p class="text-muted mb-compact">
            Sichert Datenbank, Konten, Belege, Produktbilder, Mitgliederfotos und Designmedien gemeinsam als ZIP (Format v2). Währenddessen sind andere Zugriffe kurz gesperrt.
          </p>
          <div class="btn-row mt-auto">
            <button class="btn btn-primary w-100" :disabled="dataMaintenanceBusy" @click="handleBackupDownload">
              ⬇️ Datenbank-Backup herunterladen
            </button>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-icon orange">✉️</div>
            <div>
              <div class="card-title">Backup-Zeitplan</div>
              <div class="card-subtitle">Automatischer Versand per E-Mail</div>
            </div>
          </div>
          <label class="inline-checkbox mb-compact">
            <input
              v-model="backupSchedule.enabled"
              type="checkbox"
              :disabled="!authStore.isTopAdmin || dataMaintenanceBusy"
            >
            <span>Automatischen Backup-Versand aktivieren</span>
          </label>
          <div class="form-group mb-compact">
            <label class="form-label" for="backup-time">Uhrzeit</label>
            <input
              id="backup-time"
              v-model="backupSchedule.time"
              class="form-input"
              type="time"
              :disabled="!authStore.isTopAdmin || dataMaintenanceBusy"
            >
          </div>
          <div class="btn-row">
            <button
              class="btn btn-primary w-100"
              :disabled="!authStore.isTopAdmin || dataMaintenanceBusy"
              @click="saveBackupSchedule"
            >
              💾 Backup-Zeitplan speichern
            </button>
          </div>
        </div>
      </div>

      <div class="card mt-compact">
        <div class="card-header">
          <div class="card-icon gray">♻️</div>
          <div>
            <div class="card-title">Datenbank wiederherstellen</div>
            <div class="card-subtitle">Backup einspielen und aktuelle Daten ersetzen</div>
          </div>
        </div>
        <p class="text-muted mb-compact">
          Ersetzt Datenbank und Medien durch eine vollständige v2-Sicherung mit passendem Schema. Alte v1- und Teilarchive werden abgewiesen. Maximal 256 MiB ZIP / 512 MiB entpackt. Alle Benutzer müssen sich anschließend erneut anmelden.
        </p>
        <div class="form-group mb-compact">
          <label class="form-label" for="restore-file">Backup-ZIP auswählen</label>
          <input id="restore-file" type="file" class="form-input" accept=".zip" @change="handleRestoreFileChange">
        </div>
        <p v-if="restoreFile" class="text-muted mb-compact">Gewählt: {{ restoreFile.name }}</p>
        <div class="btn-row">
          <button
            class="btn btn-warning w-100"
            :disabled="!authStore.isTopAdmin || !restoreFile || dataMaintenanceBusy"
            @click="showRestoreModal = true"
          >
            ♻️ Datenbank wiederherstellen
          </button>
        </div>
      </div>

      <AuthCredentialModal
        :show="showResetModal"
        title="Hard-Reset bestätigen"
        message="Bitte Top-Admin-Passwort eingeben und zusätzlich RESET bestätigen."
        :username="authStore.user?.username || ''"
        confirm-label="Hard-Reset ausführen"
        confirmation-label="Bestätigung"
        confirmation-placeholder="RESET"
        :error="resetModalError"
        @close="showResetModal = false; resetModalError = ''"
        @confirm="handleHardReset"
      />

      <AuthCredentialModal
        :show="showRestoreModal"
        title="Datenbank-Wiederherstellung bestätigen"
        message="Bitte Top-Admin-Passwort eingeben. Die aktuelle Datenbank wird vollständig überschrieben."
        :username="authStore.user?.username || ''"
        confirm-label="Wiederherstellung starten"
        :error="restoreModalError"
        @close="showRestoreModal = false; restoreModalError = ''"
        @confirm="handleRestore"
      />
    </div>

    <div v-if="activeSection === 'importexport' && authStore.isAdmin" class="section-content">
      <div class="section-title">
        <div class="title-icon">🔄</div>
        Import / Export
      </div>

      <div class="warning-box compact-box mb-compact">
        <span class="warning-icon">⚠️</span>
        <div class="warning-text">
          <strong>Hinweis:</strong> Der Import ist für leere Datenbanken gedacht, um Inkonsistenzen zu vermeiden.
        </div>
      </div>

      <div class="grid-2">
        <div class="card action-card" @click="showImportExportModal = true; importExportInitialTab = 'import'">
          <div class="action-icon">📥</div>
          <div class="action-title">Import (CSV / ZIP)</div>
          <div class="action-desc">Produkte, Mitglieder und Kategorien importieren.</div>
        </div>

        <div class="card action-card" @click="showImportExportModal = true; importExportInitialTab = 'export'">
          <div class="action-icon">📤</div>
          <div class="action-title">Export (CSV / ZIP)</div>
          <div class="action-desc">Datenbestände sichern und exportieren.</div>
        </div>
      </div>

      <ImportExportModal
        :show="showImportExportModal"
        :initial-tab="importExportInitialTab"
        @close="showImportExportModal = false"
      />
    </div>

    <div v-if="activeSection === 'auditlog' && authStore.isTopAdmin" class="section-content h-full-flex">
      <div class="section-title">
        <div class="title-icon">🔍</div>
        Audit-Log
      </div>
      <AuditLogPanel class="flex-grow-1" />
    </div>

    <div v-if="activeSection === 'extsettings' && authStore.isAdmin" class="section-content">
      <div class="section-title">
        <div class="title-icon">⚙️</div>
        Erweiterte Einstellungen
      </div>

      <div class="grid-2">
        <div v-if="authStore.isTopAdmin" class="card">
          <div class="card-header">
            <div class="card-icon blue">🏢</div>
            <div>
              <div class="card-title">Geschäftsdaten</div>
              <div class="card-subtitle">Vereinsname und Kontaktdaten</div>
            </div>
          </div>
          
          <div class="grid-2-compact">
            <div class="form-group">
              <label class="form-label">Firmenname</label>
              <input v-model="businessData.name" type="text" class="form-input" placeholder="KickerKasse e.V." />
            </div>
            <div class="form-group">
              <label class="form-label">Straße & Hausnr.</label>
              <input v-model="businessData.street" type="text" class="form-input" placeholder="Musterstraße 1" />
            </div>
            <div class="form-group">
              <label class="form-label">PLZ</label>
              <input v-model="businessData.zip" type="text" class="form-input" placeholder="12345" />
            </div>
            <div class="form-group">
              <label class="form-label">Ort</label>
              <input v-model="businessData.city" type="text" class="form-input" placeholder="Musterstadt" />
            </div>
            <div class="form-group">
              <label class="form-label">Telefon</label>
              <input v-model="businessData.phone" type="tel" class="form-input" placeholder="+49 123 456789" />
            </div>
            <div class="form-group">
              <label class="form-label">E-Mail</label>
              <input v-model="businessData.email" type="email" class="form-input" placeholder="info@beispiel.de" />
            </div>
          </div>
          <div class="btn-row mt-auto">
            <button class="btn btn-primary w-100" @click="saveBusinessData">💾 Speichern</button>
          </div>
        </div>

        <div class="flex-col gap-sm">
          <div v-if="authStore.isTopAdmin" class="card">
            <div class="card-header">
              <div class="card-icon purple">🖥️</div>
              <div>
                <div class="card-title">Layout-Chooser</div>
                <div class="card-subtitle">Kassenansicht</div>
              </div>
            </div>
            <div class="layout-grid-compact">
              <button
                v-for="layout in availableLayouts" :key="layout.key"
                type="button"
                class="layout-card-sm" :class="{ selected: selectedLayout === layout.key }"
                :aria-pressed="selectedLayout === layout.key"
                :aria-label="`${layout.name} als Kassenansicht auswählen`"
                @click="selectedLayout = layout.key"
              >
                <span>{{ layout.icon }} {{ layout.name }}</span>
                <span v-if="selectedLayout === layout.key" class="layout-badge-sm">Aktiv</span>
              </button>
            </div>
            <div v-if="layoutChanged" class="layout-changed-hint compact-box">
              <span>⚠️ Geändert.</span>
              <button class="btn btn-warning btn-sm ms-auto" @click="applyLayout">🔄 Neu laden</button>
            </div>
          </div>

          <div class="card">
            <div class="card-header border-none pb-0">
              <div class="card-icon orange">⚙️</div>
              <div>
                <div class="card-title">Funktionen</div>
                <div class="card-subtitle">Schnelleinstellungen</div>
              </div>
            </div>

            <div class="settings-list">
              <div v-if="authStore.isTopAdmin" class="setting-item">
                <span class="setting-item__icon">⏱️</span>
                <div class="setting-item__info">
                  <span class="setting-item__title">Sitzungszeitlimit</span>
                </div>
                <div class="setting-item__controls">
                  <button type="button" class="toggle-switch small" :class="{ active: sessionTimer.enabled }" :aria-pressed="sessionTimer.enabled" aria-label="Sitzungszeitlimit ein- oder ausschalten" @click="sessionTimer.enabled = !sessionTimer.enabled" />
                  <input v-model.number="sessionTimer.minutes" type="number" class="setting-item__input" min="1" step="1" :disabled="!sessionTimer.enabled" title="Minuten" />
                  <span class="setting-item__unit">min</span>
                  <button class="btn btn-primary btn-sm" :disabled="appSettingsStore.isSaving" @click="saveSessionTimer">Speichern</button>
                </div>
              </div>

              <div class="setting-item">
                <span class="setting-item__icon">🧾</span>
                <div class="setting-item__info">
                  <span class="setting-item__title">Deckel-Funktion</span>
                </div>
                <div class="setting-item__controls">
                  <button type="button" class="toggle-switch small" :class="{ active: deckelEnabled }" :aria-pressed="deckelEnabled" aria-label="Deckelfunktion ein- oder ausschalten" @click="deckelEnabled = !deckelEnabled" />
                  <button class="btn btn-primary btn-sm" :disabled="appSettingsStore.isSaving" @click="saveKasseSettings">Speichern</button>
                </div>
              </div>
              <div class="setting-item">
                <span class="setting-item__icon">📋</span>
                <div class="setting-item__info">
                  <span class="setting-item__title">Gästeliste</span>
                </div>
                <div class="setting-item__controls">
                  <button type="button" class="toggle-switch small" :class="{ active: guestListEnabled }" :aria-pressed="guestListEnabled" aria-label="Gästeliste ein- oder ausschalten" @click="guestListEnabled = !guestListEnabled" />
                  <button class="btn btn-primary btn-sm" :disabled="appSettingsStore.isSaving" @click="saveKasseSettings">Speichern</button>
                </div>
              </div>

              <div v-if="authStore.isTopAdmin" class="setting-item">
                <span class="setting-item__icon">🔐</span>
                <div class="setting-item__info">
                  <span class="setting-item__title">Direktanmeldung "Kasse"</span>
                </div>
                <div class="setting-item__controls">
                  <button type="button" class="toggle-switch small" :class="{ active: kasseDirectLoginEnabled }" :aria-pressed="kasseDirectLoginEnabled" aria-label="Direktanmeldung der Kasse ein- oder ausschalten" @click="kasseDirectLoginEnabled = !kasseDirectLoginEnabled" />
                  <button class="btn btn-primary btn-sm" :disabled="appSettingsStore.isSaving" @click="saveKasseSettings">Speichern</button>
                </div>
              </div>
            </div>
          </div>

          <div v-if="authStore.isAdmin" class="card">
            <div class="card-header">
              <div class="card-icon gray">🧰</div>
              <div>
                <div class="card-title">Hardware-Service</div>
                <div class="card-subtitle">USB-Kassenadapter · systemd-Dienst · Kassen-PC</div>
              </div>
              <button class="btn btn-outline btn-icon btn-sm ms-auto" title="Aktualisieren" @click="refreshHardwareStatus">🔄</button>
            </div>

            <div class="status-grid">
              <div class="status-item">
                <span :class="['status-dot', hardwareStatus.local_agent_reachable ? 'status-dot--green' : 'status-dot--red']"></span>
                <span>Agent: {{ hardwareStatus.local_agent_reachable ? 'erreichbar' : 'nicht erreichbar' }}</span>
              </div>
              <div class="status-item">
                <span :class="['status-dot', hardwareStatus.adapter_connected === true ? 'status-dot--green' : hardwareStatus.adapter_connected === false ? 'status-dot--red' : 'status-dot--gray']"></span>
                <span>Hauptschublade: {{ hardwareStatus.adapter_connected === true ? 'verbunden' : hardwareStatus.adapter_connected === false ? 'nicht verbunden' : 'Status unbekannt' }}</span>
              </div>
              <div class="status-item">
                <span :class="['status-dot', hardwareStatus.small_parts_adapter_connected === true ? 'status-dot--green' : hardwareStatus.small_parts_adapter_connected === false ? 'status-dot--red' : 'status-dot--gray']"></span>
                <span>Kleinteile-Lager: {{ hardwareStatus.small_parts_adapter_connected === true ? 'verbunden' : hardwareStatus.small_parts_adapter_connected === false ? 'nicht verbunden' : 'Status unbekannt / Agent aktualisieren' }}</span>
              </div>
              <div class="status-item" v-if="hardwareStatus.service_detail">
                <span class="status-dot status-dot--gray"></span>
                <span style="font-size:0.8em;color:var(--color-muted)">{{ hardwareStatus.service_detail }}</span>
              </div>
            </div>

            <div v-if="authStore.isTopAdmin" class="btn-row mt-compact">
              <button class="btn btn-outline btn-sm" @click="requestManualDrawerOpen('main')">
                💶 Hauptschublade öffnen
              </button>
              <button class="btn btn-outline btn-sm" @click="requestManualDrawerOpen('small_parts')">
                📦 Kleinteile-Lager öffnen
              </button>
            </div>

            <div v-if="authStore.isTopAdmin" class="local-hardware-config mt-compact">
              <div class="warning-box compact-box">
                <span class="warning-icon">🔧</span>
                <div class="warning-text">
                  Der aktuelle Hardware-Service kann jederzeit neu installiert oder aktualisiert werden.
                  Vorhandene Adapterzuordnungen und der lokale Konfigurationscode bleiben dabei erhalten.
                </div>
              </div>
              <div class="btn-row mt-compact">
                <button class="btn btn-primary btn-sm" @click="showHardwareInstallModal = true">
                  🧭 Dienst installieren / aktualisieren
                </button>
                <button class="btn btn-outline btn-sm" @click="downloadInstallerPackage">
                  ⬇ Aktuelles Installationspaket
                </button>
              </div>
            </div>

            <!-- Agent erreichbar: Status, Zuordnung und Service-Steuerung anzeigen -->
            <template v-if="hardwareStatus.local_agent_reachable">
              <div class="warning-box compact-box mt-compact" style="border-color: var(--color-success)">
                <span class="warning-icon">✅</span>
                <div class="warning-text">Agent läuft auf diesem PC (127.0.0.1:8765).</div>
              </div>
              <div v-if="hardwareStatus.multi_drawer" class="warning-box compact-box mt-compact">
                <span class="warning-icon">ℹ️</span>
                <div class="warning-text">
                  Die Adapter werden direkt auf diesem Kassen-PC erkannt und konfiguriert.
                  Der externe Server hat keinen Zugriff auf die lokalen USB-Geräte.
                </div>
              </div>
              <div
                v-if="authStore.isTopAdmin && hardwareStatus.drawer_configuration && hardwareStatus.configuration_protected"
                class="local-hardware-config mt-compact"
              >
                <div class="form-group">
                  <label class="form-label" for="hardware-config-token">Lokaler Konfigurationscode</label>
                  <input
                    id="hardware-config-token"
                    v-model.trim="hardwareConfig.token"
                    class="form-input"
                    type="password"
                    autocomplete="off"
                    placeholder="Code aus der Agent-Installation"
                  >
                  <span class="form-hint">
                    Der Code wird nur an den Agenten auf 127.0.0.1 gesendet und nicht auf dem Server gespeichert.
                  </span>
                </div>

                <div class="hardware-mapping-grid mt-compact">
                  <div class="form-group">
                    <label class="form-label" for="main-drawer-device">Hauptschublade</label>
                    <select id="main-drawer-device" v-model="hardwareConfig.main_device" class="form-input">
                      <option value="">Adapter auswählen</option>
                      <option v-for="device in hardwareStatus.available_devices" :key="`main-${device}`" :value="device">
                        {{ device }}
                      </option>
                    </select>
                    <button
                      class="btn btn-outline btn-sm"
                      :disabled="hardwareConfigBusy || !hardwareConfig.main_device || !hardwareConfig.token"
                      @click="testHardwareDevice(hardwareConfig.main_device, 'Hauptschublade')"
                    >
                      🔔 Auswahl testen
                    </button>
                  </div>

                  <div class="form-group">
                    <label class="form-label" for="small-parts-drawer-device">Kleinteile-Lager</label>
                    <select id="small-parts-drawer-device" v-model="hardwareConfig.small_parts_device" class="form-input">
                      <option value="">Adapter auswählen</option>
                      <option v-for="device in hardwareStatus.available_devices" :key="`small-${device}`" :value="device">
                        {{ device }}
                      </option>
                    </select>
                    <button
                      class="btn btn-outline btn-sm"
                      :disabled="hardwareConfigBusy || !hardwareConfig.small_parts_device || !hardwareConfig.token"
                      @click="testHardwareDevice(hardwareConfig.small_parts_device, 'Kleinteile-Lager')"
                    >
                      🔔 Auswahl testen
                    </button>
                  </div>
                </div>

                <div class="btn-row mt-compact">
                  <button
                    class="btn btn-primary btn-sm"
                    :disabled="hardwareConfigBusy || !canSaveHardwareMapping"
                    @click="saveHardwareMapping"
                  >
                    💾 Zuordnung auf diesem Client speichern
                  </button>
                </div>
              </div>
              <div
                v-else-if="authStore.isTopAdmin && hardwareStatus.cors_blocked"
                class="local-hardware-config mt-compact"
              >
                <div class="warning-box compact-box">
                  <span class="warning-icon">🔗</span>
                  <div class="warning-text">
                    Der Agent läuft auf diesem Vereins-PC, aber die aktuell verwendete PWA-Adresse
                    <code>{{ currentBrowserOrigin }}</code> ist noch nicht freigegeben.
                  </div>
                </div>
                <div class="form-group mt-compact">
                  <label class="form-label" for="hardware-pair-token">Lokaler Konfigurationscode</label>
                  <input
                    id="hardware-pair-token"
                    v-model.trim="hardwareConfig.token"
                    class="form-input"
                    type="password"
                    autocomplete="off"
                    placeholder="Code aus der Agent-Installation"
                  >
                </div>
                <button
                  class="btn btn-primary btn-sm mt-compact"
                  :disabled="hardwareConfigBusy || !hardwareConfig.token"
                  @click="pairLocalHardwareAgent"
                >
                  🔗 Diesen Browser mit dem lokalen Agenten verbinden
                </button>
              </div>
              <div
                v-else-if="authStore.isTopAdmin && hardwareStatus.multi_drawer"
                class="warning-box compact-box mt-compact"
              >
                <span class="warning-icon">⚠️</span>
                <div class="warning-text">Für die Zuordnung im Adminbereich muss der lokale Hardware-Agent aktualisiert werden.</div>
              </div>
              <div v-if="authStore.isTopAdmin" class="btn-row mt-compact">
                <button class="btn btn-outline btn-sm" @click="executeHardwareServiceAction('restart')">Neustart</button>
                <button class="btn btn-outline btn-sm" @click="executeHardwareServiceAction('stop')">Stoppen</button>
              </div>
            </template>

            <!-- Agent nicht erreichbar: Download + Installationsanleitung -->
            <template v-else>
              <div class="warning-box compact-box mt-compact">
                <span class="warning-icon">⚠️</span>
                <div class="warning-text">
                  Agent nicht erreichbar. Öffne diesen Browser auf dem Kassen-PC
                  oder installiere den Agent dort zuerst.
                </div>
              </div>

              <div v-if="authStore.isTopAdmin" class="local-hardware-config mt-compact">
                <div class="form-group">
                  <label class="form-label" for="hardware-pair-token-offline">
                    Agent bereits installiert? Lokalen Konfigurationscode eingeben
                  </label>
                  <input
                    id="hardware-pair-token-offline"
                    v-model.trim="hardwareConfig.token"
                    class="form-input"
                    type="password"
                    autocomplete="off"
                    placeholder="Code aus der Agent-Installation"
                  >
                  <span class="form-hint">
                    Damit wird ausschließlich {{ currentBrowserOrigin }} auf diesem Vereins-PC freigegeben.
                  </span>
                </div>
                <button
                  class="btn btn-primary btn-sm mt-compact"
                  :disabled="hardwareConfigBusy || !hardwareConfig.token"
                  @click="pairLocalHardwareAgent"
                >
                  🔗 Verbindung zum lokalen Agenten herstellen
                </button>
              </div>
            </template>
          </div>
        </div>

      </div>

      <BusinessDataModal
        :show="showBusinessModal"
        v-model:business-data="businessData"
        @close="showBusinessModal = false"
        @save="saveBusinessData"
      />

      <div
        v-if="showHardwareInstallModal"
        class="setup-modal-overlay"
      >
        <div class="setup-modal-card">
          <div class="setup-modal-header">
            <h3>Hardware-Service installieren oder aktualisieren</h3>
            <button class="btn btn-outline btn-sm" @click="showHardwareInstallModal = false">✕</button>
          </div>
          <p class="setup-modal-text">
            Dein Backend kann den lokalen USB-Adapter am Vereins-PC nicht direkt sehen.
            Deshalb muss der Agent lokal auf genau diesem PC installiert beziehungsweise aktualisiert werden.
          </p>
          <p class="setup-modal-requirement">
            ℹ️ Voraussetzung: <strong>Python 3.9 oder neuer</strong> muss auf dem Vereins-PC installiert sein.
            Der Installationsassistent prüft dies automatisch und installiert fehlende Python-Pakete selbstständig.
          </p>
          <ol class="setup-step-list">
            <li>Aktuelles Installationspaket hier herunterladen und auf dem Vereins-PC entpacken.</li>
            <li>
              Auf dem Vereins-PC ausführen – empfohlen: Doppelklick auf
              <code>Kickerkasse-Install.desktop</code> (grafischer Assistent).<br>
              Alternativ im Terminal: <code>python3 setup_wizard.py</code>
            </li>
            <li>
              Der Assistent ersetzt eine vorhandene Agent-Version, startet den systemd-Dienst neu und
              erhält die bestehende Adapterzuordnung sowie den lokalen Konfigurationscode.
            </li>
            <li>Diese Seite im Browser auf dem Vereins-PC öffnen und mit 🔄 prüfen.</li>
          </ol>
          <div class="setup-download-grid">
            <button class="btn btn-primary btn-sm" @click="downloadInstallerPackage">
              ⬇ Aktuelles Installationspaket herunterladen (ZIP)
            </button>
            <p class="setup-download-hint">
              Enthält alle benötigten Komponenten zur Installation.
            </p>
          </div>
        </div>
      </div>
    </div>

    <div v-if="activeSection === 'emailsettings' && authStore.isTopAdmin" class="section-content">
      <div class="section-title">
        <div class="title-icon">✉️</div>
        E-Mail-Konfiguration
      </div>

      <div class="grid-2 email-settings-grid">
        <div class="card email-card email-card--smtp">
          <div class="card-header">
            <div class="card-icon purple">📡</div>
            <div>
              <div class="card-title">SMTP-Server</div>
              <div class="card-subtitle">Versand aktivieren und Serverzugang konfigurieren</div>
            </div>
          </div>

          <div class="settings-list email-primary-switches">
            <div class="setting-item">
              <span class="setting-item__icon">✉️</span>
              <div class="setting-item__info"><span class="setting-item__title">E-Mail-Versand aktiv</span></div>
              <div class="setting-item__controls">
                <button type="button" class="toggle-switch small" :class="{ active: emailForm.email_enabled }" :aria-pressed="emailForm.email_enabled" aria-label="E-Mail-Versand ein- oder ausschalten" @click="emailForm.email_enabled = !emailForm.email_enabled" />
              </div>
            </div>
            <div class="setting-item">
              <span class="setting-item__icon">⏱️</span>
              <div class="setting-item__info"><span class="setting-item__title">Kassenbericht-Automatik aktiv</span></div>
              <div class="setting-item__controls">
                <button type="button" class="toggle-switch small" :class="{ active: emailForm.scheduled_zbon_enabled }" :aria-pressed="emailForm.scheduled_zbon_enabled" aria-label="Automatischen Kassenbericht ein- oder ausschalten" @click="emailForm.scheduled_zbon_enabled = !emailForm.scheduled_zbon_enabled" />
              </div>
            </div>
          </div>

          <div class="grid-2-compact mt-compact">
            <div class="form-group"><label class="form-label">SMTP-Host</label><input v-model.trim="emailForm.smtp_host" type="text" class="form-input" placeholder="smtp.example.org" /></div>
            <div class="form-group"><label class="form-label">SMTP-Port</label><input v-model.number="emailForm.smtp_port" type="number" min="1" max="65535" class="form-input" /></div>
            <div class="form-group"><label class="form-label">SMTP-Benutzer</label><input v-model.trim="emailForm.smtp_username" type="text" class="form-input" placeholder="optional" /></div>
            <div class="form-group"><label class="form-label">SMTP-Passwort</label><input v-model="emailForm.smtp_password" type="password" class="form-input" placeholder="optional" /></div>
            <div class="form-group"><label class="form-label">Absender</label><input v-model.trim="emailForm.email_sender" type="email" class="form-input" placeholder="noreply@verein.de" /></div>
          </div>

          <div class="settings-list mt-compact">
            <div class="setting-item">
              <span class="setting-item__icon">🔒</span>
              <div class="setting-item__info"><span class="setting-item__title">TLS verwenden</span></div>
              <div class="setting-item__controls"><button type="button" class="toggle-switch small" :class="{ active: emailForm.smtp_use_tls }" :aria-pressed="emailForm.smtp_use_tls" aria-label="TLS für SMTP ein- oder ausschalten" @click="emailForm.smtp_use_tls = !emailForm.smtp_use_tls" /></div>
            </div>
          </div>

          <div class="warning-box compact-box mt-compact"><span class="warning-icon">ℹ️</span><div class="warning-text">Diese Werte werden direkt in der Anwendung gespeichert und ersetzen die bisherige <code>.env</code>-Konfiguration.</div></div>
          <div class="btn-row mt-auto">
            <button class="btn btn-outline" :disabled="appSettingsStore.isSaving || isTestingEmailConnection" @click="testEmailConnection">{{ isTestingEmailConnection ? 'Teste Verbindung...' : '🧪 Verbindung testen' }}</button>
            <button class="btn btn-outline" :disabled="appSettingsStore.isSaving || isSendingTestEmail" @click="sendTestEmail">{{ isSendingTestEmail ? 'Sende Testmail...' : '📨 Testmail senden' }}</button>
            <button class="btn btn-primary" :disabled="appSettingsStore.isSaving" @click="saveEmailSettings">💾 E-Mail-Einstellungen speichern</button>
          </div>
        </div>

        <div class="card email-card">
          <div class="card-header"><div class="card-icon blue">📬</div><div><div class="card-title">Kassenbericht</div><div class="card-subtitle">Empfänger und Versandzeitpunkt</div></div></div>
          <div class="settings-list">
            <div class="setting-item">
              <span class="setting-item__icon">📤</span><div class="setting-item__info"><span class="setting-item__title">Beim Erstellen automatisch senden</span></div>
              <div class="setting-item__controls"><button type="button" class="toggle-switch small" :class="{ active: emailForm.send_zbon_on_create_enabled }" :aria-pressed="emailForm.send_zbon_on_create_enabled" aria-label="Kassenbericht nach Abschluss ein- oder ausschalten" @click="emailForm.send_zbon_on_create_enabled = !emailForm.send_zbon_on_create_enabled" /></div>
            </div>
          </div>
          <div class="grid-2-compact mt-compact">
            <div class="form-group"><label class="form-label">Empfänger</label><input v-model.trim="emailForm.email_recipient_zbon" type="email" class="form-input" placeholder="kassenbericht@verein.de" /></div>
            <div class="form-group"><label class="form-label">Automatischer Versand für Vortag</label><input v-model="emailForm.scheduled_zbon_time" type="time" class="form-input" /><small class="form-hint">Versendet den vollständigen Bericht des vorherigen Kalendertags.</small></div>
            <div class="form-group"><label class="form-label">Betreff-Info (optional)</label><input v-model.trim="emailForm.email_subject_zbon_info" type="text" class="form-input" maxlength="120" placeholder="z. B. Kasse 1" /><small class="form-hint">{{ emailSubjectPreview('Kassenbericht', emailForm.email_subject_zbon_info) }}</small></div>
          </div>
          <div class="warning-box compact-box mt-compact"><span class="warning-icon">{{ deliveryStatusIcon(appSettingsStore.settings.zbon_last_run_status) }}</span><div class="warning-text"><strong>Letzter automatischer Versand</strong><br>{{ formatDeliveryRun(appSettingsStore.settings.zbon_last_run_at, appSettingsStore.settings.zbon_last_run_status) }}<span v-if="appSettingsStore.settings.zbon_last_business_date"> · Berichtstag {{ appSettingsStore.settings.zbon_last_business_date }}</span><br>{{ appSettingsStore.settings.zbon_last_run_message || 'Noch kein Versandlauf protokolliert.' }}</div></div>
        </div>

        <div class="card email-card">
          <div class="card-header"><div class="card-icon blue">📉</div><div><div class="card-title">Warenbestand</div><div class="card-subtitle">Automatische Warnung bei kritischem Bestand</div></div></div>
          <div class="settings-list">
            <div class="setting-item">
              <span class="setting-item__icon">📉</span><div class="setting-item__info"><span class="setting-item__title">Lagerwarnungen aktiv</span></div>
              <div class="setting-item__controls"><button type="button" class="toggle-switch small" :class="{ active: emailForm.email_critical_stock_enabled }" :aria-pressed="emailForm.email_critical_stock_enabled" aria-label="Lagerwarnungen ein- oder ausschalten" @click="emailForm.email_critical_stock_enabled = !emailForm.email_critical_stock_enabled" /></div>
            </div>
          </div>
          <div class="grid-2-compact mt-compact">
            <div class="form-group"><label class="form-label">Empfänger (optional)</label><input v-model.trim="emailForm.email_recipient_stock" type="email" class="form-input" placeholder="lager@verein.de" /><small class="form-hint">Leer = Empfänger des Kassenberichts</small></div>
            <div class="form-group"><label class="form-label">Tägliche Prüfzeit</label><input v-model="emailForm.scheduled_stock_warning_time" type="time" class="form-input" /><small class="form-hint">Ohne kritischen Bestand wird keine Mail versendet.</small></div>
            <div class="form-group"><label class="form-label">Betreff-Info (optional)</label><input v-model.trim="emailForm.email_subject_stock_info" type="text" class="form-input" maxlength="120" placeholder="z. B. Kühlschrank" /><small class="form-hint">{{ emailSubjectPreview('Lagerwarnung', emailForm.email_subject_stock_info) }}</small></div>
          </div>
          <div v-if="emailForm.email_critical_stock_enabled && !emailForm.email_enabled" class="warning-box compact-box mt-compact"><span class="warning-icon">⚠️</span><div class="warning-text">Lagerwarnungen benötigen den aktivierten E-Mail-Versand.</div></div>
          <div v-if="emailForm.email_critical_stock_enabled && !emailForm.email_recipient_stock && !emailForm.email_recipient_zbon" class="warning-box compact-box mt-compact"><span class="warning-icon">⚠️</span><div class="warning-text">Für Lagerwarnungen fehlt ein Lager- oder Kassenbericht-Empfänger.</div></div>
          <div class="warning-box compact-box mt-compact"><span class="warning-icon">{{ deliveryStatusIcon(appSettingsStore.settings.stock_last_run_status) }}</span><div class="warning-text"><strong>Letzte automatische Lagerprüfung</strong><br>{{ formatDeliveryRun(appSettingsStore.settings.stock_last_run_at, appSettingsStore.settings.stock_last_run_status) }}<br>{{ appSettingsStore.settings.stock_last_run_message || 'Noch kein Prüflauf protokolliert.' }}</div></div>
        </div>

        <div class="card email-card">
          <div class="card-header"><div class="card-icon purple">🗄️</div><div><div class="card-title">Datenbanksicherung</div><div class="card-subtitle">Empfänger für automatische Sicherungen</div></div></div>
          <div class="grid-2-compact">
            <div class="form-group"><label class="form-label">Empfänger (optional)</label><input v-model.trim="emailForm.email_recipient_backup" type="email" class="form-input" placeholder="backup@verein.de" /><small class="form-hint">Leer = Empfänger des Kassenberichts. Zeitplan und Aktivierung werden unter Datenpflege verwaltet.</small></div>
            <div class="form-group"><label class="form-label">Betreff-Info (optional)</label><input v-model.trim="emailForm.email_subject_backup_info" type="text" class="form-input" maxlength="120" placeholder="z. B. Vollsicherung" /><small class="form-hint">{{ emailSubjectPreview('DB-Backup', emailForm.email_subject_backup_info) }}</small></div>
          </div>
        </div>
      </div>
    </div>

    <AuthCredentialModal
      :show="!!manualDrawerTarget"
      :title="manualDrawerTarget === 'small_parts' ? 'Kleinteile-Lager öffnen' : 'Hauptschublade öffnen'"
      message="Bitte Top-Admin-Passwort bestätigen."
      :username="authStore.user?.username || ''"
      confirm-label="Jetzt öffnen"
      :error="manualDrawerError"
      @close="manualDrawerTarget = null; manualDrawerError = ''"
      @confirm="confirmManualDrawerOpen"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import AuditLogPanel from '@/components/admin/AuditLogPanel.vue'
import ImportExportModal from '@/components/ImportExportModal.vue'
import { getErrorDetailMessage } from '@/services/errorMessage'
const getErrorMessage = getErrorDetailMessage
import { useAppSettingsStore } from '@/stores/appSettings'
import { useNotificationStore } from '@/stores/notification'
import { useAuthStore } from '@/stores/auth'
import { getContrastColor } from '@/services/utils'
import { LOCAL_HARDWARE_AGENT_BASE_URL, SESSION_RELOAD_FLAG_KEY } from '@/constants'
import apiService from '@/services/api'
import { failedDrawerTargets, openDrawerTargets } from '@/services/drawer'
import AuthCredentialModal from '@/components/AuthCredentialModal.vue'
import BusinessDataModal from '@/views/admin/modal/BusinessDataModal.vue'
import { useRoute, useRouter } from 'vue-router'

const appSettingsStore = useAppSettingsStore()
const notificationStore = useNotificationStore()
const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()
const manualDrawerTarget = ref(null)
const manualDrawerError = ref('')
const fetchLocalAgent = async (path, options = {}, timeoutMs = 1500) => {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    return await fetch(`${LOCAL_HARDWARE_AGENT_BASE_URL}${path}`, {
      ...options,
      signal: controller.signal,
    })
  } finally {
    window.clearTimeout(timeoutId)
  }
}

const activeSection = ref('design')

const sectionPriority = ['design', 'datamaintenance', 'importexport', 'extsettings', 'emailsettings', 'auditlog']

const canAccessSection = (section) => {
  if (section === 'importexport' || section === 'extsettings') {
    return authStore.isAdmin
  }
  if (section === 'emailsettings' || section === 'auditlog') {
    return authStore.isTopAdmin
  }
  if (section === 'datamaintenance') {
    return authStore.isTopAdmin
  }
  return section === 'design'
}

const getDefaultSection = () => {
  const allowed = sectionPriority.find(canAccessSection)
  return allowed || 'design'
}

const normalizeSection = (rawSection) => {
  const section = typeof rawSection === 'string' ? rawSection : ''
  if (!sectionPriority.includes(section)) {
    return getDefaultSection()
  }
  if (!canAccessSection(section)) {
    return getDefaultSection()
  }
  return section
}

const syncRouteSection = async (section) => {
  const querySection = typeof route.query.section === 'string' ? route.query.section : null
  if (querySection === section) {
    return
  }

  const nextQuery = {
    ...route.query,
    section,
  }

  await router.replace({
    path: route.path,
    query: nextQuery,
  })
}

const switchSection = async (targetSection) => {
  const normalized = normalizeSection(targetSection)
  if (activeSection.value !== normalized && hasUnsavedSettings.value) {
    if (!window.confirm('Ungespeicherte Änderungen verwerfen und den Bereich wechseln?')) return
    discardActiveChanges()
  }
  if (activeSection.value !== normalized) {
    activeSection.value = normalized
  }
  await syncRouteSection(normalized)
}

watch(
  () => [route.path, route.query.section],
  () => {
    const normalized = normalizeSection(route.query.section)
    if (activeSection.value !== normalized) {
      activeSection.value = normalized
    }
  },
  { immediate: true }
)

watch(
  () => authStore.role,
  () => {
    const normalized = normalizeSection(activeSection.value)
    if (normalized !== activeSection.value) {
      switchSection(normalized)
    }
  }
)

// ── Design Colors ─────────────────────────────────────
// Reduziert auf interne Logik, UI nutzt jetzt native Color-Picker für Platzersparnis
//
// Einzige Quelle der Wahrheit für die Anwendungs-Standardfarben. Sowohl der initiale
// Ladewert (falls noch keine Einstellungen vom Server vorliegen) als auch der
// "Standard wiederherstellen"-Button verwenden dieselben Werte, damit beide nicht
// mehr auseinanderlaufen können.
const DESIGN_COLOR_DEFAULTS = {
  background_color: '#D7DCE2',
  banner_color: '#131820',
  highlight_color: '#209529',
  kasse_area_background_color: '#FFFFFF',
}

const designForm = reactive({
  app_name: 'KickerKasse',
  background_color: DESIGN_COLOR_DEFAULTS.background_color,
  banner_color: DESIGN_COLOR_DEFAULTS.banner_color,
  highlight_color: DESIGN_COLOR_DEFAULTS.highlight_color,
  kasse_area_background_color: DESIGN_COLOR_DEFAULTS.kasse_area_background_color,
  kasse_products_background_scale: 100,
  kasse_products_background_opacity: 100,
  kasse_products_background_enabled: true,
})

const selectedLogo = ref(null)
const selectedLogoPreview = ref('')
const selectedKasseBackground = ref(null)
const selectedKasseBackgroundPreview = ref('')
const deckelEnabled = ref(true)
const guestListEnabled = ref(true)
const kasseDirectLoginEnabled = ref(true)

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
  designForm.app_name = appSettingsStore.settings.app_name || 'KickerKasse'
  designForm.background_color = appSettingsStore.settings.background_color || DESIGN_COLOR_DEFAULTS.background_color
  designForm.banner_color = appSettingsStore.settings.banner_color || DESIGN_COLOR_DEFAULTS.banner_color
  designForm.highlight_color = appSettingsStore.settings.highlight_color || DESIGN_COLOR_DEFAULTS.highlight_color
  designForm.kasse_area_background_color = appSettingsStore.settings.kasse_area_background_color || DESIGN_COLOR_DEFAULTS.kasse_area_background_color
  designForm.kasse_products_background_scale = appSettingsStore.settings.kasse_products_background_scale || 100
  designForm.kasse_products_background_opacity = appSettingsStore.settings.kasse_products_background_opacity ?? 100
  designForm.kasse_products_background_enabled = appSettingsStore.settings.kasse_products_background_enabled !== false
  deckelEnabled.value = appSettingsStore.settings.deckel_enabled !== false
  guestListEnabled.value = appSettingsStore.settings.guest_list_enabled !== false
  kasseDirectLoginEnabled.value = appSettingsStore.settings.kasse_direct_login_enabled !== false
  savedSnapshots.design = serverDesignSnapshot()
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
    savedSnapshots.design = serverDesignSnapshot()
    notificationStore.success('Einstellungen gespeichert')
  } catch (error) {
    notificationStore.error(getErrorMessage(error, 'Fehler beim Speichern der Einstellungen'))
  }
}

const saveKasseSettings = async () => {
  try {
    const payload = {
      deckel_enabled: deckelEnabled.value,
      guest_list_enabled: guestListEnabled.value,
    }
    if (authStore.isTopAdmin) {
      payload.kasse_direct_login_enabled = kasseDirectLoginEnabled.value
    }
    await appSettingsStore.saveAdminSettings(payload)
    deckelEnabled.value = appSettingsStore.settings.deckel_enabled !== false
    guestListEnabled.value = appSettingsStore.settings.guest_list_enabled !== false
    kasseDirectLoginEnabled.value = appSettingsStore.settings.kasse_direct_login_enabled !== false
    savedSnapshots.design = serverDesignSnapshot()
    notificationStore.success('Kassenfunktionen gespeichert')
  } catch (error) {
    notificationStore.error(getErrorMessage(error, 'Fehler beim Speichern der Kassenfunktionen'))
  }
}

const uploadLogo = async () => {
  if (!selectedLogo.value) return
  try {
    await appSettingsStore.uploadLogo(selectedLogo.value)
    selectedLogo.value = null
    selectedLogoPreview.value = ''
    await appSettingsStore.loadAdminSettings()
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
    notificationStore.success('Hintergrund erfolgreich aktualisiert')
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Fehler beim Hochladen')
  }
}

// ── Datenpflege ───────────────────────────────────────
const showResetModal = ref(false)
const showRestoreModal = ref(false)
const resetModalError = ref('')
const restoreModalError = ref('')
const showImportExportModal = ref(false)
const dataStats = ref({})
const dataMaintenanceBusy = ref(false)
const restoreFile = ref(null)
const backupSchedule = reactive({
  enabled: false,
  time: '03:00',
})

const createNoCacheConfig = () => ({
  params: { _t: Date.now() },
  headers: {
    'Cache-Control': 'no-cache',
    Pragma: 'no-cache',
  },
})

const extractFilename = (headerValue, fallbackName) => {
  const header = headerValue || ''
  const filenameStarMatch = /filename\*\s*=\s*(?:UTF-8''|)([^;]+)/i.exec(header)
  if (filenameStarMatch?.[1]) {
    const encoded = filenameStarMatch[1].trim().replace(/^"|"$/g, '')
    try {
      return decodeURIComponent(encoded)
    } catch {
      return encoded
    }
  }

  const quotedMatch = /filename\s*=\s*"((?:[^"\\]|\\.)*)"/i.exec(header)
  if (quotedMatch?.[1]) {
    return quotedMatch[1].replace(/\\"/g, '"')
  }

  const unquotedMatch = /filename\s*=\s*([^;]+)/i.exec(header)
  if (unquotedMatch?.[1]) {
    return unquotedMatch[1].trim().replace(/^"|"$/g, '')
  }

  return fallbackName
}

const triggerDownload = (blob, fileName) => {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

const loadDataStats = async () => {
  try {
    const response = await apiService.get('/admin/data-maintenance/stats', createNoCacheConfig())
    dataStats.value = response.data
  } catch (e) {
    console.error('Daten-Übersicht konnte nicht geladen werden:', e)
  }
}

const loadBackupSchedule = async () => {
  try {
    const response = await apiService.get('/app-settings', createNoCacheConfig())
    backupSchedule.enabled = !!response.data.scheduled_database_backup_enabled
    backupSchedule.time = response.data.scheduled_database_backup_time || '03:00'
  } catch (error) {
    notificationStore.error(getErrorMessage(error, 'Backup-Einstellungen konnten nicht geladen werden'))
  }
}

const handleBackupDownload = async () => {
  dataMaintenanceBusy.value = true
  try {
    const response = await apiService.post('/admin/data-maintenance/database-backup/export', {}, {
      responseType: 'blob',
    })
    const fileName = extractFilename(response.headers['content-disposition'], 'kickerkasse-db-backup.zip')
    triggerDownload(response.data, fileName)
    notificationStore.success('Vollständige Sicherung mit Medien wurde heruntergeladen')
  } catch (error) {
    notificationStore.error(getErrorMessage(error, 'Datenbank-Backup fehlgeschlagen'))
  } finally {
    dataMaintenanceBusy.value = false
  }
}

const handleRestoreFileChange = (event) => {
  const [file] = event.target.files || []
  restoreFile.value = file || null
  event.target.value = ''
}

const handleRestore = async ({ password }) => {
  restoreModalError.value = ''
  if (!restoreFile.value) {
    showRestoreModal.value = false
    notificationStore.error('Bitte zuerst eine Backup-ZIP auswählen')
    return
  }

  dataMaintenanceBusy.value = true
  try {
    const formData = new FormData()
    formData.append('auth_password', password)
    formData.append('backup_file', restoreFile.value)
    await apiService.post('/admin/data-maintenance/database-backup/restore', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    showRestoreModal.value = false
    notificationStore.success('Datenbank und Medien wurden wiederhergestellt. Bitte erneut anmelden.')
    restoreFile.value = null
    await authStore.logout()
    window.location.href = '/login'
  } catch (error) {
    // Anforderung 10: Fehler direkt im Passwortdialog anzeigen statt nur als Toast.
    restoreModalError.value = getErrorMessage(error, 'Wiederherstellung fehlgeschlagen')
  } finally {
    dataMaintenanceBusy.value = false
  }
}

const saveBackupSchedule = async () => {
  dataMaintenanceBusy.value = true
  try {
    await apiService.put('/app-settings', {
      scheduled_database_backup_enabled: backupSchedule.enabled,
      scheduled_database_backup_time: backupSchedule.time || '03:00',
    })
    notificationStore.success('Backup-Zeitplan gespeichert')
  } catch (error) {
    notificationStore.error(getErrorMessage(error, 'Backup-Zeitplan konnte nicht gespeichert werden'))
  } finally {
    dataMaintenanceBusy.value = false
  }
}

const handleHardReset = async ({ password, confirmationText }) => {
  resetModalError.value = ''
  try {
    await apiService.post('/admin/data-maintenance/hard-reset', {
      auth_password: password,
      confirmation_text: confirmationText,
    })
    showResetModal.value = false
    notificationStore.success('Hard-Reset erfolgreich durchgeführt')
    await authStore.logout()
    window.location.href = '/login'
  } catch (error) {
    // Anforderung 10: Fehler direkt im Passwortdialog anzeigen statt nur als Toast.
    resetModalError.value = getErrorMessage(error, 'Hard-Reset fehlgeschlagen')
  }
}

// ── Import / Export ───────────────────────────────────
const importExportInitialTab = ref('import')

// ── Erweiterte Einstellungen ──────────────────────────
const LAYOUT_STORAGE_KEY = 'kasseLayout'
const showBusinessModal = ref(false)
const showHardwareInstallModal = ref(false)
const sessionTimer = ref({ enabled: false, minutes: 15 })

const businessData = ref({
  name: '', street: '', zip: '', city: '',
  phone: '', email: '', taxNumber: '', registrationNumber: '',
})
const emailForm = reactive({
  email_enabled: false,
  email_sender: 'noreply@kassensystem.local',
  email_recipient_zbon: '',
  email_recipient_stock: '',
  email_recipient_backup: '',
  email_subject_zbon_info: '',
  email_subject_stock_info: '',
  email_subject_backup_info: '',
  email_critical_stock_enabled: false,
  smtp_host: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  smtp_use_tls: true,
  send_zbon_on_create_enabled: false,
  scheduled_zbon_enabled: false,
  scheduled_zbon_time: '23:59',
  scheduled_stock_warning_time: '09:00',
})
const savedSnapshots = reactive({ design: '', emailsettings: '' })
const designSnapshot = () => JSON.stringify({
  ...designForm,
  deckel_enabled: deckelEnabled.value,
  guest_list_enabled: guestListEnabled.value,
  kasse_direct_login_enabled: kasseDirectLoginEnabled.value,
  session_timer: sessionTimer.value,
})
const emailSnapshot = () => JSON.stringify(emailForm)
const serverDesignSnapshot = () => JSON.stringify({
  app_name: appSettingsStore.settings.app_name || 'KickerKasse',
  background_color: appSettingsStore.settings.background_color || DESIGN_COLOR_DEFAULTS.background_color,
  banner_color: appSettingsStore.settings.banner_color || DESIGN_COLOR_DEFAULTS.banner_color,
  highlight_color: appSettingsStore.settings.highlight_color || DESIGN_COLOR_DEFAULTS.highlight_color,
  kasse_area_background_color: appSettingsStore.settings.kasse_area_background_color || DESIGN_COLOR_DEFAULTS.kasse_area_background_color,
  kasse_products_background_scale: appSettingsStore.settings.kasse_products_background_scale || 100,
  kasse_products_background_opacity: appSettingsStore.settings.kasse_products_background_opacity ?? 100,
  kasse_products_background_enabled: appSettingsStore.settings.kasse_products_background_enabled !== false,
  deckel_enabled: appSettingsStore.settings.deckel_enabled !== false,
  guest_list_enabled: appSettingsStore.settings.guest_list_enabled !== false,
  kasse_direct_login_enabled: appSettingsStore.settings.kasse_direct_login_enabled !== false,
  session_timer: {
    enabled: !!appSettingsStore.settings.session_timer_enabled,
    minutes: Number(appSettingsStore.settings.session_timer_minutes) || 15,
  },
})
const hasUnsavedSettings = computed(() => {
  if (activeSection.value === 'design') {
    return Boolean(savedSnapshots.design) && (
      savedSnapshots.design !== designSnapshot()
      || Boolean(selectedLogo.value)
      || Boolean(selectedKasseBackground.value)
    )
  }
  if (activeSection.value === 'emailsettings') {
    return Boolean(savedSnapshots.emailsettings) && savedSnapshots.emailsettings !== emailSnapshot()
  }
  return false
})
const discardActiveChanges = () => {
  if (activeSection.value === 'design') {
    syncDesignForm()
    syncSessionTimer()
    selectedLogo.value = null
    selectedLogoPreview.value = ''
    selectedKasseBackground.value = null
    selectedKasseBackgroundPreview.value = ''
  } else if (activeSection.value === 'emailsettings') {
    syncEmailForm()
  }
}
const isTestingEmailConnection = ref(false)
const isSendingTestEmail = ref(false)
const hardwareStatus = reactive({
  service_active: false,
  adapter_connected: null,
  small_parts_adapter_connected: null,
  small_parts_device: '',
  multi_drawer: false,
  drawer_configuration: false,
  configuration_protected: false,
  available_devices: [],
  service_detail: '',
  manual_install_command: '',
  local_agent_reachable: false,
  cors_blocked: false,
  installing: false,
  install_log: '',
})
const hardwareConfig = reactive({
  token: '',
  main_device: '',
  small_parts_device: '',
})
const hardwareConfigBusy = ref(false)
const currentBrowserOrigin = window.location.origin
const canSaveHardwareMapping = computed(() => (
  !!hardwareConfig.token
  && !!hardwareConfig.main_device
  && !!hardwareConfig.small_parts_device
  && hardwareConfig.main_device !== hardwareConfig.small_parts_device
))

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
  savedSnapshots.design = serverDesignSnapshot()
}

const syncBusinessData = () => {
  businessData.value = {
    name: appSettingsStore.settings.business_name || '',
    street: appSettingsStore.settings.business_street || '',
    zip: appSettingsStore.settings.business_zip || '',
    city: appSettingsStore.settings.business_city || '',
    phone: appSettingsStore.settings.business_phone || '',
    email: appSettingsStore.settings.business_email || '',
    taxNumber: appSettingsStore.settings.business_tax_number || '',
    registrationNumber: appSettingsStore.settings.business_registration_number || '',
  }
}

const syncEmailForm = () => {
  emailForm.email_enabled = !!appSettingsStore.settings.email_enabled
  emailForm.email_sender = appSettingsStore.settings.email_sender || 'noreply@kassensystem.local'
  emailForm.email_recipient_zbon = appSettingsStore.settings.email_recipient_zbon || ''
  emailForm.email_recipient_stock = appSettingsStore.settings.email_recipient_stock || ''
  emailForm.email_recipient_backup = appSettingsStore.settings.email_recipient_backup || ''
  emailForm.email_subject_zbon_info = appSettingsStore.settings.email_subject_zbon_info || ''
  emailForm.email_subject_stock_info = appSettingsStore.settings.email_subject_stock_info || ''
  emailForm.email_subject_backup_info = appSettingsStore.settings.email_subject_backup_info || ''
  emailForm.email_critical_stock_enabled = !!appSettingsStore.settings.email_critical_stock_enabled
  emailForm.smtp_host = appSettingsStore.settings.smtp_host || ''
  emailForm.smtp_port = Number(appSettingsStore.settings.smtp_port) || 587
  emailForm.smtp_username = appSettingsStore.settings.smtp_username || ''
  emailForm.smtp_password = appSettingsStore.settings.smtp_password || ''
  emailForm.smtp_use_tls = appSettingsStore.settings.smtp_use_tls !== false
  emailForm.send_zbon_on_create_enabled = !!appSettingsStore.settings.send_zbon_on_create_enabled
  emailForm.scheduled_zbon_enabled = !!appSettingsStore.settings.scheduled_zbon_enabled
  emailForm.scheduled_zbon_time = appSettingsStore.settings.scheduled_zbon_time || '23:59'
  emailForm.scheduled_stock_warning_time = appSettingsStore.settings.scheduled_stock_warning_time || '09:00'
  savedSnapshots.emailsettings = emailSnapshot()
}

const deliveryStatusIcon = (status) => ({ SUCCESS: '✅', FAILED: '❌', SKIPPED: 'ℹ️' }[status] || '➖')

const emailSubjectPreview = (functionLabel, info) => {
  const timestamp = new Intl.DateTimeFormat('de-DE', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(new Date()).replace(',', '')
  const suffix = info?.trim() ? ` - ${info.trim()}` : ''
  return `Vorschau: ${appSettingsStore.settings.app_name} - ${functionLabel} ${timestamp}h${suffix}`
}

const formatDeliveryRun = (timestamp, status) => {
  if (!timestamp) return 'Noch kein Lauf'
  const date = new Date(timestamp)
  const label = { SUCCESS: 'Erfolgreich', FAILED: 'Fehlgeschlagen', SKIPPED: 'Keine Mail erforderlich' }[status] || 'Status unbekannt'
  return `${label} · ${date.toLocaleString('de-DE')}`
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
    notificationStore.success('Sitzungszeitlimit gespeichert')
  } catch (error) {
    notificationStore.error(getErrorMessage(error, 'Sitzungszeitlimit konnte nicht gespeichert werden'))
  }
}

const saveBusinessData = async () => {
  try {
    await appSettingsStore.saveAdminSettings({
      business_name: businessData.value.name || null,
      business_street: businessData.value.street || null,
      business_zip: businessData.value.zip || null,
      business_city: businessData.value.city || null,
      business_phone: businessData.value.phone || null,
      business_email: businessData.value.email || null,
      business_tax_number: businessData.value.taxNumber || null,
      business_registration_number: businessData.value.registrationNumber || null,
    })
    syncBusinessData()
    notificationStore.success('Geschäftsdaten gespeichert.')
    showBusinessModal.value = false
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Geschäftsdaten konnten nicht gespeichert werden')
  }
}

const saveEmailSettings = async () => {
  try {
    await appSettingsStore.saveAdminSettings({
      email_enabled: emailForm.email_enabled,
      email_sender: emailForm.email_sender || null,
      email_recipient_zbon: emailForm.email_recipient_zbon || null,
      email_recipient_stock: emailForm.email_recipient_stock || null,
      email_recipient_backup: emailForm.email_recipient_backup || null,
      email_subject_zbon_info: emailForm.email_subject_zbon_info || null,
      email_subject_stock_info: emailForm.email_subject_stock_info || null,
      email_subject_backup_info: emailForm.email_subject_backup_info || null,
      email_critical_stock_enabled: emailForm.email_critical_stock_enabled,
      smtp_host: emailForm.smtp_host || null,
      smtp_port: Number(emailForm.smtp_port) || 587,
      smtp_username: emailForm.smtp_username || null,
      smtp_password: emailForm.smtp_password || null,
      smtp_use_tls: emailForm.smtp_use_tls,
      send_zbon_on_create_enabled: emailForm.send_zbon_on_create_enabled,
      scheduled_zbon_enabled: emailForm.scheduled_zbon_enabled,
      scheduled_zbon_time: emailForm.scheduled_zbon_time,
      scheduled_zbon_report_type: 'full-zbon',
      scheduled_stock_warning_time: emailForm.scheduled_stock_warning_time,
    })
    syncEmailForm()
    notificationStore.success('E-Mail-Einstellungen gespeichert')
  } catch (error) {
    notificationStore.error(getErrorMessage(error, 'E-Mail-Einstellungen konnten nicht gespeichert werden'))
  }
}

const refreshHardwareStatus = async () => {
  hardwareStatus.local_agent_reachable = false
  hardwareStatus.cors_blocked = false
  hardwareStatus.small_parts_adapter_connected = null
  hardwareStatus.small_parts_device = ''
  hardwareStatus.multi_drawer = false
  hardwareStatus.drawer_configuration = false
  hardwareStatus.configuration_protected = false
  hardwareStatus.available_devices = []
  try {
    const localResponse = await fetchLocalAgent('/status')
    if (!localResponse.ok && localResponse.status !== 404) {
      throw new Error(`status ${localResponse.status}`)
    }
    const localData = await localResponse.json()
    hardwareStatus.service_active = true
    hardwareStatus.adapter_connected = localData?.status === 'connected'
    hardwareStatus.multi_drawer = Array.isArray(localData?.capabilities) && localData.capabilities.includes('multi_drawer')
    hardwareStatus.drawer_configuration = Array.isArray(localData?.capabilities) && localData.capabilities.includes('drawer_configuration')
    hardwareStatus.configuration_protected = localData?.configuration_protected === true
    hardwareStatus.available_devices = Array.isArray(localData?.available_devices) ? localData.available_devices : []
    hardwareStatus.small_parts_adapter_connected = hardwareStatus.multi_drawer
      ? localData?.drawers?.small_parts?.status === 'connected'
      : null
    hardwareStatus.small_parts_device = localData?.drawers?.small_parts?.device || ''
    hardwareConfig.main_device = localData?.drawers?.main?.device || ''
    hardwareConfig.small_parts_device = localData?.drawers?.small_parts?.device || ''
    hardwareStatus.service_detail = localData?.device
      ? `Hauptschublade: ${localData.device}${hardwareStatus.small_parts_device ? ` · Kleinteile-Lager: ${hardwareStatus.small_parts_device}` : ''}`
      : 'Lokaler Agent erreichbar'
    hardwareStatus.local_agent_reachable = true
    return
  } catch {
    // Fallback 1: no-cors Probe (Agent erreichbar, aber Antwort nicht auslesbar)
  }

  try {
    await fetchLocalAgent('/status', { mode: 'no-cors' })
    hardwareStatus.service_active = true
    hardwareStatus.adapter_connected = null
    hardwareStatus.small_parts_adapter_connected = null
    hardwareStatus.multi_drawer = false
    hardwareStatus.service_detail = 'Lokaler Agent erreichbar; diese PWA-Adresse muss noch lokal freigegeben werden'
    hardwareStatus.local_agent_reachable = true
    hardwareStatus.cors_blocked = true
    return
  } catch {
    // Fallback 2: serverseitiger Status (Self-Hosted-Modus)
  }

  try {
    const { data } = await apiService.get('/hardware-agent/status')
    hardwareStatus.service_active = !!data.service_active
    hardwareStatus.adapter_connected = !!data.adapter_connected
    hardwareStatus.service_detail = data.service_detail || ''
    hardwareStatus.manual_install_command = data.manual_install_command || ''
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Hardware-Status konnte nicht geladen werden')
  }
}

const pairLocalHardwareAgent = async () => {
  if (!hardwareConfig.token) {
    notificationStore.error('Bitte den lokalen Konfigurationscode eingeben')
    return
  }
  hardwareConfigBusy.value = true
  try {
    const body = new URLSearchParams({ config_token: hardwareConfig.token })
    const response = await fetchLocalAgent('/pair', { method: 'POST', body }, 4000)
    const data = await getLocalAgentResponse(response, 'Lokaler Agent konnte nicht verbunden werden')
    notificationStore.success(data.message || 'Lokaler Hardware-Agent verbunden')
    await refreshHardwareStatus()
  } catch (error) {
    console.warn('Lokales Hardware-Pairing fehlgeschlagen', error)
    notificationStore.error('Pairing fehlgeschlagen. Konfigurationscode und installierte Agent-Version prüfen.')
  } finally {
    hardwareConfigBusy.value = false
  }
}

const getLocalAgentResponse = async (response, fallback) => {
  let data = {}
  try {
    data = await response.json()
  } catch {
    // Verständliche Fallback-Meldung verwenden, wenn der Agent kein JSON geliefert hat.
  }
  if (!response.ok) {
    throw new Error(data?.message || fallback)
  }
  return data
}

const createLocalConfigRequest = (payload) => ({
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Kickerkasse-Config-Token': hardwareConfig.token,
  },
  body: JSON.stringify(payload),
})

const testHardwareDevice = async (device, label) => {
  if (!device || !hardwareConfig.token) {
    notificationStore.error('Bitte Adapter und lokalen Konfigurationscode angeben')
    return
  }
  hardwareConfigBusy.value = true
  try {
    const response = await fetchLocalAgent('/testDevice', createLocalConfigRequest({ device }), 4000)
    const data = await getLocalAgentResponse(response, 'Adaptertest fehlgeschlagen')
    notificationStore.success(`${label}: ${data.message || 'Testimpuls gesendet'}`)
  } catch (error) {
    notificationStore.error(error.message || 'Adaptertest fehlgeschlagen')
  } finally {
    hardwareConfigBusy.value = false
  }
}

const saveHardwareMapping = async () => {
  if (!canSaveHardwareMapping.value) {
    notificationStore.error('Bitte zwei verschiedene Adapter und den lokalen Konfigurationscode angeben')
    return
  }
  hardwareConfigBusy.value = true
  try {
    const response = await fetchLocalAgent('/configuration', createLocalConfigRequest({
      main_device: hardwareConfig.main_device,
      small_parts_device: hardwareConfig.small_parts_device,
    }), 4000)
    const data = await getLocalAgentResponse(response, 'Adapterzuordnung konnte nicht gespeichert werden')
    notificationStore.success(data.message || 'Adapterzuordnung lokal gespeichert')
    await refreshHardwareStatus()
  } catch (error) {
    notificationStore.error(error.message || 'Adapterzuordnung konnte nicht gespeichert werden')
  } finally {
    hardwareConfigBusy.value = false
  }
}

const requestManualDrawerOpen = (target) => {
  manualDrawerError.value = ''
  manualDrawerTarget.value = target
}

const confirmManualDrawerOpen = async ({ password }) => {
  manualDrawerError.value = ''
  try {
    const { data } = await apiService.post('/hardware-agent/open-drawer', {
      auth_password: password,
      target: manualDrawerTarget.value,
    })
    const results = await openDrawerTargets(data?.drawer_targets)
    if (failedDrawerTargets(results).length) {
      throw new Error('Der lokale Hardware-Agent konnte die Schublade nicht öffnen')
    }
    notificationStore.success(
      manualDrawerTarget.value === 'small_parts'
        ? 'Kleinteile-Lager wurde geöffnet'
        : 'Hauptschublade wurde geöffnet'
    )
    manualDrawerTarget.value = null
  } catch (error) {
    const detail = error?.response?.data?.detail
    manualDrawerError.value = typeof detail === 'object'
      ? detail.message
      : (detail || error.message || 'Schublade konnte nicht geöffnet werden')
  }
}

const executeHardwareServiceAction = async (action) => {
  if (hardwareStatus.local_agent_reachable) {
    notificationStore.info('Lokaler Agent läuft auf diesem Client. Service-Aktionen bitte lokal ausführen.')
    return
  }
  try {
    const { data } = await apiService.post('/hardware-agent/service-action', { action })
    notificationStore.success(data?.detail || 'Service-Aktion erfolgreich')
    await refreshHardwareStatus()
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Service-Aktion fehlgeschlagen')
  }
}

const downloadInstallerPackage = () => {
  // Direkt-Download vom Backend – ZIP enthält alle für die Installation benötigten
  // Komponenten (agent.py, install_agent_service.py, kickerkasse_bootstrapper.py,
  // setup_wizard.py, Kickerkasse-Install.desktop, README.txt). Einzeldateien werden dem
  // Nutzer bewusst nicht mehr separat angeboten (siehe Roadmap-UX-Sicherheit.md, Punkt 9).
  window.open('/api/hardware-agent/download-installer', '_blank')
}

const testEmailConnection = async () => {
  isTestingEmailConnection.value = true
  try {
    const response = await apiService.post('/app-settings/email/test-connection', {
      email_sender: emailForm.email_sender || null,
      smtp_host: emailForm.smtp_host || null,
      smtp_port: Number(emailForm.smtp_port) || 587,
      smtp_username: emailForm.smtp_username || null,
      smtp_password: emailForm.smtp_password || null,
      smtp_use_tls: emailForm.smtp_use_tls,
    })
    notificationStore.success(response.data?.detail || 'SMTP-Verbindung erfolgreich getestet')
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'SMTP-Verbindung fehlgeschlagen')
  } finally {
    isTestingEmailConnection.value = false
  }
}

const sendTestEmail = async () => {
  isSendingTestEmail.value = true
  try {
    const response = await apiService.post('/app-settings/email/send-test', {
      email_sender: emailForm.email_sender || null,
      recipient: emailForm.email_recipient_zbon || null,
      smtp_host: emailForm.smtp_host || null,
      smtp_port: Number(emailForm.smtp_port) || 587,
      smtp_username: emailForm.smtp_username || null,
      smtp_password: emailForm.smtp_password || null,
      smtp_use_tls: emailForm.smtp_use_tls,
    })
    notificationStore.success(response.data?.detail || 'Testmail erfolgreich gesendet')
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Testmail konnte nicht gesendet werden')
  } finally {
    isSendingTestEmail.value = false
  }
}

onMounted(async () => {
  await appSettingsStore.loadAdminSettings()
  await switchSection(route.query.section)
  syncDesignForm()
  syncSessionTimer()
  syncBusinessData()
  syncEmailForm()
  refreshHardwareStatus()
  loadDataStats()
  loadBackupSchedule()

  const serverLayout = appSettingsStore.settings.kasse_layout
  if (serverLayout) {
    selectedLayout.value = serverLayout
    initialLayout.value = serverLayout
  }
})
</script>

<style scoped lang="scss">
.save-state {
  margin: .5rem 0;
  padding: .55rem .75rem;
  border: 1px solid #f59e0b;
  border-radius: 7px;
  background: #fffbeb;
  color: #78350f;
  font-weight: 700;
  font-size: .82rem;
}
// ═══════════════════════════════════════════════════════
// CSS VARIABLES (Optimiert für Kompaktheit)
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
  --radius: 10px; // Kleinerer Radius für kompaktere Optik
  --shadow: 0 1px 3px rgba(0,0,0,0.07), 0 2px 6px rgba(0,0,0,0.04);
  --transition: all 0.2s ease-in-out;

  background: var(--app-background-color);
  padding: 0.25rem 0.75rem 0.5rem;
  border-radius: 6px;
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

.h-full-flex { flex: 1; display: flex; flex-direction: column; min-height: 0; }
.flex-grow-1 { flex: 1; min-height: 0; }
.flex-col { display: flex; flex-direction: column; }
.gap-sm { gap: 0.5rem; }
.ms-auto { margin-left: auto; }
.mt-auto { margin-top: auto; }
.mt-compact { margin-top: 0.5rem; }
.mb-compact { margin-bottom: 0.5rem; }
.w-100 { width: 100%; }
.d-none { display: none; }
.border-none { border: none !important; }
.shadow-none { box-shadow: none !important; }
.bg-transparent { background: transparent !important; }
.no-padding { padding: 0 !important; }

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
  gap: 0.4rem;
  margin: -0.25rem -0.75rem 0.5rem;
  padding: 0.25rem 0.75rem 0.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.title-row {
  display: flex;
  align-items: baseline;
  gap: 0.4rem;
}

.section-nav-label { font-size: 1.1rem; font-weight: 700; color: #333; }
.title-sep { color: #aaa; }
.page-subtitle { color: #64748b; font-size: 0.85rem; }

.section-nav-buttons {
  display: flex;
  gap: 0.3rem;
  flex-wrap: wrap;
}

.section-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.3rem 0.7rem;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #475569;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition);

  &:hover { background: #f1f5f9; }
  &.active {
    background: var(--app-highlight-color);
    border-color: var(--app-highlight-color);
    color: var(--app-highlight-contrast);
  }
}

// ═══════════════════════════════════════════════════════
// GRID SYSTEM (Kompakt)
// ═══════════════════════════════════════════════════════
.grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.6rem; }
.grid-2-compact { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.4rem; }

.grid-layout-design {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0.6rem;
  align-items: stretch;

  @media (max-width: 1100px) {
    grid-template-columns: 1fr 1fr;
  }
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

// ═══════════════════════════════════════════════════════
// CARDS & TYPOGRAPHY
// ═══════════════════════════════════════════════════════
.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.6rem;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.45rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.8rem;
  color: var(--text);
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.45rem 0.55rem;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  display: inline-block;
  border: 1px solid #cbd5e1;
}

.status-dot--green { background: #22c55e; }
.status-dot--red { background: #ef4444; }
.status-dot--gray { background: #94a3b8; }

.card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0.5rem;
}

.card-icon {
  width: 28px; height: 28px;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;

  &.blue { background: #eff6ff; }
  &.green { background: #f0fdf4; }
  &.orange { background: #fff7ed; }
  &.purple { background: #faf5ff; }
  &.red { background: #fef2f2; }
  &.gray { background: #f8fafc; }
}

.card-title { font-size: 0.9rem; font-weight: 700; color: var(--text); }
.card-subtitle { font-size: 0.75rem; color: var(--muted); }

.section-title {
  font-size: 0.95rem; font-weight: 700; margin-bottom: 0.5rem;
  display: flex; align-items: center; gap: 0.4rem;
  
  .title-icon {
    width: 24px; height: 24px; background: var(--primary-light); color: var(--primary);
    border-radius: 6px; display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem;
  }
}

// ═══════════════════════════════════════════════════════
// FORMS & COLOR PICKER (Platzsparend)
// ═══════════════════════════════════════════════════════
.form-group {
  display: flex; flex-direction: column; gap: 0.2rem;
  &.compact { gap: 0.1rem; }
}

.form-label {
  font-size: 0.75rem; font-weight: 600; color: var(--text);
  display: flex; justify-content: space-between;
  .hint { font-weight: 400; color: var(--muted); }
}

.form-input {
  width: 100%; padding: 0.35rem 0.5rem;
  border: 1px solid var(--border); border-radius: 6px;
  font-size: 0.85rem; background: var(--bg);
  &:focus { outline: none; border-color: var(--primary); }
}

.form-input[type="range"] { padding: 0; }

.local-hardware-config {
  padding: 0.6rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
}

.hardware-mapping-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.6rem;
}

@media (max-width: 720px) {
  .hardware-mapping-grid { grid-template-columns: 1fr; }
}

.form-hint {
  font-size: 0.75rem; color: var(--muted); font-style: italic;
}

.color-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.color-input-group {
  display: flex; flex-direction: column; gap: 0.2rem;
  
  label { font-size: 0.7rem; font-weight: 600; color: var(--muted); }
  
  .color-control {
    display: flex; align-items: center; gap: 0.3rem;
    
    input[type="color"] {
      width: 28px; height: 28px; padding: 0; border: 1px solid var(--border);
      border-radius: 4px; cursor: pointer; background: white;
    }
    
    .hex-input {
      flex: 1; padding: 0.25rem 0.4rem; font-family: 'SF Mono', monospace;
      font-size: 0.75rem; border: 1px solid var(--border); border-radius: 4px;
      text-transform: uppercase;
    }
  }
}

// ═══════════════════════════════════════════════════════
// MEDIA UPLOAD (Listen-Style)
// ═══════════════════════════════════════════════════════
.compact-upload {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem;
  background: var(--bg);
  border: 1px dashed var(--border);
  border-radius: 6px;

  .upload-preview {
    width: 40px; height: 40px; background: white; border-radius: 4px;
    display: flex; align-items: center; justify-content: center;
    border: 1px solid var(--border); overflow: hidden; flex-shrink: 0;
    
    img { max-width: 100%; max-height: 100%; object-fit: contain; }
    span { font-size: 0.6rem; color: var(--muted); font-weight: bold; }
    
    &.bg-preview img { object-fit: cover; }
  }

  .upload-actions {
    display: flex; flex-direction: column; gap: 0.2rem; flex: 1;
    flex-direction: row; align-items: center;
  }
}

.bg-settings-grid {
  display: flex; flex-direction: column; gap: 0.4rem;
  padding: 0.4rem; background: var(--bg); border-radius: 6px;
}

// ═══════════════════════════════════════════════════════
// PREVIEW BOX (Kompakt)
// ═══════════════════════════════════════════════════════
.preview-box {
  border-radius: 8px; overflow: hidden; border: 1px solid var(--border);
  display: flex; flex-direction: column; background: var(--preview-background);
  height: 100%; min-height: 180px;
}

.preview-banner {
  background: var(--preview-banner); color: var(--preview-banner-contrast);
  border-bottom: 2px solid var(--preview-highlight); padding: 0.3rem 0.5rem;
  display: flex; align-items: center; gap: 0.4rem;
  img { height: 16px; object-fit: contain; }
  span { font-weight: 700; font-size: 0.7rem; }
}

.preview-body { flex: 1; display: flex; overflow: hidden; }
.preview-products { flex: 1; display: flex; flex-direction: column; }
.preview-highlight-bar { background: var(--preview-highlight); color: var(--preview-highlight-contrast); padding: 0.2rem 0.4rem; font-size: 0.6rem; font-weight: 600; }
.preview-kasse { flex: 1; background-color: var(--preview-kasse-area); background-image: var(--preview-bg-image); background-size: cover; background-position: center; display: flex; align-items: center; justify-content: center; }
.preview-kasse-label { font-size: 0.6rem; font-weight: 600; color: var(--preview-kasse-area-contrast); opacity: 0.7; }
.preview-sidebar { width: 30%; border-left: 1px solid rgba(0,0,0,0.1); background: rgba(255,255,255,0.85); display: flex; flex-direction: column; gap: 0.2rem; padding: 0.3rem; }
.preview-receipt-item { height: 6px; background: #e2e8f0; border-radius: 2px; &--wide { width: 70%; } }
.preview-total { margin-top: auto; background: var(--preview-highlight); color: var(--preview-highlight-contrast); border-radius: 3px; font-size: 0.6rem; font-weight: 700; text-align: center; padding: 0.15rem; }

// ═══════════════════════════════════════════════════════
// BUTTONS & CONTROLS
// ═══════════════════════════════════════════════════════
.btn-row { display: flex; gap: 0.4rem; flex-wrap: wrap; }
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 0.3rem;
  padding: 0.4rem 0.8rem; border-radius: 6px; border: none; font-size: 0.8rem;
  font-weight: 600; cursor: pointer; transition: var(--transition);
  &.btn-sm { padding: 0.25rem 0.5rem; font-size: 0.75rem; }
  &.btn-icon { padding: 0.25rem; width: 26px; height: 26px; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}

.btn-primary { background: var(--primary); color: white; }
.btn-success { background: var(--success); color: white; }
.btn-warning { background: var(--warning); color: white; }
.btn-danger { background: var(--danger); color: white; }
.btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); }

.toggle-row { display: flex; align-items: center; justify-content: space-between; }
.toggle-switch {
  position: relative; width: 36px; height: 20px; background: #cbd5e1;
  min-width: 36px; min-height: 20px; padding: 0; border: 0; appearance: none;
  border-radius: 10px; cursor: pointer; transition: var(--transition);
  &::after { content: ''; position: absolute; top: 2px; left: 2px; width: 16px; height: 16px; background: white; border-radius: 50%; transition: var(--transition); }
  &.active { background: var(--success); &::after { left: 18px; } }
  &.small { width: 30px; height: 16px; min-width: 30px; min-height: 16px; &::after { width: 12px; height: 12px; } &.active::after { left: 16px; } }
  &:focus-visible { outline: 3px solid var(--focus-ring); outline-offset: 3px; }
}

@media (max-width: 768px), (pointer: coarse) {
  .toggle-switch,
  .toggle-switch.small {
    width: 44px;
    height: 44px;
    min-width: 44px;
    min-height: 44px;
    border-radius: 0;
    background: linear-gradient(#cbd5e1, #cbd5e1) center / 36px 20px no-repeat;

    &::after {
      top: 14px;
      left: 4px;
      width: 16px;
      height: 16px;
    }

    &.active {
      background: linear-gradient(var(--success), var(--success)) center / 36px 20px no-repeat;

      &::after { left: 24px; }
    }
  }
}
.toggle-label-text { font-size: 0.75rem; font-weight: 600; }
.email-card--smtp { grid-column: 1 / -1; }
.email-primary-switches { margin-bottom: .25rem; }

@media (max-width: 900px) {
  .email-card--smtp { grid-column: auto; }
}

// ═══════════════════════════════════════════════════════
// DATA OVERVIEW GRID (Datenpflege)
// ═══════════════════════════════════════════════════════
.data-overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 0.4rem;
}

.overview-tile {
  background: var(--bg); padding: 0.4rem 0.6rem; border-radius: 6px;
  display: flex; flex-direction: column; justify-content: center;
  border: 1px solid var(--border);
  
  .tile-label { font-size: 0.7rem; color: var(--muted); }
  .tile-value { font-size: 1.1rem; font-weight: 700; color: var(--text); }
}

// ═══════════════════════════════════════════════════════
// LAYOUT CHOOSER & SETTINGS (Erweitert)
// ═══════════════════════════════════════════════════════
.layout-grid-compact {
  display: flex; flex-wrap: wrap; gap: 0.4rem;
}

.layout-card-sm {
  border: 1px solid var(--border); border-radius: 6px; padding: 0.3rem 0.6rem;
  font-size: 0.75rem; font-weight: 600; cursor: pointer; background: var(--bg);
  display: flex; align-items: center; gap: 0.4rem; position: relative;
  color: var(--text); font-family: inherit; text-align: left;
  
  &.selected { border-color: var(--primary); background: var(--primary-light); }
}

.layout-badge-sm {
  background: var(--primary); color: white; font-size: 0.6rem;
  padding: 1px 4px; border-radius: 4px; margin-left: auto;
}

.settings-list {
  display: flex; flex-direction: column; gap: 0.4rem;
}

.setting-item {
  display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem;
  background: var(--bg); border-radius: 6px; border: 1px solid var(--border);
  
  &__icon { font-size: 1rem; width: 20px; text-align: center; }
  &__info { flex: 1; display: flex; flex-direction: column; }
  &__title { font-size: 0.8rem; font-weight: 700; color: var(--text); }
  &__controls { display: flex; align-items: center; gap: 0.4rem; }
  &__input { width: 45px; padding: 0.2rem; border: 1px solid var(--border); border-radius: 4px; text-align: center; font-size: 0.75rem; }
  &__unit { font-size: 0.7rem; color: var(--muted); }
}

// ═══════════════════════════════════════════════════════
// ALERTS & DIVIDERS
// ═══════════════════════════════════════════════════════
.warning-box {
  display: flex; gap: 0.5rem; background: var(--warning-bg);
  border: 1px solid #fde68a; border-radius: 6px; padding: 0.5rem;
  &.danger { background: var(--danger-bg); border-color: #fecaca; color: #991b1b; }
  .warning-icon { font-size: 1rem; }
  .warning-text { font-size: 0.75rem; }
}

.compact-box { padding: 0.4rem 0.5rem; }
.divider.compact { margin: 0.3rem 0; border-top: 1px solid var(--border); border-bottom: none; }

// ═══════════════════════════════════════════════════════
// ACTION CARDS (Import/Export)
// ═══════════════════════════════════════════════════════
.action-card {
  align-items: center; text-align: center; gap: 0.4rem; padding: 1rem;
  border: 1px dashed var(--border); cursor: pointer;
  &:hover { border-color: var(--primary); background: var(--primary-light); }
  .action-icon { font-size: 2rem; }
  .action-title { font-weight: 700; font-size: 0.9rem; }
  .action-desc { font-size: 0.75rem; color: var(--muted); }
}

.setup-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1300;
  padding: 0.75rem;
}

.setup-modal-card {
  width: min(720px, 100%);
  max-height: 90vh;
  overflow: auto;
  background: #fff;
  border-radius: 10px;
  border: 1px solid var(--border);
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.28);
  padding: 0.9rem;
}

.setup-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.5rem;

  h3 {
    margin: 0;
    font-size: 1rem;
  }
}

.setup-modal-text {
  margin: 0 0 0.6rem;
  color: var(--text);
  font-size: 0.82rem;
}

.setup-modal-requirement {
  margin: 0 0 0.7rem;
  padding: 0.5rem 0.7rem;
  border-radius: 8px;
  background: rgba(37, 99, 235, 0.08);
  border: 1px solid rgba(37, 99, 235, 0.25);
  color: var(--text);
  font-size: 0.8rem;
}

.setup-step-list {
  margin: 0 0 0.7rem;
  padding-left: 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.8rem;
  color: var(--text);
}

.setup-download-grid {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}

.setup-download-hint {
  margin: 0;
  font-size: 0.75rem;
  color: var(--muted);
}
</style>
