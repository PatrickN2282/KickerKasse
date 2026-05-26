<template>
  <div v-if="show" class="modal-overlay">
    <div class="modal-dialog">
      <div class="modal-header">
        <div class="modal-header-title">
          <h3>🎫 Gutschein bearbeiten <span class="header-pipe">|</span> <span class="header-sub">Wert und Details ändern</span></h3>
        </div>
        <button class="close-btn" @click="$emit('close')">
          ✕
        </button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label>Wert (€)</label>
          <input
            :value="valueDisplay"
            type="number"
            min="0.01"
            step="0.01"
            @input="$emit('update:value-display', $event.target.value)"
          >
        </div>
        <div
          v-if="editingVoucher?.voucher_type === 'GIFT'"
          class="form-group"
        >
          <label>Grund</label>
          <select :value="reason" @change="$emit('update:reason', $event.target.value)">
            <option value="DYP_SIEGER">
              DYP-Sieger
            </option>
            <option value="PROMOTION">
              Promotion
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>Beschreibung</label>
          <input
            :value="description"
            type="text"
            maxlength="255"
            @input="$emit('update:description', $event.target.value)"
          >
        </div>
        <div
          v-if="editError"
          class="error-message"
        >
          ❌ {{ editError }}
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn-secondary" @click="$emit('close')">
          Abbrechen / Zurück
        </button>
        <button class="btn-primary" :disabled="updatingVoucher" @click="$emit('save')">
          {{ updatingVoucher ? '⏳ Speichert...' : '✓ Speichern' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: { type: Boolean, required: true },
  editingVoucher: { type: Object, default: null },
  valueDisplay: { type: String, default: '' },
  reason: { type: String, default: 'DYP_SIEGER' },
  description: { type: String, default: '' },
  editError: { type: String, default: '' },
  updatingVoucher: { type: Boolean, default: false },
})

defineEmits(['close', 'save', 'update:value-display', 'update:reason', 'update:description'])
</script>

<style scoped lang="scss">
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(20, 24, 30, 0.45);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-dialog {
  width: min(520px, calc(100vw - 2rem));
  background: #ffffff;
  border-radius: 16px;
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

.form-group {
  margin-bottom: 0.85rem;

  label {
    display: block;
    font-weight: 600;
    margin-bottom: 0.35rem;
    color: #334155;
  }

  input,
  select {
    width: 100%;
    padding: 0.55rem 0.75rem;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    font-size: 0.9rem;
  }
}

.error-message {
  margin-top: 0.75rem;
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  border: 1px solid #fecaca;
  background: #fee2e2;
  color: #991b1b;
  font-size: 0.85rem;
}

.btn-primary,
.btn-secondary {
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 0.6rem 0.9rem;
  cursor: pointer;
  font-size: 0.88rem;
  font-weight: 700;
  transition: all 0.15s ease;
}

.btn-primary {
  background: #0275d8;
  color: white;

  &:hover:not(:disabled) {
    background: #025aa5;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.btn-secondary {
  background: #f1f5f9;
  border-color: #cbd5e1;
  color: #334155;

  &:hover:not(:disabled) {
    background: #e2e8f0;
  }
}
</style>
