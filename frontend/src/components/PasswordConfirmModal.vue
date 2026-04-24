<template>
  <div v-if="show" class="modal-overlay">
    <div class="modal-card">
      <h3>{{ title }}</h3>
      <p v-if="message" class="message">{{ message }}</p>
      <p v-if="adminRequired" class="admin-hint">Hinweis: Für diese Aktion werden explizit Adminrechte benötigt.</p>

      <div class="form-group">
        <label>Benutzername</label>
        <input :value="username" type="text" class="form-input" readonly />
      </div>

      <div class="form-group">
        <label>Passwort</label>
        <input
          ref="passwordInput"
          v-model="password"
          type="password"
          class="form-input"
          placeholder="Passwort eingeben"
          @keyup.enter="submit"
        />
      </div>

      <div class="button-row">
        <button @click="close" class="btn btn-secondary">Abbrechen / Zurück</button>
        <button @click="submit" class="btn btn-primary" :disabled="!password">{{ confirmLabel }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'

const props = defineProps({
  show: Boolean,
  title: {
    type: String,
    default: 'Zugangsdaten bestätigen',
  },
  message: {
    type: String,
    default: '',
  },
  username: {
    type: String,
    default: '',
  },
  confirmLabel: {
    type: String,
    default: 'Bestätigen',
  },
  adminRequired: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'confirm'])

const password = ref('')
const passwordInput = ref(null)

const close = () => {
  password.value = ''
  emit('close')
}

const submit = () => {
  if (!password.value) return
  emit('confirm', password.value)
  password.value = ''
}

watch(() => props.show, async (show) => {
  if (!show) {
    password.value = ''
    return
  }

  await nextTick()
  passwordInput.value?.focus()
})
</script>

<style scoped lang="scss">
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 2500;
}

.modal-card {
  width: min(100%, 420px);
  background: #fff;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
}

.message,
.admin-hint {
  margin: 0 0 1rem;
}

.message {
  white-space: pre-line;
}

.admin-hint {
  color: #b71c1c;
  font-weight: 600;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 1rem;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
}

.button-row {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn {
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  cursor: pointer;
  font-weight: 600;
}

.btn-secondary {
  background: #e2e8f0;
  color: #1e293b;
}

.btn-primary {
  background: var(--app-highlight-color);
  color: var(--app-highlight-contrast);
}
</style>
