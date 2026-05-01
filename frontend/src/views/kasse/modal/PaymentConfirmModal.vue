<template>
  <div v-if="show" class="modal">
    <div class="modal-content payment-modal">
      <template v-if="paymentResult">
        <h3>Verkauf abgeschlossen</h3>
        <p class="info-text">Der Verkauf wurde erfolgreich gebucht.</p>
        <div v-if="paymentResult.issued_prepaid_voucher_numbers?.length" class="issued-voucher-panel">
          <h4>💳 Verzehrkarten ausgegeben</h4>
          <div class="issued-voucher-box">
            <div v-for="vNum in paymentResult.issued_prepaid_voucher_numbers" :key="vNum" class="issued-voucher-number">
              {{ vNum }}
            </div>
          </div>
          <div class="issued-voucher-alert">
            <p class="issued-voucher-note">
              Nummer auf der Verzehrkarte notieren - Einlösung ohne Nummer nicht möglich
            </p>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="$emit('close')" class="btn btn-confirm-payment" :class="{ selected: true }">
            Fertig
          </button>
        </div>
      </template>
      <template v-else>
        <h3>{{ paymentSource === 'deckel' ? 'Deckel abrechnen' : 'Zahlung bestätigen' }}</h3>
        <div class="payment-method-chip">
          {{ paymentMethodLabel }}
        </div>
        <div class="payment-summary-list">
          <div v-for="item in summaryItems" :key="item.line_id || `${paymentSource}-${item.product_id}-${item.unit_price_cents}-${item.is_internal_material ? 'internal' : 'regular'}`" class="payment-summary-item">
            <div class="payment-summary-copy">
              <span>{{ item.quantity }}× {{ item.product_name }}</span>
              <small v-if="item.note">{{ item.note }}</small>
            </div>
            <strong>{{ formatPrice(item.total_price_cents) }}</strong>
          </div>
        </div>
        <div class="payment-summary-totals">
          <div class="total-row">
            <span>Zwischensumme</span>
            <strong>{{ formatPrice(subtotal) }}</strong>
          </div>
          <div v-if="paymentSource === 'cart' && hasAppliedVoucher" class="total-row">
            <span>Gutscheine</span>
            <strong>-{{ formatPrice(voucherAppliedAmount) }}</strong>
          </div>
          <div v-if="paymentSource === 'cart' && hasAppliedBalance" class="total-row">
            <span>Mitgliedsguthaben</span>
            <strong>-{{ formatPrice(balanceAppliedAmount) }}</strong>
          </div>
          <div v-if="paymentSource === 'cart' && pendingPaymentMethod === 'BALANCE'" class="total-row">
            <span>Mitglied</span>
            <strong>{{ selectedMemberName }}</strong>
          </div>
          <div v-if="paymentSource === 'deckel'" class="total-row">
            <span>Deckel</span>
            <strong>{{ activePaymentDeckel?.name }}</strong>
          </div>
          <div class="total-row grand-total modal-grand-total">
            <span>Zu zahlen</span>
            <strong>{{ formatPrice(total) }}</strong>
          </div>
        </div>
        <div v-if="pendingPaymentMethod === 'CASH'" class="cash-payment-fields">
          <label>
            Bar gegeben
            <input
              ref="cashGivenInput"
              :value="modelValue"
              @input="$emit('update:modelValue', $event.target.value)"
              type="number"
              min="0"
              step="0.01"
              class="form-input"
              @keyup.enter="$emit('confirm')"
            />
          </label>
          <label>
            Rückgeld
            <input :value="cashChangeDisplay" type="text" class="form-input" readonly />
          </label>
          <div v-if="cashChangeCents > 0" class="tip-donate-row">
            <button
              type="button"
              class="btn btn-tip-donate"
              @click="$emit('confirm-with-tip')"
              :disabled="processing"
            >
              💝 Rückgeld spenden ({{ formatPrice(cashChangeCents) }})
            </button>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="$emit('confirm')" class="btn btn-confirm-payment" :class="{ selected: true }" :disabled="processing">
            {{ processing ? '⏳ Wird verarbeitet...' : 'Bestätigen' }}
          </button>
          <button @click="$emit('close')" class="btn btn-danger" :disabled="processing">
            Abbrechen / Zurück
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { formatPrice } from '@/services/utils'

const props = defineProps({
  show: Boolean,
  paymentResult: { type: Object, default: null },
  paymentSource: { type: String, default: 'cart' },
  summaryItems: { type: Array, default: () => [] },
  subtotal: { type: Number, default: 0 },
  total: { type: Number, default: 0 },
  hasAppliedVoucher: Boolean,
  voucherAppliedAmount: { type: Number, default: 0 },
  hasAppliedBalance: Boolean,
  balanceAppliedAmount: { type: Number, default: 0 },
  selectedMemberName: { type: String, default: '' },
  activePaymentDeckel: { type: Object, default: null },
  pendingPaymentMethod: { type: String, default: null },
  paymentMethodLabel: { type: String, default: '' },
  modelValue: { type: [Number, String], default: '' },
  cashChangeDisplay: { type: String, default: '' },
  cashChangeCents: { type: Number, default: 0 },
  processing: Boolean,
})

defineEmits(['update:modelValue', 'confirm', 'confirm-with-tip', 'close'])

const cashGivenInput = ref(null)

watch(() => props.show, (val) => {
  if (val && props.pendingPaymentMethod === 'CASH') {
    nextTick(() => {
      cashGivenInput.value?.focus()
      cashGivenInput.value?.select?.()
    })
  }
})
</script>

<style scoped lang="scss">
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;

  .modal-content {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    width: 90%;
    max-width: 400px;
    max-height: 80vh;
    overflow-y: auto;

    h3 {
      margin-top: 0;
      color: #333;
    }

    .form-input {
      width: 100%;
      padding: 0.75rem;
      border: 1px solid #ddd;
      border-radius: 4px;
      margin-bottom: 1rem;
      font-size: 1rem;
    }

    &.payment-modal {
      max-width: 560px;

      .cash-payment-fields {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 1rem;
        margin-bottom: 1rem;

        label {
          font-weight: 600;
          color: #334155;
        }

        .form-input {
          margin-bottom: 0;
          margin-top: 0.5rem;
        }

        .tip-donate-row {
          grid-column: 1 / -1;
        }
      }
    }
  }
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
}

.payment-method-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
  padding: 0.45rem 0.85rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-banner-color) 12%, white 88%);
  color: var(--app-banner-color);
  font-weight: 600;
}

.payment-summary-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 280px;
  overflow-y: auto;
  margin-bottom: 1rem;
}

.payment-summary-item,
.payment-summary-totals .total-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.payment-summary-item {
  padding: 0.65rem 0.75rem;
  border-radius: 6px;
  background: #f5f5f5;

  .payment-summary-copy {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    min-width: 0;

    small {
      color: #5b6470;
      font-size: 0.75rem;
      white-space: normal;
    }
  }
}

.payment-summary-totals {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.total-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  width: 100%;
}

.grand-total {
  padding-top: 0.55rem;
  border-top: 1px solid color-mix(in srgb, var(--app-banner-color) 25%, white 75%);
}

.payment-summary-totals .modal-grand-total {
  margin-top: 0.35rem;
  padding: 0.95rem 1rem;
  align-items: center;
  border: 2px solid color-mix(in srgb, var(--app-highlight-color) 30%, var(--app-banner-color) 70%);
  border-radius: 10px;
  background: color-mix(in srgb, var(--app-highlight-color) 10%, white 90%);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);

  span,
  strong {
    color: var(--app-banner-color);
  }

  span {
    font-size: 1rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  strong {
    font-size: 1.7rem;
    font-weight: 800;
  }
}

.btn-tip-donate {
  width: 100%;
  padding: 0.5rem 1rem;
  background: #e65100;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.15s;

  &:not(:disabled):hover {
    background: #bf360c;
  }

  &:disabled {
    background: #bdbdbd;
    cursor: not-allowed;
  }
}

.issued-voucher-panel {
  margin-top: 1rem;

  h4 {
    margin-bottom: 0.75rem;
  }
}

.issued-voucher-box {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  border-radius: 10px;
  background: linear-gradient(135deg, #dcfce7, #bbf7d0);
  border: 1px solid #22c55e;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.4);
}

.issued-voucher-number {
  font-size: 1.25rem;
  font-weight: 800;
  color: #166534;
  text-align: center;
  font-family: monospace;
}

.issued-voucher-alert {
  margin-top: 0.75rem;
  padding: 0.9rem 1rem;
  border-radius: 10px;
  border: 2px solid #ef4444;
  background: linear-gradient(135deg, #fef2f2, #fee2e2);
}

.issued-voucher-note {
  margin: 0;
  color: #991b1b;
  font-weight: 700;
}

.info-text {
  font-size: 0.85rem;
  color: #666;
  margin: 0;
  padding: 0.5rem;
  background: #f9f9f9;
  border-radius: 4px;
}

.btn {
  padding: 0.75rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:not(:disabled):hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
}

.btn-confirm-payment {
  background: #2e7d32;
  color: #fff;
  box-shadow: 0 0 0 2px rgba(46, 125, 50, 0.2);

  &.selected {
    box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.24), 0 0 16px rgba(46, 125, 50, 0.45);
  }

  &:not(:disabled):hover {
    background: #256a29;
  }
}

.btn-danger {
  background-color: #f44336;
  color: white;

  &:not(:disabled):hover {
    background-color: #da190b;
  }
}
</style>
