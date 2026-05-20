<template>
  <div class="modal-overlay">
    <div class="modal-dialog">
      <div class="modal-header">
        <div>
          <h3>📒 Deckel: {{ activeDeckel.name }}</h3>
          <p class="subtitle">Gebuchte Positionen und Abrechnung</p>
        </div>
        <button class="close-btn" @click="closeDeckelDetailsModal">✕</button>
      </div>
      <div class="modal-body">
        <p class="info-text">Hier sehen Sie alle bisher gebuchten Artikel und können den Deckel direkt bar abrechnen.</p>
        <div class="payment-summary-list">
          <div v-for="item in activeDeckel.items" :key="`deckel-${item.id || item.product_id}-${item.unit_price_cents}`" class="payment-summary-item">
            <div class="payment-summary-copy">
              <span>{{ item.quantity }}× {{ item.product_name }}</span>
              <small v-if="item.note">{{ item.note }}</small>
            </div>
            <strong>{{ formatPrice(item.total_price_cents) }}</strong>
          </div>
        </div>
        <div class="payment-summary-totals">
          <div class="total-row grand-total">
            <span>Gesamt</span>
            <strong>{{ formatPrice(activeDeckel.total_amount_cents) }}</strong>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button @click="closeDeckelDetailsModal" class="btn btn-secondary">Abbrechen / Zurück</button>
        <button @click="openDeckelPaymentConfirmation(activeDeckel)" class="btn btn-confirm-payment" :class="{ selected: true }">
          💰 Zahlen - BAR
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue'
const {
  activeDeckel, formatPrice, openDeckelPaymentConfirmation, closeDeckelDetailsModal,
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
  max-width: 560px;
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
.btn-secondary {
  background: #f8fafc;
  color: #475569;
  border: 1px solid #cbd5e1;
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
.payment-summary-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 280px;
  overflow-y: auto;
}
.payment-summary-item {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  .payment-summary-copy {
    display: flex; flex-direction: column; gap: 0.15rem; min-width: 0;
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
.btn-confirm-payment {
  background: #2e7d32;
  color: #fff;
  box-shadow: 0 0 0 2px rgba(46, 125, 50, 0.2);
  &.selected { box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.24), 0 0 16px rgba(46, 125, 50, 0.45); }
  &:not(:disabled):hover { background: #256a29; }
}
</style>
