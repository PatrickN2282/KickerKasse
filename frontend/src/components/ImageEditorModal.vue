<template>
  <div v-if="show" class="modal-overlay" @click.self="closeModal">
    <div class="modal-card editor-modal-card">
      <header class="modal-header">
        <div>
          <h3>{{ title }}</h3>
          <p class="modal-subtitle">{{ subtitle }}</p>
        </div>
        <button type="button" class="close-btn" @click="closeModal">✕</button>
      </header>

      <div class="modal-body">
        <div
          ref="cropFrameEl"
          class="crop-frame"
          :style="cropFrameStyle"
          :class="{ 'is-empty': !localImageSrc }"
          @mousedown.prevent="onCropDragStart"
          @wheel.prevent="onCropWheel"
          @touchstart.prevent="onCropTouchStart"
          @touchmove.prevent="onCropTouchMove"
          @touchend="onCropTouchEnd"
        >
          <img
            v-if="localImageSrc"
            :src="localImageSrc"
            class="crop-source-img"
            :style="cropImgStyle"
            draggable="false"
            alt=""
          >
          <div v-else class="empty-state">Kein Bild ausgewählt.</div>
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
            :disabled="!localImageSrc"
            @input="onZoomSliderInput"
          >
          <span class="zoom-icon">+</span>
          <span class="zoom-pct">{{ zoomPercent }}%</span>
        </div>

        <div class="crop-actions">
          <button type="button" class="btn-action" :disabled="!localImageSrc" @click="resetCrop">↺ Ausrichtung zurücksetzen</button>
          <button
            v-if="canRestore && restoreSource"
            type="button"
            class="btn-action btn-action-restore"
            @click="restoreOriginalImage"
          >
            🔄 {{ restoreLabel }}
          </button>
          <button
            v-if="canDelete"
            type="button"
            class="btn-action btn-action-danger"
            @click="deleteImage"
          >
            🗑 {{ deleteLabel }}
          </button>
        </div>
      </div>

      <footer class="modal-footer">
        <button type="button" class="btn btn-secondary" @click="closeModal">Abbrechen</button>
        <button type="button" class="btn btn-success" :disabled="!localImageSrc" @click="applyCrop">Ausschnitt übernehmen</button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  imageSrc: {
    type: String,
    default: null,
  },
  restoreSource: {
    type: String,
    default: null,
  },
  title: {
    type: String,
    default: 'Bild bearbeiten',
  },
  subtitle: {
    type: String,
    default: 'Verschieben und zoomen, um den passenden Ausschnitt festzulegen.',
  },
  aspectRatio: {
    type: Number,
    default: 3 / 2,
  },
  frameWidth: {
    type: Number,
    default: 320,
  },
  outputWidth: {
    type: Number,
    default: 600,
  },
  jpegQuality: {
    type: Number,
    default: 0.92,
  },
  canRestore: {
    type: Boolean,
    default: false,
  },
  restoreLabel: {
    type: String,
    default: 'Originalbild wiederherstellen',
  },
  canDelete: {
    type: Boolean,
    default: false,
  },
  deleteLabel: {
    type: String,
    default: 'Bild löschen',
  },
})

const emit = defineEmits(['close', 'apply', 'delete'])

const cropFrameEl = ref(null)
const localImageSrc = ref(null)
const cropNaturalW = ref(0)
const cropNaturalH = ref(0)
const cropScale = ref(1)
const cropMinScale = ref(0.1)
const cropPanX = ref(0)
const cropPanY = ref(0)
const cropIsDragging = ref(false)
const cropDragLastX = ref(0)
const cropDragLastY = ref(0)
const cropLastPinchDist = ref(0)

const frameHeight = computed(() => Math.round(props.frameWidth / props.aspectRatio))
const outputHeight = computed(() => Math.round(props.outputWidth / props.aspectRatio))

const cropFrameStyle = computed(() => ({
  width: `${props.frameWidth}px`,
  height: `${frameHeight.value}px`,
  cursor: cropIsDragging.value ? 'grabbing' : 'grab',
}))

const cropImgStyle = computed(() => ({
  position: 'absolute',
  left: `${cropPanX.value}px`,
  top: `${cropPanY.value}px`,
  width: `${cropNaturalW.value * cropScale.value}px`,
  height: `${cropNaturalH.value * cropScale.value}px`,
  userSelect: 'none',
  pointerEvents: 'none',
}))

const zoomPercent = computed(() => {
  if (cropMinScale.value <= 0) return 100
  return Math.round(cropScale.value / cropMinScale.value * 100)
})

const removeMouseListeners = () => {
  document.removeEventListener('mousemove', onDocCropMouseMove)
  document.removeEventListener('mouseup', onDocCropMouseUp)
}

const resetState = () => {
  localImageSrc.value = null
  cropNaturalW.value = 0
  cropNaturalH.value = 0
  cropScale.value = 1
  cropMinScale.value = 0.1
  cropPanX.value = 0
  cropPanY.value = 0
  cropIsDragging.value = false
  cropDragLastX.value = 0
  cropDragLastY.value = 0
  cropLastPinchDist.value = 0
  removeMouseListeners()
}

const centerCrop = () => {
  const scaledW = cropNaturalW.value * cropScale.value
  const scaledH = cropNaturalH.value * cropScale.value
  cropPanX.value = (props.frameWidth - scaledW) / 2
  cropPanY.value = (frameHeight.value - scaledH) / 2
}

const clampPan = () => {
  const scaledW = cropNaturalW.value * cropScale.value
  const scaledH = cropNaturalH.value * cropScale.value
  cropPanX.value = Math.min(0, Math.max(props.frameWidth - scaledW, cropPanX.value))
  cropPanY.value = Math.min(0, Math.max(frameHeight.value - scaledH, cropPanY.value))
}

const loadCropImageDimensions = (source) => {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => {
      localImageSrc.value = source
      cropNaturalW.value = img.naturalWidth
      cropNaturalH.value = img.naturalHeight
      const scaleToFitW = props.frameWidth / img.naturalWidth
      const scaleToFitH = frameHeight.value / img.naturalHeight
      cropMinScale.value = Math.max(scaleToFitW, scaleToFitH)
      cropScale.value = cropMinScale.value
      centerCrop()
      resolve(true)
    }
    img.onerror = () => {
      resetState()
      resolve(false)
    }
    img.src = source
  })
}

const restoreOriginalImage = async () => {
  if (!props.restoreSource) return
  await loadCropImageDimensions(props.restoreSource)
}

const resetCrop = () => {
  if (!localImageSrc.value) return
  cropScale.value = cropMinScale.value
  centerCrop()
}

const onCropDragStart = (event) => {
  if (!localImageSrc.value) return
  cropIsDragging.value = true
  cropDragLastX.value = event.clientX
  cropDragLastY.value = event.clientY
  document.addEventListener('mousemove', onDocCropMouseMove)
  document.addEventListener('mouseup', onDocCropMouseUp)
}

const onDocCropMouseMove = (event) => {
  if (!cropIsDragging.value) return
  const dx = event.clientX - cropDragLastX.value
  const dy = event.clientY - cropDragLastY.value
  cropPanX.value += dx
  cropPanY.value += dy
  cropDragLastX.value = event.clientX
  cropDragLastY.value = event.clientY
  clampPan()
}

const onDocCropMouseUp = () => {
  cropIsDragging.value = false
  removeMouseListeners()
}

const zoomAroundPoint = (newScale, centerX, centerY) => {
  const factor = newScale / cropScale.value
  cropPanX.value = centerX - (centerX - cropPanX.value) * factor
  cropPanY.value = centerY - (centerY - cropPanY.value) * factor
  cropScale.value = newScale
  clampPan()
}

const onCropWheel = (event) => {
  if (!localImageSrc.value) return
  const direction = event.deltaY > 0 ? -1 : 1
  const delta = direction * 0.08 * cropScale.value
  const newScale = Math.max(cropMinScale.value, Math.min(cropMinScale.value * 5, cropScale.value + delta))
  zoomAroundPoint(newScale, props.frameWidth / 2, frameHeight.value / 2)
}

const onZoomSliderInput = (event) => {
  if (!localImageSrc.value) return
  const newScale = parseFloat(event.target.value)
  zoomAroundPoint(newScale, props.frameWidth / 2, frameHeight.value / 2)
}

const onCropTouchStart = (event) => {
  if (!localImageSrc.value) return
  if (event.touches.length === 1) {
    cropIsDragging.value = true
    cropDragLastX.value = event.touches[0].clientX
    cropDragLastY.value = event.touches[0].clientY
    cropLastPinchDist.value = 0
  } else if (event.touches.length === 2) {
    cropIsDragging.value = false
    const dx = event.touches[0].clientX - event.touches[1].clientX
    const dy = event.touches[0].clientY - event.touches[1].clientY
    cropLastPinchDist.value = Math.hypot(dx, dy)
  }
}

const onCropTouchMove = (event) => {
  if (!localImageSrc.value) return
  if (event.touches.length === 1 && cropIsDragging.value) {
    const dx = event.touches[0].clientX - cropDragLastX.value
    const dy = event.touches[0].clientY - cropDragLastY.value
    cropPanX.value += dx
    cropPanY.value += dy
    cropDragLastX.value = event.touches[0].clientX
    cropDragLastY.value = event.touches[0].clientY
    clampPan()
  } else if (event.touches.length === 2 && cropLastPinchDist.value > 0) {
    const dx = event.touches[0].clientX - event.touches[1].clientX
    const dy = event.touches[0].clientY - event.touches[1].clientY
    const dist = Math.hypot(dx, dy)
    const newScale = Math.max(cropMinScale.value, Math.min(cropMinScale.value * 5, cropScale.value * (dist / cropLastPinchDist.value)))
    const frameRect = cropFrameEl.value?.getBoundingClientRect() || {
      left: 0,
      top: 0,
      right: 0,
      bottom: 0,
      width: 0,
      height: 0,
      x: 0,
      y: 0,
    }
    const midX = (event.touches[0].clientX + event.touches[1].clientX) / 2 - frameRect.left
    const midY = (event.touches[0].clientY + event.touches[1].clientY) / 2 - frameRect.top
    zoomAroundPoint(newScale, midX, midY)
    cropLastPinchDist.value = dist
  }
}

const onCropTouchEnd = () => {
  cropIsDragging.value = false
  cropLastPinchDist.value = 0
}

const getCroppedResult = () => {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement('canvas')
    canvas.width = props.outputWidth
    canvas.height = outputHeight.value
    const ctx = canvas.getContext('2d')
    if (!ctx) {
      reject(new Error('Canvas context unavailable'))
      return
    }

    const img = new Image()
    img.onload = () => {
      const sx = Math.max(0, -cropPanX.value / cropScale.value)
      const sy = Math.max(0, -cropPanY.value / cropScale.value)
      const sw = Math.min(props.frameWidth / cropScale.value, img.naturalWidth - sx)
      const sh = Math.min(frameHeight.value / cropScale.value, img.naturalHeight - sy)
      ctx.drawImage(img, sx, sy, sw, sh, 0, 0, props.outputWidth, outputHeight.value)
      const dataUrl = canvas.toDataURL('image/jpeg', props.jpegQuality)
      canvas.toBlob((blob) => {
        if (!blob) {
          reject(new Error('Canvas toBlob empty'))
          return
        }
        resolve({ blob, dataUrl })
      }, 'image/jpeg', props.jpegQuality)
    }
    img.onerror = () => reject(new Error('Image loading failed'))
    img.src = localImageSrc.value
  })
}

const applyCrop = async () => {
  if (!localImageSrc.value) return
  const result = await getCroppedResult()
  emit('apply', result)
}

const closeModal = () => {
  emit('close')
}

const deleteImage = () => {
  emit('delete')
}

watch(
  () => [props.show, props.imageSrc],
  async ([show, imageSrc]) => {
    if (!show || !imageSrc) {
      resetState()
      return
    }
    await loadCropImageDimensions(imageSrc)
  },
  { immediate: true }
)

onUnmounted(() => {
  removeMouseListeners()
})
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
  z-index: 1100;
  padding: 1rem;
}

.modal-card {
  background: white;
  width: 100%;
  max-width: 520px;
  max-height: 650px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  overflow: hidden;
}

.modal-header {
  padding: 0.95rem 1.2rem;
  border-bottom: 1px solid #e2e8f0;
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
}

.modal-subtitle {
  margin: 0.35rem 0 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.85rem;
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
  padding: 1.2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  overflow-y: auto;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}

.crop-frame {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  border: 2px solid #0ea5e9;
  background: linear-gradient(135deg, #e2e8f0, #cbd5e1);
  touch-action: none;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.35);
}

.crop-source-img {
  display: block;
  max-width: none;
  max-height: none;
}

.empty-state {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #64748b;
  font-size: 0.9rem;
  padding: 1rem;
}

.crop-zoom-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
}

.zoom-icon {
  font-size: 1.1rem;
  color: #64748b;
  font-weight: 700;
  user-select: none;
}

.zoom-slider {
  flex: 1;
  cursor: pointer;
  accent-color: #0ea5e9;
}

.zoom-pct {
  font-size: 0.8rem;
  color: #475569;
  min-width: 3rem;
  text-align: right;
  font-weight: 700;
}

.crop-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  justify-content: center;
}

.btn-action {
  border: 1px solid #cbd5e1;
  background: white;
  color: #334155;
  padding: 0.45rem 0.8rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.82rem;

  &:hover:not(:disabled) {
    background: #f8fafc;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.btn-action-restore {
  border-color: #fcd34d;
  color: #92400e;
  background: #fffbeb;

  &:hover:not(:disabled) {
    background: #fef3c7;
  }
}

.btn-action-danger {
  border-color: #fecaca;
  color: #b91c1c;
  background: #fff5f5;

  &:hover:not(:disabled) {
    background: #fef2f2;
  }
}

.modal-footer {
  padding: 0.85rem 1.2rem;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn {
  padding: 0.6rem 1.1rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-size: 0.9rem;
  min-height: 40px;
}

.btn-success {
  background: #10b981;
  color: white;
}

.btn-secondary {
  background: #e2e8f0;
  color: #475569;
}

@media (max-width: 640px) {
  .modal-card {
    max-width: 100%;
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .btn {
    width: 100%;
  }
}
</style>
