<template>
  <div class="data-maintenance">
    <h2>Datenpflege</h2>

    <div v-if="authStore.isTopAdmin" class="section-card">
      <h3>Vollständiges Datenbank-Backup</h3>
      <p class="section-copy">
        Erstellt ein vollständiges Backup der Datenbank als ZIP-Datei.
      </p>
      <button
        class="btn btn-primary"
        :disabled="isBusy"
        @click="handleBackupDownload"
      >
        ⬇️ Vollständiges Datenbank-Backup herunterladen
      </button>
    </div>

    <div v-if="authStore.isTopAdmin" class="section-card">
      <h3>Datenbank wiederherstellen</h3>
      <p class="section-copy warning-copy">
        Stellt die komplette Datenbank aus einer Backup-ZIP wieder her und überschreibt alle aktuellen Daten.
      </p>
      <label class="file-input">
        <span>Backup-ZIP auswählen</span>
        <input type="file" accept=".zip" @change="handleRestoreFileChange">
      </label>
      <p v-if="restoreFile" class="file-name">{{ restoreFile.name }}</p>
      <button
        class="btn btn-warning"
        :disabled="!authStore.isTopAdmin || !restoreFile || isBusy"
        @click="showRestoreModal = true"
      >
        ♻️ Datenbank wiederherstellen
      </button>
    </div>

    <div v-if="authStore.isTopAdmin" class="section-card">
      <h3>Regelmäßiger Backup-E-Mail-Versand</h3>
      <p class="section-copy">
        Zeitgesteuerter Versand des Datenbank-Backups per E-Mail (Empfänger aus den E-Mail-Einstellungen).
      </p>
      <label class="inline-checkbox">
        <input
          v-model="backupSchedule.enabled"
          type="checkbox"
          :disabled="!authStore.isTopAdmin || isBusy"
        >
        Automatischen Backup-Versand aktivieren
      </label>
      <div class="time-row">
        <label for="backup-time">Uhrzeit</label>
        <input
          id="backup-time"
          v-model="backupSchedule.time"
          type="time"
          :disabled="!authStore.isTopAdmin || isBusy"
        >
      </div>
      <button
        class="btn btn-secondary"
        :disabled="!authStore.isTopAdmin || isBusy"
        @click="saveBackupSchedule"
      >
        💾 Backup-Zeitplan speichern
      </button>
    </div>

    <div v-if="authStore.isTopAdmin" class="warning-box">
      <p>
        Der Hard-Reset entfernt Transaktionen, Benutzer, Mitglieder, Produkte, Statistiken,
        Gutscheine, Verzehrkarten und Kategorien unwiderruflich.
      </p>
    </div>

    <button
      v-if="authStore.isTopAdmin"
      class="btn btn-danger"
      :disabled="!authStore.isTopAdmin"
      @click="showResetModal = true"
    >
      🧨 Hard-Reset starten
    </button>

    <div v-if="!authStore.isTopAdmin" class="warning-box">
      Diese kritischen Funktionen sind ausschließlich für den Top-Admin sichtbar und nutzbar.
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

    <CredentialConfirmModal
      :show="showRestoreModal"
      title="Datenbank-Wiederherstellung bestätigen"
      message="Bitte Top-Admin-Passwort eingeben. Die aktuelle Datenbank wird vollständig überschrieben."
      :username="authStore.user?.username || ''"
      confirm-label="Wiederherstellung starten"
      @close="showRestoreModal = false"
      @confirm="handleRestore"
    />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import apiService from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import CredentialConfirmModal from '@/components/CredentialConfirmModal.vue'

const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const showResetModal = ref(false)
const showRestoreModal = ref(false)
const restoreFile = ref(null)
const isBusy = ref(false)
const backupSchedule = reactive({
  enabled: false,
  time: '03:00',
})

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

const loadBackupSchedule = async () => {
  try {
    const response = await apiService.get('/app-settings')
    backupSchedule.enabled = !!response.data.scheduled_database_backup_enabled
    backupSchedule.time = response.data.scheduled_database_backup_time || '03:00'
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Backup-Einstellungen konnten nicht geladen werden')
  }
}

onMounted(() => {
  if (authStore.isTopAdmin) {
    loadBackupSchedule()
  }
})

const handleBackupDownload = async () => {
  isBusy.value = true
  try {
    const response = await apiService.post('/admin/data-maintenance/database-backup/export', {}, {
      responseType: 'blob',
    })
    const fileName = extractFilename(response.headers['content-disposition'], 'kickerkasse-db-backup.zip')
    triggerDownload(response.data, fileName)
    notificationStore.success('Datenbank-Backup wurde heruntergeladen')
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Datenbank-Backup fehlgeschlagen')
  } finally {
    isBusy.value = false
  }
}

const handleRestoreFileChange = (event) => {
  const [file] = event.target.files || []
  restoreFile.value = file || null
  event.target.value = ''
}

const handleRestore = async ({ password }) => {
  showRestoreModal.value = false
  if (!restoreFile.value) {
    notificationStore.error('Bitte zuerst eine Backup-ZIP auswählen')
    return
  }

  isBusy.value = true
  try {
    const formData = new FormData()
    formData.append('auth_password', password)
    formData.append('backup_file', restoreFile.value)
    await apiService.post('/admin/data-maintenance/database-backup/restore', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    notificationStore.success('Datenbank wurde aus dem Backup wiederhergestellt')
    restoreFile.value = null
    await authStore.logout()
    window.location.href = '/login'
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Wiederherstellung fehlgeschlagen')
  } finally {
    isBusy.value = false
  }
}

const saveBackupSchedule = async () => {
  isBusy.value = true
  try {
    await apiService.put('/app-settings', {
      scheduled_database_backup_enabled: backupSchedule.enabled,
      scheduled_database_backup_time: backupSchedule.time || '03:00',
    })
    notificationStore.success('Backup-Zeitplan gespeichert')
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Backup-Zeitplan konnte nicht gespeichert werden')
  } finally {
    isBusy.value = false
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
</script>

<style scoped lang="scss">
.data-maintenance {
  background: white;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-card {
  border: 1px solid #dbe3ee;
  border-radius: 10px;
  padding: 0.9rem 1rem;

  h3 {
    margin: 0 0 0.5rem;
  }
}

.section-copy {
  margin: 0 0 0.75rem;
  color: #475569;
}

.warning-copy {
  color: #b45309;
}

.file-input {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-bottom: 0.5rem;
}

.file-name {
  margin: 0 0 0.75rem;
  font-size: 0.9rem;
  color: #334155;
}

.inline-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.time-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.warning-box {
  padding: 0.75rem 1rem;
  border-radius: 10px;
  background: #fff4e5;
  border: 1px solid #f59e0b;
  color: #7c2d12;
}

.access-note {
  font-weight: 700;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 700;
}

.btn-danger {
  background: #dc2626;
  color: white;
}

.btn-danger:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-warning {
  background: #d97706;
  color: white;
}

.btn-secondary {
  background: #475569;
  color: white;
}
</style>
