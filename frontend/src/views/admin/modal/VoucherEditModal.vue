<template>
  <div v-if="show" class="voucher-edit-modal modal-overlay">
    <div class="modal-card">
      <h3>🎫 Gutschein bearbeiten</h3>
      <div class="form-group">
        <label>Wert (€)</label>
        <input v-model="localForm.valueDisplay" type="number" min="0.01" step="0.01">
      </div>
      <div v-if="editingVoucher?.voucher_type === 'GIFT'" class="form-group">
        <label>Grund</label>
        <select v-model="localForm.reason">
          <option value="DYP_SIEGER">DYP-Sieger</option>
          <option value="PROMOTION">Promotion</option>
        </select>
      </div>
      <div class="form-group">
        <label>Beschreibung</label>
        <input v-model="localForm.description" type="text" maxlength="255">
      </div>
      <div v-if="editError" class="error-message">
        ❌ {{ editError }}
      </div>
      <div class="button-row">
        <button class="btn-primary" :disabled="updatingVoucher" @click="handleSave">
          {{ updatingVoucher ? '⏳ Speichert...' : '✓ Speichern' }}
        </button>
        <button class="btn-secondary" @click="$emit('close')">
          Abbrechen / Zurück
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  show: { type: Boolean, required: true },
  editingVoucher: { type: Object, default: null },
  initialEditForm: {
    type: Object,
    default: () => ({ valueDisplay: '', reason: 'DYP_SIEGER', description: '' }),
  },
  editError: { type: String, default: null },
  updatingVoucher: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'save'])

const localForm = ref({ ...props.initialEditForm })

watch(() => props.initialEditForm, (val) => {
  if (val) localForm.value = { ...val }
}, { deep: true })

const handleSave = () => {
  emit('save', { ...localForm.value })
}
</script>

<style scoped lang="scss">
.voucher-edit-modal {
  --primary: #3b82f6;
  --border: #e2e8f0;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);

  h3 {
    margin: 0 0 1.5rem;
    font-size: 1.2rem;
  }
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

  input,
  select {
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

.error-message {
  color: #dc2626;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.button-row {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-top: 1.5rem;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.btn-secondary {
  background: #e2e8f0;
  color: #475569;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}
</style>
