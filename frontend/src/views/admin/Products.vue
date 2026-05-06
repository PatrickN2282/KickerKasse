<template>
  <div class="admin-products">
    <div class="page-header">
      <div>
        <h2>Produktverwaltung</h2>
        <p class="page-subtitle">Produkte und Preise im gleichen Layout wie die Mitgliederverwaltung pflegen.</p>
      </div>
      <button class="btn btn-primary" @click="openCreateModal">
        <span class="icon">+</span> Neues Produkt
      </button>
    </div>

    <div v-if="productStore.isLoading" class="loading-state">
      <div class="spinner"></div>
      <p>Daten werden geladen...</p>
    </div>

    <div v-else>
      <div class="table-toolbar">
        <input
          v-model="productSearch"
          type="text"
          placeholder="Nach Produktname suchen..."
          class="search-input"
        >
      </div>
      <div class="products-table-wrapper">
        <table class="products-table">
          <thead>
            <tr>
              <th>Bild</th>
              <th>Name</th>
              <th>Warengruppe</th>
              <th>Preis</th>
              <th>Mitgliedspreis</th>
              <th>Lager</th>
              <th class="text-right">Aktionen</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="product in filteredProducts" :key="product.id">
              <td class="product-image-cell">
                <div class="product-thumb-frame">
                  <img
                    v-if="product.image_path"
                    :src="`/api/products/${product.id}/image`"
                    :alt="product.name"
                    class="product-thumb"
                  >
                  <span v-else class="product-thumb-placeholder">Bild</span>
                </div>
              </td>
              <td>
                <div class="product-name-cell">
                  <span class="font-bold">{{ product.name }}</span>
                  <div class="product-badges">
                    <span v-if="hasMemberPrice(product)" class="badge badge-info">Rabatt</span>
                    <span v-if="product.is_unlimited_stock" class="badge badge-dark">∞</span>
                  </div>
                </div>
              </td>
              <td>{{ product.warengruppe || '—' }}</td>
              <td>{{ formatPrice(product.price_cents) }}</td>
              <td>
                <span :class="['badge', hasMemberPrice(product) ? 'badge-success' : 'badge-light']">
                  {{ hasMemberPrice(product) ? formatPrice(product.member_price_cents) : 'Kein Sonderpreis' }}
                </span>
              </td>
              <td>
                <span :class="['badge', product.is_unlimited_stock ? 'badge-dark' : (product.stock_quantity > 0 ? 'badge-success' : 'badge-danger')]">
                  {{ product.is_unlimited_stock ? '∞' : product.stock_quantity }}
                </span>
              </td>
              <td class="text-right">
                <div class="action-cell">
                  <button class="btn-action" @click="editProduct(product)">Bearbeiten</button>
                  <button class="btn-action btn-action-danger" @click="deleteProduct(product.id)">Löschen</button>
                </div>
              </td>
            </tr>
            <tr v-if="filteredProducts.length === 0">
              <td colspan="7" class="empty-state-cell">Keine Produkte gefunden</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="showProductModal" class="modal-overlay" @click.self="closeProductModal">
      <div class="modal-card">
        <header class="modal-header">
          <div>
            <h3>{{ editingId ? 'Produkt bearbeiten' : 'Neues Produkt anlegen' }}</h3>
            <p class="modal-subtitle">Pflichtangaben, Preise und Bild im angepassten Admin-Layout verwalten.</p>
          </div>
          <button class="modal-close" @click="closeProductModal">×</button>
        </header>

        <form class="modal-body-layout" @submit.prevent="handleSaveProduct">
          <aside class="modal-sidebar">
            <div class="product-image-panel">
              <!-- Image loaded: show card preview + action buttons -->
              <template v-if="cropImageSrc">
                <p class="image-editor-label">Vorschau: Kassenkarte</p>
                <div class="kasse-card-preview product-btn-preview">
                  <div class="card-img">
                    <span v-if="hasMemberPrice({ member_price_cents: formData.memberPrice !== null ? 1 : null })" class="card-badge discount-badge">Rabatt</span>
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
                  <button type="button" class="btn-crop-open" @click="showCropModal = true">✂ Bildausschnitt anpassen</button>
                  <label class="upload-button">
                    Anderes Bild
                    <input type="file" accept="image/*" hidden @change="handleImageUpload">
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
                  <input id="image" type="file" accept="image/*" hidden @change="handleImageUpload">
                </label>
              </template>
            </div>

            <div class="sidebar-info-box">
              <label class="checkbox-card">
                <input id="unlimited-stock" v-model="formData.isUnlimitedStock" type="checkbox" @change="handleUnlimitedStockChange">
                <div class="checkbox-content">
                  <span class="label">Unendlich verfügbar</span>
                  <span class="desc">Artikel ohne Bestand, z. B. Eintrittspreise, bleiben immer buchbar.</span>
                </div>
              </label>

              <label class="checkbox-card">
                <input id="variable-price" v-model="formData.isVariablePrice" type="checkbox">
                <div class="checkbox-content">
                  <span class="label">Variabler Endpreis</span>
                  <span class="desc">Beim Hinzufügen zum Warenkorb wird nach dem Preis gefragt.</span>
                </div>
              </label>

              <div class="summary-card">
                <span class="label">Lagerbestand</span>
                <span class="value">{{ formData.isUnlimitedStock ? '∞' : formData.stock }}</span>
                <span class="desc">Pflege nur noch über Korrektur-Buchungen im Bereich Finanzen.</span>
              </div>
            </div>
          </aside>

          <main class="modal-form-content">
            <section class="form-section">
              <h4>Allgemeine Informationen</h4>
              <div class="form-row">
                <div class="form-group">
                  <label for="name">Name*</label>
                  <input id="name" v-model="formData.name" type="text" required>
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
            </section>

            <section class="form-section">
              <h4>Preisgestaltung</h4>
              <div class="form-row">
                <div class="form-group">
                  <label for="price">Preis (€)*</label>
                  <input id="price" v-model.number="formData.price" type="number" step="0.01" required>
                </div>
                <div class="form-group">
                  <label for="member-price">Mitgliedspreis (€)</label>
                  <input id="member-price" v-model.number="formData.memberPrice" type="number" step="0.01">
                </div>
              </div>
            </section>
          </main>

          <footer class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeProductModal">Abbrechen</button>
            <button type="submit" class="btn btn-success">
              {{ editingId ? 'Änderungen speichern' : 'Produkt anlegen' }}
            </button>
          </footer>
        </form>
      </div>
    </div>
  </div>

  <!-- Crop Sub-Modal -->
  <div v-if="showCropModal" class="modal-overlay crop-modal-overlay" @click.self="showCropModal = false">
    <div class="crop-modal-card">
      <header class="modal-header">
        <div>
          <h3>Bildausschnitt anpassen</h3>
          <p class="modal-subtitle">Verschieben und zoomen – Änderungen werden beim Speichern des Produkts übernommen.</p>
        </div>
        <button class="modal-close" @click="showCropModal = false">×</button>
      </header>

      <div class="crop-modal-body">
        <div
          ref="cropFrameEl"
          class="crop-frame"
          :style="{ cursor: cropIsDragging ? 'grabbing' : 'grab' }"
          @mousedown.prevent="onCropDragStart"
          @wheel.prevent="onCropWheel"
          @touchstart.prevent="onCropTouchStart"
          @touchmove.prevent="onCropTouchMove"
          @touchend="onCropTouchEnd"
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
            @input="onZoomSliderInput"
          >
          <span class="zoom-icon">+</span>
          <span class="zoom-pct">{{ cropMinScale > 0 ? Math.round(cropScale / cropMinScale * 100) : 100 }}%</span>
        </div>
        <div class="crop-action-row">
          <button type="button" class="btn-crop-reset" @click="resetCrop">↺ Zurücksetzen</button>
          <button
            v-if="cropOriginalSrc"
            type="button"
            class="btn-crop-reset btn-crop-restore"
            @click="restoreOriginalImage"
          >🔄 Originalbild</button>
        </div>
      </div>

      <footer class="crop-modal-footer">
        <button type="button" class="btn btn-success" @click="showCropModal = false">Fertig</button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useProductStore } from '@/stores/product'
import { useNotificationStore } from '@/stores/notification'
import { formatPrice } from '@/services/utils'

const productStore = useProductStore()
const notificationStore = useNotificationStore()

const showProductModal = ref(false)
const showCropModal = ref(false)
const editingId = ref(null)
const imagePreview = ref(null)
const imageFile = ref(null)
const lastFiniteStock = ref(0)
const productSearch = ref('')
const formData = reactive({
  name: '',
  warengruppe: '',
  price: 0,
  memberPrice: null,
  stock: 0,
  isUnlimitedStock: false,
  isVariablePrice: false,
})

// ── Image crop editor ─────────────────────────────────────────────────────────
// Crop frame dimensions (pixels in the editor DOM); 3:2 aspect ratio
const CROP_ASPECT = 3 / 2
const CROP_W = 320
const CROP_H = Math.round(CROP_W / CROP_ASPECT)   // 213 px
// Output image size written to the server (same 3:2 aspect)
const OUTPUT_W = 600
const OUTPUT_H = Math.round(OUTPUT_W / CROP_ASPECT) // 400 px
// JPEG encode quality (0–1); 0.92 balances file size and visual quality
const JPEG_QUALITY = 0.92
// Card preview image-area dimensions
const PREVIEW_W = 180
const PREVIEW_H = Math.round(PREVIEW_W / CROP_ASPECT)  // ≈ 120 px
const PREVIEW_SCALE = PREVIEW_W / CROP_W

const cropImageSrc = ref(null)     // always a data-URL (or null)
const cropOriginalSrc = ref(null)  // original (pre-crop) data-URL for reset
const cropIsNewUpload = ref(false) // true when the user uploaded a new file this session
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
const cropFrameEl = ref(null)   // template ref for the crop-frame div

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

const canRestoreOriginal = computed(() => !!(cropOriginalSrc.value && cropOriginalSrc.value !== cropImageSrc.value))

const hasMemberPrice = (product) => product.member_price_cents !== null && product.member_price_cents !== undefined

const getProductSearchText = (product) => [
  product?.name,
  product?.warengruppe,
  product?.description,
  product?.stock_quantity,
  product?.price_cents,
  product?.member_price_cents,
]
  .filter(value => value !== null && value !== undefined && value !== '')
  .join(' ')
  .toLowerCase()

const filteredProducts = computed(() => {
  const search = productSearch.value.trim().toLowerCase()

  if (!search) {
    return productStore.products
  }

  return productStore.products.filter(product => getProductSearchText(product).includes(search))
})

const warengruppeOptions = computed(() => (
  [...new Set(
    productStore.products
      .map(product => product?.warengruppe?.trim())
      .filter(Boolean),
  )].sort((left, right) => left.localeCompare(right, 'de'))
))

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

const openCreateModal = () => {
  resetForm()
  showProductModal.value = true
}

const closeProductModal = () => {
  showProductModal.value = false
  resetForm()
}

const handleSaveProduct = async () => {
  // Build the cropped file blob when the image was changed/added
  if (cropImageSrc.value && cropModified.value) {
    try {
      const blob = await getCroppedBlob()
      imageFile.value = new File([blob], 'product-image.jpg', { type: 'image/jpeg' })
    } catch (err) {
      console.error('Crop failed:', err)
      notificationStore.error('Fehler beim Verarbeiten des Bildes')
      return
    }
  }

  if (editingId.value) {
    const imageUploadSuccess = await uploadImageToProduct(editingId.value)
    if (!imageUploadSuccess && imageFile.value) {
      return
    }

    const result = await productStore.updateProduct(editingId.value, {
      name: formData.name,
      warengruppe: formData.warengruppe || null,
      price_cents: Math.round(formData.price * 100),
      member_price_cents: toMemberPriceCents(),
      stock_quantity: formData.isUnlimitedStock ? 0 : formData.stock,
      is_unlimited_stock: formData.isUnlimitedStock,
      is_variable_price: formData.isVariablePrice,
    })

    if (result) {
      notificationStore.success('Produkt aktualisiert')
      resetForm()
    } else {
      notificationStore.error(productStore.error)
    }
  } else {
    const result = await productStore.createProduct({
      name: formData.name,
      warengruppe: formData.warengruppe || null,
      price_cents: Math.round(formData.price * 100),
      member_price_cents: toMemberPriceCents(),
      stock_quantity: formData.isUnlimitedStock ? 0 : formData.stock,
      is_unlimited_stock: formData.isUnlimitedStock,
      is_variable_price: formData.isVariablePrice,
    })

    if (result) {
      if (imageFile.value) {
        const imageUploadSuccess = await uploadImageToProduct(result.id)
        if (!imageUploadSuccess) {
          notificationStore.warning('Produkt erstellt, aber Bild-Upload fehlgeschlagen')
        } else {
          notificationStore.success('Produkt mit Bild erstellt')
        }
      } else {
        notificationStore.success('Produkt erstellt')
      }
      resetForm()
    } else {
      notificationStore.error(productStore.error)
    }
  }
}

const uploadImageToProduct = async (productId) => {
  if (!imageFile.value) return true

  // If this is a new upload, first save the original (uncropped) image for future resets
  if (cropIsNewUpload.value && cropOriginalSrc.value) {
    try {
      const origBlob = await dataUrlToBlob(cropOriginalSrc.value)
      const origFormData = new FormData()
      origFormData.append('file', new File([origBlob], 'original.jpg', { type: 'image/jpeg' }))
      await fetch(`/api/products/${productId}/original-image`, {
        method: 'POST',
        body: origFormData,
        credentials: 'include',
      })
    } catch (err) {
      console.error('Original image upload error:', err)
    }
  }

  try {
    const formDataUpload = new FormData()
    formDataUpload.append('file', imageFile.value)

    const response = await fetch(`/api/products/${productId}/image`, {
      method: 'POST',
      body: formDataUpload,
      credentials: 'include',
    })

    if (response.ok) {
      imageFile.value = null
      cropIsNewUpload.value = false
      return true
    } else {
      notificationStore.error('Bild-Upload fehlgeschlagen')
      return false
    }
  } catch (error) {
    console.error('Image upload error:', error)
    notificationStore.error('Fehler beim Bild-Upload')
    return false
  }
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
  imagePreview.value = null
  editingId.value = null
  showProductModal.value = false
  showCropModal.value = false
  // Reset crop state
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

const editProduct = async (product) => {
  editingId.value = product.id
  formData.name = product.name
  formData.warengruppe = product.warengruppe || ''
  formData.price = product.price_cents / 100
  formData.memberPrice = hasMemberPrice(product) ? product.member_price_cents / 100 : null
  formData.stock = product.stock_quantity
  formData.isUnlimitedStock = !!product.is_unlimited_stock
  formData.isVariablePrice = !!product.is_variable_price
  lastFiniteStock.value = product.stock_quantity
  imageFile.value = null
  imagePreview.value = null
  cropModified.value = false
  cropIsNewUpload.value = false
  showProductModal.value = true

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

      // Try to load the original (pre-crop) image for reset functionality
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
}

const handleImageUpload = (event) => {
  const file = event.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => {
    cropImageSrc.value = e.target.result
    cropOriginalSrc.value = e.target.result  // new upload is the new original
    cropIsNewUpload.value = true
    loadCropImageDimensions(e.target.result)
    cropModified.value = true
  }
  reader.readAsDataURL(file)
  // Reset input so the same file can be re-selected
  event.target.value = ''
}

// ── Crop helper functions ─────────────────────────────────────────────────────
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
  // Only mark as modified if a new file was uploaded (otherwise reverting to min-zoom is just visual)
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
    // Convert screen midpoint to frame-relative coordinates
    const frameRect = cropFrameEl.value ? cropFrameEl.value.getBoundingClientRect() : { left: 0, top: 0 }
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

const getCroppedBlob = () => new Promise((resolve, reject) => {
  const canvas = document.createElement('canvas')
  canvas.width = OUTPUT_W
  canvas.height = OUTPUT_H
  const ctx = canvas.getContext('2d')
  const img = new Image()
  img.onload = () => {
    // Source rect in original image pixels corresponding to the crop frame.
    // panX/panY is the position of the scaled image's top-left inside the crop frame.
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

const deleteProduct = async (productId) => {
  if (confirm('Wirklich löschen?')) {
    const result = await productStore.deleteProduct(productId)

    if (result) {
      if (editingId.value === productId) {
        resetForm()
      }
      notificationStore.success('Produkt gelöscht')
    } else {
      notificationStore.error(productStore.error || 'Fehler beim Löschen')
    }
  }
}

onMounted(async () => {
  await productStore.getProducts()
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onDocCropMouseMove)
  document.removeEventListener('mouseup', onDocCropMouseUp)
})
</script>

<style scoped lang="scss">
.admin-products {
  --primary: #3b82f6;
  --success: #10b981;
  --bg-main: #f8fafc;
  --border: #e2e8f0;
  padding: 1.5rem;
  background: white;
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;

  h2 {
    font-size: 1.5rem;
    color: #1e293b;
  }
}

.page-subtitle,
.modal-subtitle {
  color: #64748b;
}

.page-subtitle {
  margin-top: 0.25rem;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 3rem 1rem;
  color: #64748b;
}

.spinner {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  border: 3px solid #e2e8f0;
  border-top-color: var(--primary);
  animation: spin 0.8s linear infinite;
}

.table-toolbar {
  margin-bottom: 1rem;
}

.search-input {
  width: 100%;
  padding: 0.85rem 1rem;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 0.95rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;

  &:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
  }
}

.products-table-wrapper {
  background: white;
  border-radius: 12px;
  border: 1px solid var(--border);
  overflow-x: auto;
  overflow-y: hidden;
}

.products-table {
  width: 100%;
  min-width: 760px;
  border-collapse: collapse;

  th {
    background: #f1f5f9;
    padding: 1rem;
    font-size: 0.8rem;
    text-transform: uppercase;
    color: #64748b;
    text-align: left;
  }

  td {
    padding: 1rem;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
  }
}

.text-right {
  text-align: right;
}

.empty-state-cell {
  text-align: center;
  color: #64748b;
}

.action-cell {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
  flex-wrap: wrap;
  white-space: nowrap;
  width: 100%;
}

.font-bold {
  font-weight: 600;
}

.product-name-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.product-badges {
  display: inline-flex;
  gap: 0.35rem;
}

.product-image-cell {
  width: 84px;
}

.product-thumb-frame {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  overflow: hidden;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
}

.product-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-thumb-placeholder {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 600;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.3rem 0.7rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
}

.badge-success {
  background: #dcfce7;
  color: #166534;
}

.badge-light {
  background: #f1f5f9;
  color: #475569;
}

.badge-info {
  background: #dbeafe;
  color: #1d4ed8;
}

.badge-danger {
  background: #fee2e2;
  color: #b91c1c;
}

.badge-dark {
  background: #e2e8f0;
  color: #0f172a;
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

.profile-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
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

  .desc {
    display: block;
    margin-top: 0.4rem;
    font-size: 0.78rem;
    color: #065f46;
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

.btn-action {
  border: 1px solid var(--border);
  background: white;
  color: #334155;
  padding: 0.45rem 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.btn-action-danger {
  border-color: #fecaca;
  color: #b91c1c;
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
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .modal-footer,
  .action-cell {
    flex-direction: column;
  }

  .btn,
  .btn-action {
    width: 100%;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

// ── Crop editor & card preview ────────────────────────────────────────────────
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

// The crop frame: fixed size, clips the image
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

.crop-action-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  align-self: flex-start;
}

// Card preview mimics .product-btn from Kasse.vue
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

.crop-file-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
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

// Crop sub-modal
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

.crop-modal-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.crop-modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
}
</style>
