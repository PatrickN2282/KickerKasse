<template>
  <div v-if="show" class="modal">
    <div class="modal-content voucher-modal">
      <h3>🎫 Gutschein einlösen</h3>

      <!-- Step 1: Input Voucher Number -->
      <div v-if="!validated" class="step">
        <input
          :value="modelValue"
          @input="$emit('update:modelValue', $event.target.value)"
          type="text"
          :placeholder="`Gutscheinnummer eingeben (z. B. ${voucherPrefix}001)`"
          class="form-input voucher-input"
          @keyup.enter="$emit('validate')"
          autocomplete="off"
        />

        <div v-if="error" class="error-message">
          ❌ {{ error }}
        </div>

        <div class="button-group">
          <button
            @click="$emit('validate')"
            :disabled="!hasValidInput || validating"
            class="btn btn-primary"
          >
            {{ validating ? '⏳ Wird überprüft...' : '✓ Überprüfen' }}
          </button>
          <button @click="$emit('close')" class="btn btn-secondary">
            Abbrechen / Zurück
          </button>
        </div>
      </div>

      <!-- Step 2: Show Validation Result -->
      <div v-else-if="validation && !redeemed" class="step">
        <div :class="['validation-result', validation.valid ? 'valid' : 'invalid']">
          <h4>{{ validation.valid ? '✅ Gültig' : '❌ Ungültig' }}</h4>
          <table class="voucher-details">
            <tr>
              <td>Nummer:</td>
              <td><strong>{{ validation.voucher_number }}</strong></td>
            </tr>
            <tr>
              <td>Typ:</td>
              <td>{{ validation.voucher_type === 'GIFT' ? '🎁 Gutschein' : '💳 Verzehrkarte' }}</td>
            </tr>
            <tr>
              <td>Wert:</td>
              <td><strong>{{ (validation.value_cents / 100).toFixed(2) }}€</strong></td>
            </tr>
            <tr v-if="validation.valid && cartSubtotal > 0">
              <td>Anrechnung:</td>
              <td><strong>{{ (validation.applicable_amount_cents / 100).toFixed(2) }}€</strong></td>
            </tr>
            <tr v-if="validation.valid && validation.remaining_value_cents > 0">
              <td>Restwert:</td>
              <td>{{ (validation.remaining_value_cents / 100).toFixed(2) }}€</td>
            </tr>
            <tr v-if="getExpiredStatusLabel(validation)">
              <td>Status:</td>
              <td>{{ getExpiredStatusLabel(validation) }}</td>
            </tr>
            <tr v-if="validation.reason">
              <td>Grund:</td>
              <td>{{ formatVoucherReason(validation.reason) }}</td>
            </tr>
          </table>
          <p v-if="validation.message" class="info-text">
            ℹ️ {{ validation.message }}
          </p>
        </div>

        <div class="button-group">
          <button
            v-if="validation.valid"
            @click="$emit('redeem')"
            :disabled="redeeming"
            class="btn"
            :class="validation.covers_cart_total ? 'btn-success' : 'btn-primary'"
          >
            {{ actionLabel }}
          </button>
          <button @click="$emit('secondary-action')" class="btn btn-secondary">
            Abbrechen / Zurück
          </button>
        </div>
      </div>

      <!-- Step 3: Success Message -->
      <div v-else-if="redeemed" class="step">
        <div class="success-message">
          <h4>✅ Gutschein eingelöst!</h4>
          <table class="voucher-details">
            <tr>
              <td>Nummer:</td>
              <td><strong>{{ redeemed.voucher_number }}</strong></td>
            </tr>
            <tr>
              <td>Typ:</td>
              <td>{{ redeemed.voucher_type === 'GIFT' ? '🎁 Gutschein' : '💳 Verzehrkarte' }}</td>
            </tr>
            <tr>
              <td>Wert:</td>
              <td><strong>{{ (redeemed.value_cents / 100).toFixed(2) }}€</strong></td>
            </tr>
          </table>
          <p class="info-text">
            {{ redeemed.message }}
          </p>
        </div>

        <div class="button-group">
          <button @click="$emit('close')" class="btn btn-primary">
            ✓ Fertig
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: Boolean,
  modelValue: { type: String, default: '' },
  voucherPrefix: { type: String, default: '' },
  validated: Boolean,
  validation: { type: Object, default: null },
  redeemed: { type: Object, default: null },
  error: { type: String, default: null },
  hasValidInput: Boolean,
  validating: Boolean,
  redeeming: Boolean,
  cartSubtotal: { type: Number, default: 0 },
  actionLabel: { type: String, default: '' },
})

defineEmits(['update:modelValue', 'validate', 'redeem', 'secondary-action', 'close'])

const voucherReasonLabels = {
  DYP_SIEGER: 'DYP-Sieger',
  PROMOTION: 'Promotion',
}

const formatVoucherReason = (reason) => {
  if (!reason) return '-'
  return voucherReasonLabels[reason] || reason
}

const getExpiredStatusLabel = (voucher) => {
  if (voucher?.status === 'EXPIRED') {
    return '⏰ Abgelaufen'
  }
  return ''
}
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

    &.voucher-modal {
      max-width: 500px;

      .voucher-input {
        text-transform: uppercase;
        font-family: monospace;
        letter-spacing: 0.1em;
      }

      .step {
        animation: fadeIn 0.2s;
      }

      .validation-result {
        border: 2px solid #ddd;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;

        h4 {
          margin-top: 0;
          margin-bottom: 1rem;
        }

        &.valid {
          background: #d4edda;
          border-color: #c3e6cb;
          color: #155724;

          h4 { color: #155724; }
        }

        &.invalid {
          background: #f8d7da;
          border-color: #f5c6cb;
          color: #721c24;

          h4 { color: #721c24; }
        }
      }

      .voucher-details {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 1rem;
        font-size: 0.9rem;

        tr {
          border-bottom: 1px solid rgba(0, 0, 0, 0.1);
        }

        td {
          padding: 0.5rem;

          &:first-child {
            color: #666;
            font-weight: 500;
            width: 100px;
          }

          &:last-child {
            text-align: right;
          }
        }
      }

      .success-message {
        background: #d4edda;
        border: 2px solid #c3e6cb;
        border-radius: 8px;
        padding: 1.5rem;
        color: #155724;
        margin-bottom: 1.5rem;

        h4 {
          margin-top: 0;
          margin-bottom: 1rem;
          color: #155724;
        }
      }

      .info-text {
        font-size: 0.85rem;
        color: #666;
        margin: 0;
        padding: 0.5rem;
        background: #f9f9f9;
        border-radius: 4px;
      }

      .error-message {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 4px;
        color: #721c24;
        padding: 0.75rem;
        margin-bottom: 1rem;
        font-size: 0.9rem;
      }

      .button-group {
        display: flex;
        gap: 0.75rem;
        justify-content: flex-end;

        button {
          flex: 1;
        }
      }
    }
  }
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

.btn-primary {
  background: var(--app-highlight-color);
  color: var(--app-highlight-contrast);
}

.btn-secondary {
  background: #e2e8f0;
  color: #1e293b;
}

.btn-success {
  background-color: #4caf50;
  color: white;

  &:not(:disabled):hover {
    background-color: #45a049;
  }
}
</style>
