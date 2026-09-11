<template>
  <Teleport to="body">
    <div v-if="show" class="auth-modal-overlay">
    <div ref="dialogRef" class="auth-modal" role="dialog" aria-modal="true" :aria-label="title">
      <header class="auth-modal__header">
        <div class="auth-modal__brand">
          <div class="brand-badge">KK</div>
          <div class="brand-copy">
            <h3>{{ title }}</h3>
            <p>{{ subtitle || 'Zugangsdaten eingeben' }}</p>
          </div>
        </div>
        <button class="close-btn" type="button" @click="requestClose" aria-label="Schließen">✕</button>
      </header>

      <section class="auth-modal__body">
        <p v-if="message" class="message">{{ message }}</p>
        <p v-if="adminRequired" class="admin-hint">Hinweis: Für diese Aktion werden ausdrücklich Adminrechte benötigt.</p>

        <div class="form-group">
          <label for="credential-username">Benutzername</label>
          <input
            v-if="allowUsernameEdit"
            v-model="localUsername"
            id="credential-username"
            type="text"
            class="form-input"
            placeholder="Benutzername eingeben"
          />
          <select
            v-if="allowUsernameEdit && showUsernameSuggestions"
            v-model="selectedSuggestion"
            class="form-input form-input--select"
            @change="applySuggestedUsername"
          >
            <option value="">Benutzer aus Liste wählen…</option>
            <option v-for="name in resolvedUsernames" :key="name" :value="name">{{ name }}</option>
          </select>
          <input
            v-else-if="!allowUsernameEdit"
            v-model="localUsername"
            id="credential-username"
            type="text"
            class="form-input"
            :readonly="!allowUsernameEdit"
            :aria-readonly="!allowUsernameEdit ? 'true' : 'false'"
          />
        </div>

        <div class="form-group">
          <label for="credential-password">Passwort</label>
          <input
            ref="passwordInput"
            id="credential-password"
            v-model="password"
            type="password"
            class="form-input"
            :class="{ 'form-input-error': error, shake: shakeKey }"
            placeholder="Passwort eingeben"
            @keyup.enter="submit"
          />
          <p v-if="error" class="field-error" role="alert">{{ error }}</p>
        </div>

        <div v-if="confirmationLabel" class="form-group">
          <label>{{ confirmationLabel }}</label>
          <input
            v-model="confirmationText"
            type="text"
            class="form-input"
            :placeholder="confirmationPlaceholder"
            @keyup.enter="submit"
          />
        </div>
      </section>

      <footer class="auth-modal__footer">
        <button class="btn btn-secondary" type="button" @click="requestClose">Abbrechen</button>
        <button class="btn btn-primary" type="button" :disabled="isSubmitDisabled" @click="submit">{{ confirmLabel }}</button>
      </footer>
    </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, ref, toRef, watch } from 'vue'
import apiService from '@/services/api'
import { useModalFocus } from '@/composables/useModalFocus'

const props = defineProps({
  show: Boolean,
  title: { type: String, default: 'Zugangsdaten bestätigen' },
  subtitle: { type: String, default: 'Zugangsdaten eingeben' },
  message: { type: String, default: '' },
  username: { type: String, default: '' },
  usernames: { type: Array, default: () => [] },
  allowUsernameEdit: { type: Boolean, default: false },
  confirmLabel: { type: String, default: 'Bestätigen' },
  confirmationLabel: { type: String, default: '' },
  confirmationPlaceholder: { type: String, default: '' },
  adminRequired: { type: Boolean, default: false },
  error: { type: String, default: '' },
})

const emit = defineEmits(['close', 'confirm', 'update:usernames'])

const localUsername = ref('')
const password = ref('')
const confirmationText = ref('')
const passwordInput = ref(null)
const shakeKey = ref(false)
const resolvedUsernames = ref([...props.usernames])
const loadingUsernames = ref(false)
const selectedSuggestion = ref('')
const dialogRef = ref(null)

const showUsernameSuggestions = computed(() => props.allowUsernameEdit && resolvedUsernames.value.length > 0)
const isSubmitDisabled = computed(() => !localUsername.value.trim() || !password.value || (!!props.confirmationLabel && !confirmationText.value.trim()))

const reset = () => {
  localUsername.value = props.username || ''
  password.value = ''
  confirmationText.value = ''
  selectedSuggestion.value = ''
}

const applySuggestedUsername = () => {
  if (!selectedSuggestion.value) return
  localUsername.value = selectedSuggestion.value
  selectedSuggestion.value = ''
}

const loadUsernames = async () => {
  if (!props.allowUsernameEdit || resolvedUsernames.value.length || loadingUsernames.value) return
  loadingUsernames.value = true
  try {
    const response = await apiService.get('/auth/usernames', {
      params: { include_inactive: true },
    })
    const usernames = Array.isArray(response.data) ? response.data : []
    if (usernames.length && !localUsername.value) {
      localUsername.value = usernames[0]
    }
    resolvedUsernames.value = usernames
    emit('update:usernames', usernames)
  } catch {
    resolvedUsernames.value = []
    emit('update:usernames', [])
  } finally {
    loadingUsernames.value = false
  }
}

const close = () => {
  reset()
  emit('close')
}

const { requestClose } = useModalFocus(toRef(props, 'show'), dialogRef, { onClose: close })

const submit = () => {
  if (isSubmitDisabled.value) return
  emit('confirm', {
    username: localUsername.value.trim(),
    password: password.value,
    confirmationText: confirmationText.value.trim(),
  })
}

watch(() => props.show, async (show) => {
  if (!show) {
    reset()
    return
  }
  reset()
  resolvedUsernames.value = [...props.usernames]
  await loadUsernames()
  await nextTick()
  passwordInput.value?.focus()
})

watch(() => props.error, (value) => {
  if (!value) return
  password.value = ''
  shakeKey.value = false
  nextTick(() => {
    shakeKey.value = true
    passwordInput.value?.focus()
    setTimeout(() => { shakeKey.value = false }, 400)
  })
})

watch(() => props.username, () => {
  if (!props.show) localUsername.value = props.username || ''
})
</script>

<style scoped lang="scss">
.auth-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 4000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.25rem;
  background: radial-gradient(circle at 20% 15%, rgba(14, 116, 144, 0.28), transparent 46%),
              radial-gradient(circle at 85% 85%, rgba(2, 132, 199, 0.22), transparent 50%),
              rgba(15, 23, 42, 0.56);
  backdrop-filter: blur(5px);
}

.auth-modal {
  width: min(100%, 500px);
  max-height: min(92vh, 720px);
  display: grid;
  grid-template-rows: auto 1fr auto;
  border-radius: 18px;
  overflow: hidden;
  background: #ffffff;
  box-shadow: 0 28px 65px rgba(2, 6, 23, 0.42);
  border: 1px solid rgba(148, 163, 184, 0.35);
}

.auth-modal__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem 1.15rem;
  background: linear-gradient(120deg, #0f766e 0%, #0369a1 62%, #0ea5e9 100%);
}

.auth-modal__brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.brand-badge {
  width: 2rem;
  height: 2rem;
  border-radius: 999px;
  display: grid;
  place-items: center;
  font-weight: 800;
  letter-spacing: 0.03em;
  color: #0f172a;
  background: #e0f2fe;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.45);
}

.brand-copy h3 {
  margin: 0;
  color: #f8fafc;
  font-size: 1.02rem;
  line-height: 1.2;
}

.brand-copy p {
  margin: 0.15rem 0 0;
  color: rgba(240, 249, 255, 0.92);
  font-size: 0.84rem;
}

.close-btn {
  width: 2rem;
  height: 2rem;
  border-radius: 999px;
  border: 1px solid rgba(240, 249, 255, 0.55);
  color: #f8fafc;
  background: rgba(248, 250, 252, 0.14);
  cursor: pointer;
}

.auth-modal__body {
  padding: 1rem 1.15rem 0.9rem;
  overflow-y: auto;
}

.message {
  margin: 0 0 0.8rem;
  color: #334155;
  white-space: pre-line;
}

.admin-hint {
  margin: 0 0 0.9rem;
  color: #9a3412;
  font-size: 0.86rem;
  background: #ffedd5;
  border: 1px solid #fdba74;
  border-radius: 10px;
  padding: 0.45rem 0.6rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 0.95rem;
}

.form-group label {
  color: #0f172a;
  font-weight: 700;
  font-size: 0.88rem;
}

.form-input {
  width: 100%;
  padding: 0.72rem 0.74rem;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #0f172a;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #0ea5e9;
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15);
  background: #ffffff;
}

.form-input-error {
  border-color: #c62828 !important;
  box-shadow: 0 0 0 3px rgba(198, 40, 40, 0.12);
}

.field-error {
  margin: 0.15rem 0 0;
  color: #c62828;
  font-size: 0.82rem;
  font-weight: 700;
}

.auth-modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.65rem;
  padding: 0.85rem 1.15rem 1rem;
  border-top: 1px solid #e2e8f0;
  background: linear-gradient(180deg, rgba(241, 245, 249, 0.7), rgba(255, 255, 255, 0.95));
}

.btn {
  min-width: 7.25rem;
  border: none;
  border-radius: 10px;
  padding: 0.62rem 0.95rem;
  font-weight: 700;
  cursor: pointer;
}

.btn-secondary {
  border: 1px solid #cbd5e1;
  color: #334155;
  background: #f8fafc;
}

.btn-primary {
  color: #ffffff;
  background: linear-gradient(120deg, #0284c7 0%, #0f766e 100%);
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.shake {
  animation: password-shake 0.4s ease-in-out;
}

@keyframes password-shake {
  10%,
  90% { transform: translateX(-1px); }
  20%,
  80% { transform: translateX(2px); }
  30%,
  50%,
  70% { transform: translateX(-4px); }
  40%,
  60% { transform: translateX(4px); }
}
</style>
