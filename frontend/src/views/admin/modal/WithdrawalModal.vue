<template>
  <div
    v-if="show"
    class="confirmation-overlay"
  >
    <div class="kk-dialog kk-dialog--narrow">
      <div class="kk-dialog__header">
        <div>
          <h3>💸 Abschöpfung durchführen</h3>
          <p class="kk-dialog__subtitle">
            Barbetrag aus der Kasse entnehmen
          </p>
        </div>
        <button
          class="kk-dialog__close"
          @click="$emit('close')"
        >
          ✕
        </button>
      </div>

      <div class="kk-dialog__body kk-withdrawal-body">
        <div class="kk-form-group">
          <label>Betrag (€)</label>
          <input
            :value="amount"
            type="number"
            min="0"
            step="0.01"
            class="form-input large"
            placeholder="0,00"
            @input="$emit('update:amount', $event.target.value)"
          >
        </div>

        <div class="kk-form-group">
          <label>Durchgeführt von</label>
          <button
            class="kk-select-btn"
            @click="$emit('open-user-picker')"
          >
            {{ selectedUserName || 'Benutzer auswählen …' }}
          </button>
        </div>

        <div class="kk-form-group">
          <label>Notiz (optional)</label>
          <input
            :value="note"
            type="text"
            class="form-input"
            placeholder="z. B. Vereinskasse, Bank …"
            @input="$emit('update:note', $event.target.value)"
          >
        </div>
      </div>

      <div class="kk-dialog__footer">
        <button
          class="btn btn-secondary"
          @click="$emit('close')"
        >
          Abbrechen
        </button>
        <button
          class="btn btn-warning"
          @click="$emit('confirm')"
        >
          Abschöpfen
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: { type: Boolean, required: true },
  amount: { type: [String, Number], default: '' },
  note: { type: String, default: '' },
  selectedUserName: { type: String, default: '' },
})

defineEmits(['close', 'confirm', 'open-user-picker', 'update:amount', 'update:note'])
</script>

<style scoped lang="scss">
.confirmation-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1500;
  padding: 1.5rem;
  overflow-y: auto;
}

.kk-dialog {
  background: #ffffff;
  border-radius: 20px;
  width: min(80vw, 1100px);
  max-height: min(82vh, 900px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow:
    0 32px 64px rgba(15, 23, 42, 0.28),
    0 0 0 1px rgba(15, 23, 42, 0.06);
}

.kk-dialog--narrow {
  width: min(80vw, 560px);
}

.kk-dialog__header {
  padding: 1rem 1.4rem;
  background: #0f766e;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  flex-shrink: 0;

  h3 {
    margin: 0;
    color: #ffffff;
    font-size: 1.05rem;
    font-weight: 600;
    line-height: 1.3;
  }
}

.kk-dialog__subtitle {
  margin: 0.3rem 0 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.82rem;
}

.kk-dialog__close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
  font-size: 1rem;
  cursor: pointer;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  transition: background 0.15s;

  &:hover {
    background: rgba(255, 255, 255, 0.28);
  }
}

.kk-dialog__body {
  padding: 1.4rem;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.kk-withdrawal-body {
  gap: 0.85rem;
}

.kk-dialog__footer {
  padding: 1rem 1.4rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.65rem;
  flex-shrink: 0;
  background: #f8fafc;
  flex-wrap: wrap;
}

.kk-form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  text-align: left;

  label {
    font-size: 0.8rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
}

.kk-select-btn {
  width: 100%;
  padding: 0.75rem 1rem;
  text-align: left;
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.9rem;
  color: #1e293b;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    background: #f1f5f9;
    border-color: #94a3b8;
  }
}

.form-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;

  &.large {
    font-size: 1.35rem;
    padding: 0.9rem 1rem;
    font-weight: 600;
    width: 100%;
  }
}

.btn {
  padding: 0.65rem 1.25rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;

  &:hover {
    background: #e2e8f0;
  }
}

.btn-warning {
  background: #ff9800;
  color: white;

  &:hover {
    background: #e65100;
  }
}

@media (max-width: 640px) {
  .confirmation-overlay {
    padding: 0.75rem;
    align-items: flex-start;
  }

  .kk-dialog {
    width: 100%;
    max-height: calc(100dvh - 1.5rem);
    border-radius: 14px;
  }

  .kk-dialog__footer {
    flex-direction: column;

    .btn {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>
