<template>
  <div class="login-container">
    <div class="login-card">
      <h1>Kassensoftware</h1>
      <form @submit.prevent="handleLogin">
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

        <button type="submit" class="btn btn-primary" :disabled="isLoading">
          {{ isLoading ? 'Login läuft...' : 'Login' }}
        </button>

        <div v-if="error" class="alert alert-error">{{ error }}</div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  password: '',
})

const isLoading = ref(false)
const error = ref(null)

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
</script>

<style scoped lang="scss">
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;

  h1 {
    text-align: center;
    color: #333;
    margin-bottom: 2rem;
  }
}

.form-group {
  margin-bottom: 1.5rem;

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #333;
  }
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;

  &:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
}

.btn {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:not(:disabled):hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
}

.btn-primary {
  background-color: #667eea;
  color: white;

  &:not(:disabled):hover {
    background-color: #5568d3;
  }
}

.alert {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 4px;

  &.alert-error {
    background-color: #ffebee;
    color: #c62828;
    border: 1px solid #ef5350;
  }
}
</style>
