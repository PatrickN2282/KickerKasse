<template>
  <div v-if="show && activeDeckel" class="modal">
    <div class="modal-content payment-modal">
      <h3>📒 Deckel: {{ activeDeckel.name }}</h3>
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
      <div class="modal-actions">
        <button @click="$emit('pay', activeDeckel)" class="btn btn-confirm-payment" :class="{ selected: true }">
          💰 Zahlen - BAR
        </button>
        <button @click="$emit('close')" class="btn btn-danger">
          Abbrechen / Zurück
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatPrice } from '@/services/utils'

defineProps({
  show: Boolean,
  activeDeckel: { type: Object, default: null },
})

defineEmits(['pay', 'close'])
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

    &.payment-modal {
      max-width: 560px;
    }
  }
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
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

.info-text {
  font-size: 0.85rem;
  color: #666;
  margin: 0 0 1rem 0;
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
