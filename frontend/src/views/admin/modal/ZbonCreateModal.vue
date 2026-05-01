<template>
  <div
    v-if="show"
    class="confirmation-overlay"
  >
    <div class="confirmation-dialog zbon-create-dialog">
      <h3>Z-Bon erstellen</h3>
      <div class="zbon-create-layout">
        <div class="zbon-create-main">
          <div class="zbon-note-box">
            Kassenprüfer wählen → Kassenbestand zählen → ggf. Abschöpfung vornehmen → mit neuem Kassenbestand abgleichen → Z-Bon erstellen
          </div>
          <div class="selection-grid">
            <div class="selection-group">
              <label>Erstellt von</label>
              <button
                class="member-select-btn"
                @click="$emit('openUserPicker', 'createdByUserId')"
              >
                {{ getSelectedUserName(zbonForm.createdByUserId, 'Benutzer auswählen') }}
              </button>
            </div>
            <div class="selection-group">
              <label>Kassenprüfer</label>
              <div class="selection-actions">
                <button
                  class="member-select-btn"
                  @click="$emit('openMemberPicker', 'verifiedByUserId')"
                >
                  {{ getSelectedVerifierName(zbonForm.verifiedByUserId, 'Mitglied auswählen') }}
                </button>
                <button
                  v-if="zbonForm.verifiedByUserId"
                  class="clear-selection-btn"
                  @click="$emit('clearVerifier')"
                >
                  Entfernen
                </button>
              </div>
            </div>
          </div>
          <div class="summary-grid compact-summary-grid">
            <div class="summary-card modal-summary-card">
              <div class="card-label">
                Vorheriger Barbestand
              </div>
              <div class="card-value">
                {{ formatEuroValue(dailyStats.opening_balance) }}
              </div>
            </div>
            <div class="summary-card modal-summary-card">
              <div class="card-label">
                Buchungs-Range
              </div>
              <div class="card-value">
                {{ currentReceiptLabel }}
              </div>
            </div>
            <div class="summary-card modal-summary-card">
              <div class="card-label">
                Abschöpfungen Zeitraum
              </div>
              <div class="card-value">
                {{ formatPrice(zbonModalWithdrawalTotalCents) }}
              </div>
            </div>
            <div class="summary-card modal-summary-card">
              <div class="card-label">
                Neuer Barbestand Soll
              </div>
              <div class="card-value">
                {{ zbonModalCashCalculatedDisplay }}
              </div>
            </div>
          </div>
          <div class="zbon-balance-group">
            <div class="selection-group zbon-counted-group">
              <label>Gezählter Kassenbestand</label>
              <input
                v-model="localCountedCash"
                type="number"
                min="0"
                step="0.01"
                class="form-input"
                placeholder="0,00"
              >
            </div>
            <div class="summary-grid zbon-side-summary">
              <div class="summary-card modal-summary-card">
                <div class="card-label">
                  Abschöpfung im Modal
                </div>
                <div class="card-value">
                  {{ formatPrice(newWithdrawalsCents) }}
                </div>
              </div>
              <div class="summary-card modal-summary-card">
                <div class="card-label">
                  Neuer Ist-Bestand
                </div>
                <div class="card-value">
                  {{ zbonNewCashBalanceDisplay }}
                </div>
              </div>
              <div class="summary-card modal-summary-card">
                <div class="card-label">
                  Differenz
                </div>
                <div class="card-value">
                  {{ zbonDifferenceDisplay }}
                </div>
              </div>
            </div>
            <small
              v-if="zbonFinalCashInvalid"
              class="zbon-warning-text"
            >
              Der gezählte Bestand darf nicht kleiner als die im Modal vorgenommenen Abschöpfung sein.
            </small>
          </div>
        </div>
        <div class="zbon-create-side">
          <div class="confirmation-buttons zbon-create-buttons">
            <button
              class="btn btn-info"
              @click="$emit('openCashCounterModal')"
            >
              💰 Kasse zählen
            </button>
            <button
              class="btn btn-warning"
              @click="$emit('openWithdrawalModal')"
            >
              💸 Abschöpfung
            </button>
            <button
              :class="['btn', canCreateZbon ? 'btn-ready' : 'btn-disabled']"
              :disabled="!canCreateZbon"
              @click="$emit('requestZBonCreate')"
            >
              ✓ Z-Bon erstellen
            </button>
            <button
              class="btn btn-secondary"
              @click="$emit('close')"
            >
              Abbrechen / Zurück
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  show: { type: Boolean, required: true },
  zbonForm: { type: Object, required: true },
  zbonCountedCash: { type: String, default: '' },
  dailyStats: { type: Object, required: true },
  currentReceiptLabel: { type: String, default: '' },
  zbonModalCashCalculatedDisplay: { type: String, default: '' },
  zbonModalWithdrawalTotalCents: { type: Number, default: 0 },
  newWithdrawalsCents: { type: Number, default: 0 },
  zbonNewCashBalanceDisplay: { type: String, default: '' },
  zbonDifferenceDisplay: { type: String, default: '' },
  zbonFinalCashInvalid: { type: Boolean, default: false },
  canCreateZbon: { type: Boolean, default: false },
  formatPrice: { type: Function, required: true },
  formatEuroValue: { type: Function, required: true },
  getSelectedUserName: { type: Function, required: true },
  getSelectedVerifierName: { type: Function, required: true },
})

const emit = defineEmits([
  'openUserPicker',
  'openMemberPicker',
  'clearVerifier',
  'openCashCounterModal',
  'openWithdrawalModal',
  'requestZBonCreate',
  'close',
  'update:zbonCountedCash',
])

const localCountedCash = ref(props.zbonCountedCash)

watch(localCountedCash, (val) => {
  emit('update:zbonCountedCash', val)
})

watch(() => props.zbonCountedCash, (val) => {
  if (val !== localCountedCash.value) localCountedCash.value = val
})
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

.zbon-create-dialog {
  max-width: min(92vw, 1080px);
  width: min(92vw, 1080px);
  text-align: left;
}

.zbon-create-layout {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr);
  gap: 1rem;
  align-items: start;
}

.zbon-create-main {
  min-width: 0;
}

.zbon-note-box {
  margin-bottom: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  background: #eef4ff;
  border: 1px solid #c8d8f2;
  color: #22446b;
  font-weight: 500;
}

.selection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem;
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

.selection-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
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

.clear-selection-btn {
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #475569;
  border-radius: 8px;
  padding: 0.75rem 0.9rem;
  cursor: pointer;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.compact-summary-grid {
  margin-bottom: 0;
  gap: 0.75rem;
}

.zbon-side-summary {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.summary-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(102, 126, 234, 0.2);

  .card-label {
    font-size: 0.9rem;
    opacity: 0.9;
    margin-bottom: 0.5rem;
  }

  .card-value {
    font-size: 1.8rem;
    font-weight: bold;
  }
}

.modal-summary-card {
  padding: 1.15rem;

  .card-label {
    font-size: 0.82rem;
    margin-bottom: 0.35rem;
  }

  .card-value {
    font-size: 1.45rem;
    line-height: 1.2;
  }
}

.zbon-balance-group {
  padding: 0.9rem;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid #cbd5e1;
}

.zbon-counted-group {
  margin-bottom: 0.75rem;
}

.form-input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  width: 100%;
}

.zbon-warning-text {
  display: block;
  margin-top: 0.75rem;
  color: #b91c1c;
  font-weight: 600;
}

.zbon-create-side {
  min-width: 0;
}

.confirmation-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.zbon-create-buttons {
  flex-direction: column;
  align-items: stretch;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
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

.btn-secondary {
  background: #f5f5f5;
  color: #666;
  border: 1px solid #ddd;

  &:hover {
    background: #e0e0e0;
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
  .zbon-create-layout {
    grid-template-columns: 1fr;
  }

  .zbon-side-summary {
    grid-template-columns: 1fr;
  }

  .selection-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
