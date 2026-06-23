<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-brand">
        <img :src="appSettingsStore.logoUrl" alt="KGB - KickerKasse" class="login-logo" />
      </div>

      <div v-if="showSetupHint" class="setup-hint">
        <strong>Erststart erkannt.</strong>
        <span>Bitte führe das Initial-Setup aus, bevor sich weitere Benutzer anmelden.</span>
        <button type="button" class="btn btn-primary setup-btn" @click="setupWizardVisible = true">Initial-Setup starten</button>
      </div>

      <!-- Normalbetrieb: Kasse-Button prominent -->
      <template v-if="!showSetupHint">
        <button
          type="button"
          class="btn-kasse"
          :disabled="isLoading"
          @click="handleKasseLogin"
        >
          <span class="btn-kasse__label">{{ isLoading ? 'Anmeldung läuft...' : 'Kasse anmelden' }}</span>
          <span class="btn-kasse__sub">Direkt als Kassensystem anmelden</span>
        </button>

        <div class="divider">
          <span>oder anmelden</span>
        </div>
      </template>

      <form @submit.prevent="handleLogin">
        <div class="form-row">
          <div class="form-group">
            <label for="username">Benutzer</label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              class="form-input"
              placeholder="Benutzername"
              required
            />
          </div>
          <div class="form-group">
            <label for="password">Passwort</label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              class="form-input"
              placeholder="••••••••"
              required
            />
          </div>
          <button type="submit" class="btn btn-login" :disabled="isLoading || showSetupHint">
            {{ isLoading ? '…' : '→' }}
          </button>
        </div>

        <div v-if="error" class="alert alert-error">{{ error }}</div>
      </form>

      <div class="login-footer">
        <PwaInstallButton />
      </div>
    </div>

    <InitialSetupWizardModal
      :show="setupWizardVisible"
      :dismissible="false"
      @close="setupWizardVisible = false"
      @completed="handleSetupCompleted"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import InitialSetupWizardModal from '@/components/InitialSetupWizardModal.vue'
import PwaInstallButton from '@/components/PwaInstallButton.vue'
import { useAuthStore } from '@/stores/auth'
import { useAppSettingsStore } from '@/stores/appSettings'
import { INITIAL_SETUP_LOCK_KEY } from '@/constants'

const router = useRouter()
const authStore = useAuthStore()
const appSettingsStore = useAppSettingsStore()

const form = reactive({
  username: '',
  password: '',
})

const isLoading = ref(false)
const error = ref(null)
const setupWizardVisible = ref(false)
const setupLockActive = ref(sessionStorage.getItem(INITIAL_SETUP_LOCK_KEY) === '1')
const showSetupHint = computed(() => authStore.setupRequired)

const pushSetupHistoryState = () => {
  window.history.pushState({ setupLock: true }, document.title)
}

const handleSetupLockPopState = () => {
  if (!setupLockActive.value) {
    return
  }

  setupWizardVisible.value = true
  pushSetupHistoryState()
}

const enableSetupLock = () => {
  setupLockActive.value = true
  setupWizardVisible.value = true
  sessionStorage.setItem(INITIAL_SETUP_LOCK_KEY, '1')
}

const disableSetupLock = () => {
  setupLockActive.value = false
  sessionStorage.removeItem(INITIAL_SETUP_LOCK_KEY)
}

watch(
  setupLockActive,
  (active) => {
    if (active) {
      pushSetupHistoryState()
      window.addEventListener('popstate', handleSetupLockPopState)
      return
    }

    window.removeEventListener('popstate', handleSetupLockPopState)
  },
  { immediate: true }
)

const handleLogin = async () => {
  isLoading.value = true
  error.value = null

  const success = await authStore.login(form.username, form.password)

  if (success) {
    router.push('/')
  } else {
    error.value = authStore.error
  }

  isLoading.value = false
}

const handleKasseLogin = async () => {
  isLoading.value = true
  error.value = null

  const success = await authStore.loginAsKasse()

  if (success) {
    router.push('/')
  } else {
    error.value = authStore.error
  }

  isLoading.value = false
}

const handleSetupCompleted = async () => {
  disableSetupLock()
  setupWizardVisible.value = false
  await appSettingsStore.loadAdminSettings()
  router.push('/')
}

onMounted(async () => {
  if (setupLockActive.value) {
    setupWizardVisible.value = true
  }

  const status = await authStore.fetchSetupStatus()
  if (status?.setup_required) {
    enableSetupLock()
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('popstate', handleSetupLockPopState)
})
</script>

<style scoped lang="scss">
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--app-background-color);
  padding: 1rem;
}

.login-card {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.12);
  width: 100%;
  max-width: 480px;
  border-top: 4px solid var(--app-highlight-color);
}

.login-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.login-logo {
  width: min(320px, 100%);
  height: 130px;
  object-fit: contain;
  margin-bottom: 1.25rem;
}

/* ── Kasse-Button ─────────────────────────────────────── */
.btn-kasse {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  width: 100%;
  padding: 1.5rem 1rem;
  border: none;
  border-radius: 14px;
  cursor: pointer;
  background-color: var(--app-highlight-color);
  color: white;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.18);
  transition: filter 0.15s, transform 0.1s, box-shadow 0.15s;

  &:hover:not(:disabled) {
    filter: brightness(1.08);
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.22);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.btn-kasse__label {
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  line-height: 1;
}

.btn-kasse__sub {
  font-size: 0.78rem;
  font-weight: 400;
  opacity: 0.82;
  letter-spacing: 0.02em;
}

/* ── Divider ──────────────────────────────────────────── */
.divider {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 1.25rem 0 1rem;
  color: #bbb;
  font-size: 0.8rem;

  &::before,
  &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #e8e8e8;
  }
}

/* ── Login-Zeile ──────────────────────────────────────── */
.form-row {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;

  .form-group {
    flex: 1;
    min-width: 0;
  }
}

.form-group {
  label {
    display: block;
    margin-bottom: 0.3rem;
    font-weight: 500;
    font-size: 0.8rem;
    color: #666;
  }
}

.form-input {
  width: 100%;
  padding: 0.6rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 0.9rem;
  box-sizing: border-box;

  &:focus {
    outline: none;
    border-color: var(--app-highlight-color);
    box-shadow: 0 0 0 3px rgba(92, 143, 58, 0.15);
  }
}

/* ── Buttons ──────────────────────────────────────────── */
.btn {
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.btn-login {
  flex-shrink: 0;
  padding: 0.6rem 1rem;
  font-size: 1.1rem;
  background-color: var(--app-highlight-color);
  color: white;
  align-self: flex-end;
  white-space: nowrap;
  line-height: 1;
  /* Gleiche Höhe wie form-input */
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ── Setup-Hint ───────────────────────────────────────── */
.setup-hint {
  margin-bottom: 1.25rem;
  padding: 1rem;
  border-radius: 12px;
  background: rgba(25, 118, 210, 0.08);
  color: #12467a;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.setup-btn {
  margin-top: 0.25rem;
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  background-color: var(--app-highlight-color);
  color: white;
}

.btn-primary {
  background-color: var(--app-highlight-color);
  color: white;
}

/* ── Alert ────────────────────────────────────────────── */
.alert {
  margin-top: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.88rem;

  &.alert-error {
    background-color: #ffebee;
    color: #c62828;
    border: 1px solid #ef5350;
  }
}

/* ── Footer ───────────────────────────────────────────── */
.login-footer {
  margin-top: 1.25rem;
}
</style>
