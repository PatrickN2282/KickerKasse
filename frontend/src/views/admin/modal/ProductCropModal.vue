<template>
  <div
    v-if="show"
    class="modal-overlay crop-modal-overlay"
    @click.self="$emit('close')"
  >
    <div class="crop-modal-card">
      <header class="modal-header">
        <div>
          <h3>Bildausschnitt anpassen</h3>
          <p class="modal-subtitle">Verschieben und zoomen – Änderungen werden beim Speichern des Produkts übernommen.</p>
        </div>
        <button
          class="modal-close"
          @click="$emit('close')"
        >
          ×
        </button>
      </header>

      <div class="crop-modal-body">
        <div
          ref="cropFrameEl"
          class="crop-frame"
          :style="{ cursor: cropIsDragging ? 'grabbing' : 'grab' }"
          @mousedown.prevent="$emit('drag-start', $event)"
          @wheel.prevent="$emit('wheel', $event)"
          @touchstart.prevent="$emit('touch-start', $event)"
          @touchmove.prevent="$emit('touch-move', $event)"
          @touchend="$emit('touch-end')"
        >
          <img
            :src="cropImageSrc"
            class="crop-source-img"
            :style="cropImgStyle"
            draggable="false"
            alt=""
          >
        </div>

        <div class="crop-zoom-row">
          <span class="zoom-icon">−</span>
          <input
            :value="cropScale"
            type="range"
            :min="cropMinScale"
            :max="cropMinScale * 5"
            :step="0.005"
            class="zoom-slider"
            @input="$emit('zoom-input', $event)"
          >
          <span class="zoom-icon">+</span>
          <span class="zoom-pct">{{ cropMinScale > 0 ? Math.round(cropScale / cropMinScale * 100) : 100 }}%</span>
        </div>
        <div class="crop-action-row">
          <button
            type="button"
            class="btn-crop-reset"
            @click="$emit('reset-crop')"
          >
            ↺ Zurücksetzen
          </button>
          <button
            v-if="cropOriginalSrc"
            type="button"
            class="btn-crop-reset btn-crop-restore"
            @click="$emit('restore-original')"
          >
            🔄 Originalbild
          </button>
        </div>
      </div>

      <footer class="crop-modal-footer">
        <button
          type="button"
          class="btn btn-success"
          @click="$emit('close')"
        >
          Fertig
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  show: { type: Boolean, required: true },
  cropImageSrc: { type: String, default: null },
  cropOriginalSrc: { type: String, default: null },
  cropScale: { type: Number, default: 1 },
  cropMinScale: { type: Number, default: 0.1 },
  cropPanX: { type: Number, default: 0 },
  cropPanY: { type: Number, default: 0 },
  cropIsDragging: { type: Boolean, default: false },
  cropImgStyle: { type: Object, default: () => ({}) },
})

defineEmits(['close', 'drag-start', 'wheel', 'touch-start', 'touch-move', 'touch-end', 'zoom-input', 'reset-crop', 'restore-original'])

const cropFrameEl = ref(null)

defineExpose({ cropFrameEl })
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

.crop-modal-overlay {
  z-index: 1001;
}

.crop-modal-card {
  --success: #10b981;
  --border: #e2e8f0;
  --primary: #3b82f6;
  background: white;
  width: 100%;
  max-width: 480px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.35);
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
}

.modal-close {
  border: none;
  background: transparent;
  font-size: 1.6rem;
  line-height: 1;
  cursor: pointer;
  color: #6b7280;
}

.crop-modal-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.crop-frame {
  width: 320px;
  height: 213px;
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  border: 2px solid var(--primary);
  background: #e2e8f0;
  flex-shrink: 0;
  touch-action: none;
  user-select: none;
}

.crop-source-img {
  display: block;
  max-width: none;
  max-height: none;
}

.crop-zoom-row {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;

  .zoom-icon {
    font-size: 1rem;
    color: #64748b;
    font-weight: 700;
    line-height: 1;
    cursor: default;
    user-select: none;
  }

  .zoom-pct {
    font-size: 0.72rem;
    color: #64748b;
    min-width: 2.6rem;
    text-align: right;
  }
}

.zoom-slider {
  flex: 1;
  cursor: pointer;
  accent-color: var(--primary);
}

.crop-action-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  align-self: flex-start;
}

.btn-crop-reset {
  align-self: flex-start;
  padding: 0.3rem 0.75rem;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: white;
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
  cursor: pointer;

  &:hover {
    background: #f1f5f9;
  }
}

.btn-crop-restore {
  border-color: #fcd34d;
  color: #92400e;
  background: #fffbeb;

  &:hover {
    background: #fef3c7;
  }
}

.crop-modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
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
</style>
