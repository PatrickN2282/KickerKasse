<template>
  <div v-if="show" class="modal">
    <div class="modal-content voucher-modal">
      <h3>📒 Neuen Deckel anlegen</h3>
      <p class="info-text">Der aktuelle Bon wird unter einem Namen zwischengespeichert und kann später bar bezahlt werden.</p>
      <input
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        type="text"
        placeholder="Name des Deckels"
        class="form-input voucher-input"
        @keyup.enter="$emit('create')"
      />
      <div class="button-group">
        <button @click="$emit('create')" :disabled="!canCreate" class="btn btn-primary">
          ✓ Speichern
        </button>
        <button @click="$emit('close')" class="btn btn-secondary">
          Abbrechen / Zurück
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: Boolean,
  modelValue: { type: String, default: '' },
  canCreate: Boolean,
})

defineEmits(['update:modelValue', 'create', 'close'])
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

    &.voucher-modal {
      max-width: 500px;

      .voucher-input {
        text-transform: uppercase;
        font-family: monospace;
        letter-spacing: 0.1em;
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
  }
}

.info-text {
  font-size: 0.85rem;
  color: #666;
  margin: 0 0 1rem 0;
  padding: 0.5rem;
  background: #f9f9f9;
  border-radius: 4px;
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
  background: var(--app-highlight-color);
  color: var(--app-highlight-contrast);
}

.btn-secondary {
  background: #e2e8f0;
  color: #1e293b;
}
</style>
