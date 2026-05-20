<template>
  <div class="modal-overlay">
    <div class="modal-dialog">
      <div class="modal-header">
        <div>
          <h3>📒 Deckelübersicht</h3>
          <p class="subtitle">Gespeicherte Deckel verwalten</p>
        </div>
        <button class="close-btn" @click="closeDeckelOverviewModal">✕</button>
      </div>
      <div class="modal-body">
        <p class="info-text">Vorhandene Deckel können eingesehen, mit dem aktuellen Bon erweitert oder direkt bar abgerechnet werden.</p>
        <div v-if="deckelList.length === 0" class="empty-state">Keine gespeicherten Deckel vorhanden</div>
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
      </div>
      <div class="modal-footer">
        <button @click="closeDeckelOverviewModal" class="btn btn-secondary">Schließen</button>
        <button @click="openDeckelCreateModalFromOverview" :disabled="cartStore.items.length === 0" class="btn btn-primary">
          + Neuen Deckel anlegen
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
.btn-info {
  background: var(--app-banner-color);
  color: var(--app-banner-contrast);
  &:not(:disabled):hover { opacity: 0.9; }
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
.empty-state {
  text-align: center;
  color: #94a3b8;
  padding: 2rem;
  font-size: 0.95rem;
}
.deckel-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.deckel-list-item {
  width: 100%;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.9rem;
  background: #fff;
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  text-align: left;
  cursor: pointer;
  &:hover { border-color: #0ea5e9; }
}
.deckel-actions-inline {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}
</style>
