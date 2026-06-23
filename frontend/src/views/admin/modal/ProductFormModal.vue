<template>
  <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card modal-compact">
      <header class="modal-header">
        <div>
          <h3>{{ editingId ? 'Produkt bearbeiten' : 'Neues Produkt anlegen' }}</h3>
          <p class="modal-subtitle">Preise, Bild und Bestände verwalten.</p>
        </div>
        <button type="button" class="close-btn" @click="$emit('close')">✕</button>
      </header>

      <form class="modal-compact-layout" @submit.prevent="$emit('save')">
        <div class="modal-scroller">
          <div class="main-form-grid">
            <div class="image-upload-section">
              <span class="section-label">Produktbild Vorschau</span>

              <template v-if="imagePreviewSrc">
                <template v-if="isGif">
                  <div class="image-preview-shell">
                    <div class="kasse-card-preview">
                      <div class="card-img">
                        <span v-if="formData.memberPrice !== null && formData.memberPrice !== ''" class="card-badge discount-badge">Rabatt</span>
                        <img
                          :src="imagePreviewSrc"
                          :alt="productPreviewAlt"
                          class="preview-crop-img preview-static-img"
                          draggable="false"
                        >
                        <span class="gif-badge">GIF 🎬</span>
                      </div>
                      <div class="card-body">
                        <div class="card-name">{{ formData.name || 'Produktname' }}</div>
                        <div class="card-bottom">
                          <span class="card-price">{{ previewPriceText }}</span>
                          <span class="card-stock">{{ formData.isUnlimitedStock ? '∞' : formData.stock }}</span>
                        </div>
                      </div>
                    </div>
                    <button
                      type="button"
                      class="image-remove-btn"
                      aria-label="Produktbild löschen"
                      title="Bild löschen"
                      @click.stop="$emit('remove-image')"
                    >
                      ✕
                    </button>
                  </div>
                  <label class="upload-button hint-upload gif-replace-btn">
                    Bild ersetzen
                    <input id="image" type="file" accept="image/*" hidden @change="$emit('image-upload', $event)">
                  </label>
                </template>

                <template v-else>
                  <div class="image-preview-shell">
                    <button
                      type="button"
                      class="image-preview-trigger"
                      aria-label="Produktbild anpassen"
                      @click="$emit('open-crop')"
                    >
                      <div class="kasse-card-preview interactive-image-card">
                        <div class="card-img">
                          <span v-if="formData.memberPrice !== null && formData.memberPrice !== ''" class="card-badge discount-badge">Rabatt</span>
                          <img
                            :src="imagePreviewSrc"
                            :alt="productPreviewAlt"
                            class="preview-crop-img preview-static-img"
                            draggable="false"
                          >
                          <span class="image-preview-overlay">Anpassen</span>
                        </div>
                        <div class="card-body">
                          <div class="card-name">{{ formData.name || 'Produktname' }}</div>
                          <div class="card-bottom">
                            <span class="card-price">{{ previewPriceText }}</span>
                            <span class="card-stock">{{ formData.isUnlimitedStock ? '∞' : formData.stock }}</span>
                          </div>
                        </div>
                      </div>
                    </button>
                    <button
                      type="button"
                      class="image-remove-btn"
                      aria-label="Produktbild löschen"
                      title="Bild löschen"
                      @click.stop="$emit('remove-image')"
                    >
                      ✕
                    </button>
                  </div>
                </template>

                <p
                  v-if="isGif"
                  class="gif-hint"
                >
                  Animierte GIFs bleiben erhalten und werden deshalb aktuell nicht im Editor zugeschnitten oder skaliert.
                </p>
              </template>

              <template v-else>
                <div class="avatar-display compact-avatar">
                  <div class="photo-placeholder">
                    <span>Kein Bild ausgewählt</span>
                  </div>
                </div>
                <label class="upload-button hint-upload">
                  Bild auswählen
                  <input id="image" type="file" accept="image/*" hidden @change="$emit('image-upload', $event)">
                </label>
              </template>
            </div>

            <div class="fields-section">
              <div class="form-group">
                <label for="name">Name*</label>
                <input id="name" v-model="formData.name" type="text" required placeholder="z.B. Fritz-Kola 0,33l">
              </div>

              <div class="form-group">
                <label for="warengruppe">Warengruppe</label>
                <input
                  id="warengruppe"
                  v-model.trim="formData.warengruppe"
                  type="text"
                  list="warengruppe-options"
                  placeholder="Neue oder bestehende Gruppe"
                >
                <datalist id="warengruppe-options">
                  <option v-for="group in warengruppeOptions" :key="group" :value="group" />
                </datalist>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="price">Preis (€)*</label>
                  <input id="price" v-model.number="formData.price" type="number" step="0.01" required>
                </div>
                <div class="form-group">
                  <label for="member-price">Mitgliedspreis (€)</label>
                  <input id="member-price" v-model.number="formData.memberPrice" type="number" step="0.01" placeholder="Optional">
                </div>
              </div>
            </div>
          </div>

          <div class="options-form-grid">
            <div class="toggle-row">
              <label class="toggle-switch">
                <input id="unlimited-stock" v-model="formData.isUnlimitedStock" type="checkbox" @change="$emit('unlimited-stock-change')">
                <span class="toggle-track"><span class="toggle-thumb"></span></span>
                <span class="toggle-label">
                  <span class="label">Unendlich verfügbar</span>
                  <span class="desc">Für immaterielle Artikel (z.B. Eintritte oder Umlagen)</span>
                </span>
              </label>

              <label class="toggle-switch">
                <input id="variable-price" v-model="formData.isVariablePrice" type="checkbox">
                <span class="toggle-track"><span class="toggle-thumb"></span></span>
                <span class="toggle-label">
                  <span class="label">Variabler Endpreis</span>
                  <span class="desc">Der Preis wird erst beim Bonieren abgefragt</span>
                </span>
              </label>
            </div>

            <div class="summary-card compact-summary">
              <!-- Zeile 1: Lagerbestand + Menge + Korrekturen-Button -->
              <div class="stock-row">
                <span class="label">Lagerbestand</span>
                <span class="value">{{ formData.isUnlimitedStock ? '∞' : formData.stock }}</span>
                <button
                  v-if="editingId && showCorrectionsShortcut"
                  type="button"
                  class="corrections-jump-btn"
                  title="Bestandskorrekturen erfolgen über das Finanzen-Modul"
                  aria-label="Zu Finanzen → Korrekturen wechseln"
                  @click="$emit('go-to-corrections')"
                >
                  ↗ Korrekturen
                </button>
              </div>
              <!-- Zeile 2: Mindestbestand + E-Mail-Toggle -->
              <div class="stock-row">
                <div class="form-group minimum-stock-group">
                  <label for="minimum-stock">Mindestbestand</label>
                  <input
                    id="minimum-stock"
                    v-model.number="formData.minimumStock"
                    type="number"
                    min="0"
                    step="1"
                    :disabled="formData.isUnlimitedStock"
                  >
                </div>
                <label class="toggle-switch toggle-switch--inner">
                  <input
                    id="notify-on-low-stock"
                    v-model="formData.notifyOnLowStock"
                    type="checkbox"
                    :disabled="formData.isUnlimitedStock"
                  >
                  <span class="toggle-track"><span class="toggle-thumb"></span></span>
                  <span class="toggle-label">
                    <span class="label">E-Mail bei Unterschreitung</span>
                  </span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <footer class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="$emit('close')">Abbrechen</button>
          <button type="submit" class="btn btn-success">
            {{ editingId ? 'Änderungen speichern' : 'Produkt anlegen' }}
          </button>
        </footer>
      </form>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: { type: Boolean, required: true },
  editingId: { type: [Number, String], default: null },
  imagePreviewSrc: { type: String, default: null },
  isGif: { type: Boolean, default: false },
  productPreviewAlt: { type: String, default: '' },
  previewPriceText: { type: String, default: '' },
  warengruppeOptions: { type: Array, required: true },
  showCorrectionsShortcut: { type: Boolean, default: false },
})

const formData = defineModel('formData', {
  type: Object,
  required: true,
})

defineEmits(['close', 'save', 'open-crop', 'image-upload', 'unlimited-stock-change', 'go-to-corrections', 'remove-image'])
</script>

<style scoped lang="scss">
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-card {
  --border: #e2e8f0;
  --primary: #3b82f6;

  background: white;
  width: 100%;
  max-height: 650px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.modal-compact {
  max-width: 650px;
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
    margin: 0.35rem 0 0;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.9);
  }
}

.modal-compact-layout {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-scroller {
  padding: 1rem 1.2rem;
  overflow-y: auto;
  max-height: calc(650px - 110px);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.main-form-grid {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 1.5rem;
  align-items: start;
}

.section-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #64748b;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.image-upload-section {
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

.image-preview-shell {
  position: relative;
  width: fit-content;
}

.image-remove-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 22px;
  height: 22px;
  border: none;
  border-radius: 999px;
  background: #dc2626;
  color: #fff;
  font-size: 0.85rem;
  font-weight: 700;
  line-height: 1;
  display: grid;
  place-items: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.35);

  &:hover {
    background: #b91c1c;
  }
}

.compact-avatar {
  width: 100%;
  height: 120px;
  border-radius: 10px;
  background: #f8fafc;
  margin-bottom: 0.5rem;
}

.image-preview-trigger {
  display: block;
  width: 100%;
  padding: 0;
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.interactive-image-card {
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}

.card-img {
  position: relative;
}

.image-preview-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.58);
  color: #fff;
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.image-preview-trigger:hover .interactive-image-card,
.image-preview-trigger:focus-visible .interactive-image-card {
  transform: translateY(-1px);
  border-color: #93c5fd;
  box-shadow: 0 8px 18px rgba(14, 165, 233, 0.18);
}

.image-preview-trigger:hover .image-preview-overlay,
.image-preview-trigger:focus-visible .image-preview-overlay {
  opacity: 1;
}

.image-preview-trigger:focus-visible {
  outline: 2px solid #38bdf8;
  outline-offset: 4px;
  border-radius: 12px;
}

.hint-upload {
  width: 100%;
  font-size: 0.85rem;
  text-align: center;
  padding: 0.5rem;
}

.gif-replace-btn {
  margin-top: 0.4rem;
}

.gif-badge {
  position: absolute;
  bottom: 3px;
  right: 3px;
  z-index: 1;
  font-size: 9px;
  font-weight: 800;
  padding: 2px 4px;
  border-radius: 3px;
  background: #fef3c7;
  color: #92400e;
}

.gif-hint {
  margin: 0.45rem 0 0;
  font-size: 0.73rem;
  line-height: 1.35;
  color: #92400e;
}

.fields-section {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;

  .form-group {
    margin-bottom: 0;
  }
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.form-group {
  label {
    display: block;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 0.35rem;
    color: #334155;
  }

  input {
    width: 100%;
    padding: 0.55rem 0.75rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.9rem;
    color: #0f172a;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;

    &:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
  }
}

.options-form-grid {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  border-top: 1px dashed var(--border);
  padding-top: 1.1rem;
}

.toggle-row {
  display: flex;
  gap: 1.25rem;
  flex-wrap: wrap;
}

.toggle-switch {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  cursor: pointer;
  user-select: none;
  flex: 1;
  min-width: 180px;

  input {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
  }

  .toggle-track {
    flex-shrink: 0;
    width: 36px;
    height: 20px;
    border-radius: 999px;
    background: #cbd5e1;
    position: relative;
    transition: background 0.18s ease;

    .toggle-thumb {
      position: absolute;
      top: 3px;
      left: 3px;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: #fff;
      box-shadow: 0 1px 3px rgba(0,0,0,0.2);
      transition: transform 0.18s ease;
    }
  }

  input:checked ~ .toggle-track {
    background: #10b981;
    .toggle-thumb { transform: translateX(16px); }
  }

  input:disabled ~ .toggle-track {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .toggle-label {
    .label {
      display: block;
      font-size: 0.85rem;
      font-weight: 600;
      color: #1e293b;
    }
    .desc {
      display: block;
      font-size: 0.72rem;
      color: #64748b;
      line-height: 1.3;
      margin-top: 0.05rem;
    }
  }
}

.toggle-switch--inner {
  margin-bottom: 0.35rem;
  flex: none;
}

.compact-summary {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: 8px;
  padding: 0.65rem 0.85rem;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem 1.25rem;

  .stock-row {
    display: flex;
    align-items: center;
    gap: 0.6rem;
  }

  .label {
    font-size: 0.75rem;
    text-transform: uppercase;
    color: #065f46;
    font-weight: 600;
    letter-spacing: 0.02em;
    white-space: nowrap;
  }

  .value {
    font-size: 0.95rem;
    font-weight: 700;
    color: #047857;
    margin: 0;
    line-height: 1;
  }
}

.minimum-stock-group {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  label {
    font-size: 0.75rem;
    color: #065f46;
    font-weight: 600;
    white-space: nowrap;
    margin: 0;
  }

  input {
    width: 70px;
  }
}


.corrections-jump-btn {
  margin-top: 0.5rem;
  align-self: flex-start;
  border: 1px solid #93c5fd;
  background: #dbeafe;
  color: #1e3a8a;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  cursor: pointer;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border);
  background: #f8fafc;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn {
  padding: 0.55rem 1.1rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-size: 0.9rem;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  transition: opacity 0.15s ease;

  &:hover {
    opacity: 0.9;
  }
}

.btn-success { background: #10b981; color: white; }
.btn-secondary { background: #e2e8f0; color: #475569; }

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

.kasse-card-preview {
  width: 180px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.07);

  .card-img {
    height: 80px;
    overflow: hidden;
    background: #eef1f7;
    position: relative;
  }

  .preview-crop-img {
    display: block;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .card-badge {
    position: absolute;
    top: 3px;
    left: 3px;
    z-index: 1;
    font-size: 9px;
    font-weight: 800;
    padding: 2px 4px;
    border-radius: 3px;

    &.discount-badge {
      background: #fffbeb;
      color: #d97706;
    }
  }

  .card-body {
    padding: 5px 6px 6px;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .card-name {
    font-size: 0.72rem;
    font-weight: 700;
    line-height: 1.2;
    color: #111827;
  }

  .card-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: auto;
  }

  .card-price {
    font-size: 0.82rem;
    font-weight: 800;
    color: var(--primary);
    letter-spacing: -0.02em;
  }

  .card-stock {
    font-size: 0.64rem;
    color: #64748b;
    font-weight: 500;
  }
}

.avatar-display {
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed var(--border);
}

.photo-placeholder {
  text-align: center;
  color: #94a3b8;
  font-size: 0.8rem;
  line-height: 1.4;
}

.upload-button {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  border: 1px solid var(--border);
  background: white;
  color: #334155;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.15s ease;

  &:hover {
    background: #f8fafc;
  }
}

@media (max-width: 640px) {
  .main-form-grid {
    grid-template-columns: 1fr;
    gap: 1.25rem;
  }

  .image-upload-section {
    align-items: center;

    .kasse-card-preview {
      width: 100%;
      max-width: 240px;
    }
  }

  .options-form-grid {
    gap: 0.75rem;
  }

  .toggle-row {
    flex-direction: column;
    gap: 0.65rem;
  }

  .modal-footer {
    flex-direction: column-reverse;

    .btn {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>
