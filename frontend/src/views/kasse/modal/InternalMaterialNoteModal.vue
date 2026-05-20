<template>
  <div class="modal-overlay">
    <div class="modal-dialog">
      <div class="modal-header">
        <div>
          <h3>Notiz für internes Material</h3>
          <p class="subtitle">{{ pendingInternalMaterialProduct.name }}</p>
        </div>
        <button class="close-btn" @click="closeInternalMaterialNoteModal">✕</button>
      </div>
      <div class="modal-body">
        <p class="info-text">
          Optional können Sie eine Notiz für
          <strong>{{ pendingInternalMaterialProduct.name }}</strong>
          hinterlegen.
        </p>
        <textarea
          v-model.trim="internalMaterialNote"
          class="form-input"
          rows="4"
          maxlength="500"
          placeholder="z. B. Einsatzort, Zweck oder Ansprechpartner"
        ></textarea>
      </div>
      <div class="modal-footer">
        <button @click="closeInternalMaterialNoteModal" class="btn btn-secondary">Abbrechen / Zurück</button>
        <button @click="confirmInternalMaterialSelection" class="btn btn-confirm-payment" :class="{ selected: true }">
          Artikel hinzufügen
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue'
const {
  pendingInternalMaterialProduct, internalMaterialNote,
  confirmInternalMaterialSelection, closeInternalMaterialNoteModal,
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
  max-width: 460px;
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
.form-input {
  width: 100%;
  padding: 0.65rem 0.8rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  box-sizing: border-box;
  &[rows] { resize: vertical; min-height: 110px; }
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
.btn-confirm-payment {
  background: #2e7d32;
  color: #fff;
  box-shadow: 0 0 0 2px rgba(46, 125, 50, 0.2);
  &.selected { box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.24), 0 0 16px rgba(46, 125, 50, 0.45); }
  &:not(:disabled):hover { background: #256a29; }
}
</style>
