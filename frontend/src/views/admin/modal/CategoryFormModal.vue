<template>
  <div
    v-if="show"
    class="modal-overlay"
  >
    <div class="modal-card modal-compact">
      <header class="modal-header">
        <div>
          <h3>{{ editingId ? 'Kategorie bearbeiten' : 'Neue Kategorie anlegen' }}</h3>
          <p class="modal-subtitle">Kategorie mit Namen, Beschreibung und Anzeigeeinstellungen verwalten.</p>
        </div>
        <button class="close-btn" type="button" @click="$emit('close')">✕</button>
      </header>

      <form class="modal-compact-layout" @submit.prevent="$emit('save')">
        <div class="modal-scroller">
          <section class="form-section">
            <div class="form-row form-row-3">
              <div class="form-group">
                <label for="name">Name</label>
                <input id="name" v-model="formData.name" type="text" required>
              </div>
              <div class="form-group form-group-narrow">
                <label for="display_order">Reihenfolge</label>
                <input id="display_order" v-model.number="formData.display_order" type="number">
              </div>
              <div class="form-group form-group-toggle">
                <label for="is_active">In Kasse sichtbar</label>
                <label class="toggle-switch" title="Die Kategorie wird direkt in der Kasse als auswählbarer Bereich angezeigt.">
                  <input id="is_active" v-model="formData.is_active_in_kasse" type="checkbox">
                  <span class="toggle-track">
                    <span class="toggle-thumb"></span>
                  </span>
                </label>
              </div>
            </div>
            <div class="form-group">
              <label for="description">Beschreibung</label>
              <textarea id="description" v-model="formData.description" rows="2"></textarea>
            </div>
          </section>

          <section class="form-section">
            <h4>Farbe</h4>
            <div class="color-picker-section">
              <div class="color-options">
                <button
                  type="button"
                  class="color-option color-option-none"
                  :class="{ selected: !formData.color }"
                  title="Keine Farbe"
                  @click="formData.color = null"
                >
                  <span class="no-color-icon">✕</span>
                </button>

                <button
                  v-for="pastel in pastelColors"
                  :key="pastel.value"
                  type="button"
                  class="color-option"
                  :class="{ selected: formData.color === pastel.value }"
                  :style="{ background: pastel.value }"
                  :title="pastel.label"
                  @click="formData.color = pastel.value"
                ></button>

                <label class="color-option color-option-custom" :class="{ selected: isCustomColor }" title="Eigene Farbe wählen">
                  <span v-if="isCustomColor" class="custom-color-preview" :style="{ background: formData.color }"></span>
                  <span v-else class="custom-color-icon">🎨</span>
                  <input
                    type="color"
                    :value="formData.color || '#ffffff'"
                    @input="formData.color = $event.target.value"
                  >
                </label>

                <span v-if="formData.color" class="color-preview-chip" :style="{ borderColor: formData.color, background: formData.color + '33' }">
                  Vorschau
                </span>
                <button v-if="formData.color" type="button" class="btn-clear-color" @click="formData.color = null">Entfernen</button>
              </div>
            </div>
          </section>
        </div>

        <footer class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="$emit('close')">Abbrechen</button>
          <button type="submit" class="btn btn-success">
            {{ editingId ? 'Änderungen speichern' : 'Kategorie anlegen' }}
          </button>
        </footer>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, toRefs } from 'vue'

const props = defineProps({
  show: { type: Boolean, required: true },
  editingId: { type: [Number, String], default: null },
  pastelColors: { type: Array, required: true },
})
const { pastelColors } = toRefs(props)

const formData = defineModel('formData', {
  type: Object,
  required: true,
})

defineEmits(['close', 'save'])

const isCustomColor = computed(() => (
  !!formData.value.color && !pastelColors.value.some(pastel => pastel.value === formData.value.color)
))
</script>

<style scoped lang="scss">
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-card {
  --border: #e2e8f0;

  background: white;
  width: 100%;
  max-height: min(560px, 90vh);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.modal-compact {
  max-width: 560px;
}

.modal-header {
  padding: 0.9rem 1.2rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  background: linear-gradient(90deg, #0f766e 0%, #0ea5e9 100%);

  h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #ffffff;
  }

  .modal-subtitle {
    margin: 0.15rem 0 0;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.9);
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

.modal-compact-layout {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-scroller {
  padding: 0.85rem 1.2rem 1.1rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.form-section {
  margin-bottom: 0;

  h4 {
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.3rem;
    margin-bottom: 0.55rem;
  }
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.form-row-3 {
  grid-template-columns: 1.6fr 0.9fr 1fr;
  align-items: end;
}

.form-group {
  margin-bottom: 0.65rem;

  label {
    display: block;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 0.3rem;
    color: #334155;
  }

  input,
  textarea {
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.9rem;
    background: white;

    &:focus {
      outline: none;
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
  }

  textarea {
    resize: vertical;
    min-height: 52px;
  }
}

.form-group-narrow input {
  padding-right: 0.4rem;
}

.form-group-toggle {
  display: flex;
  flex-direction: column;

  label:first-child {
    margin-bottom: 0.3rem;
  }
}

// Toggle-Switch ersetzt die frühere Checkbox-Karte, um die Dialoghöhe zu reduzieren
// (Referenz-Layout: Modal "Artikel zuordnen").
.toggle-switch {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  gap: 0.65rem;
  min-height: 38px;
  position: relative;

  input {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
  }

  .toggle-track {
    width: 42px;
    height: 24px;
    background: #94a3b8;
    border-radius: 999px;
    position: relative;
    transition: background 0.15s ease;
    flex-shrink: 0;
    border: 1px solid #64748b;
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.25);
  }

  .toggle-thumb {
    position: absolute;
    top: 2px;
    left: 2px;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: white;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
    transition: transform 0.15s ease;
  }

  input:checked + .toggle-track {
    background: #10b981;
    border-color: #10b981;
  }

  input:checked + .toggle-track .toggle-thumb {
    transform: translateX(18px);
  }

  input:focus-visible + .toggle-track {
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
  }
}

.color-picker-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.color-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
}

.color-option {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: transform 0.12s, border-color 0.12s;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;

  &:hover {
    transform: scale(1.12);
  }

  &.selected {
    border-color: #1e293b;
    box-shadow: 0 0 0 2px white inset;
  }
}

.color-option-none {
  background: #f1f5f9;
  border: 2px dashed #cbd5e1;
  color: #94a3b8;

  &.selected {
    border-color: #1e293b;
    border-style: solid;
  }
}

.no-color-icon {
  font-size: 0.7rem;
  font-weight: 700;
}

.color-option-custom {
  background: #f8fafc;
  border: 2px dashed #94a3b8;
  cursor: pointer;
  overflow: visible;

  &.selected {
    border-style: solid;
    border-color: #1e293b;
  }

  input[type="color"] {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    opacity: 0;
    cursor: pointer;
    padding: 0;
    border: none;
  }
}

.custom-color-preview {
  width: 100%;
  height: 100%;
  display: block;
  border-radius: 6px;
  position: absolute;
  inset: 0;
}

.custom-color-icon {
  font-size: 1rem;
  pointer-events: none;
}

.color-preview-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.7rem;
  border-radius: 999px;
  border: 2px solid;
  font-size: 0.8rem;
  font-weight: 600;
}

.btn-clear-color {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.8rem;
  color: #64748b;
  text-decoration: underline;
  padding: 0;

  &:hover {
    color: #b91c1c;
  }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1rem 1.2rem;
  border-top: 1px solid var(--border);
}

.btn {
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 0.55rem 0.9rem;
  cursor: pointer;
  font-weight: 700;
  font-size: 0.88rem;
  transition: all 0.15s ease;
}

.btn-success {
  background: #10b981;
  color: white;

  &:hover {
    background: #059669;
  }
}

.btn-secondary {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #334155;

  &:hover {
    background: #f1f5f9;
  }
}

@media (max-width: 560px) {
  .form-row,
  .form-row-3 {
    grid-template-columns: 1fr;
  }
}
</style>
