<template>
  <div class="modal">
    <div class="modal-content voucher-modal">
      <h3>📒 Neuen Deckel anlegen</h3>
      <p class="info-text">Der aktuelle Bon wird unter einem Namen zwischengespeichert und kann später bar bezahlt werden.</p>
      <input
        v-model="deckelName"
        type="text"
        placeholder="Name des Deckels"
        class="form-input voucher-input"
        @keyup.enter="createDeckel"
      />
      <div class="button-group">
        <button @click="createDeckel" :disabled="!deckelName.trim() || cartStore.items.length === 0" class="btn btn-primary">
          ✓ Speichern
        </button>
        <button @click="closeDeckelCreateModal" class="btn btn-secondary">
          Abbrechen / Zurück
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue'
const { deckelName, cartStore, createDeckel, closeDeckelCreateModal } = inject('kasse')
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

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 1rem;
  font-size: 1rem;
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

.modal-content.voucher-modal {
  max-width: 500px;

  .voucher-input {
    font-family: monospace;
  }

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
