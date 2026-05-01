<template>
  <div v-if="show" class="modal">
    <div class="modal-content voucher-modal deckel-overview-modal">
      <h3>📒 Deckelübersicht</h3>
      <p class="info-text">Vorhandene Deckel können eingesehen, mit dem aktuellen Bon erweitert oder direkt bar abgerechnet werden.</p>
      <div v-if="deckelList.length === 0" class="empty-bon">Keine gespeicherten Deckel vorhanden</div>
      <div v-else class="deckel-list">
        <button
          v-for="deckel in deckelList"
          :key="deckel.id"
          class="deckel-list-item"
          @click="$emit('open-details', deckel)"
        >
          <div>
            <strong>{{ deckel.name }}</strong>
            <div>{{ deckel.items.length }} Positionen · {{ formatPrice(deckel.total_amount_cents) }}</div>
          </div>
          <div class="deckel-actions-inline" @click.stop>
            <button class="btn btn-primary" :disabled="!cartHasItems" @click="$emit('book-to-deckel', deckel)">
              Buchen
            </button>
            <button class="btn btn-info" @click="$emit('pay-deckel', deckel)">
              Zahlen
            </button>
          </div>
        </button>
      </div>
      <div class="button-group">
        <button @click="$emit('create-new')" :disabled="!cartHasItems" class="btn btn-primary">
          + Neuen Deckel anlegen
        </button>
        <button @click="$emit('close')" class="btn btn-secondary">
          Schließen
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatPrice } from '@/services/utils'

defineProps({
  show: Boolean,
  deckelList: { type: Array, default: () => [] },
  cartHasItems: Boolean,
})

defineEmits(['open-details', 'book-to-deckel', 'pay-deckel', 'create-new', 'close'])
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

    &.voucher-modal {
      max-width: 500px;

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

.info-text {
  font-size: 0.85rem;
  color: #666;
  margin: 0 0 1rem 0;
  padding: 0.5rem;
  background: #f9f9f9;
  border-radius: 4px;
}

.empty-bon {
  text-align: center;
  color: #999;
  padding: 2rem 1rem;
  font-size: 0.95rem;
}

.deckel-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.deckel-list-item {
  width: 100%;
  border: 1px solid #d7dde4;
  border-radius: 8px;
  padding: 0.9rem;
  background: #fff;
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  text-align: left;
  cursor: pointer;
}

.deckel-actions-inline {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
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

.btn-info {
  background-color: var(--app-banner-color);
  color: var(--app-banner-contrast);

  &:not(:disabled):hover {
    opacity: 0.9;
  }
}
</style>
