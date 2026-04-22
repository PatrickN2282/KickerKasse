<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-brand">
        <img :src="appSettingsStore.logoUrl" alt="KGB - KickerKasse" class="login-logo" />
      </div>
      <form @submit.prevent="handleLogin">
        <template v-if="showSetupFlow">
          <p class="setup-hint">
            Beim ersten Start muss einmalig ein Top-Admin eingerichtet werden.
          </p>
        </template>
        <div class="form-group">
          <label for="username">Benutzername:</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            class="form-input"
            required
          />
        </div>

        <div class="form-group">
          <label for="password">Passwort:</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            class="form-input"
            required
          />
        </div>

        <div
          v-if="showSetupFlow"
          class="form-group"
        >
          <label for="email">E-Mail (optional):</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            class="form-input"
          />
        </div>

        <div
          v-if="showSetupFlow"
          class="form-group"
        >
          <label for="password_confirm">Passwort wiederholen:</label>
          <input
            id="password_confirm"
            v-model="form.passwordConfirm"
            type="password"
            class="form-input"
            required
          />
        </div>

        <button type="submit" class="btn btn-primary" :disabled="isLoading">
          {{ isLoading ? (showSetupFlow ? 'Einrichtung läuft...' : 'Login läuft...') : (showSetupFlow ? 'Top-Admin einrichten' : 'Login') }}
        </button>

        <button
          v-if="!showSetupFlow"
          type="button"
          class="btn btn-secondary"
          :disabled="isLoading"
          @click="handleKasseLogin"
        >
          {{ isLoading ? 'Anmeldung läuft...' : 'Kasse anmelden' }}
        </button>

        <div v-if="error" class="alert alert-error">{{ error }}</div>
      </form>
      <div class="login-footer">
        <PwaInstallButton />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppSettingsStore } from '@/stores/appSettings'
import PwaInstallButton from '@/components/PwaInstallButton.vue'

const router = useRouter()
const authStore = useAuthStore()
const appSettingsStore = useAppSettingsStore()

const form = reactive({
  username: '',
  password: '',
  passwordConfirm: '',
  email: '',
})

const isLoading = ref(false)
const error = ref(null)
const showSetupFlow = computed(() => authStore.setupRequired)

const handleLogin = async () => {
  isLoading.value = true
  error.value = null

  if (showSetupFlow.value && form.password !== form.passwordConfirm) {
    error.value = 'Die Passwörter stimmen nicht überein'
    isLoading.value = false
    return
  }

  const success = showSetupFlow.value
    ? await authStore.completeTopAdminSetup({
      username: form.username,
      password: form.password,
      email: form.email,
    })
    : await authStore.login(form.username, form.password)

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

onMounted(() => {
  authStore.fetchSetupStatus()
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
  max-width: 420px;
  border-top: 4px solid var(--app-highlight-color);

  h1 {
    text-align: center;
    color: #333;
    margin-bottom: 1.5rem;
  }
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
  margin-bottom: 1rem;
}

.form-group {
  margin-bottom: 1.25rem;

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #333;
  }
}

.setup-hint {
  margin-bottom: 1.25rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  background: rgba(25, 118, 210, 0.08);
  color: #12467a;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;

  &:focus {
    outline: none;
    border-color: var(--app-highlight-color);
    box-shadow: 0 0 0 3px rgba(92, 143, 58, 0.15);
  }
}

.btn {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary {
  background-color: var(--app-highlight-color);
  color: white;
}

.btn-secondary {
  margin-top: 0.75rem;
  background-color: var(--app-banner-color);
  color: var(--app-banner-contrast);
 }

.alert {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 8px;

  &.alert-error {
    background-color: #ffebee;
    color: #c62828;
    border: 1px solid #ef5350;
  }
}

.login-footer {
  margin-top: 1.25rem;
  display: flex;
  justify-content: center;
}
</style>
