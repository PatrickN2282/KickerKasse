<template>
  <div
    v-if="show"
    class="modal-overlay"
  >
    <div class="modal-dialog">
      <div class="modal-header">
        <div class="modal-header-title">
          <h3>{{ title }} <span class="header-pipe">|</span> <span class="header-sub">Zugangsdaten eingeben</span></h3>
        </div>
        <button
          class="close-btn"
          @click="close"
        >
          ✕
        </button>
      </div>
      <div class="modal-body">
        <p
          v-if="message"
          class="message"
        >
          {{ message }}
        </p>

        <div class="form-group">
          <label>Benutzername</label>
          <input
            ref="usernameInput"
            v-model="localUsername"
            :readonly="!allowUsernameEdit"
            :aria-readonly="!allowUsernameEdit ? 'true' : 'false'"
            type="text"
            class="form-input"
          >
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
          >
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
          >
        </div>
      </div>
      <div class="modal-footer">
        <button
          class="btn btn-secondary"
          @click="close"
        >
          Abbrechen / Zurück
        </button>
        <button
          class="btn btn-primary"
          :disabled="isSubmitDisabled"
          @click="submit"
        >
          {{ confirmLabel }}
        </button>
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
  max-width: 460px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  overflow: hidden;
}

.modal-header {
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(90deg, #0f766e 0%, #0ea5e9 100%);
  flex-shrink: 0;
}

.modal-header-title {
  display: flex;
  align-items: center;
  min-width: 0;

  h3 {
    margin: 0;
    color: #ffffff;
    font-size: 1.05rem;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .header-pipe {
    margin: 0 0.5rem;
    opacity: 0.5;
  }

  .header-sub {
    font-weight: 400;
    opacity: 0.88;
    font-size: 0.92rem;
  }
}

.close-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.45);
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
  font-size: 1.1rem;
  cursor: pointer;
  display: grid;
  place-items: center;
  flex-shrink: 0;

  &:hover {
    background: rgba(255, 255, 255, 0.3);
  }
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
  flex-shrink: 0;
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
  box-sizing: border-box;
}

.btn {
  border: none;
  border-radius: 8px;
  padding: 0.65rem 1rem;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;

  &:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }
}

.btn-secondary {
  background: #f8fafc;
  color: #475569;
  border: 1px solid #cbd5e1;
}

.btn-primary {
  background: var(--app-highlight-color);
  color: var(--app-highlight-contrast);
}
</style>
