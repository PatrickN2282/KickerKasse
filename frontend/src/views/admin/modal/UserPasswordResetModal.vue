<template>
  <div v-if="resettingPasswordFor" class="user-pw-reset-modal modal-overlay" @click.self="$emit('close')">
    <div class="modal-card modal-card-form modal-card-compact">
      <header class="modal-header">
        <div>
          <h3>Passwort neu vergeben</h3>
          <p class="modal-subtitle">Neues Passwort für <strong>{{ resettingPasswordFor.username }}</strong> festlegen.</p>
        </div>
        <button class="modal-close" @click="$emit('close')">×</button>
      </header>

      <div class="modal-form-content">
        <section class="form-section compact-section">
          <div class="form-group">
            <label for="reset-password">Neues Passwort</label>
            <input
              id="reset-password"
              v-model="localPassword"
              type="password"
              minlength="8"
              placeholder="Mindestens 8 Zeichen"
            >
          </div>
        </section>

        <footer class="modal-footer">
          <button class="btn btn-secondary" @click="$emit('close')">Abbrechen</button>
          <button class="btn btn-success" :disabled="localPassword.length < 8" @click="handleSave">
            Speichern
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  resettingPasswordFor: { type: Object, default: null },
})

const emit = defineEmits(['close', 'save'])

const localPassword = ref('')

watch(() => props.resettingPasswordFor, (val) => {
  if (val) localPassword.value = ''
})

const handleSave = () => {
  emit('save', localPassword.value)
}
</script>

<style scoped lang="scss">
.user-pw-reset-modal {
  --primary: #3b82f6;
  --success: #10b981;
  --border: #e2e8f0;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-card {
  background: white;
  width: 100%;
  max-width: 900px;
  max-height: 90vh;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.modal-card-form {
  max-width: 760px;
}

.modal-card-compact {
  max-width: 520px;
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  gap: 1rem;

  h3 {
    margin: 0;
    font-size: 1.25rem;
  }
}

.modal-subtitle {
  color: #64748b;
  margin-top: 0.25rem;
  font-size: 0.875rem;
}

.modal-form-content {
  padding: 1.5rem;
  overflow-y: auto;
}

.form-section {
  margin-bottom: 2rem;
}

.compact-section {
  margin-bottom: 1rem;
}

.form-group {
  margin-bottom: 1rem;

  label {
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    margin-bottom: 0.4rem;
    color: #1e293b;
  }

  input {
    width: 100%;
    padding: 0.6rem 0.8rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.95rem;

    &:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
  }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.btn {
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  border: none;

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.btn-success {
  background: var(--success);
  color: white;
}

.btn-secondary {
  background: #e2e8f0;
  color: #475569;
}

.modal-close {
  border: none;
  background: transparent;
  font-size: 1.6rem;
  line-height: 1;
  cursor: pointer;
  color: #6b7280;
}
</style>
