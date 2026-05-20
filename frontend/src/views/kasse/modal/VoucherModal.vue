<template>
  <div class="modal-overlay">
    <div class="modal-dialog">
      <div class="modal-header">
        <div>
          <h3>🎫 Gutschein einlösen</h3>
          <p class="subtitle">Gutscheinnummer eingeben und einlösen</p>
        </div>
        <button class="close-btn" @click="closeVoucherModal">✕</button>
      </div>
      <div class="modal-body">
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
        </div>

        <!-- Step 2: Show Validation Result -->
        <div v-else-if="voucherValidation && !voucherRedeemed" class="step">
          <div :class="['validation-result', voucherValidation.valid ? 'valid' : 'invalid']">
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
                <td>{{ getExpiredStatusLabel(voucherValidation) }}</td>
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
            <p class="info-text">{{ voucherRedeemed.message }}</p>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <template v-if="!voucherValidated">
          <button @click="closeVoucherModal" class="btn btn-secondary">Abbrechen / Zurück</button>
          <button @click="validateVoucher" :disabled="!hasValidVoucherInput || validatingVoucher" class="btn btn-primary">
            {{ validatingVoucher ? '⏳ Wird überprüft...' : '✓ Überprüfen' }}
          </button>
        </template>
        <template v-else-if="voucherValidation && !voucherRedeemed">
          <button @click="handleVoucherSecondaryAction" class="btn btn-secondary">Abbrechen / Zurück</button>
          <button v-if="voucherValidation.valid" @click="redeemVoucher" :disabled="redeemingVoucher" class="btn" :class="voucherValidation.covers_cart_total ? 'btn-success' : 'btn-primary'">
            {{ voucherActionLabel }}
          </button>
        </template>
        <template v-else-if="voucherRedeemed">
          <button @click="closeVoucherModal" class="btn btn-primary">✓ Fertig</button>
        </template>
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
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1.25rem;
}
.modal-dialog {
  background: #ffffff;
  border-radius: 16px;
  width: 100%;
  max-width: 500px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  overflow: hidden;
}
.modal-header {
  padding: 1rem 1.25rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: linear-gradient(90deg, #0f766e 0%, #0ea5e9 100%);
  flex-shrink: 0;
  h3 { margin: 0; color: #ffffff; font-size: 1.1rem; }
  .subtitle { margin: 0.35rem 0 0; color: rgba(255,255,255,0.9); font-size: 0.85rem; }
}
.close-btn {
  width: 34px; height: 34px; border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.45);
  background: rgba(255,255,255,0.18);
  color: #ffffff; font-size: 1.1rem; cursor: pointer;
  display: grid; place-items: center; flex-shrink: 0;
  &:hover { background: rgba(255,255,255,0.3); }
}
.modal-body {
  padding: 1rem 1.25rem;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.modal-footer {
  padding: 0.95rem 1.25rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  background: #ffffff;
  flex-shrink: 0;
}
.btn {
  border-radius: 8px;
  padding: 0.65rem 1rem;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.9rem;
  border: none;
  &:disabled { opacity: 0.6; cursor: not-allowed; }
}
.btn-primary {
  background: linear-gradient(90deg, #0f766e 0%, #0ea5e9 100%);
  color: #fff;
  &:not(:disabled):hover { opacity: 0.9; }
}
.btn-secondary {
  background: #f8fafc;
  color: #475569;
  border: 1px solid #cbd5e1;
}
.btn-success {
  background: #16a34a;
  color: #fff;
  &:not(:disabled):hover { background: #15803d; }
}
.form-input {
  width: 100%;
  padding: 0.65rem 0.8rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  box-sizing: border-box;
}
.info-text {
  font-size: 0.85rem;
  color: #64748b;
  margin: 0;
  padding: 0.5rem 0.75rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.voucher-input {
  text-transform: uppercase;
  font-family: monospace;
  letter-spacing: 0.1em;
}
.step { animation: fadeIn 0.2s; }
.validation-result {
  border: 2px solid #ddd;
  border-radius: 10px;
  padding: 1.25rem;
  h4 { margin: 0 0 1rem; }
  &.valid { background: #d4edda; border-color: #c3e6cb; color: #155724; h4 { color: #155724; } }
  &.invalid { background: #f8d7da; border-color: #f5c6cb; color: #721c24; h4 { color: #721c24; } }
}
.voucher-details {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
  font-size: 0.9rem;
  tr { border-bottom: 1px solid rgba(0,0,0,0.1); }
  td {
    padding: 0.5rem;
    &:first-child { color: #666; font-weight: 500; width: 100px; }
    &:last-child { text-align: right; }
  }
}
.success-message {
  background: #d4edda;
  border: 2px solid #c3e6cb;
  border-radius: 10px;
  padding: 1.25rem;
  color: #155724;
  h4 { margin: 0 0 1rem; color: #155724; }
}
.error-message {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 8px;
  color: #721c24;
  padding: 0.75rem;
  font-size: 0.9rem;
}
</style>
