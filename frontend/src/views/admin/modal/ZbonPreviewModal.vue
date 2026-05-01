<template>
  <div v-if="show && zBonHtml" class="zbon-preview-modal confirmation-overlay">
    <div class="confirmation-dialog zbon-preview-dialog">
      <h3>{{ title }}</h3>
      <div class="zbon-preview-frame-shell">
        <iframe
          :srcdoc="zBonHtml"
          class="zbon-preview-frame"
          title="Z-Bon Vorschau"
        />
      </div>
      <div class="confirmation-buttons">
        <button class="btn btn-success" @click="$emit('download')">
          ⬇️ HTML herunterladen
        </button>
        <button class="btn btn-secondary" @click="$emit('close')">
          Abbrechen / Zurück
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: { type: Boolean, required: true },
  zBonHtml: { type: String, default: '' },
  title: { type: String, default: '📋 Z-Bon Vorschau' },
})

defineEmits(['close', 'download'])
</script>

<style scoped lang="scss">
.zbon-preview-modal {
  --success: #10b981;
  --border: #e2e8f0;
}

.confirmation-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.zbon-preview-dialog {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  width: 100%;
  max-width: 900px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.2);

  h3 {
    margin: 0 0 1rem;
    font-size: 1.1rem;
  }
}

.zbon-preview-frame-shell {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-bottom: 1rem;
}

.zbon-preview-frame {
  width: 100%;
  height: 60vh;
  border: none;
  display: block;
}

.confirmation-buttons {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.btn {
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.btn-success {
  background: var(--success);
  color: white;
}

.btn-secondary {
  background: #e2e8f0;
  color: #475569;
}
</style>
