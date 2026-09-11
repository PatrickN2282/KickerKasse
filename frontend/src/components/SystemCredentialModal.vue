<template>
  <div v-if="show" class="modal-overlay">
    <div class="modal-dialog">
      <div class="modal-header">
        <div class="modal-header-title">
          <h3>{{ title }}</h3>
        </div>
        <button class="close-btn" @click="close">✕</button>
      </div>
      <div class="modal-body">
        <p v-if="subtitle" class="subtitle-inline">{{ subtitle }}</p>
        <p v-if="message" class="message">{{ message }}</p>
        <p v-if="adminRequired" class="admin-hint">Hinweis: Für diese Aktion werden explizit Adminrechte benötigt.</p>

        <div class="form-group">
          <label>Benutzername</label>
          <input
            v-if="allowUsernameEdit"
            v-model="localUsername"
            type="text"
            class="form-input"
            placeholder="Benutzername eingeben"
          />
          <select
            v-if="allowUsernameEdit && showUsernameSuggestions"
            v-model="selectedSuggestion"
            class="form-input"
            @change="applySuggestedUsername"
          >
            <option value="">Benutzer aus Liste wählen…</option>
            <option v-for="name in resolvedUsernames" :key="name" :value="name">{{ name }}</option>
          </select>
          <input
            v-else
            v-model="localUsername"
            type="text"
            class="form-input"
            :readonly="!allowUsernameEdit"
            :aria-readonly="!allowUsernameEdit ? 'true' : 'false'"
          />
        </div>

        <div class="form-group">
          <label>Passwort</label>
          <input
            ref="passwordInput"
            v-model="password"
            type="password"
            class="form-input"
            :class="{ 'form-input-error': error, shake: shakeKey }"
            placeholder="Passwort eingeben"
            @keyup.enter="submit"
          />
          <p v-if="error" class="field-error">{{ error }}</p>
        </div>

        <div v-if="confirmationLabel" class="form-group">
          <label>{{ confirmationLabel }}</label>
          <input v-model="confirmationText" type="text" class="form-input" :placeholder="confirmationPlaceholder" @keyup.enter="submit" />
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" @click="close">Abbrechen / Zurück</button>
        <button class="btn btn-primary" :disabled="isSubmitDisabled" @click="submit">{{ confirmLabel }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import apiService from '@/services/api'

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
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 460px;
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
}
.modal-header-title h3 { margin: 0; color: #fff; }
.subtitle-inline {
  margin: 0 0 0.9rem;
  color: #475569;
  font-size: 0.92rem;
  font-weight: 600;
}
.close-btn {
  width: 34px; height: 34px; border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.45);
  background: rgba(255,255,255,0.18);
  color: #fff; cursor: pointer;
}
.modal-body { padding: 1rem 1.25rem; overflow-y: auto; flex: 1; }
.modal-footer { padding: 0.95rem 1.25rem; border-top: 1px solid #e2e8f0; display: flex; gap: 0.75rem; justify-content: flex-end; }
.form-group { display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 1rem; }
.form-input { width: 100%; padding: 0.75rem; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; }
.btn { border: none; border-radius: 8px; padding: 0.65rem 1rem; cursor: pointer; font-weight: 600; font-size: 0.9rem; }
.btn-secondary { background: #f8fafc; color: #475569; border: 1px solid #cbd5e1; }
.btn-primary { background: var(--app-highlight-color); color: var(--app-highlight-contrast); }
.form-input-error { border-color: #c62828 !important; box-shadow: 0 0 0 3px rgba(198, 40, 40, 0.12); }
.field-error { margin: 0.4rem 0 0; color: #c62828; font-size: 0.82rem; font-weight: 600; }
.shake { animation: password-shake 0.4s ease-in-out; }
@keyframes password-shake { 10%,90% { transform: translateX(-1px); } 20%,80% { transform: translateX(2px); } 30%,50%,70% { transform: translateX(-4px); } 40%,60% { transform: translateX(4px); } }
</style>
