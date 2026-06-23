<template>
  <div
    v-if="show && zBonHtml"
    class="confirmation-overlay"
  >
    <div class="kk-dialog kk-dialog--wide">
      <div class="kk-dialog__header">
        <div>
          <h3>{{ title }}</h3>
          <p class="kk-dialog__subtitle">
            Nur zur Ansicht – Download über den Button unten
          </p>
        </div>
        <button
          class="kk-dialog__close"
          @click="$emit('close')"
        >
          ✕
        </button>
      </div>

      <div
        class="kk-dialog__body"
        style="padding: 1rem;"
      >
        <div class="kk-preview-shell">
          <iframe
            :srcdoc="zBonHtml"
            class="kk-preview-frame"
            title="Kassenbericht-Vorschau"
          />
        </div>
      </div>

      <div class="kk-dialog__footer">
        <button
          class="btn btn-secondary"
          @click="$emit('close')"
        >
          Schließen
        </button>
        <button
          class="btn btn-success"
          @click="$emit('download')"
        >
          ⬇️ HTML herunterladen
        </button>
        <button
          v-if="canSendEmail"
          class="btn btn-primary"
          @click="$emit('send-email')"
        >
          ✉️ Vorschau per E-Mail senden
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: { type: Boolean, required: true },
  zBonHtml: { type: String, default: '' },
  title: { type: String, default: '📋 Kassenbericht-Vorschau' },
  canSendEmail: { type: Boolean, default: false },
})

defineEmits(['close', 'download', 'send-email'])
</script>

<style scoped lang="scss">
.confirmation-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1500;
  padding: 1.5rem;
  overflow-y: auto;
}

.kk-dialog {
  background: #ffffff;
  border-radius: 20px;
  width: min(80vw, 1100px);
  max-height: min(82vh, 900px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow:
    0 32px 64px rgba(15, 23, 42, 0.28),
    0 0 0 1px rgba(15, 23, 42, 0.06);
}

.kk-dialog--wide {
  width: min(90vw, 1400px);
  max-height: min(88vh, 960px);
}

.kk-dialog__header {
  padding: 1rem 1.4rem;
  background: #0f766e;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  flex-shrink: 0;

  h3 {
    margin: 0;
    color: #ffffff;
    font-size: 1.05rem;
    font-weight: 600;
    line-height: 1.3;
  }
}

.kk-dialog__subtitle {
  margin: 0.3rem 0 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.82rem;
}

.kk-dialog__close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
  font-size: 1rem;
  cursor: pointer;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  transition: background 0.15s;

  &:hover {
    background: rgba(255, 255, 255, 0.28);
  }
}

.kk-dialog__body {
  padding: 1.4rem;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.kk-dialog__footer {
  padding: 1rem 1.4rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.65rem;
  flex-shrink: 0;
  background: #f8fafc;
  flex-wrap: wrap;
}

.kk-preview-shell {
  flex: 1;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 500px;
}

.kk-preview-frame {
  width: 100%;
  flex: 1;
  border: none;
  display: block;
  min-height: 500px;
}

.btn {
  padding: 0.65rem 1.25rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;

  &:hover {
    background: #e2e8f0;
  }
}

.btn-success {
  background: #4caf50;
  color: white;

  &:hover {
    background: #45a049;
  }
}

.btn-primary {
  background: #2563eb;
  color: white;

  &:hover {
    background: #1d4ed8;
  }
}

@media (max-width: 900px) {
  .kk-dialog--wide {
    width: 96vw;
  }
}

@media (max-width: 640px) {
  .confirmation-overlay {
    padding: 0.75rem;
    align-items: flex-start;
  }

  .kk-dialog {
    width: 100%;
    max-height: calc(100dvh - 1.5rem);
    border-radius: 14px;
  }

  .kk-dialog__footer {
    flex-direction: column;

    .btn {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>
