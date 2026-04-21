<template>
  <div v-if="show" class="modal-overlay">
    <div class="modal-card">
      <h3>{{ title }}</h3>
      <p v-if="message" class="message">{{ message }}</p>

      <div class="form-group">
        <label>Benutzername</label>
        <input
          ref="usernameInput"
          v-model="localUsername"
          :readonly="!allowUsernameEdit"
          type="text"
          class="form-input"
        />
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

      <div
        v-if="confirmationLabel"
        class="form-group"
      >
        <label>{{ confirmationLabel }}</label>
        <input
          v-model="confirmationText"
          type="text"
          class="form-input"
          :placeholder="confirmationPlaceholder"
          @keyup.enter="submit"
        />
      </div>

      <div class="button-row">
        <button @click="close" class="btn btn-secondary">Abbrechen / Zurück</button>
        <button @click="submit" class="btn btn-primary" :disabled="isSubmitDisabled">{{ confirmLabel }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'

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
  allowUsernameEdit: {
    type: Boolean,
    default: false,
  },
  confirmLabel: {
    type: String,
    default: 'Bestätigen',
  },
  confirmationLabel: {
    type: String,
    default: '',
  },
  confirmationPlaceholder: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['close', 'confirm'])

const localUsername = ref('')
const password = ref('')
const confirmationText = ref('')
const usernameInput = ref(null)
const passwordInput = ref(null)

const isSubmitDisabled = computed(() => (
  !localUsername.value.trim()
  || !password.value
  || (!!props.confirmationLabel && !confirmationText.value.trim())
))

const reset = () => {
  localUsername.value = props.username || ''
  password.value = ''
  confirmationText.value = ''
}

const close = () => {
  reset()
  emit('close')
}

const submit = () => {
  if (isSubmitDisabled.value) return
  emit('confirm', {
    username: localUsername.value.trim(),
    password: password.value,
    confirmationText: confirmationText.value.trim(),
  })
  reset()
}

watch(() => props.show, async (show) => {
  if (!show) {
    reset()
    return
  }

  reset()
  await nextTick()
  if (props.allowUsernameEdit) {
    usernameInput.value?.focus()
  } else {
    passwordInput.value?.focus()
  }
})

watch(() => props.username, () => {
  if (!props.show) {
    localUsername.value = props.username || ''
  }
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
  width: min(100%, 460px);
  background: #fff;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
}

.message {
  margin: 0 0 1rem;
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
