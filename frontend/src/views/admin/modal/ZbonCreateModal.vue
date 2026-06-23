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
        <!-- Info-Zeile 1: Ablaufschritte -->
        <div class="kk-info-bar kk-info-bar--steps">
          <span class="kk-step">① Kassenprüfer wählen</span>
          <span class="kk-step-sep">→</span>
          <span class="kk-step">② Kasse zählen</span>
          <span class="kk-step-sep">→</span>
          <span class="kk-step">③ ggf. Abschöpfung</span>
          <span class="kk-step-sep">→</span>
          <span class="kk-step">④ Kassenbericht erstellen</span>
        </div>
        <!-- Info-Zeile 2: E-Mail-Hinweis -->
        <div
          v-if="autoEmailOnCreate"
          class="kk-info-bar kk-info-bar--mail"
        >
          📧 <strong>E-Mail-Versand: aktiv</strong>&nbsp;|&nbsp;Bericht wird nach Erstellung automatisch versendet.
        </div>

        <!-- Haupt-Spalten: Personen + Eingabe links | Finanzen rechts -->
        <div class="kk-main-grid">
          <!-- Linke Spalte: Benutzerauswahl + Kasseneingabe -->
          <div class="kk-col-left">
            <div class="kk-section-label">Benutzer</div>
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

            <div class="kk-section-label kk-section-label--spaced">Kassenzählung</div>
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

            <div
              v-if="showDifferenceReason"
              class="kk-counted-input"
            >
              <label>Grund für die Differenz <span class="kk-label-warn">⚠ Pflichtfeld</span></label>
              <textarea
                :value="differenceReason"
                class="form-input"
                rows="3"
                placeholder="Grund für die Abweichung zwischen SOLL und IST …"
                @input="$emit('update:difference-reason', $event.target.value)"
              />
              <small class="kk-hint-text kk-hint-text--warning">Diese Angabe wird auf dem Kassenbericht vermerkt.</small>
            </div>

            <small
              v-if="finalCashInvalid"
              class="kk-warning-text"
            >
              ⚠ Der gezählte Bestand darf nicht kleiner als die im Modal vorgenommene Abschöpfung sein.
            </small>
          </div>

          <!-- Rechte Spalte: Saldo-Übersicht + Ergebnis -->
          <div class="kk-col-right">
            <div class="kk-section-label">Saldo-Übersicht</div>
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
              <div class="kk-balance-row kk-balance-row--highlight">
                <span>Neuer Barbestand Soll</span>
                <strong>{{ cashCalculatedDisplay }}</strong>
              </div>
            </div>

            <div class="kk-section-label kk-section-label--spaced">Ergebnis</div>
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
          </div>
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
  showDifferenceReason: { type: Boolean, default: false },
  differenceReason: { type: String, default: '' },
  newWithdrawalsDisplay: { type: String, default: '0,00 €' },
  newCashBalanceDisplay: { type: String, default: '-' },
  differenceDisplay: { type: String, default: '-' },
  finalCashInvalid: { type: Boolean, default: false },
  canCreate: { type: Boolean, default: false },
  autoEmailOnCreate: { type: Boolean, default: false },
})

defineEmits([
  'close',
  'open-user-picker',
  'open-member-picker',
  'clear-verifier',
  'update:counted-cash',
  'update:difference-reason',
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
  align-items: center;
  justify-content: center;
  z-index: 1500;
  padding: 1.5rem;
  /* kein overflow-y: auto hier – Scroll bleibt im Body */
}

.kk-dialog {
  background: #ffffff;
  border-radius: 20px;
  width: min(85vw, 1200px);
  max-height: min(85vh, 900px);
  display: flex;
  flex-direction: column;
  /* overflow: hidden verhindert, dass Footer wegscrollt */
  overflow: hidden;
  box-shadow:
    0 32px 64px rgba(15, 23, 42, 0.28),
    0 0 0 1px rgba(15, 23, 42, 0.06);
}

.kk-dialog__header {
  padding: 1rem 1.4rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-shrink: 0;
  border-bottom: 1px solid #f1f5f9;
}

/* Body scrollt intern – Header und Footer bleiben fixiert */
.kk-dialog__body {
  padding: 1rem 1.4rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  /* Padding-bottom damit der letzte Inhalt nicht direkt am Footer klebt */
  padding-bottom: 0.5rem;
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

/* ── Info-Zeilen: jeweils volle Breite, untereinander ── */
.kk-info-bar {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  border-radius: 10px;
  padding: 0.5rem 1rem;
  font-size: 0.84rem;
  font-weight: 500;
  flex-shrink: 0;
  width: 100%;
  box-sizing: border-box;
}

.kk-info-bar--steps {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1e40af;
}

.kk-info-bar--mail {
  background: #ecfeff;
  border: 1px solid #99f6e4;
  color: #0f766e;

  strong {
    font-weight: 700;
  }
}

.kk-step {
  font-weight: 600;
  white-space: nowrap;
}

.kk-step-sep {
  color: #93c5fd;
  font-weight: 400;
}

/* ── Haupt-Grid ── */
.kk-main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
  flex: 1;
  min-height: 0;
}

.kk-col-left {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
  min-height: 0;
  overflow-y: auto;
}

.kk-col-right {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
  /* Rechte Spalte scrollt nicht mit – bleibt immer sichtbar */
  position: sticky;
  top: 0;
  align-self: start;
}

/* ── Section Labels ── */
.kk-section-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.kk-section-label--spaced {
  margin-top: 0.4rem;
}

.kk-label-warn {
  font-size: 0.75rem;
  color: #b45309;
  font-weight: 700;
  margin-left: 0.4rem;
  text-transform: none;
  letter-spacing: 0;
}

/* ── Formular-Gruppen ── */
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
  padding: 0.7rem 1rem;
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
  padding: 0.7rem 0.85rem;
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

/* ── Saldo-Box ── */
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

  &.kk-balance-row--highlight {
    background: #f1f5f9;

    strong {
      color: #0f766e;
    }
  }

  strong {
    color: #1e293b;
    font-weight: 700;

    &.warning {
      color: #b45309;
    }
  }
}

/* ── Kasseneingabe ── */
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
    font-size: 1.3rem;
    padding: 0.7rem 1rem;
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

  .form-input {
    width: 100%;
    border: 1px solid #dbe3ee;
    border-radius: 10px;
    padding: 0.75rem 0.85rem;
    font-size: 0.98rem;

    &:focus {
      outline: none;
      border-color: #0f766e;
    }
  }
}

.kk-hint-text {
  color: #64748b;
  font-size: 0.8rem;
}

.kk-hint-text--warning {
  color: #b45309;
  font-weight: 600;
}

/* ── Ergebnis-Box ── */
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
}

/* ── Buttons ── */
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

/* ── Responsive ── */
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

  .kk-main-grid {
    grid-template-columns: 1fr;
  }

  .kk-info-bar {
    flex-wrap: wrap;
    white-space: normal;
  }

  .kk-info-steps {
    flex-wrap: wrap;
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