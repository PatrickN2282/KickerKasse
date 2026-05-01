<template>
  <div v-if="show" class="category-modal modal-overlay" @click.self="$emit('close')">
    <div class="modal-card modal-card-form">
      <header class="modal-header">
        <div>
          <h3>{{ editingId ? 'Kategorie bearbeiten' : 'Neue Kategorie anlegen' }}</h3>
          <p class="modal-subtitle">Kategorie mit Namen, Beschreibung und Anzeigeeinstellungen kompakt verwalten.</p>
        </div>
        <button class="modal-close" @click="$emit('close')">×</button>
      </header>

      <form class="modal-form-content" @submit.prevent="handleSubmit">
        <section class="form-section">
          <h4>Stammdaten</h4>
          <div class="form-row">
            <div class="form-group">
              <label for="cat-name">Name</label>
              <input id="cat-name" v-model="localForm.name" type="text" required>
            </div>
            <div class="form-group">
              <label for="cat-display-order">Anzeigereihenfolge</label>
              <input id="cat-display-order" v-model.number="localForm.display_order" type="number">
            </div>
          </div>
          <div class="form-group">
            <label for="cat-description">Beschreibung</label>
            <textarea id="cat-description" v-model="localForm.description" rows="3"></textarea>
          </div>
        </section>

        <section class="form-section">
          <h4>Farbe</h4>
          <div class="color-picker-section">
            <p class="color-picker-hint">Wähle eine Farbe für diese Kategorie – sie erscheint am Chip und am Produktrahmen in der Kasse.</p>

            <div class="color-options">
              <button
                type="button"
                class="color-option color-option-none"
                :class="{ selected: !localForm.color }"
                title="Keine Farbe"
                @click="localForm.color = null"
              >
                <span class="no-color-icon">✕</span>
              </button>

              <button
                v-for="pastel in pastelColors"
                :key="pastel.value"
                type="button"
                class="color-option"
                :class="{ selected: localForm.color === pastel.value }"
                :style="{ background: pastel.value }"
                :title="pastel.label"
                @click="localForm.color = pastel.value"
              ></button>

              <label class="color-option color-option-custom" :class="{ selected: isCustomColor }" title="Eigene Farbe wählen">
                <span v-if="isCustomColor" class="custom-color-preview" :style="{ background: localForm.color }"></span>
                <span v-else class="custom-color-icon">🎨</span>
                <input
                  type="color"
                  :value="localForm.color || '#ffffff'"
                  @input="setCustomColor($event.target.value)"
                >
              </label>
            </div>

            <div v-if="localForm.color" class="color-preview-row">
              <span class="color-preview-chip" :style="{ borderColor: localForm.color, background: localForm.color + '33' }">
                Vorschau Chip
              </span>
              <span class="color-preview-card" :style="{ borderColor: localForm.color }">
                Vorschau Karte
              </span>
              <button type="button" class="btn-clear-color" @click="localForm.color = null">Farbe entfernen</button>
            </div>
          </div>
        </section>

        <section class="form-section highlight">
          <h4>Darstellung</h4>
          <label class="checkbox-card">
            <input id="cat-is-active" v-model="localForm.is_active_in_kasse" type="checkbox">
            <div class="checkbox-content">
              <span class="label">In Kassenansicht sichtbar</span>
              <span class="desc">Die Kategorie wird direkt in der Kasse als auswählbarer Bereich angezeigt.</span>
            </div>
          </label>
        </section>

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
import { ref, computed, watch } from 'vue'

const props = defineProps({
  show: { type: Boolean, required: true },
  editingId: { type: Number, default: null },
  initialFormData: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['close', 'save'])

const pastelColors = [
  { value: '#FFB3B3', label: 'Rosé' },
  { value: '#FFCBA4', label: 'Pfirsich' },
  { value: '#FFF2A8', label: 'Gelb' },
  { value: '#B5EAD7', label: 'Mint' },
  { value: '#B5D5FF', label: 'Hellblau' },
  { value: '#C3B1E1', label: 'Lavendel' },
  { value: '#FFD1DC', label: 'Pink' },
  { value: '#D7E8BA', label: 'Limette' },
  { value: '#FFF8E1', label: 'Creme' },
  { value: '#E0F2F1', label: 'Türkis' },
  { value: '#FFE4C4', label: 'Bisque' },
  { value: '#F0E6FF', label: 'Flieder' },
]

const localForm = ref({
  name: '',
  description: '',
  color: null,
  display_order: 0,
  is_active_in_kasse: true,
})

watch(() => props.initialFormData, (val) => {
  if (val) localForm.value = { ...val }
}, { immediate: true, deep: true })

const isCustomColor = computed(() => (
  !!localForm.value.color && !pastelColors.some(p => p.value === localForm.value.color)
))

const setCustomColor = (hex) => {
  localForm.value.color = hex
}

const handleSubmit = () => {
  emit('save', { ...localForm.value })
}
</script>

<style scoped lang="scss">
.category-modal {
  --primary: #3b82f6;
  --success: #10b981;
  --border: #e2e8f0;
}

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
  background: white;
  width: 100%;
  max-width: 900px;
  max-height: 90vh;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.modal-card-form {
  max-width: 760px;
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  gap: 1rem;

  h3 {
    margin: 0;
    font-size: 1.25rem;
  }
}

.modal-subtitle {
  color: #64748b;
  margin-top: 0.25rem;
  font-size: 0.875rem;
}

.modal-form-content {
  padding: 1.5rem;
  overflow-y: auto;
}

.form-section {
  margin-bottom: 2rem;

  h4 {
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
  }

  &.highlight {
    background: #f0f7ff;
    padding: 1.25rem;
    border-radius: 12px;
    border: 1px solid #bae6fd;
  }
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  margin-bottom: 1rem;

  label {
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    margin-bottom: 0.4rem;
    color: #1e293b;
  }

  input,
  textarea {
    width: 100%;
    padding: 0.6rem 0.8rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.95rem;

    &:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
  }
}

.color-picker-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.color-picker-hint {
  font-size: 0.82rem;
  color: #64748b;
  margin: 0;
}

.color-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
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
}

.color-option-custom {
  background: white;
  border: 2px dashed #cbd5e1;
  cursor: pointer;
  overflow: hidden;

  input[type="color"] {
    position: absolute;
    width: 0;
    height: 0;
    opacity: 0;
    pointer-events: none;
  }

  &.selected {
    border-color: #1e293b;
    border-style: solid;
  }
}

.custom-color-preview {
  width: 100%;
  height: 100%;
  border-radius: 6px;
  display: block;
}

.custom-color-icon {
  font-size: 0.95rem;
}

.color-preview-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.color-preview-chip {
  padding: 0.3rem 0.75rem;
  border-radius: 999px;
  border: 2px solid;
  font-size: 0.8rem;
  font-weight: 600;
}

.color-preview-card {
  padding: 0.3rem 0.75rem;
  border-radius: 8px;
  border: 2px solid;
  font-size: 0.8rem;
}

.btn-clear-color {
  background: none;
  border: none;
  cursor: pointer;
  color: #64748b;
  font-size: 0.8rem;
  text-decoration: underline;
}

.checkbox-card {
  display: flex;
  gap: 0.75rem;
  padding: 0.9rem 1rem;
  background: white;
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;

  .label {
    font-weight: 600;
    font-size: 0.9rem;
  }

  .desc {
    font-size: 0.75rem;
    color: #64748b;
    display: block;
  }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid var(--border);
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

.modal-close {
  border: none;
  background: transparent;
  font-size: 1.6rem;
  line-height: 1;
  cursor: pointer;
  color: #6b7280;
}
</style>
