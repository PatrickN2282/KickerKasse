<template>
  <div v-if="show" class="modal-overlay">
    <div class="modal-dialog">
      <div class="modal-header">
        <h3>Kassenzählung</h3>
        <button @click="$emit('close')" class="close-btn">✕</button>
      </div>

      <div class="modal-content">
        <p class="description">
          Geben Sie die Anzahl der Münzen und Scheine ein, um die Kasse zu zählen:
        </p>

        <div class="cash-counter">
          <!-- Coins Section -->
          <div class="section">
            <h4>Münzen</h4>
            <div class="counter-grid">
              <div
                v-for="denomination in coinDenominations"
                :key="`coin-${denomination}`"
                class="counter-item"
              >
                <label>{{ denomination }}€</label>
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
                  {{ (cashCount.coins[denomination] * denomination).toFixed(2) }}€
                </div>
              </div>
            </div>
          </div>

          <!-- Notes Section -->
          <div class="section">
            <h4>Scheine</h4>
            <div class="counter-grid">
              <div
                v-for="denomination in noteDenominations"
                :key="`note-${denomination}`"
                class="counter-item"
              >
                <label>{{ denomination }}€</label>
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
                  {{ (cashCount.notes[denomination] * denomination).toFixed(2) }}€
                </div>
              </div>
            </div>
          </div>

          <!-- Total -->
          <div class="total-section">
            <div class="total-item">
              <span>Münzen Summe:</span>
              <strong>{{ coinTotal.toFixed(2) }}€</strong>
            </div>
            <div class="total-item">
              <span>Scheine Summe:</span>
              <strong>{{ noteTotal.toFixed(2) }}€</strong>
            </div>
            <div class="total-item highlight">
              <span>Gesamtbetrag:</span>
              <strong>{{ totalCashCount.toFixed(2) }}€</strong>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="reset" class="btn btn-secondary">Zurücksetzen</button>
        <button @click="cancel" class="btn btn-secondary">Abbrechen</button>
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
const coinDenominations = [0.01, 0.02, 0.05, 0.10, 0.20, 0.50, 1, 2]

// German note denominations in EUR
const noteDenominations = [5, 10, 20, 50, 100, 200, 500]

// Cash count state
const cashCount = ref({
  coins: {
    '0.01': 0,
    '0.02': 0,
    '0.05': 0,
    '0.10': 0,
    '0.20': 0,
    '0.50': 0,
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
      '0.10': 0,
      '0.20': 0,
      '0.50': 0,
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
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-dialog {
  background: white;
  border-radius: 8px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;

  h3 {
    margin: 0;
    color: #333;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #999;

    &:hover {
      color: #333;
    }
  }
}

.modal-content {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;

  .description {
    color: #666;
    margin: 0 0 1.5rem 0;
    font-size: 0.95rem;
  }
}

.cash-counter {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.section {
  h4 {
    margin: 0 0 0.75rem 0;
    color: #333;
    font-size: 0.95rem;
    font-weight: 600;
  }
}

.counter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}

.counter-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;

  label {
    font-weight: 600;
    color: #333;
    font-size: 0.9rem;
  }

  .input-group {
    display: flex;
    gap: 0.3rem;
    align-items: center;

    .btn-qty {
      width: 30px;
      height: 30px;
      border: 1px solid #ddd;
      background: white;
      cursor: pointer;
      border-radius: 4px;
      font-weight: bold;
      transition: all 0.2s;

      &:hover {
        background: #f0f0f0;
        border-color: #999;
      }

      &:active {
        background: #e0e0e0;
      }
    }

    .qty-input {
      flex: 1;
      border: 1px solid #ddd;
      border-radius: 4px;
      text-align: center;
      font-size: 0.9rem;
      padding: 0.4rem;
      font-weight: 600;

      &:focus {
        outline: none;
        border-color: #1976d2;
        box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.1);
      }
    }
  }

  .subtotal {
    text-align: center;
    font-weight: 600;
    color: #667eea;
    font-size: 0.85rem;
  }
}

.total-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 2px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.total-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f5f5f5;
  border-radius: 4px;

  span {
    color: #666;
    font-size: 0.9rem;
  }

  strong {
    color: #333;
    font-size: 0.95rem;
  }

  &.highlight {
    background: #e3f2fd;
    border: 1px solid #90caf9;

    span {
      color: #1976d2;
      font-weight: 600;
    }

    strong {
      color: #1976d2;
      font-size: 1.1rem;
    }
  }
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #eee;
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;

  .btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 4px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      transform: translateY(-2px);
    }

    &.btn-primary {
      background: #4caf50;
      color: white;

      &:hover {
        background: #45a049;
      }
    }

    &.btn-secondary {
      background: #f5f5f5;
      color: #666;
      border: 1px solid #ddd;

      &:hover {
        background: #e0e0e0;
      }
    }
  }
}
</style>
