<template>
  <div v-if="show && product" class="modal">
    <div class="modal-content internal-material-note-modal">
      <h3>Preis eingeben</h3>
      <p class="info-text">
        Bitte geben Sie den Verkaufspreis für
        <strong>{{ product.name }}</strong>
        ein.
      </p>
      <label class="form-input-label">
        Preis (€)
        <input
          ref="variablePriceInput"
          :value="modelValue"
          @input="$emit('update:modelValue', $event.target.value)"
          type="number"
          min="0"
          step="0.01"
          class="form-input"
          placeholder="0.00"
          @keyup.enter="$emit('confirm')"
        />
      </label>
      <div class="modal-actions">
        <button
          @click="$emit('confirm')"
          class="btn btn-confirm-payment"
          :class="{ selected: true }"
          :disabled="!isValid"
        >
          Artikel hinzufügen
        </button>
        <button @click="$emit('close')" class="btn btn-danger">
          Abbrechen / Zurück
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  show: Boolean,
  product: { type: Object, default: null },
  modelValue: { type: [String, Number], default: '' },
  isValid: Boolean,
})

defineEmits(['update:modelValue', 'confirm', 'close'])

const variablePriceInput = ref(null)

watch(() => props.show, (val) => {
  if (val) {
    nextTick(() => {
      variablePriceInput.value?.focus()
      variablePriceInput.value?.select?.()
    })
  }
})
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

    &.internal-material-note-modal {
      max-width: 460px;
    }
  }
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
}

.form-input-label {
  display: block;
  font-weight: 600;
  color: #334155;
  margin-bottom: 1rem;

  .form-input {
    margin-top: 0.5rem;
    width: 100%;
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

.btn-confirm-payment {
  background: #2e7d32;
  color: #fff;
  box-shadow: 0 0 0 2px rgba(46, 125, 50, 0.2);

  &.selected {
    box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.24), 0 0 16px rgba(46, 125, 50, 0.45);
  }

  &:not(:disabled):hover {
    background: #256a29;
  }
}

.btn-danger {
  background-color: #f44336;
  color: white;

  &:not(:disabled):hover {
    background-color: #da190b;
  }
}
</style>
