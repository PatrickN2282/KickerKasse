<template>
  <div class="data-maintenance">
    <h2>Datenpflege</h2>

    <div class="warning-box">
      <p>
        Der Hard-Reset entfernt Transaktionen, Benutzer, Mitglieder, Produkte, Statistiken,
        Gutscheine, Verzehrkarten und Kategorien unwiderruflich.
      </p>
      <p
        v-if="!authStore.isTopAdmin"
        class="access-note"
      >
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
</template>

<script setup>
import { ref } from 'vue'
import apiService from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import CredentialConfirmModal from '@/components/CredentialConfirmModal.vue'

const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const showResetModal = ref(false)

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
  padding: 2rem;
  border-radius: 8px;
}

.warning-box {
  margin: 1.5rem 0;
  padding: 1rem 1.25rem;
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
</style>
