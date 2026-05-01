<template>
  <div
    v-if="show"
    class="confirmation-overlay"
  >
    <div class="confirmation-dialog">
      <h3>Abschöpfung</h3>
      <div class="filter-group">
        <label>Betrag in EUR</label>
        <input
          v-model="withdrawalForm.amount"
          type="number"
          min="0"
          step="0.01"
          class="form-input"
        >
      </div>
      <div class="selection-group">
        <label>Durchgeführt von</label>
        <button
          class="member-select-btn"
          @click="$emit('openUserPicker', 'withdrawalUserId')"
        >
          {{ getSelectedUserName(selectedWithdrawalUserId, 'Benutzer auswählen') }}
        </button>
      </div>
      <div class="filter-group">
        <label>Notiz (optional)</label>
        <input
          v-model="withdrawalForm.note"
          type="text"
          class="form-input"
          placeholder="z. B. Vereinskasse"
        >
      </div>
      <div class="confirmation-buttons">
        <button
          class="btn btn-secondary"
          @click="$emit('close')"
        >
          Abbrechen / Zurück
        </button>
        <button
          class="btn btn-warning"
          @click="$emit('submit')"
        >
          💸 Abschöpfen
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: { type: Boolean, required: true },
  withdrawalForm: { type: Object, required: true },
  selectedWithdrawalUserId: { type: [Number, String], default: null },
  getSelectedUserName: { type: Function, required: true },
})

defineEmits(['close', 'submit', 'openUserPicker'])
</script>

<style scoped lang="scss">
.confirmation-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1500;
}

.confirmation-dialog {
  background: #dde2e8;
  border-radius: 8px;
  padding: 2rem;
  max-width: 400px;
  width: min(100%, 520px);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  text-align: center;

  h3 {
    margin: 0 0 0.75rem 0;
    color: #333;
  }

  p {
    margin: 0 0 1.5rem 0;
    color: #666;
  }
}

.filter-group {
  margin-bottom: 1rem;
  text-align: left;

  label {
    display: block;
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: 0.35rem;
  }
}

.selection-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  text-align: left;

  label {
    font-weight: 600;
    font-size: 0.9rem;
  }
}

.form-input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  width: 100%;
}

.member-select-btn {
  padding: 0.75rem 0.9rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #f8fafc;
  text-align: left;
  font-weight: 600;
  color: #1e293b;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: #eef2f7;
    border-color: #94a3b8;
  }
}

.confirmation-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-secondary {
  background: #f5f5f5;
  color: #666;
  border: 1px solid #ddd;

  &:hover {
    background: #e0e0e0;
  }
}

.btn-warning {
  background: #ff9800;
  color: white;

  &:hover {
    background: #e65100;
  }
}
</style>
