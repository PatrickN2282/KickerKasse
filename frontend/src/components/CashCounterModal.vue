<template>
  <div v-if="show" class="modal-overlay">
    <div class="modal-dialog">
      <div class="modal-header">
        <div>
          <h3>Kassenzählung</h3>
          <p class="subtitle">Alle Münzen und Scheine im Kassenbestand erfassen</p>
        </div>
        <button @click="$emit('close')" class="close-btn">✕</button>
      </div>

      <div class="modal-content">
        <div class="cash-counter">
          <section class="section">
            <h4>Münzen</h4>
            <div class="counter-list">
              <div
                v-for="denomination in coinDenominations"
                :key="`coin-${denomination}`"
                class="counter-item"
              >
                <label>{{ formatDenomination(denomination) }}</label>
                <div class="input-group">
                  <button @click="decrementCoin(denomination)" class="btn-qty">−</button>
                  <input
                    v-model.number="cashCount.coins[denomination]"
                    type="number"
                    min="0"
                    class="qty-input"
                  />
                  <button @click="incrementCoin(denomination)" class="btn-qty">+</button>
                </div>
                <div class="subtotal">
                  {{ formatCurrency(cashCount.coins[denomination] * denomination) }}
                </div>
              </div>
            </div>
          </section>

          <section class="section">
            <h4>Scheine</h4>
            <div class="counter-list">
              <div
                v-for="denomination in noteDenominations"
                :key="`note-${denomination}`"
                class="counter-item"
              >
                <label>{{ formatDenomination(denomination) }}</label>
                <div class="input-group">
                  <button @click="decrementNote(denomination)" class="btn-qty">−</button>
                  <input
                    v-model.number="cashCount.notes[denomination]"
                    type="number"
                    min="0"
                    class="qty-input"
                  />
                  <button @click="incrementNote(denomination)" class="btn-qty">+</button>
                </div>
                <div class="subtotal">
                  {{ formatCurrency(cashCount.notes[denomination] * denomination) }}
                </div>
              </div>
            </div>
          </section>

          <div class="total-section">
            <div class="total-item">
              <span>Münzen Summe:</span>
              <strong>{{ formatCurrency(coinTotal) }}</strong>
            </div>
            <div class="total-item">
              <span>Scheine Summe:</span>
              <strong>{{ formatCurrency(noteTotal) }}</strong>
            </div>
            <div class="total-item highlight">
              <span>Gesamtbetrag:</span>
              <strong>{{ formatCurrency(totalCashCount) }}</strong>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="reset" class="btn btn-secondary">Zurücksetzen</button>
        <button @click="cancel" class="btn btn-secondary">Abbrechen / Zurück</button>
        <button @click="confirm" class="btn btn-primary">✓ Bestätigen</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'confirm'])

// German coin denominations in EUR
const coinDenominations = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2]

// German note denominations in EUR
const noteDenominations = [5, 10, 20, 50, 100, 200, 500]

// Cash count state
const cashCount = ref({
  coins: {
    '0.01': 0,
    '0.02': 0,
    '0.05': 0,
    '0.1': 0,
    '0.2': 0,
    '0.5': 0,
    '1': 0,
    '2': 0,
  },
  notes: {
    '5': 0,
    '10': 0,
    '20': 0,
    '50': 0,
    '100': 0,
    '200': 0,
    '500': 0,
  },
})

const coinTotal = computed(() => {
  return Object.entries(cashCount.value.coins).reduce((sum, [denom, count]) => {
    return sum + (parseFloat(denom) * count)
  }, 0)
})

const noteTotal = computed(() => {
  return Object.entries(cashCount.value.notes).reduce((sum, [denom, count]) => {
    return sum + (parseFloat(denom) * count)
  }, 0)
})

const totalCashCount = computed(() => {
  return coinTotal.value + noteTotal.value
})

const formatCurrency = (value) => {
  return `${Number(value).toFixed(2)} EUR`
}

const formatDenomination = (value) => {
  return `${Number(value).toFixed(value < 1 ? 2 : 0)} EUR`
}

const incrementCoin = (denom) => {
  const key = denom.toString()
  cashCount.value.coins[key]++
}

const decrementCoin = (denom) => {
  const key = denom.toString()
  if (cashCount.value.coins[key] > 0) {
    cashCount.value.coins[key]--
  }
}

const incrementNote = (denom) => {
  const key = denom.toString()
  cashCount.value.notes[key]++
}

const decrementNote = (denom) => {
  const key = denom.toString()
  if (cashCount.value.notes[key] > 0) {
    cashCount.value.notes[key]--
  }
}

const reset = () => {
  cashCount.value = {
    coins: {
      '0.01': 0,
      '0.02': 0,
      '0.05': 0,
      '0.1': 0,
      '0.2': 0,
      '0.5': 0,
      '1': 0,
      '2': 0,
    },
    notes: {
      '5': 0,
      '10': 0,
      '20': 0,
      '50': 0,
      '100': 0,
      '200': 0,
      '500': 0,
    },
  }
}

const cancel = () => {
  reset()
  emit('close')
}

const confirm = () => {
  emit('confirm', {
    coins: cashCount.value.coins,
    notes: cashCount.value.notes,
    total: totalCashCount.value,
  })
  reset()
  emit('close')
}
</script>

<style scoped lang="scss">
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1.25rem;
}

.modal-dialog {
  background: #ffffff;
  border-radius: 16px;
  width: 100%;
  max-width: 980px;
  max-height: 92vh;
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

  h3 {
    margin: 0;
    color: #ffffff;
    font-size: 1.1rem;
  }

  .subtitle {
    margin: 0.35rem 0 0;
    color: rgba(255, 255, 255, 0.9);
    font-size: 0.85rem;
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

    &:hover {
      background: rgba(255, 255, 255, 0.3);
    }
  }
}

.modal-content {
  padding: 1rem 1.25rem;
  overflow-y: auto;
  flex: 1;
}

.cash-counter {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.section {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.85rem;
  background: #f8fafc;

  h4 {
    margin: 0 0 0.7rem 0;
    color: #0f172a;
    font-size: 0.9rem;
    font-weight: 600;
  }
}

.counter-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.counter-item {
  display: grid;
  grid-template-columns: minmax(70px, 1fr) minmax(140px, 1fr) minmax(90px, auto);
  align-items: center;
  gap: 0.6rem;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 0.45rem 0.55rem;

  label {
    font-weight: 600;
    color: #1f2937;
    font-size: 0.83rem;
  }

  .input-group {
    display: flex;
    gap: 0.35rem;
    align-items: center;

    .btn-qty {
      width: 30px;
      height: 30px;
      border: 1px solid #cbd5e1;
      background: #f8fafc;
      cursor: pointer;
      border-radius: 8px;
      font-weight: bold;
      transition: all 0.2s;

      &:hover {
        background: #e2e8f0;
        border-color: #94a3b8;
      }

      &:active {
        background: #cbd5e1;
      }
    }

    .qty-input {
      flex: 1;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      text-align: center;
      font-size: 0.9rem;
      padding: 0.35rem;
      font-weight: 600;
      min-width: 58px;

      &:focus {
        outline: none;
        border-color: #0ea5e9;
        box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.16);
      }
    }
  }

  .subtotal {
    text-align: right;
    font-weight: 600;
    color: #0f766e;
    font-size: 0.82rem;
  }
}

.total-section {
  grid-column: 1 / -1;
  margin-top: 0.2rem;
  padding-top: 0.2rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.total-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.7rem 0.85rem;
  background: #f1f5f9;
  border-radius: 10px;
  min-width: 220px;
  flex: 1;

  span {
    color: #334155;
    font-size: 0.86rem;
  }

  strong {
    color: #0f172a;
    font-size: 0.92rem;
  }

  &.highlight {
    background: #dcfce7;
    border: 1px solid #86efac;

    span {
      color: #166534;
      font-weight: 600;
    }

    strong {
      color: #166534;
      font-size: 1.06rem;
    }
  }
}

.modal-footer {
  padding: 0.95rem 1.25rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  background: #ffffff;

  .btn {
    padding: 0.65rem 1.2rem;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      transform: translateY(-1px);
    }

    &.btn-primary {
      background: #059669;
      color: white;

      &:hover {
        background: #047857;
      }
    }

    &.btn-secondary {
      background: #f8fafc;
      color: #475569;
      border: 1px solid #cbd5e1;

      &:hover {
        background: #e2e8f0;
      }
    }
  }
}

@media (max-width: 900px) {
  .modal-dialog {
    max-height: 96vh;
  }

  .cash-counter {
    grid-template-columns: 1fr;
  }

  .counter-item {
    grid-template-columns: minmax(70px, 1fr) minmax(130px, 1fr) auto;
  }
}

@media (max-width: 560px) {
  .modal-overlay {
    padding: 0.5rem;
  }

  .modal-header,
  .modal-content,
  .modal-footer {
    padding-left: 0.75rem;
    padding-right: 0.75rem;
  }

  .counter-item {
    grid-template-columns: 1fr;
    gap: 0.35rem;
  }

  .subtotal {
    text-align: left;
  }

  .modal-footer {
    flex-wrap: wrap;

    .btn {
      flex: 1;
      min-width: 120px;
    }
  }
}
</style>
