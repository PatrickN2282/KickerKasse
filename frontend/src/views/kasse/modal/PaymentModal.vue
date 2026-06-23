<template>
  <div class="modal-overlay">
    <div class="modal-dialog" :class="{ 'modal-dialog--wide': isBalancePayment }">
      <div class="modal-header">
        <div>
          <h3>
            <template v-if="paymentResult">Verkauf abgeschlossen</template>
            <template v-else>{{ paymentSource === 'deckel' ? 'Deckel abrechnen' : 'Zahlung bestätigen' }}</template>
          </h3>
          <p class="subtitle">
            <template v-if="!paymentResult">{{ getPaymentMethodLabel(pendingPaymentMethod) }}</template>
            <template v-else>Buchung erfolgreich gespeichert</template>
          </p>
        </div>
        <button class="close-btn" @click="closePaymentConfirmation">✕</button>
      </div>

      <div :class="isBalancePayment && !paymentResult ? 'modal-body-twocol' : 'modal-body'">

        <!-- ── LINKE Spalte: Mitgliedskarte + Guthaben-Flow ── -->
        <div v-if="isBalancePayment && !paymentResult && selectedMember" class="col-member">

          <!-- Mitgliedskarte analog MemberModal -->
          <div class="member-card-display">
            <div class="member-card-img">
              <img
                v-if="selectedMember.photo_path"
                :src="`/api/members/${selectedMember.id}/photo`"
                :alt="getMemberFullName(selectedMember)"
              />
              <div v-else class="member-card-img-placeholder">👤</div>

              <!-- Guthaben-Blase wie in MemberModal -->
              <div class="balance-badge">
                💰 {{ formatPrice(selectedMemberBalance) }}
              </div>
            </div>
            <div class="member-card-body">
              <div class="member-card-name">{{ getMemberShortName(selectedMember) }}</div>
            </div>
          </div>

          <!-- Guthaben-Abzug in Rot -->
          <div class="balance-deduct-block">
            <div class="balance-deduct-label">Verwendetes Guthaben</div>
            <div class="balance-deduct-amount">
              −{{ formatPrice(isInsufficientBalance ? selectedMemberBalance : paymentTotal) }}
            </div>
          </div>

          <!-- Neues Guthaben grüner Kasten -->
          <div class="balance-new-block">
            <div class="balance-new-label">Neues Guthaben nach Kauf</div>
            <div class="balance-new-amount">{{ formatPrice(newBalanceAfterPurchase) }}</div>
          </div>
        </div>

        <!-- ── RECHTE Spalte / normaler Inhalt ── -->
        <div class="col-main">
          <template v-if="paymentResult">
            <p class="info-text">Der Verkauf wurde erfolgreich gebucht.</p>
            <div v-if="paymentResult.issued_prepaid_voucher_numbers?.length" class="issued-voucher-panel">
              <h4>💳 Verzehrkarten ausgegeben</h4>
              <div class="issued-voucher-box">
                <div v-for="voucherNumber in paymentResult.issued_prepaid_voucher_numbers" :key="voucherNumber" class="issued-voucher-number">
                  {{ voucherNumber }}
                </div>
              </div>
              <div class="issued-voucher-alert">
                <p class="issued-voucher-note">
                  Nummer auf der Verzehrkarte notieren - Einlösung ohne Nummer nicht möglich
                </p>
              </div>
            </div>
          </template>

          <template v-else>
            <div class="payment-summary-list">
              <div
                v-for="item in paymentSummaryItems"
                :key="item.line_id || `${paymentSource}-${item.product_id}-${item.unit_price_cents}-${item.is_internal_material ? 'internal' : 'regular'}`"
                class="payment-summary-item"
              >
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
                <strong>{{ formatPrice(paymentSubtotal) }}</strong>
              </div>
              <div v-if="paymentSource === 'cart' && hasAppliedVoucher" class="total-row">
                <span>Gutscheine</span>
                <strong>-{{ formatPrice(voucherAppliedAmount) }}</strong>
              </div>
              <div v-if="paymentSource === 'cart' && hasAppliedBalance" class="total-row">
                <span>Mitgliedsguthaben</span>
                <strong>-{{ formatPrice(balanceAppliedAmount) }}</strong>
              </div>
              <div v-if="paymentSource === 'deckel'" class="total-row">
                <span>Deckel</span>
                <strong>{{ activePaymentDeckel?.name }}</strong>
              </div>

              <!-- Normaler Fall: Gesamtbetrag -->
              <div v-if="!isInsufficientBalance" class="total-row grand-total modal-grand-total">
                <span>Zu zahlen</span>
                <strong>{{ formatPrice(paymentTotal) }}</strong>
              </div>

              <!-- Nicht genug Guthaben: Restbetrag bar -->
              <template v-else>
                <div class="total-row grand-total total-row--subdued">
                  <span>Gesamtbetrag</span>
                  <strong>{{ formatPrice(paymentTotal) }}</strong>
                </div>
                <div class="balance-deduction-row">
                  <div class="balance-deduction-line">
                    <span>⬇ Guthaben {{ selectedMemberName }}</span>
                    <strong>-{{ formatPrice(selectedMemberBalance) }}</strong>
                  </div>
                </div>
                <div class="total-row grand-total modal-grand-total modal-grand-total--cash">
                  <span>💵 Jetzt bar zahlen</span>
                  <strong>{{ formatPrice(effectiveCashTotal) }}</strong>
                </div>
              </template>
            </div>

            <div v-if="pendingPaymentMethod === 'CASH' || isInsufficientBalance" class="cash-payment-fields">
              <label>
                Bar gegeben
                <input
                  ref="cashGivenInput"
                  v-model="cashGiven"
                  type="number"
                  min="0"
                  step="0.01"
                  class="form-input"
                  @keyup.enter="confirmPayment"
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
                  @click="confirmPaymentWithTip"
                  :disabled="processingPayment"
                >
                  💝 Rückgeld spenden ({{ formatPrice(cashChangeCents) }})
                </button>
              </div>
            </div>
          </template>
        </div>

      </div>

      <div class="modal-footer">
        <template v-if="paymentResult">
          <button @click="closePaymentConfirmation" class="btn btn-primary">Fertig</button>
        </template>
        <template v-else>
          <button @click="closePaymentConfirmation" class="btn btn-secondary" :disabled="processingPayment">
            Abbrechen / Zurück
          </button>
          <button @click="confirmPayment" class="btn btn-confirm-payment" :class="{ selected: true }" :disabled="processingPayment">
            <template v-if="processingPayment">⏳ Wird verarbeitet...</template>
            <template v-else>
              <span class="btn-confirm-payment__line">Kauf</span>
              <span class="btn-confirm-payment__line">abschließen</span>
            </template>
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, inject, computed } from 'vue'
const kasse = inject('kasse')
const {
  pendingPaymentMethod, processingPayment, paymentResult,
  cartSubtotal, voucherAppliedAmount, balanceAppliedAmount,
  hasAppliedVoucher, hasAppliedBalance, cashGiven,
  paymentSummaryItems, paymentSubtotal, paymentTotal,
  cashChangeDisplay, cashChangeCents, selectedMemberName, selectedMemberBalance, selectedMember,
  showPaymentConfirmModal, closePaymentConfirmation,
  confirmPayment, confirmPaymentWithTip, formatPrice, getPaymentMethodLabel,
  handleCheckout, paymentSource, activePaymentDeckel, isInsufficientBalance, effectiveCashTotal,
  getMemberFullName, getMemberShortName, formatBalance,
} = kasse

const cashGivenInput = ref(null)

const isBalancePayment = computed(() =>
  pendingPaymentMethod.value === 'BALANCE' || isInsufficientBalance.value
)

const newBalanceAfterPurchase = computed(() => {
  const balance = selectedMemberBalance.value ?? 0
  const total = paymentTotal.value ?? 0
  if (isInsufficientBalance.value) return 0
  return Math.max(0, balance - total)
})

watch(() => kasse.showPaymentConfirmModal.value, (val) => {
  if (val && (kasse.pendingPaymentMethod.value === 'CASH' || kasse.isInsufficientBalance.value)) {
    nextTick(() => {
      cashGivenInput.value?.focus()
      cashGivenInput.value?.select?.()
    })
  }
})
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
  max-width: 650px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  overflow: hidden;

  &--wide {
    max-width: 950px;
  }
}

.modal-header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
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

/* ── Body layouts ─────────────────────────────────────────── */
.modal-body {
  padding: 1rem 1.25rem;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.modal-body-twocol {
  flex: 1;
  display: flex;
  flex-direction: row;
  align-items: stretch;
  overflow: hidden;
  min-height: 0;
}

/* ── Linke Spalte: Mitgliedskarte ─────────────────────────── */
.col-member {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  padding: 1rem;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  overflow-y: auto;
}

/* Mitgliedskarte — analog MemberModal */
.member-card-display {
  border: 1.5px solid color-mix(in srgb, var(--app-banner-color, #0f766e) 22%, white 78%);
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.member-card-img {
  width: 100%;
  aspect-ratio: 1 / 1;
  background: #eef1f7;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.member-card-img-placeholder {
  font-size: 2.8rem;
}

/* Guthaben-Blase auf dem Foto — identisch zu MemberModal */
.balance-badge {
  position: absolute;
  bottom: 6px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 255, 255, 0.92);
  color: var(--app-highlight-color);
  font-size: 0.95rem;
  font-weight: 700;
  padding: 0.25rem 0.6rem;
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  white-space: nowrap;
  backdrop-filter: blur(2px);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.member-card-body {
  padding: 0.35rem 0.4rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.member-card-name {
  font-size: 0.95rem;
  font-weight: 700;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
  text-align: center;
}

/* Abzug in Rot */
.balance-deduct-block {
  background: #fef2f2;
  border: 1.5px solid #fca5a5;
  border-radius: 8px;
  padding: 0.25rem 0.25rem;
  display: flex;
  flex-direction: column;
  align-items: center; /* Zentriert die Flex-Kinder horizontal */
  text-align: center;  /* Zentriert den Text bei Zeilenumbrüchen */
  gap: 0.15rem;
}

.balance-deduct-label {
  font-size: 0.7rem;
  font-weight: 600;
  color: #991b1b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.balance-deduct-amount {
  font-size: 1.2rem;
  font-weight: 800;
  color: #dc2626;
}

/* Neues Guthaben grün */
.balance-new-block {
  background: color-mix(in srgb, var(--app-highlight-color, #0f766e) 10%, white 90%);
  border: 2px solid color-mix(in srgb, var(--app-highlight-color, #0f766e) 40%, white 60%);
  border-radius: 8px;
  padding: 0.25rem 0.25rem;
  display: flex;
  flex-direction: column;
  align-items: center; /* Zentriert die Flex-Kinder horizontal */
  text-align: center;  /* Zentriert den Text bei Zeilenumbrüchen */
  gap: 0.15rem;
}

.balance-new-label {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--app-highlight-color, #0f766e);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.balance-new-amount {
  font-size: 1.35rem;
  font-weight: 800;
  color: var(--app-highlight-color, #0f766e);
}

/* ── Rechte Spalte: Berechnung ────────────────────────────── */
.col-main {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
}

/* ── Footer ───────────────────────────────────────────────── */
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
}

.btn-secondary {
  background: #f8fafc;
  color: #475569;
  border: 1px solid #cbd5e1;
}

.btn-confirm-payment {
  background: #2e7d32;
  color: #fff;
  box-shadow: 0 0 0 2px rgba(46, 125, 50, 0.2);
  &.selected { box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.24), 0 0 16px rgba(46, 125, 50, 0.45); }
  &:not(:disabled):hover { background: #256a29; }
}

.btn-confirm-payment__line {
  display: block;
  line-height: 1.1;
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
  &:not(:disabled):hover { background: #bf360c; }
  &:disabled { background: #bdbdbd; cursor: not-allowed; }
}

/* ── Artikel-Liste & Totals ───────────────────────────────── */
.form-input {
  width: 100%;
  padding: 0.65rem 0.8rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  box-sizing: border-box;
  margin-top: 0.4rem;
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

.cash-payment-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;

  label {
    font-weight: 600;
    color: #334155;
    font-size: 0.9rem;
  }

  .tip-donate-row { grid-column: 1 / -1; }
}

.payment-summary-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 200px;
  overflow-y: auto;
}

.payment-summary-item {
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  gap: 1rem;

  .payment-summary-copy {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    min-width: 0;

    small { color: #64748b; font-size: 0.75rem; }
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
  border-top: 1px solid #e2e8f0;
}

.payment-summary-totals .modal-grand-total {
  margin-top: 0.35rem;
  padding: 0.95rem 1rem;
  align-items: center;
  border: 2px solid color-mix(in srgb, var(--app-highlight-color) 30%, var(--app-banner-color) 70%);
  border-radius: 10px;
  background: color-mix(in srgb, var(--app-highlight-color) 10%, white 90%);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);

  span, strong { color: var(--app-banner-color); }
  span { font-size: 1rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em; }
  strong { font-size: 1.7rem; font-weight: 800; }
}

.total-row--subdued {
  padding-top: 0.55rem;
  border-top: 1px solid #e2e8f0;
  opacity: 0.6;
  font-size: 0.9rem;
}

.balance-deduction-row {
  padding: 0.45rem 0.75rem;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;

  .balance-deduction-line {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    font-size: 0.88rem;
    color: #166534;

    strong { color: #15803d; font-weight: 700; }
  }
}

.modal-grand-total--cash {
  span, strong { color: #b45309 !important; }
  border-color: #f59e0b !important;
  background: linear-gradient(135deg, #fffbeb, #fef3c7) !important;
}

/* ── Voucher ──────────────────────────────────────────────── */
.issued-voucher-panel {
  h4 { margin: 0 0 0.75rem; }
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
</style>
