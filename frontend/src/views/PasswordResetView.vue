<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-brand">
        <img :src="appSettingsStore.logoUrl" alt="KGB - KickerKasse" class="login-logo" />
      </div>

      <h2 class="reset-title">Neues Passwort festlegen</h2>

      <template v-if="!success">
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="new-password">Neues Passwort</label>
            <input
              id="new-password"
              v-model="form.password"
              type="password"
              class="form-input"
              placeholder="Mindestens 8 Zeichen"
              minlength="8"
              required
            />
          </div>
          <div class="form-group">
            <label for="new-password-confirm">Passwort wiederholen</label>
            <input
              id="new-password-confirm"
              v-model="form.passwordConfirm"
              type="password"
              class="form-input"
              :class="{ 'form-input-error': mismatch }"
              placeholder="Passwort erneut eingeben"
              minlength="8"
              required
            />
            <p v-if="mismatch" class="field-error">Die Passwörter stimmen nicht überein.</p>
          </div>

          <button type="submit" class="btn btn-login-full" :disabled="isSubmitting || mismatch || !form.password">
            {{ isSubmitting ? 'Wird gespeichert…' : 'Passwort speichern' }}
          </button>

          <div v-if="error" class="alert alert-error">{{ error }}</div>
        </form>
      </template>

      <template v-else>
        <p class="success-message">
          Dein Passwort wurde erfolgreich zurückgesetzt. Du kannst dich jetzt mit dem neuen
          Passwort anmelden.
        </p>
        <router-link to="/login" class="btn btn-login-full btn-link">Zur Anmeldung</router-link>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import apiService from '@/services/api'
import { useAppSettingsStore } from '@/stores/appSettings'

const route = useRoute()
const appSettingsStore = useAppSettingsStore()

const form = reactive({
  password: '',
  passwordConfirm: '',
})

const isSubmitting = ref(false)
const error = ref('')
const success = ref(false)

const mismatch = computed(() => (
  Boolean(form.password) && Boolean(form.passwordConfirm) && form.password !== form.passwordConfirm
))

const handleSubmit = async () => {
  if (mismatch.value || !form.password) return
  isSubmitting.value = true
  error.value = ''
  try {
    await apiService.post('/auth/password-reset/confirm', {
      token: route.params.token,
      new_password: form.password,
    })
    success.value = true
  } catch (err) {
    error.value = err.response?.data?.detail || 'Passwort konnte nicht zurückgesetzt werden.'
  } finally {
    isSubmitting.value = false
  }
}
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
  max-width: 440px;
  border-top: 4px solid var(--app-highlight-color);
}

.login-brand {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}

.login-logo {
  max-height: 64px;
}

.reset-title {
  text-align: center;
  margin: 0 0 1.25rem;
  font-size: 1.15rem;
  color: #1e293b;
}

.form-group {
  margin-bottom: 1rem;

  label {
    display: block;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 0.35rem;
    color: #334155;
  }
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  box-sizing: border-box;
  font-size: 0.95rem;
}

.form-input-error {
  border-color: #c62828 !important;
  box-shadow: 0 0 0 3px rgba(198, 40, 40, 0.12);
}

.field-error {
  margin: 0.4rem 0 0;
  color: #c62828;
  font-size: 0.82rem;
  font-weight: 600;
}

.btn-login-full {
  width: 100%;
  padding: 0.8rem;
  border: none;
  border-radius: 10px;
  background: var(--app-highlight-color);
  color: var(--app-highlight-contrast, #fff);
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  text-align: center;
  text-decoration: none;
  display: inline-block;

  &:disabled { opacity: 0.55; cursor: not-allowed; }
}

.btn-link {
  margin-top: 0.5rem;
}

.alert {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
}

.alert-error {
  background: #ffebee;
  color: #c62828;
  border: 1px solid #ffcdd2;
}

.success-message {
  color: #166534;
  font-size: 0.95rem;
  line-height: 1.5;
  text-align: center;
  margin: 0 0 1.25rem;
}
</style>
