<template>
  <div
    v-if="show"
    class="modal-overlay product-modal"
    @click.self="handleClose"
  >
    <div class="modal-card">
      <header class="modal-header">
        <div>
          <h3>{{ editingId ? 'Produkt bearbeiten' : 'Neues Produkt anlegen' }}</h3>
          <p class="modal-subtitle">Pflichtangaben, Preise und Bild im angepassten Admin-Layout verwalten.</p>
        </div>
        <button
          class="modal-close"
          @click="handleClose"
        >
          ×
        </button>
      </header>

      <form
        class="modal-body-layout"
        @submit.prevent="handleSaveProduct"
      >
        <aside class="modal-sidebar">
          <div class="product-image-panel">
            <!-- Image loaded: show card preview + action buttons -->
            <template v-if="cropImageSrc">
              <p class="image-editor-label">Vorschau: Kassenkarte</p>
              <div class="kasse-card-preview product-btn-preview">
                <div class="card-img">
                  <span
                    v-if="hasMemberPrice({ member_price_cents: formData.memberPrice !== null ? 1 : null })"
                    class="card-badge discount-badge"
                  >Rabatt</span>
                  <img
                    :src="cropImageSrc"
                    class="preview-crop-img"
                    :style="cropPreviewImgStyle"
                    draggable="false"
                    alt=""
                  >
                </div>
                <div class="card-body">
                  <div class="card-name">{{ formData.name || 'Produktname' }}</div>
                  <div class="card-bottom">
                    <span class="card-price">{{ previewPriceText }}</span>
                    <span class="card-stock">{{ formData.isUnlimitedStock ? '∞' : formData.stock }}</span>
                  </div>
                </div>
              </div>

              <div class="crop-sidebar-actions">
                <button
                  type="button"
                  class="btn-crop-open"
                  @click="showCropModal = true"
                >
                  ✂ Bildausschnitt anpassen
                </button>
                <label class="upload-button">
                  Anderes Bild
                  <input
                    type="file"
                    accept="image/*"
                    hidden
                    @change="handleImageUpload"
                  >
                </label>
              </div>
            </template>

            <!-- Default view: no image selected yet -->
            <template v-else>
              <div class="avatar-display">
                <div class="photo-placeholder">
                  <span>Bild hochladen</span>
                </div>
              </div>
              <label class="upload-button">
                Bild auswählen
                <input
                  id="image"
                  type="file"
                  accept="image/*"
                  hidden
                  @change="handleImageUpload"
                >
              </label>
            </template>
          </div>

          <div class="sidebar-info-box">
            <label class="checkbox-card">
              <input
                id="unlimited-stock"
                v-model="formData.isUnlimitedStock"
                type="checkbox"
                @change="handleUnlimitedStockChange"
              >
              <div class="checkbox-content">
                <span class="label">Unendlich verfügbar</span>
                <span class="desc">Artikel ohne Bestand, z. B. Eintrittspreise, bleiben immer buchbar.</span>
              </div>
            </label>

            <label class="checkbox-card">
              <input
                id="variable-price"
                v-model="formData.isVariablePrice"
                type="checkbox"
              >
              <div class="checkbox-content">
                <span class="label">Variabler Endpreis</span>
                <span class="desc">Beim Hinzufügen zum Warenkorb wird nach dem Preis gefragt.</span>
              </div>
            </label>

            <div class="summary-card">
              <span class="label">Lagerbestand</span>
              <span class="value">{{ formData.isUnlimitedStock ? '∞' : formData.stock }}</span>
            </div>
          </div>
        </aside>

        <main class="modal-form-content">
          <section class="form-section">
            <h4>Allgemeine Informationen</h4>
            <div class="form-row">
              <div class="form-group">
                <label for="name">Name*</label>
                <input
                  id="name"
                  v-model="formData.name"
                  type="text"
                  required
                >
              </div>
              <div class="form-group">
                <label for="warengruppe">Warengruppe</label>
                <input
                  id="warengruppe"
                  v-model.trim="formData.warengruppe"
                  type="text"
                  list="warengruppe-options"
                  placeholder="Neue oder bestehende Warengruppe"
                >
                <datalist id="warengruppe-options">
                  <option
                    v-for="group in warengruppeOptions"
                    :key="group"
                    :value="group"
                  />
                </datalist>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label for="stock">Lagerbestand*</label>
                <input
                  id="stock"
                  v-model.number="formData.stock"
                  type="number"
                  min="0"
                  :disabled="formData.isUnlimitedStock"
                  required
                >
              </div>
            </div>
          </section>

          <section class="form-section">
            <h4>Preisgestaltung</h4>
            <div class="form-row">
              <div class="form-group">
                <label for="price">Preis (€)*</label>
                <input
                  id="price"
                  v-model.number="formData.price"
                  type="number"
                  step="0.01"
                  required
                >
              </div>
              <div class="form-group">
                <label for="member-price">Mitgliedspreis (€)</label>
                <input
                  id="member-price"
                  v-model.number="formData.memberPrice"
                  type="number"
                  step="0.01"
                >
              </div>
            </div>
          </section>
        </main>

        <footer class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            @click="handleClose"
          >
            Abbrechen
          </button>
          <button
            type="submit"
            class="btn btn-success"
          >
            {{ editingId ? 'Änderungen speichern' : 'Produkt anlegen' }}
          </button>
        </footer>
      </form>
    </div>
  </div>

  <!-- Crop sub-modal -->
  <ProductCropModal
    ref="cropModalRef"
    :show="showCropModal"
    :crop-image-src="cropImageSrc"
    :crop-original-src="cropOriginalSrc"
    :crop-scale="cropScale"
    :crop-min-scale="cropMinScale"
    :crop-pan-x="cropPanX"
    :crop-pan-y="cropPanY"
    :crop-is-dragging="cropIsDragging"
    :crop-img-style="cropImgStyle"
    @close="showCropModal = false"
    @drag-start="onCropDragStart"
    @wheel="onCropWheel"
    @touch-start="onCropTouchStart"
    @touch-move="onCropTouchMove"
    @touch-end="onCropTouchEnd"
    @zoom-input="onZoomSliderInput"
    @reset-crop="resetCrop"
    @restore-original="restoreOriginalImage"
  />
</template>

<script setup>
import { ref, reactive, watch, computed, onUnmounted } from 'vue'
import { useNotificationStore } from '@/stores/notification'
import ProductCropModal from './ProductCropModal.vue'

const props = defineProps({
  show: { type: Boolean, required: true },
  editingId: { type: Number, default: null },
  editingProduct: { type: Object, default: null },
  warengruppeOptions: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'save'])

const notificationStore = useNotificationStore()

// ── Form state ────────────────────────────────────────────────────────────────
const formData = reactive({
  name: '',
  warengruppe: '',
  price: 0,
  memberPrice: null,
  stock: 0,
  isUnlimitedStock: false,
  isVariablePrice: false,
})
const lastFiniteStock = ref(0)
const imageFile = ref(null)

// ── Crop constants ────────────────────────────────────────────────────────────
const CROP_ASPECT = 3 / 2
const CROP_W = 320
const CROP_H = Math.round(CROP_W / CROP_ASPECT)   // 213 px
const OUTPUT_W = 600
const OUTPUT_H = Math.round(OUTPUT_W / CROP_ASPECT) // 400 px
const JPEG_QUALITY = 0.92
const PREVIEW_W = 180
const PREVIEW_H = Math.round(PREVIEW_W / CROP_ASPECT)  // ≈ 120 px
const PREVIEW_SCALE = PREVIEW_W / CROP_W

// ── Crop state ────────────────────────────────────────────────────────────────
const showCropModal = ref(false)
const cropImageSrc = ref(null)
const cropOriginalSrc = ref(null)
const cropIsNewUpload = ref(false)
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
const cropModified = ref(false)

const cropModalRef = ref(null)

// ── Computed ──────────────────────────────────────────────────────────────────
const cropImgStyle = computed(() => ({
  position: 'absolute',
  left: `${cropPanX.value}px`,
  top: `${cropPanY.value}px`,
  width: `${cropNaturalW.value * cropScale.value}px`,
  height: `${cropNaturalH.value * cropScale.value}px`,
  userSelect: 'none',
  pointerEvents: 'none',
}))

const cropPreviewImgStyle = computed(() => {
  if (!cropNaturalW.value) return {}
  return {
    position: 'absolute',
    left: `${cropPanX.value * PREVIEW_SCALE}px`,
    top: `${cropPanY.value * PREVIEW_SCALE}px`,
    width: `${cropNaturalW.value * cropScale.value * PREVIEW_SCALE}px`,
    height: `${cropNaturalH.value * cropScale.value * PREVIEW_SCALE}px`,
    userSelect: 'none',
    pointerEvents: 'none',
  }
})

const previewPriceText = computed(() => {
  const cents = formData.price ? Math.round(formData.price * 100) : 0
  return `${(cents / 100).toFixed(2).replace('.', ',')} €`
})

const hasMemberPrice = (product) => product.member_price_cents !== null && product.member_price_cents !== undefined

// ── Helpers ───────────────────────────────────────────────────────────────────
const toMemberPriceCents = () => (
  formData.memberPrice === null || formData.memberPrice === ''
    ? null
    : Math.round(formData.memberPrice * 100)
)

const handleUnlimitedStockChange = () => {
  if (formData.isUnlimitedStock) {
    lastFiniteStock.value = formData.stock
    formData.stock = 0
    return
  }
  if (formData.stock === 0 && lastFiniteStock.value > 0) {
    formData.stock = lastFiniteStock.value
  }
}

const resetForm = () => {
  formData.name = ''
  formData.warengruppe = ''
  formData.price = 0
  formData.memberPrice = null
  formData.stock = 0
  formData.isUnlimitedStock = false
  formData.isVariablePrice = false
  lastFiniteStock.value = 0
  imageFile.value = null
  showCropModal.value = false
  cropImageSrc.value = null
  cropOriginalSrc.value = null
  cropIsNewUpload.value = false
  cropNaturalW.value = 0
  cropNaturalH.value = 0
  cropScale.value = 1
  cropMinScale.value = 0.1
  cropPanX.value = 0
  cropPanY.value = 0
  cropIsDragging.value = false
  cropModified.value = false
}

const handleClose = () => {
  resetForm()
  emit('close')
}

// ── Crop helpers ──────────────────────────────────────────────────────────────
const loadCropImageDimensions = (dataUrl) => new Promise((resolve) => {
  const img = new Image()
  img.onload = () => {
    cropNaturalW.value = img.naturalWidth
    cropNaturalH.value = img.naturalHeight
    const scaleToFitW = CROP_W / img.naturalWidth
    const scaleToFitH = CROP_H / img.naturalHeight
    cropMinScale.value = Math.max(scaleToFitW, scaleToFitH)
    cropScale.value = cropMinScale.value
    centerCrop()
    resolve()
  }
  img.onerror = () => {
    notificationStore.error('Bild konnte nicht geladen werden')
    resolve()
  }
  img.src = dataUrl
})

const clampPan = () => {
  const scaledW = cropNaturalW.value * cropScale.value
  const scaledH = cropNaturalH.value * cropScale.value
  cropPanX.value = Math.min(0, Math.max(CROP_W - scaledW, cropPanX.value))
  cropPanY.value = Math.min(0, Math.max(CROP_H - scaledH, cropPanY.value))
}

const centerCrop = () => {
  const scaledW = cropNaturalW.value * cropScale.value
  const scaledH = cropNaturalH.value * cropScale.value
  cropPanX.value = (CROP_W - scaledW) / 2
  cropPanY.value = (CROP_H - scaledH) / 2
}

const resetCrop = () => {
  cropScale.value = cropMinScale.value
  centerCrop()
  if (cropIsNewUpload.value) {
    cropModified.value = true
  }
}

const restoreOriginalImage = async () => {
  if (!cropOriginalSrc.value) return
  cropImageSrc.value = cropOriginalSrc.value
  await loadCropImageDimensions(cropOriginalSrc.value)
  cropModified.value = true
}

const onCropDragStart = (event) => {
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
  cropModified.value = true
}

const onDocCropMouseUp = () => {
  cropIsDragging.value = false
  document.removeEventListener('mousemove', onDocCropMouseMove)
  document.removeEventListener('mouseup', onDocCropMouseUp)
}

const onCropWheel = (event) => {
  const direction = event.deltaY > 0 ? -1 : 1
  const delta = direction * 0.08 * cropScale.value
  const newScale = Math.max(cropMinScale.value, Math.min(cropMinScale.value * 5, cropScale.value + delta))
  const zoomCenterX = CROP_W / 2
  const zoomCenterY = CROP_H / 2
  const factor = newScale / cropScale.value
  cropPanX.value = zoomCenterX - (zoomCenterX - cropPanX.value) * factor
  cropPanY.value = zoomCenterY - (zoomCenterY - cropPanY.value) * factor
  cropScale.value = newScale
  clampPan()
  cropModified.value = true
}

const onZoomSliderInput = (event) => {
  const newScale = parseFloat(event.target.value)
  const oldScale = cropScale.value
  if (oldScale > 0) {
    const factor = newScale / oldScale
    const zoomCenterX = CROP_W / 2
    const zoomCenterY = CROP_H / 2
    cropPanX.value = zoomCenterX - (zoomCenterX - cropPanX.value) * factor
    cropPanY.value = zoomCenterY - (zoomCenterY - cropPanY.value) * factor
  }
  cropScale.value = newScale
  clampPan()
  cropModified.value = true
}

const onCropTouchStart = (event) => {
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
  if (event.touches.length === 1 && cropIsDragging.value) {
    const dx = event.touches[0].clientX - cropDragLastX.value
    const dy = event.touches[0].clientY - cropDragLastY.value
    cropPanX.value += dx
    cropPanY.value += dy
    cropDragLastX.value = event.touches[0].clientX
    cropDragLastY.value = event.touches[0].clientY
    clampPan()
    cropModified.value = true
  } else if (event.touches.length === 2 && cropLastPinchDist.value > 0) {
    const dx = event.touches[0].clientX - event.touches[1].clientX
    const dy = event.touches[0].clientY - event.touches[1].clientY
    const dist = Math.hypot(dx, dy)
    const factor = dist / cropLastPinchDist.value
    const newScale = Math.max(cropMinScale.value, Math.min(cropMinScale.value * 5, cropScale.value * factor))
    const frameRect = cropModalRef.value?.cropFrameEl?.getBoundingClientRect() ?? { left: 0, top: 0 }
    const midX = (event.touches[0].clientX + event.touches[1].clientX) / 2 - frameRect.left
    const midY = (event.touches[0].clientY + event.touches[1].clientY) / 2 - frameRect.top
    const f = newScale / cropScale.value
    cropPanX.value = midX - (midX - cropPanX.value) * f
    cropPanY.value = midY - (midY - cropPanY.value) * f
    cropScale.value = newScale
    clampPan()
    cropLastPinchDist.value = dist
    cropModified.value = true
  }
}

const onCropTouchEnd = () => {
  cropIsDragging.value = false
  cropLastPinchDist.value = 0
}

const dataUrlToBlob = (dataUrl) => new Promise((resolve, reject) => {
  const parts = dataUrl.split(',')
  const mimeMatch = parts[0].match(/:(.*?);/)
  if (!mimeMatch) { reject(new Error('Invalid data URL')); return }
  const mime = mimeMatch[1]
  const bStr = atob(parts[1])
  const n = bStr.length
  const u8arr = new Uint8Array(n)
  for (let i = 0; i < n; i++) u8arr[i] = bStr.charCodeAt(i)
  resolve(new Blob([u8arr], { type: mime }))
})

const getCroppedBlob = () => new Promise((resolve, reject) => {
  const canvas = document.createElement('canvas')
  canvas.width = OUTPUT_W
  canvas.height = OUTPUT_H
  const ctx = canvas.getContext('2d')
  const img = new Image()
  img.onload = () => {
    const sx = Math.max(0, -cropPanX.value / cropScale.value)
    const sy = Math.max(0, -cropPanY.value / cropScale.value)
    const sw = Math.min(CROP_W / cropScale.value, img.naturalWidth - sx)
    const sh = Math.min(CROP_H / cropScale.value, img.naturalHeight - sy)
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, OUTPUT_W, OUTPUT_H)
    canvas.toBlob((blob) => {
      if (blob) resolve(blob)
      else reject(new Error('Canvas toBlob failed'))
    }, 'image/jpeg', JPEG_QUALITY)
  }
  img.onerror = reject
  img.src = cropImageSrc.value
})

const handleImageUpload = (event) => {
  const file = event.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => {
    cropImageSrc.value = e.target.result
    cropOriginalSrc.value = e.target.result
    cropIsNewUpload.value = true
    loadCropImageDimensions(e.target.result)
    cropModified.value = true
  }
  reader.readAsDataURL(file)
  event.target.value = ''
}

// ── Watch editingProduct ──────────────────────────────────────────────────────
watch(() => props.editingProduct, async (product) => {
  if (!product) return

  formData.name = product.name
  formData.warengruppe = product.warengruppe || ''
  formData.price = product.price_cents / 100
  formData.memberPrice = hasMemberPrice(product) ? product.member_price_cents / 100 : null
  formData.stock = product.stock_quantity
  formData.isUnlimitedStock = !!product.is_unlimited_stock
  formData.isVariablePrice = !!product.is_variable_price
  lastFiniteStock.value = product.stock_quantity
  imageFile.value = null
  cropModified.value = false
  cropIsNewUpload.value = false

  if (product.image_path) {
    try {
      const resp = await fetch(`/api/products/${product.id}/image`, { credentials: 'include' })
      if (!resp.ok) throw new Error(`Image load failed: ${resp.status}`)
      const blob = await resp.blob()
      const dataUrl = await new Promise((resolve) => {
        const reader = new FileReader()
        reader.onload = (e) => resolve(e.target.result)
        reader.readAsDataURL(blob)
      })
      cropImageSrc.value = dataUrl
      await loadCropImageDimensions(dataUrl)

      try {
        const origResp = await fetch(`/api/products/${product.id}/original-image`, { credentials: 'include' })
        if (origResp.ok) {
          const origBlob = await origResp.blob()
          cropOriginalSrc.value = await new Promise((resolve) => {
            const reader = new FileReader()
            reader.onload = (e) => resolve(e.target.result)
            reader.readAsDataURL(origBlob)
          })
        } else {
          cropOriginalSrc.value = null
        }
      } catch {
        cropOriginalSrc.value = null
      }
    } catch {
      cropImageSrc.value = null
      cropOriginalSrc.value = null
      notificationStore.warning('Produktbild konnte nicht geladen werden')
    }
  } else {
    cropImageSrc.value = null
    cropOriginalSrc.value = null
  }
}, { immediate: true, deep: true })

// ── Save ──────────────────────────────────────────────────────────────────────
const handleSaveProduct = async () => {
  let finalImageFile = null
  let originalImageFile = null

  if (cropImageSrc.value && cropModified.value) {
    try {
      const blob = await getCroppedBlob()
      finalImageFile = new File([blob], 'product-image.jpg', { type: 'image/jpeg' })
    } catch (err) {
      console.error('Crop failed:', err)
      notificationStore.error('Fehler beim Verarbeiten des Bildes')
      return
    }
  }

  if (cropIsNewUpload.value && cropOriginalSrc.value) {
    try {
      const origBlob = await dataUrlToBlob(cropOriginalSrc.value)
      originalImageFile = new File([origBlob], 'original.jpg', { type: 'image/jpeg' })
    } catch (err) {
      console.error('Original image conversion error:', err)
    }
  }

  emit('save', {
    name: formData.name,
    warengruppe: formData.warengruppe || null,
    price_cents: Math.round(formData.price * 100),
    member_price_cents: toMemberPriceCents(),
    stock_quantity: formData.isUnlimitedStock ? 0 : formData.stock,
    is_unlimited_stock: formData.isUnlimitedStock,
    is_variable_price: formData.isVariablePrice,
    imageFile: finalImageFile,
    originalImageFile,
    cropIsNewUpload: cropIsNewUpload.value,
  })
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onDocCropMouseMove)
  document.removeEventListener('mouseup', onDocCropMouseUp)
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
  z-index: 1000;
  padding: 1rem;
}

.modal-card {
  --primary: #3b82f6;
  --success: #10b981;
  --bg-main: #f8fafc;
  --border: #e2e8f0;
  background: white;
  width: 100%;
  max-width: 1050px;
  max-height: 90vh;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
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

.modal-body-layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  overflow: hidden;
}

.modal-sidebar {
  padding: 1.5rem;
  background: var(--bg-main);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  overflow-y: auto;
}

.product-image-panel,
.sidebar-info-box {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.modal-form-content {
  padding: 1.5rem;
  overflow-y: auto;
  max-height: calc(90vh - 160px);
}

.avatar-display {
  width: 150px;
  height: 150px;
  margin: 0 auto;
  border-radius: 20px;
  background: #fff;
  border: 2px dashed #cbd5e1;
  overflow: hidden;
}

.photo-placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 1rem;
  font-size: 0.8rem;
  color: #94a3b8;
}

.upload-button {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  padding: 0.65rem 1rem;
  border-radius: 8px;
  background: white;
  border: 1px solid var(--border);
  cursor: pointer;
  font-weight: 600;
  color: #334155;
}

.checkbox-card,
.summary-card {
  padding: 0.9rem 1rem;
  background: white;
  border: 1px solid var(--border);
  border-radius: 10px;
}

.checkbox-card {
  display: flex;
  gap: 0.75rem;
  cursor: pointer;
}

.checkbox-content {
  display: flex;
  flex-direction: column;

  .label {
    font-weight: 600;
    font-size: 0.9rem;
  }

  .desc {
    font-size: 0.75rem;
    color: #64748b;
  }
}

.summary-card {
  background: #ecfdf5;
  border-color: #a7f3d0;

  .label {
    font-size: 0.7rem;
    text-transform: uppercase;
    color: #065f46;
    font-weight: 700;
  }

  .value {
    display: block;
    margin-top: 0.35rem;
    font-size: 1.3rem;
    font-weight: 700;
    color: #047857;
  }
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

  input {
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

.btn {
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.btn-primary {
  background: var(--primary);
  color: white;
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

.modal-footer {
  grid-column: 1 / -1;
  padding: 1.5rem;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

// ── Crop editor & card preview ─────────────────────────────────────────────────
.image-editor-label {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
  margin: 0;
}

.image-editor-hint {
  font-size: 0.72rem;
  color: #94a3b8;
  margin: -0.4rem 0 0;
}

.preview-label {
  margin-top: 0.5rem;
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
    flex-shrink: 0;
    position: relative;
  }

  .preview-crop-img {
    display: block;
    max-width: none;
    max-height: none;
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
    letter-spacing: 0.04em;
    line-height: 1.4;

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
    font-size: .72rem;
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
    font-size: .82rem;
    font-weight: 800;
    color: var(--primary);
    letter-spacing: -0.02em;
  }

  .card-stock {
    font-size: .64rem;
    color: #64748b;
    font-weight: 500;
  }
}

.crop-sidebar-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.btn-crop-open {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  padding: 0.65rem 1rem;
  border-radius: 8px;
  background: var(--primary);
  border: none;
  cursor: pointer;
  font-weight: 600;
  color: white;
  font-size: 0.9rem;

  &:hover {
    background: #2563eb;
  }
}

.crop-file-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .modal-body-layout,
  .form-row {
    grid-template-columns: 1fr;
  }

  .modal-sidebar {
    border-right: none;
    border-bottom: 1px solid var(--border);
  }
}

@media (max-width: 640px) {
  .modal-footer {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }
}
</style>
