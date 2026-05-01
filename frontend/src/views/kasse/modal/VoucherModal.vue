<template>
  <div class="modal">
    <div class="modal-content voucher-modal">
      <h3>🎫 Gutschein einlösen</h3>

      <!-- Step 1: Input Voucher Number -->
      <div v-if="!voucherValidated" class="step">
        <input
          v-model="voucherNumber"
          type="text"
          :placeholder="`Gutscheinnummer eingeben (z. B. ${voucherPrefix}001)`"
          class="form-input voucher-input"
          @keyup.enter="validateVoucher"
          autocomplete="off"
        />

        <div v-if="voucherError" class="error-message">
          ❌ {{ voucherError }}
        </div>

        <div class="button-group">
          <button
            @click="validateVoucher"
            :disabled="!hasValidVoucherInput || validatingVoucher"
            class="btn btn-primary"
          >
            {{ validatingVoucher ? '⏳ Wird überprüft...' : '✓ Überprüfen' }}
          </button>
          <button @click="closeVoucherModal" class="btn btn-secondary">
            Abbrechen / Zurück
          </button>
        </div>
      </div>

      <!-- Step 2: Show Validation Result -->
      <div v-else-if="voucherValidation && !voucherRedeemed" class="step">
        <div
          :class="['validation-result', voucherValidation.valid ? 'valid' : 'invalid']"
        >
          <h4>{{ voucherValidation.valid ? '✅ Gültig' : '❌ Ungültig' }}</h4>
          <table class="voucher-details">
            <tr>
              <td>Nummer:</td>
              <td><strong>{{ voucherValidation.voucher_number }}</strong></td>
            </tr>
            <tr>
              <td>Typ:</td>
              <td>{{ voucherValidation.voucher_type === 'GIFT' ? '🎁 Gutschein' : '💳 Verzehrkarte' }}</td>
            </tr>
            <tr>
              <td>Wert:</td>
              <td><strong>{{ (voucherValidation.value_cents / 100).toFixed(2) }}€</strong></td>
            </tr>
            <tr v-if="voucherValidation.valid && cartSubtotal > 0">
              <td>Anrechnung:</td>
              <td><strong>{{ (voucherValidation.applicable_amount_cents / 100).toFixed(2) }}€</strong></td>
            </tr>
            <tr v-if="voucherValidation.valid && voucherValidation.remaining_value_cents > 0">
              <td>Restwert:</td>
              <td>{{ (voucherValidation.remaining_value_cents / 100).toFixed(2) }}€</td>
            </tr>
            <tr v-if="getExpiredStatusLabel(voucherValidation)">
              <td>Status:</td>
              <td>
                {{ getExpiredStatusLabel(voucherValidation) }}
              </td>
            </tr>
            <tr v-if="voucherValidation.reason">
              <td>Grund:</td>
              <td>{{ formatVoucherReason(voucherValidation.reason) }}</td>
            </tr>
          </table>
          <p v-if="voucherValidation.message" class="info-text">
            ℹ️ {{ voucherValidation.message }}
          </p>
        </div>

        <div class="button-group">
          <button
            v-if="voucherValidation.valid"
            @click="redeemVoucher"
            :disabled="redeemingVoucher"
            class="btn"
            :class="voucherValidation.covers_cart_total ? 'btn-success' : 'btn-primary'"
          >
            {{ voucherActionLabel }}
          </button>
          <button @click="handleVoucherSecondaryAction" class="btn btn-secondary">
            Abbrechen / Zurück
          </button>
        </div>
      </div>

      <!-- Step 3: Success Message -->
      <div v-else-if="voucherRedeemed" class="step">
        <div class="success-message">
          <h4>✅ Gutschein eingelöst!</h4>
          <table class="voucher-details">
            <tr>
              <td>Nummer:</td>
              <td><strong>{{ voucherRedeemed.voucher_number }}</strong></td>
            </tr>
            <tr>
              <td>Typ:</td>
              <td>{{ voucherRedeemed.voucher_type === 'GIFT' ? '🎁 Gutschein' : '💳 Verzehrkarte' }}</td>
            </tr>
            <tr>
              <td>Wert:</td>
              <td><strong>{{ (voucherRedeemed.value_cents / 100).toFixed(2) }}€</strong></td>
            </tr>
          </table>
          <p class="info-text">
            {{ voucherRedeemed.message }}
          </p>
        </div>

        <div class="button-group">
          <button @click="closeVoucherModal" class="btn btn-primary">
            ✓ Fertig
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue'
const {
  voucherNumber, voucherValidation, voucherValidated, voucherRedeemed,
  voucherError, validatingVoucher, redeemingVoucher, voucherPrefix,
  cartSubtotal, voucherActionLabel, hasValidVoucherInput,
  validateVoucher, redeemVoucher, closeVoucherModal, handleVoucherSecondaryAction,
  formatVoucherReason, getExpiredStatusLabel,
} = inject('kasse')
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
  }
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
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
  background-color: var(--app-highlight-color);
  color: var(--app-highlight-contrast, white);

  &:not(:disabled):hover {
    opacity: 0.9;
  }
}

.btn-secondary {
  background-color: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;

  &:not(:disabled):hover {
    background-color: #e0e0e0;
  }
}

.btn-success {
  background-color: #4caf50;
  color: white;

  &:not(:disabled):hover {
    background-color: #45a049;
  }
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 1rem;
  font-size: 1rem;
}

.info-text {
  font-size: 0.85rem;
  color: #666;
  margin: 0;
  padding: 0.5rem;
  background: #f9f9f9;
  border-radius: 4px;
}

.modal-content.voucher-modal {
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

      h4 {
        color: #155724;
      }
    }

    &.invalid {
      background: #f8d7da;
      border-color: #f5c6cb;
      color: #721c24;

      h4 {
        color: #721c24;
      }
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
</style>
