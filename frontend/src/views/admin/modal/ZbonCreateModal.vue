<template>
  <div
    v-if="show"
    class="confirmation-overlay"
  >
    <div class="kk-dialog">
      <div class="kk-dialog__header">
        <div>
          <h3>🧾 Kassenbericht erstellen</h3>
          <p class="kk-dialog__subtitle">
            Kassenabschluss durchführen und Z-Bon erstellen
          </p>
        </div>
        <button
          class="kk-dialog__close"
          @click="$emit('close')"
        >
          ✕
        </button>
      </div>

      <div class="kk-dialog__body">
        <!-- Ablauf-Hinweis -->
        <div class="kk-info-box">
          Kassenprüfer wählen → Kasse zählen → ggf. Abschöpfung → Kassenbericht erstellen
        </div>

        <!-- Benutzer-Auswahl -->
        <div class="kk-form-grid">
          <div class="kk-form-group">
            <label>Erstellt von</label>
            <button
              class="kk-select-btn"
              @click="$emit('open-user-picker', 'createdByUserId')"
            >
              {{ createdByUserName || 'Benutzer auswählen …' }}
            </button>
          </div>
          <div class="kk-form-group">
            <label>Kassenprüfer</label>
            <div class="kk-selection-row">
              <button
                class="kk-select-btn"
                @click="$emit('open-member-picker', 'verifiedByUserId')"
              >
                {{ verifiedByMemberName || 'Mitglied auswählen …' }}
              </button>
              <button
                v-if="verifiedByMemberName"
                class="kk-clear-btn"
                @click="$emit('clear-verifier')"
              >
                Entfernen
              </button>
            </div>
          </div>
        </div>

        <!-- Saldo-Übersicht -->
        <div class="kk-balance-box">
          <div class="kk-balance-row">
            <span>Vorheriger Barbestand</span>
            <strong>{{ openingBalanceDisplay }}</strong>
          </div>
          <div class="kk-balance-row">
            <span>Buchungs-Range</span>
            <strong>{{ receiptLabel }}</strong>
          </div>
          <div class="kk-balance-row">
            <span>Abschöpfungen Zeitraum</span>
            <strong class="warning">{{ withdrawalTotalDisplay }}</strong>
          </div>
          <div class="kk-balance-row">
            <span>Neuer Barbestand Soll</span>
            <strong>{{ cashCalculatedDisplay }}</strong>
          </div>
        </div>

        <!-- Kassenbestand eingeben -->
        <div class="kk-counted-input">
          <label>Gezählter Kassenbestand (€)</label>
          <input
            :value="countedCash"
            type="number"
            min="0"
            step="0.01"
            class="form-input large"
            placeholder="0,00"
            @input="$emit('update:counted-cash', $event.target.value)"
          >
        </div>

        <!-- Ergebnis -->
        <div class="kk-result-box">
          <div class="kk-result-row">
            <span>Abschöpfung im Modal</span>
            <strong>{{ newWithdrawalsDisplay }}</strong>
          </div>
          <div class="kk-result-row">
            <span>Neuer Ist-Bestand</span>
            <strong>{{ newCashBalanceDisplay }}</strong>
          </div>
          <div
            class="kk-result-row"
            :class="{ error: finalCashInvalid }"
          >
            <span>Differenz</span>
            <strong>{{ differenceDisplay }}</strong>
          </div>
        </div>

        <small
          v-if="finalCashInvalid"
          class="kk-warning-text"
        >
          Der gezählte Bestand darf nicht kleiner als die im Modal vorgenommene Abschöpfung sein.
        </small>
      </div>

      <div class="kk-dialog__footer">
        <button
          class="btn btn-secondary"
          @click="$emit('close')"
        >
          Abbrechen
        </button>
        <button
          class="btn btn-info"
          @click="$emit('open-cash-counter')"
        >
          💰 Kasse zählen
        </button>
        <button
          class="btn btn-warning"
          @click="$emit('open-withdrawal')"
        >
          💸 Abschöpfung
        </button>
        <button
          :class="['btn', canCreate ? 'btn-ready' : 'btn-disabled']"
          :disabled="!canCreate"
          @click="$emit('request-create')"
        >
          ✓ Kassenbericht erstellen
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: { type: Boolean, required: true },
  createdByUserName: { type: String, default: '' },
  verifiedByMemberName: { type: String, default: '' },
  openingBalanceDisplay: { type: String, default: '-' },
  receiptLabel: { type: String, default: 'keine Belege' },
  withdrawalTotalDisplay: { type: String, default: '0,00 €' },
  cashCalculatedDisplay: { type: String, default: '-' },
  countedCash: { type: [String, Number], default: '' },
  newWithdrawalsDisplay: { type: String, default: '0,00 €' },
  newCashBalanceDisplay: { type: String, default: '-' },
  differenceDisplay: { type: String, default: '-' },
  finalCashInvalid: { type: Boolean, default: false },
  canCreate: { type: Boolean, default: false },
})

defineEmits([
  'close',
  'open-user-picker',
  'open-member-picker',
  'clear-verifier',
  'update:counted-cash',
  'open-cash-counter',
  'open-withdrawal',
  'request-create',
])
</script>

<style scoped lang="scss">
.confirmation-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  z-index: 1500;
  padding: 1.5rem;
  overflow-y: auto;
}

.kk-dialog {
  background: #ffffff;
  border-radius: 20px;
  width: min(80vw, 1100px);
  max-height: none !important;
  display: flex;
  flex-direction: column;
  overflow: visible !important;
  box-shadow:
    0 32px 64px rgba(15, 23, 42, 0.28),
    0 0 0 1px rgba(15, 23, 42, 0.06);
  margin: auto;
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
  overflow-y: visible !important;
  flex: 0 0 auto !important;
  min-height: unset !important;
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
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

.kk-info-box {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1e40af;
  padding: 0.85rem 1.1rem;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 500;
  line-height: 1.5;
}

.kk-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;

  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
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

.kk-clear-btn {
  padding: 0.75rem 0.85rem;
  background: transparent;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  color: #94a3b8;
  font-size: 0.85rem;
  cursor: pointer;
  white-space: nowrap;

  &:hover {
    background: #f1f5f9;
    color: #64748b;
  }
}

.kk-selection-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.kk-balance-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
}

.kk-balance-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.55rem 1rem;
  font-size: 0.88rem;
  border-bottom: 1px solid #f1f5f9;
  color: #475569;

  &:last-child {
    border-bottom: none;
  }

  strong {
    color: #1e293b;
    font-weight: 700;

    &.warning {
      color: #b45309;
    }
  }
}

.kk-counted-input {
  label {
    display: block;
    font-size: 0.8rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
  }

  .form-input.large {
    font-size: 1.5rem;
    padding: 0.85rem 1.1rem;
    font-weight: 700;
    width: 100%;
    border-radius: 10px;
    border: 1.5px solid #cbd5e1;
    transition: border-color 0.15s;

    &:focus {
      outline: none;
      border-color: #0f766e;
    }
  }
}

.kk-result-box {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 12px;
  overflow: hidden;
}

.kk-result-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.55rem 1rem;
  font-size: 0.9rem;
  border-bottom: 1px solid #dcfce7;
  color: #166534;

  &:last-child {
    border-bottom: none;
  }

  strong {
    font-weight: 700;
  }

  &.error {
    background: #fff1f2;
    color: #b91c1c;

    strong {
      color: #b91c1c;
    }
  }
}

.kk-warning-text {
  display: block;
  color: #b91c1c;
  font-size: 0.82rem;
  font-weight: 600;
  margin-top: -0.5rem;
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

.btn-info {
  background: #00bcd4;
  color: white;

  &:hover {
    background: #0097a7;
  }
}

.btn-warning {
  background: #ff9800;
  color: white;

  &:hover {
    background: #e65100;
  }
}

.btn-ready {
  background: #2e7d32;
  color: white;
}

.btn-disabled {
  background: #9ca3af;
  color: white;
  cursor: not-allowed;
}

@media (max-width: 900px) {
  .kk-dialog {
    width: min(94vw, 1100px);
    max-height: none !important;
    border-radius: 16px;
  }
}

@media (max-width: 640px) {
  .confirmation-overlay {
    padding: 0.75rem;
    align-items: flex-start;
  }

  .kk-dialog {
    width: 100%;
    max-height: none !important;
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
