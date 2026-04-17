<template>
  <div class="admin-settings">
    <h2>Design & Logo</h2>

    <div class="settings-grid">
      <section class="settings-card">
        <h3>Farben</h3>
        <div class="form-group">
          <label for="appName">App-Überschrift</label>
          <input id="appName" v-model.trim="form.app_name" type="text" class="form-input" maxlength="120" />
        </div>
        <div class="form-group">
          <label for="backgroundColor">Hintergrundfarbe</label>
          <input id="backgroundColor" v-model="form.background_color" type="color" class="color-input" />
        </div>
        <div class="form-group">
          <label for="bannerColor">Bannerfarbe</label>
          <input id="bannerColor" v-model="form.banner_color" type="color" class="color-input" />
        </div>
        <div class="form-group">
          <label for="highlightColor">Highlight-Farbe</label>
          <input id="highlightColor" v-model="form.highlight_color" type="color" class="color-input" />
        </div>
        <button class="btn btn-primary" :disabled="appSettingsStore.isSaving" @click="saveSettings">
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
          <span class="preview-title">{{ form.app_name }}</span>
        </div>
        <div class="preview-highlight">Highlight-Fläche</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useAppSettingsStore } from '@/stores/appSettings'
import { useNotificationStore } from '@/stores/notification'

const appSettingsStore = useAppSettingsStore()
const notificationStore = useNotificationStore()

const getPreviewContrast = (hexColor, dark = '#111827', light = '#FFFFFF') => {
  const hex = (hexColor || '').replace('#', '')
  if (hex.length !== 6) {
    return light
  }

  const red = parseInt(hex.slice(0, 2), 16)
  const green = parseInt(hex.slice(2, 4), 16)
  const blue = parseInt(hex.slice(4, 6), 16)
  const brightness = ((red * 299) + (green * 587) + (blue * 114)) / 1000

  return brightness >= 160 ? dark : light
}

const form = reactive({
  app_name: 'KGB - KickerKasse',
  background_color: '#D7DCE2',
  banner_color: '#131820',
  highlight_color: '#5C8F3A',
})
const selectedLogo = ref(null)
const selectedLogoPreview = ref('')

const syncForm = () => {
  form.app_name = appSettingsStore.settings.app_name
  form.background_color = appSettingsStore.settings.background_color
  form.banner_color = appSettingsStore.settings.banner_color
  form.highlight_color = appSettingsStore.settings.highlight_color
}

const previewStyle = computed(() => ({
  '--preview-background': form.background_color,
  '--preview-banner': form.banner_color,
  '--preview-highlight': form.highlight_color,
  '--preview-banner-contrast': getPreviewContrast(form.banner_color),
  '--preview-highlight-contrast': getPreviewContrast(form.highlight_color),
}))

const previewLogoUrl = computed(() => selectedLogoPreview.value || appSettingsStore.logoUrl)

const handleLogoSelection = (event) => {
  const [file] = event.target.files || []
  if (!file) return
  selectedLogo.value = file
  selectedLogoPreview.value = URL.createObjectURL(file)
}

const saveSettings = async () => {
  try {
    await appSettingsStore.saveThemeSettings({ ...form })
    syncForm()
    notificationStore.success('Design-Einstellungen gespeichert')
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

onMounted(async () => {
  await appSettingsStore.loadAdminSettings()
  syncForm()
})
</script>

<style scoped lang="scss">
.admin-settings {
  background: white;
  padding: 2rem;
  border-radius: 8px;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.5rem;
}

.settings-card {
  background: #f5f5f5;
  padding: 1.5rem;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.color-input,
.form-input {
  width: 100%;
}

.logo-preview {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 180px;
  background: white;
  border-radius: 8px;
  padding: 1rem;

  img {
    max-width: 100%;
    max-height: 150px;
    object-fit: contain;
  }
}

.preview-card {
  margin-top: 1.5rem;
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

.btn {
  padding: 0.75rem 1.25rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

.btn-primary {
  background: var(--app-highlight-color);
  color: white;
}

.btn-success {
  background: var(--app-banner-color);
  color: white;
}
</style>
