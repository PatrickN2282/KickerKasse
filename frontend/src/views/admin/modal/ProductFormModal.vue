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
                  <label class="upload-button hint-upload gif-replace-btn">
                    Bild ersetzen
                    <input id="image" type="file" accept="image/*" hidden @change="$emit('image-upload', $event)">
                  </label>
                </template>

                <template v-else>
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
                </template>
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
            <div class="checkbox-group-wrapper">
              <label class="checkbox-card compact-cb">
                <input id="unlimited-stock" v-model="formData.isUnlimitedStock" type="checkbox" @change="$emit('unlimited-stock-change')">
                <div class="checkbox-content">
                  <span class="label">Unendlich verfügbar</span>
                  <span class="desc">Für immaterielle Artikel (z.B. Eintritte oder Umlagen)</span>
                </div>
              </label>

              <label class="checkbox-card compact-cb">
                <input id="variable-price" v-model="formData.isVariablePrice" type="checkbox">
                <div class="checkbox-content">
                  <span class="label">Variabler Endpreis</span>
                  <span class="desc">Der Preis wird erst beim Bonieren abgefragt</span>
                </div>
              </label>
            </div>

            <div class="summary-card compact-summary">
              <div class="summary-text-layout">
                <span class="label">Lagerbestand</span>
                <span class="value">{{ formData.isUnlimitedStock ? '∞' : formData.stock }}</span>
              </div>
              <span class="desc">Bestandskorrekturen erfolgen über das Finanzen-Modul.</span>
              <button
                v-if="editingId && showCorrectionsShortcut"
                type="button"
                class="corrections-jump-btn"
                title="Zu Finanzen → Korrekturen wechseln"
                aria-label="Zu Finanzen → Korrekturen wechseln"
                @click="$emit('go-to-corrections')"
              >
                ↗ Korrekturen
              </button>
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

defineEmits(['close', 'save', 'open-crop', 'image-upload', 'unlimited-stock-change', 'go-to-corrections'])
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
  display: grid;
  grid-template-columns: 1fr 200px;
  gap: 1rem;
  border-top: 1px dashed var(--border);
  padding-top: 1.25rem;
}

.checkbox-group-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.compact-cb {
  padding: 0.65rem 0.85rem;
  background: #f8fafc;
  display: flex;
  gap: 0.6rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  cursor: pointer;
  align-items: flex-start;
  transition: background-color 0.15s ease, border-color 0.15s ease;

  &:hover {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }

  input {
    margin-top: 0.2rem;
  }

  .checkbox-content {
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

.compact-summary {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  justify-content: center;

  .summary-text-layout {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }

  .label {
    font-size: 0.7rem;
    text-transform: uppercase;
    color: #065f46;
    font-weight: 700;
    letter-spacing: 0.02em;
  }

  .value {
    font-size: 1.3rem;
    font-weight: 800;
    color: #047857;
    margin: 0;
    line-height: 1;
  }

  .desc {
    font-size: 0.7rem;
    color: #065f46;
    margin-top: 0.35rem;
    line-height: 1.2;
    opacity: 0.85;
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
    height: 62px;
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
    grid-template-columns: 1fr;
    gap: 1rem;
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
