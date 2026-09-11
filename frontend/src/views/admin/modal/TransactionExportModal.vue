<template>
  <div
    v-if="show"
    class="export-overlay"
    role="dialog"
    aria-modal="true"
    aria-labelledby="transaction-export-title"
  >
    <div class="export-dialog">
      <header class="export-header">
        <div>
          <h3 id="transaction-export-title">
            Transaktionsliste exportieren
          </h3>
          <p>Vorschau der aktuell gefilterten Transaktionen</p>
        </div>
        <button
          class="close-button"
          type="button"
          aria-label="Schließen"
          @click="$emit('close')"
        >
          ✕
        </button>
      </header>

      <div class="export-body">
        <div
          v-if="loading"
          class="loading-state"
        >
          Vorschau wird erstellt …
        </div>
        <iframe
          v-else-if="html"
          :srcdoc="html"
          class="preview-frame"
          title="Vorschau der Transaktionsliste"
        />
        <div
          v-else
          class="loading-state"
        >
          Keine Vorschau verfügbar.
        </div>
      </div>

      <footer class="export-footer">
        <button
          class="btn btn-secondary"
          type="button"
          @click="$emit('close')"
        >
          Schließen
        </button>
        <button
          class="btn btn-csv"
          type="button"
          :disabled="loading || downloading"
          @click="$emit('download', 'csv')"
        >
          ⬇️ CSV herunterladen
        </button>
        <button
          class="btn btn-pdf"
          type="button"
          :disabled="loading || downloading"
          @click="$emit('download', 'pdf')"
        >
          ⬇️ PDF herunterladen
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: { type: Boolean, required: true },
  html: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  downloading: { type: Boolean, default: false },
})

defineEmits(['close', 'download'])
</script>

<style scoped lang="scss">
.export-overlay {
  position: fixed;
  inset: 0;
  z-index: 1600;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.25rem;
  overflow-y: auto;
  background: rgba(15, 23, 42, 0.68);
  backdrop-filter: blur(5px);
}

.export-dialog {
  width: min(94vw, 1420px);
  height: min(90vh, 960px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 30px 70px rgba(15, 23, 42, 0.32);
}

.export-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.35rem;
  color: #fff;
  background: #0f766e;

  h3 { margin: 0; font-size: 1.08rem; }
  p { margin: 0.25rem 0 0; color: rgba(255, 255, 255, 0.8); font-size: 0.82rem; }
}

.close-button {
  width: 32px;
  height: 32px;
  border: 1px solid rgba(255, 255, 255, 0.45);
  border-radius: 50%;
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
  cursor: pointer;
}

.export-body {
  flex: 1;
  min-height: 0;
  padding: 1rem;
  background: #f1f5f9;
}

.preview-frame {
  width: 100%;
  height: 100%;
  min-height: 520px;
  border: 1px solid #cbd5e1;
  border-radius: 9px;
  background: #fff;
}

.loading-state {
  height: 100%;
  min-height: 300px;
  display: grid;
  place-items: center;
  color: #64748b;
}

.export-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.65rem;
  padding: 0.9rem 1.35rem;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}

.btn {
  padding: 0.6rem 1rem;
  border: none;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;

  &:disabled { opacity: 0.55; cursor: wait; }
}

.btn-secondary { border: 1px solid #cbd5e1; color: #475569; background: #fff; }
.btn-csv { color: #fff; background: #047857; }
.btn-pdf { color: #fff; background: #b91c1c; }

@media (max-width: 640px) {
  .export-overlay { padding: 0.5rem; align-items: flex-start; }
  .export-dialog { width: 100%; height: calc(100dvh - 1rem); border-radius: 12px; }
  .export-footer { flex-direction: column; }
  .btn { width: 100%; }
}
</style>
