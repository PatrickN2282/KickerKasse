<template>
  <div v-if="show && modalData" class="voucher-created-modal modal-overlay">
    <div class="modal-card created-voucher-modal">
      <h3>{{ modalData.title }}</h3>
      <p class="info-text">
        {{ modalData.subtitle }}
      </p>
      <div class="created-voucher-box">
        <div
          v-for="voucherNumber in modalData.numbers"
          :key="voucherNumber"
          class="created-voucher-number"
        >
          {{ voucherNumber }}
        </div>
      </div>
      <div class="created-voucher-alert">
        <p class="created-voucher-note">
          {{ modalData.note }}
        </p>
      </div>
      <div class="button-row created-voucher-actions">
        <button
          v-if="modalData.showClubAccountButton"
          class="btn-secondary"
          @click="$emit('openClubAccount')"
        >
          🏦 Gutscheinkonto öffnen
        </button>
        <button class="btn-secondary" @click="$emit('close')">
          Schließen
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: { type: Boolean, required: true },
  modalData: { type: Object, default: null },
})

defineEmits(['close', 'openClubAccount'])
</script>

<style scoped lang="scss">
.voucher-created-modal {
  --border: #e2e8f0;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.created-voucher-modal {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  width: 100%;
  max-width: 560px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);

  h3 {
    margin: 0 0 0.75rem;
    font-size: 1.2rem;
  }
}

.info-text {
  color: #64748b;
  font-size: 0.9rem;
  margin-bottom: 1.25rem;
}

.created-voucher-box {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.created-voucher-number {
  font-family: monospace;
  font-size: 1.2rem;
  font-weight: 700;
  background: #f0f9ff;
  border: 2px solid #bae6fd;
  color: #0369a1;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  letter-spacing: 0.05em;
}

.created-voucher-alert {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1.25rem;
}

.created-voucher-note {
  margin: 0;
  font-size: 0.875rem;
  color: #92400e;
}

.button-row {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.created-voucher-actions {
  justify-content: flex-end;
}

.btn-secondary {
  background: #e2e8f0;
  color: #475569;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}
</style>
