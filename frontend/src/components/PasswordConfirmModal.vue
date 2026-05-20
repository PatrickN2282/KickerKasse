<template>
  <div v-if="show" class="modal-overlay">
    <div class="modal-dialog">
      <div class="modal-header">
        <div>
          <h3>{{ title }}</h3>
          <p class="subtitle">Zugangsdaten eingeben</p>
        </div>
        <button class="close-btn" @click="close">✕</button>
      </div>
      <div class="modal-body">
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
      </div>
      <div class="modal-footer">
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
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.25rem;
  z-index: 2500;
}
.modal-dialog {
  background: #ffffff;
  border-radius: 16px;
  width: 100%;
  max-width: 420px;
  max-height: 650px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  overflow: hidden;
}
.modal-header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: linear-gradient(90deg, #0f766e 0%, #0ea5e9 100%);
  h3 { margin: 0; color: #ffffff; font-size: 1.1rem; }
  .subtitle { margin: 0.35rem 0 0; color: rgba(255,255,255,0.9); font-size: 0.85rem; }
}
.close-btn {
  width: 34px; height: 34px; border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.45);
  background: rgba(255,255,255,0.18);
  color: #ffffff; font-size: 1.1rem; cursor: pointer;
  display: grid; place-items: center; flex-shrink: 0;
  &:hover { background: rgba(255,255,255,0.3); }
}
.modal-body {
  padding: 1rem 1.25rem;
  overflow-y: auto;
  flex: 1;
}
.modal-footer {
  padding: 0.95rem 1.25rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  background: #ffffff;
}
.message { white-space: pre-line; margin: 0 0 1rem; }
.admin-hint { color: #b71c1c; font-weight: 600; margin: 0 0 1rem; }
.form-group {
  display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 1rem;
}
.form-input {
  width: 100%; padding: 0.75rem;
  border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box;
}
.btn {
  border: none; border-radius: 8px;
  padding: 0.65rem 1rem; cursor: pointer; font-weight: 600; font-size: 0.9rem;
  &:disabled { opacity: 0.55; cursor: not-allowed; }
}
.btn-secondary { background: #f8fafc; color: #475569; border: 1px solid #cbd5e1; }
.btn-primary { background: var(--app-highlight-color); color: var(--app-highlight-contrast); }
</style>
