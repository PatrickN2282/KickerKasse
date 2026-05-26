<template>
  <div
    v-if="show"
    class="modal-overlay"
    @click.self="emit('close')"
  >
    <div class="modal-dialog">
      <div class="modal-header">
        <div class="modal-header-title">
          <h3>ℹ️ Help &amp; Info <span class="header-pipe">|</span> <span class="header-sub">Über KickerKasse</span></h3>
        </div>
        <button
          class="close-btn"
          @click="emit('close')"
        >
          ✕
        </button>
      </div>

      <div class="modal-body">
        <p>
          KickerKasse ist ein privates Projekt und wurde speziell auf die Anforderungen unseres Kickervereins zugeschnitten.
        </p>
        <p>
          Projekt-Link:
          <a
            href="https://github.com/PatrickN2282/KickerKasse"
            target="_blank"
            rel="noopener noreferrer"
          >
            github.com/PatrickN2282/KickerKasse
          </a>
        </p>
        <p>
          <strong>Disclaimer:</strong> Es handelt sich nicht um ein revisionssicheres, TSE-fähiges Kassensystem.
          Ziel ist es, die Lagerhaltung und die Kassenzugangssteuerung zu vereinfachen.
        </p>
        <p>
          Für weitere Ideen oder Fehlermeldungen gern direkt an mich wenden.
        </p>
      </div>

      <div class="modal-footer">
        <button
          class="btn btn-secondary"
          @click="emit('close')"
        >
          Schließen
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close'])
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
  z-index: 1200;
  padding: 1.25rem;
  overflow-y: auto;
}

.modal-dialog {
  background: #ffffff;
  border-radius: 16px;
  width: min(760px, 100%);
  max-height: 80vh;
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

  .header-pipe {
    margin: 0 0.5rem;
    opacity: 0.5;
  }

  .header-sub {
    font-weight: 400;
    opacity: 0.88;
    font-size: 0.92rem;
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
  display: grid;
  gap: 0.75rem;
  overflow-y: auto;
  color: #334155;
  line-height: 1.45;

  p {
    margin: 0;
  }

  a {
    color: var(--app-highlight-color);
    font-weight: 600;
    word-break: break-word;
  }
}

.modal-footer {
  padding: 0.95rem 1.25rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
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
}

.btn-secondary {
  background: #f8fafc;
  color: #475569;
  border: 1px solid #cbd5e1;
}

@media (max-width: 640px) {
  .modal-overlay {
    padding: 0.75rem;
    align-items: stretch;
  }

  .modal-dialog {
    width: 100%;
    max-height: calc(100vh - 1.5rem);
  }

  .modal-header-title h3 {
    white-space: normal;
  }
}
</style>
