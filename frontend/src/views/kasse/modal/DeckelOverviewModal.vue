<template>
  <div class="modal">
    <div class="modal-content voucher-modal deckel-overview-modal">
      <h3>📒 Deckelübersicht</h3>
      <p class="info-text">Vorhandene Deckel können eingesehen, mit dem aktuellen Bon erweitert oder direkt bar abgerechnet werden.</p>
      <div v-if="deckelList.length === 0" class="empty-bon">Keine gespeicherten Deckel vorhanden</div>
      <div v-else class="deckel-list">
        <button
          v-for="deckel in deckelList"
          :key="deckel.id"
          class="deckel-list-item"
          @click="openDeckelDetails(deckel)"
        >
          <div>
            <strong>{{ deckel.name }}</strong>
            <div>{{ deckel.items.length }} Positionen · {{ formatPrice(deckel.total_amount_cents) }}</div>
          </div>
          <div class="deckel-actions-inline" @click.stop>
            <button class="btn btn-primary" :disabled="cartStore.items.length === 0" @click="bookCurrentCartToDeckel(deckel)">
              Buchen
            </button>
            <button class="btn btn-info" @click="openDeckelForPayment(deckel)">
              Zahlen
            </button>
          </div>
        </button>
      </div>
      <div class="button-group">
        <button @click="openDeckelCreateModalFromOverview" :disabled="cartStore.items.length === 0" class="btn btn-primary">
          + Neuen Deckel anlegen
        </button>
        <button @click="closeDeckelOverviewModal" class="btn btn-secondary">
          Schließen
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue'
const {
  deckelList, cartStore, openDeckelDetails, bookCurrentCartToDeckel,
  openDeckelForPayment, openDeckelCreateModalFromOverview, closeDeckelOverviewModal,
  formatPrice,
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

.btn-info {
  background-color: var(--app-banner-color);
  color: var(--app-banner-contrast);

  &:not(:disabled):hover {
    opacity: 0.9;
  }
}

.info-text {
  font-size: 0.85rem;
  color: #666;
  margin: 0;
  padding: 0.5rem;
  background: #f9f9f9;
  border-radius: 4px;
  margin-bottom: 1rem;
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

.modal-content.voucher-modal {
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
</style>
