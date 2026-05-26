<template>
  <div v-if="show && user" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card modal-compact">
      <header class="modal-header">
        <div>
          <h3>Passwort neu vergeben</h3>
          <p class="modal-subtitle">Neues Passwort für <strong>{{ user.username }}</strong> festlegen.</p>
        </div>
        <button class="modal-close" @click="$emit('close')">×</button>
      </header>

      <div class="modal-compact-layout">
        <div class="modal-scroller">
          <section class="form-section compact-section">
            <div class="form-group">
              <label for="reset-password">Neues Passwort</label>
              <input
                id="reset-password"
                :value="modelValue"
                type="password"
                minlength="8"
                placeholder="Mindestens 8 Zeichen"
                @input="$emit('update:modelValue', $event.target.value)"
              >
            </div>
          </section>
        </div>

        <footer class="modal-footer">
          <button class="btn btn-secondary" @click="$emit('close')">Abbrechen</button>
          <button class="btn btn-success" :disabled="modelValue.length < 8" @click="$emit('submit')">
            Speichern
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: { type: Boolean, required: true },
  user: { type: Object, default: null },
  modelValue: { type: String, default: '' },
})

defineEmits(['close', 'submit', 'update:modelValue'])
</script>

<style scoped lang="scss">
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
  --border: #e2e8f0;
  --success: #10b981;

  background: white;
  width: 100%;
  max-height: calc(100vh - 2rem);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.modal-compact {
  max-width: 680px;
}

.modal-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;

  h3 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: #1e293b;
  }

  .modal-subtitle {
    margin: 0.15rem 0 0 0;
    font-size: 0.85rem;
    color: #64748b;
  }
}

.modal-compact-layout {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-scroller {
  padding: 1.5rem;
  overflow-y: auto;
  max-height: calc(85vh - 120px);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-section {
  margin-bottom: 0;
}

.compact-section {
  margin-bottom: 0;
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

  input {
    width: 100%;
    padding: 0.55rem 0.75rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.9rem;
    color: #0f172a;

    &:focus {
      outline: none;
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
  }
}

.btn {
  padding: 0.55rem 1.1rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-size: 0.9rem;
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
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: #6b7280;
  padding: 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border);
  background: #f8fafc;
}

@media (max-width: 600px) {
  .modal-card {
    min-height: auto;
  }

  .btn {
    width: 100%;
  }
}
</style>
