<template>
  <div v-if="show && modalData" class="modal-overlay">
    <div class="modal-dialog created-voucher-modal">
      <div class="modal-header">
        <div class="modal-header-title">
          <h3>{{ modalData.title }}</h3>
        </div>
        <button class="close-btn" @click="$emit('close')">
          ✕
        </button>
      </div>
      <div class="modal-body">
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
      </div>
      <div class="modal-footer created-voucher-actions">
        <button
          v-if="modalData.showClubAccountButton"
          class="btn-secondary"
          @click="$emit('open-club-account')"
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

defineEmits(['close', 'open-club-account'])
</script>

<style scoped lang="scss">
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(20, 24, 30, 0.45);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-dialog {
  width: min(520px, calc(100vw - 2rem));
  background: #ffffff;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  overflow: hidden;
}

.modal-header {
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(90deg, #0f766e 0%, #0ea5e9 100%);
  flex-shrink: 0;
}

.modal-header-title {
  display: flex;
  align-items: center;
  min-width: 0;

  h3 {
    margin: 0;
    color: #ffffff;
    font-size: 1.05rem;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.close-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.45);
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
  font-size: 1.1rem;
  cursor: pointer;
  display: grid;
  place-items: center;
  flex-shrink: 0;

  &:hover {
    background: rgba(255, 255, 255, 0.3);
  }
}

.modal-body {
  padding: 1rem 1.25rem;
  overflow-y: auto;
  flex: 1;
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

.btn-secondary {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 0.6rem 0.9rem;
  cursor: pointer;
  font-size: 0.88rem;
  font-weight: 700;
  transition: all 0.15s ease;
  background: #f1f5f9;
  color: #334155;

  &:hover {
    background: #e2e8f0;
  }
}

.created-voucher-modal {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.created-voucher-box {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  border-radius: 10px;
  background: linear-gradient(135deg, #dcfce7, #bbf7d0);
  border: 1px solid #22c55e;
}

.created-voucher-number {
  font-family: monospace;
  font-size: 1.25rem;
  font-weight: 800;
  color: #166534;
  text-align: center;
}

.created-voucher-note {
  margin: 0;
  color: #991b1b;
  font-weight: 700;
}

.created-voucher-alert {
  padding: 0.9rem 1rem;
  border-radius: 10px;
  border: 2px solid #ef4444;
  background: linear-gradient(135deg, #fef2f2, #fee2e2);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.45) inset;
}

.created-voucher-actions {
  flex-wrap: wrap;
}
</style>
