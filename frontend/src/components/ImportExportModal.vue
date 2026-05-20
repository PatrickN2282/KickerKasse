<template>
  <div v-if="show" class="modal-overlay" @click.self="closeModal">
    <div class="modal-card import-export-modal">
      <header class="modal-header">
        <div>
          <h3>Import / Export</h3>
          <p class="modal-subtitle">Produkte, Mitglieder und Kategorien als CSV oder ZIP austauschen.</p>
        </div>
        <button class="modal-close" @click="closeModal">×</button>
      </header>

      <div class="modal-body">
        <div class="tab-row">
          <button
            type="button"
            :class="['tab-button', { active: activeTab === 'import' }]"
            @click="activeTab = 'import'"
          >
            ⬆️ Import
          </button>
          <button
            type="button"
            :class="['tab-button', { active: activeTab === 'export' }]"
            @click="activeTab = 'export'"
          >
            ⬇️ Export
          </button>
        </div>

        <div class="modal-scroller import-export-scroller">
          <section v-if="activeTab === 'import'" class="panel-stack">
            <div class="description-box">
              <h4>Import vorbereiten</h4>
              <p>
                Lade eine CSV- oder ZIP-Datei hoch. Der Datensatz wird automatisch erkannt und kann vor dem Import
                zuvor geprüft werden.
              </p>
            </div>

            <section class="form-section">
              <h4>1. Datenquelle</h4>
              <label class="file-dropzone">
                <span class="file-dropzone-title">Daten-Datei auswählen</span>
                <span class="file-dropzone-hint">CSV oder ZIP mit exportierten Daten</span>
                <input type="file" accept=".csv,.zip" @change="handleDataFileChange" />
              </label>
              <p v-if="importForm.dataFile" class="file-chip">{{ importForm.dataFile.name }}</p>
            </section>

            <section v-if="importForm.analysis" class="form-section">
              <h4>2. Erkannte Bereiche</h4>
              <p class="section-copy">
                Folgende Bereiche wurden erkannt. Die Auswahl kannst du bei Bedarf vor dem Import anpassen.
              </p>
              <div class="section-grid">
                <label
                  v-for="section in sectionOptions"
                  :key="`import-${section.key}`"
                  class="checkbox-card section-card"
                  :class="{ disabled: !isDetected(section.key) }"
                >
                  <input
                    v-model="importForm.selectedSections[section.key]"
                    type="checkbox"
                    :disabled="!isDetected(section.key)"
                  >
                  <div class="checkbox-content">
                    <span class="label">{{ section.label }}</span>
                    <span class="desc">
                      {{ isDetected(section.key) ? detectedRowLabel(section.key) : 'Nicht in der Datei enthalten' }}
                    </span>
                  </div>
                </label>
              </div>
            </section>

            <section v-if="shouldShowImportMedia" class="form-section highlight">
              <h4>3. Mediadaten</h4>
              <p class="section-copy">
                Für erkannte Produkt- oder Mitgliederdaten können optional Bilder übernommen werden.
              </p>
              <label class="checkbox-card">
                <input v-model="importForm.importMedia" type="checkbox">
                <div class="checkbox-content">
                  <span class="label">Zusätzliche Mediadaten importieren</span>
                  <span class="desc">{{ importMediaHint }}</span>
                </div>
              </label>

              <label v-if="importForm.importMedia" class="file-dropzone compact">
                <span class="file-dropzone-title">Optionale Medien-ZIP auswählen</span>
                <span class="file-dropzone-hint">Nur nötig, wenn die Daten-Datei keine Bilder enthält.</span>
                <input type="file" accept=".zip" @change="handleMediaFileChange" />
              </label>
              <p v-if="importForm.mediaFile" class="file-chip">{{ importForm.mediaFile.name }}</p>
            </section>

            <div v-if="importError" class="status-box error">{{ importError }}</div>
          </section>

          <section v-else class="panel-stack">
            <div class="description-box">
              <h4>Export zusammenstellen</h4>
              <p>
                Wähle die gewünschten Bereiche aus. Einzelne Bereiche werden als CSV exportiert, Kombinationen oder
                Medien als ZIP-Datei.
              </p>
            </div>

            <section class="form-section">
              <h4>1. Bereiche auswählen</h4>
              <div class="section-grid">
                <label
                  v-for="section in sectionOptions"
                  :key="`export-${section.key}`"
                  class="checkbox-card section-card"
                >
                  <input v-model="exportForm.sections[section.key]" type="checkbox">
                  <div class="checkbox-content">
                    <span class="label">{{ section.label }}</span>
                    <span class="desc">{{ section.description }}</span>
                  </div>
                </label>
              </div>
            </section>

            <section class="form-section highlight">
              <h4>2. Mediadaten</h4>
              <label class="checkbox-card" :class="{ disabled: !exportMediaAvailable }">
                <input v-model="exportForm.includeMedia" type="checkbox" :disabled="!exportMediaAvailable">
                <div class="checkbox-content">
                  <span class="label">Produkt- und Mitgliederbilder mitsichern</span>
                  <span class="desc">
                    {{ exportMediaAvailable ? 'Bilder werden der ZIP-Datei hinzugefügt.' : 'Nur bei Produkte oder Mitglieder verfügbar.' }}
                  </span>
                </div>
              </label>
            </section>

            <div class="status-box info">
              {{ exportResultHint }}
            </div>
          </section>
        </div>
      </div>

      <footer class="modal-footer">
        <button type="button" class="btn btn-secondary" @click="closeModal">Schließen</button>
        <button
          v-if="activeTab === 'import'"
          type="button"
          class="btn btn-success"
          :disabled="isBusy || !canImport"
          @click="runImport"
        >
          {{ isBusy ? 'Import läuft...' : 'Import starten' }}
        </button>
        <button
          v-else
          type="button"
          class="btn btn-primary"
          :disabled="isBusy || !canExport"
          @click="runExport"
        >
          {{ isBusy ? 'Export läuft...' : 'Export herunterladen' }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import apiService from '@/services/api'
import { useNotificationStore } from '@/stores/notification'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'imported'])

const notificationStore = useNotificationStore()

const sectionOptions = [
  { key: 'products', label: 'Produkte', description: 'Artikel, Preise, Optionen und Kategorie-Zuordnungen.' },
  { key: 'members', label: 'Mitglieder', description: 'Stammdaten, Guthaben und optionale Profilbilder.' },
  { key: 'categories', label: 'Kategorien', description: 'Namen, Farben, Reihenfolgen und Sichtbarkeit.' },
]

const activeTab = ref('import')
const isBusy = ref(false)
const importError = ref('')

const exportForm = reactive({
  sections: {
    products: true,
    members: false,
    categories: false,
  },
  includeMedia: false,
})

const importForm = reactive({
  dataFile: null,
  mediaFile: null,
  analysis: null,
  selectedSections: {
    products: false,
    members: false,
    categories: false,
  },
  importMedia: false,
})

const resetImportState = () => {
  importForm.dataFile = null
  importForm.mediaFile = null
  importForm.analysis = null
  importForm.importMedia = false
  importError.value = ''
  Object.keys(importForm.selectedSections).forEach((key) => {
    importForm.selectedSections[key] = false
  })
}

const resetModalState = () => {
  activeTab.value = 'import'
  isBusy.value = false
  exportForm.sections.products = true
  exportForm.sections.members = false
  exportForm.sections.categories = false
  exportForm.includeMedia = false
  resetImportState()
}

watch(() => props.show, (isVisible) => {
  if (!isVisible) {
    resetModalState()
  }
})

const selectedExportSections = computed(() => Object.entries(exportForm.sections)
  .filter(([, enabled]) => enabled)
  .map(([key]) => key))

const selectedImportSections = computed(() => Object.entries(importForm.selectedSections)
  .filter(([, enabled]) => enabled)
  .map(([key]) => key))

const exportMediaAvailable = computed(() => selectedExportSections.value.some(section => ['products', 'members'].includes(section)))
const canExport = computed(() => selectedExportSections.value.length > 0)
const canImport = computed(() => !!importForm.dataFile && selectedImportSections.value.length > 0)

const shouldShowImportMedia = computed(() => {
  const mediaSections = importForm.analysis?.supports_media_sections || []
  return mediaSections.length > 0
})

const importMediaHint = computed(() => {
  const embedded = importForm.analysis?.embedded_media_sections || []
  const provided = importForm.analysis?.provided_media_sections || []
  if (embedded.length && provided.length) {
    return 'Bilder wurden in der Daten-Datei erkannt und können zusätzlich durch die separate ZIP ergänzt werden.'
  }
  if (embedded.length) {
    return 'Die Daten-Datei enthält bereits passende Bilder.'
  }
  if (provided.length) {
    return 'Die ausgewählte Medien-ZIP enthält passende Bilder.'
  }
  return 'Optional können passende Produkt- oder Mitgliederbilder aus einer separaten ZIP übernommen werden.'
})

const exportResultHint = computed(() => {
  if (!selectedExportSections.value.length) {
    return 'Bitte wähle mindestens einen Bereich aus.'
  }
  if (selectedExportSections.value.length === 1 && !exportForm.includeMedia) {
    return `Es wird eine CSV-Datei für ${sectionLabel(selectedExportSections.value[0])} erzeugt.`
  }
  return 'Es wird eine ZIP-Datei mit allen gewählten Bereichen erzeugt.'
})

watch(exportMediaAvailable, (available) => {
  if (!available) {
    exportForm.includeMedia = false
  }
})

const sectionLabel = (key) => sectionOptions.find(section => section.key === key)?.label || key

const isDetected = (key) => (importForm.analysis?.detected_sections || []).includes(key)

const detectedRowLabel = (key) => {
  const rows = Number(importForm.analysis?.row_counts?.[key] || 0)
  return `${rows} Datensätze erkannt`
}

const closeModal = () => {
  emit('close')
}

const analyzeImport = async () => {
  if (!importForm.dataFile) {
    importForm.analysis = null
    return
  }

  isBusy.value = true
  importError.value = ''

  try {
    const formData = new FormData()
    formData.append('data_file', importForm.dataFile)
    if (importForm.mediaFile) {
      formData.append('media_file', importForm.mediaFile)
    }

    const response = await apiService.post('/admin/import-export/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    importForm.analysis = response.data
    Object.keys(importForm.selectedSections).forEach((key) => {
      importForm.selectedSections[key] = isDetected(key)
    })
    importForm.importMedia = !!response.data.can_import_media
  } catch (error) {
    importForm.analysis = null
    importError.value = error.response?.data?.detail || 'Import-Datei konnte nicht analysiert werden'
  } finally {
    isBusy.value = false
  }
}

const handleDataFileChange = async (event) => {
  const [file] = event.target.files || []
  resetImportState()
  importForm.dataFile = file || null
  if (importForm.dataFile) {
    await analyzeImport()
  }
  event.target.value = ''
}

const handleMediaFileChange = async (event) => {
  const [file] = event.target.files || []
  importForm.mediaFile = file || null
  if (importForm.dataFile) {
    await analyzeImport()
  }
  event.target.value = ''
}

const extractFilename = (headerValue, fallbackName) => {
  const match = /filename="([^"]+)"/.exec(headerValue || '')
  return match?.[1] || fallbackName
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

const runExport = async () => {
  if (!canExport.value) return

  isBusy.value = true
  try {
    const response = await apiService.post('/admin/import-export/export', {
      sections: selectedExportSections.value,
      include_media: exportForm.includeMedia,
    }, {
      responseType: 'blob',
    })

    const fileName = extractFilename(response.headers['content-disposition'], 'import-export.zip')
    triggerDownload(response.data, fileName)
    notificationStore.success('Export wurde erstellt')
    closeModal()
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Export fehlgeschlagen')
  } finally {
    isBusy.value = false
  }
}

const buildImportSummary = (result) => {
  const entries = Object.entries(result?.results || {})
  if (!entries.length) return 'Import abgeschlossen'

  return entries.map(([section, summary]) => {
    const parts = []
    if (summary.created !== undefined) parts.push(`${summary.created} neu`)
    if (summary.updated !== undefined) parts.push(`${summary.updated} aktualisiert`)
    if (summary.media_imported !== undefined) parts.push(`${summary.media_imported} Bilder`)
    return `${sectionLabel(section)}: ${parts.join(', ')}`
  }).join(' · ')
}

const runImport = async () => {
  if (!canImport.value) return

  isBusy.value = true
  importError.value = ''

  try {
    const formData = new FormData()
    formData.append('data_file', importForm.dataFile)
    formData.append('selected_sections', JSON.stringify(selectedImportSections.value))
    formData.append('import_media', String(importForm.importMedia))
    if (importForm.mediaFile) {
      formData.append('media_file', importForm.mediaFile)
    }

    const response = await apiService.post('/admin/import-export/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    notificationStore.success(buildImportSummary(response.data))
    emit('imported', response.data)
    closeModal()
  } catch (error) {
    importError.value = error.response?.data?.detail || 'Import fehlgeschlagen'
    notificationStore.error(importError.value)
  } finally {
    isBusy.value = false
  }
}
</script>

<style scoped lang="scss">
.import-export-modal {
  --modal-size: 650px;
  width: min(var(--modal-size), calc(100vw - 2rem));
  max-width: var(--modal-size);
  height: min(var(--modal-size), calc(100vh - 2rem));
  display: flex;
  flex-direction: column;
}

.modal-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.tab-row {
  display: flex;
  gap: 0.5rem;
  padding: 0 1.25rem 0.85rem;
}

.tab-button {
  flex: 1;
  border: 1px solid #dbe3ee;
  background: #f8fafc;
  color: #475569;
  border-radius: 10px;
  padding: 0.55rem 0.9rem;
  font-weight: 700;
  cursor: pointer;

  &.active {
    background: var(--app-highlight-color);
    border-color: var(--app-highlight-color);
    color: var(--app-highlight-contrast);
  }
}

.import-export-scroller {
  padding: 0 1.25rem;
}

.panel-stack {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  padding-bottom: 0.25rem;
}

.description-box,
.status-box {
  border-radius: 12px;
  padding: 0.85rem 0.95rem;
  border: 1px solid #dbe3ee;
  background: #f8fafc;

  h4,
  p {
    margin: 0;
  }

  h4 {
    margin-bottom: 0.35rem;
    color: #1e293b;
  }

  p {
    color: #475569;
    font-size: 0.88rem;
  }
}

.status-box.info {
  background: #eff6ff;
  border-color: #bfdbfe;
  color: #1d4ed8;
}

.status-box.error {
  background: #fef2f2;
  border-color: #fecaca;
  color: #b91c1c;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;

  h4 {
    margin: 0;
    color: #1e293b;
  }
}

.form-section.highlight {
  padding: 0.85rem 0.95rem;
  border-radius: 12px;
  background: color-mix(in srgb, var(--app-highlight-color) 10%, white);
  border: 1px solid color-mix(in srgb, var(--app-highlight-color) 35%, white);
}

.section-copy {
  margin: 0;
  color: #64748b;
  font-size: 0.88rem;
}

.section-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.65rem;
}

.section-card.disabled,
.checkbox-card.disabled {
  opacity: 0.55;
}

.checkbox-card {
  display: flex;
  gap: 0.7rem;
  align-items: flex-start;
  padding: 0.8rem 0.9rem;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #dbe3ee;

  input {
    margin-top: 0.2rem;
  }
}

.checkbox-content {
  display: flex;
  flex-direction: column;
  gap: 0.18rem;

  .label {
    font-weight: 700;
    color: #1e293b;
  }

  .desc {
    color: #64748b;
    font-size: 0.84rem;
  }
}

.file-dropzone {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  border: 1px dashed #94a3b8;
  border-radius: 12px;
  background: #fff;
  padding: 0.9rem 1rem;
  cursor: pointer;

  input {
    display: none;
  }
}

.file-dropzone.compact {
  padding: 0.75rem 0.9rem;
}

.file-dropzone-title {
  font-weight: 700;
  color: #1e293b;
}

.file-dropzone-hint {
  color: #64748b;
  font-size: 0.84rem;
}

.file-chip {
  margin: 0;
  align-self: flex-start;
  padding: 0.3rem 0.6rem;
  border-radius: 999px;
  background: #e2e8f0;
  color: #334155;
  font-size: 0.82rem;
  font-weight: 600;
}

@media (max-width: 720px) {
  .import-export-modal {
    width: calc(100vw - 1rem);
    height: calc(100vh - 1rem);
  }

  .tab-row,
  .import-export-scroller {
    padding-left: 1rem;
    padding-right: 1rem;
  }
}
</style>
