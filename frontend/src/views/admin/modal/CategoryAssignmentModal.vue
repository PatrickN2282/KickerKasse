<template>
  <div
    v-if="show && category"
    class="modal-overlay"
    @click.self="$emit('close')"
  >
    <div class="modal-card modal-compact">
      <header class="modal-header">
        <div>
          <h3>Artikel zuordnen</h3>
          <p class="modal-subtitle">{{ category.name }}</p>
        </div>
        <button class="close-btn" type="button" @click="$emit('close')">✕</button>
      </header>

      <div class="assign-modal-body">
        <div class="assign-add-section">
          <p class="assign-section-label">Nicht zugeordnete Artikel (klicken zum Hinzufügen):</p>
          <div v-if="unassignedProducts.length > 0" class="product-pick-list">
            <button
              v-for="product in unassignedProducts"
              :key="`pick-${category.id}-${product.id}`"
              type="button"
              class="product-pick-item"
              @click="$emit('assign-product', product.id)"
            >
              <img
                v-if="product.image_path"
                :src="`/api/products/${product.id}/image`"
                :alt="product.name"
                class="product-pick-img"
              >
              <span v-else class="product-pick-img product-pick-img-placeholder">📦</span>
              <span class="product-pick-name">{{ product.name }}</span>
            </button>
          </div>
          <div v-else class="assign-empty">Alle Artikel sind bereits zugeordnet</div>
        </div>

        <div v-if="assignedProducts.length > 0" class="assign-product-list">
          <div
            v-for="product in assignedProducts"
            :key="`assign-row-${product.id}`"
            class="assign-product-row"
          >
            <img v-if="product.image_path" :src="`/api/products/${product.id}/image`" :alt="product.name" class="assign-product-thumb">
            <span v-else class="assign-product-thumb assign-product-thumb-placeholder">📦</span>
            <span class="assign-product-name">{{ product.name }}</span>
            <button
              class="btn-tag-remove"
              type="button"
              title="Zuordnung entfernen"
              @click="$emit('remove-product', product.id)"
            >
              ×
            </button>
          </div>
        </div>
        <div v-else class="assign-empty">Noch kein Artikel zugeordnet</div>
      </div>

      <footer class="modal-footer">
        <button class="btn btn-secondary" type="button" @click="$emit('close')">Schließen</button>
      </footer>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: { type: Boolean, required: true },
  category: { type: Object, default: null },
  assignedProducts: { type: Array, default: () => [] },
  unassignedProducts: { type: Array, default: () => [] },
})

defineEmits(['close', 'assign-product', 'remove-product'])
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

.assign-modal-body {
  padding: 1rem 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
}

.assign-product-list {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.assign-product-row {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.55rem 0.7rem;
  border: 1px solid #dbeafe;
  border-radius: 10px;
  background: #eff6ff;
}

.assign-product-name {
  flex: 1;
  font-weight: 600;
  color: #0f172a;
}

.btn-tag-remove {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 1.15rem;
  color: #b91c1c;
}

.assign-empty {
  text-align: center;
  color: #64748b;
  font-size: 0.85rem;
  padding: 1rem 0.5rem;
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
  background: #f8fafc;
}

.assign-add-section {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.assign-section-label {
  margin: 0;
  font-size: 0.85rem;
  color: #475569;
  font-weight: 600;
}

.product-pick-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 0.6rem;
}

.product-pick-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  width: 100%;
  padding: 0.6rem 0.7rem;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  background: white;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;

  &:hover {
    border-color: #3b82f6;
    box-shadow: 0 10px 18px rgba(59, 130, 246, 0.12);
    transform: translateY(-1px);
  }
}

.product-pick-name {
  font-weight: 600;
  color: #1e293b;
}

.product-pick-img,
.assign-product-thumb {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  object-fit: cover;
  background: #e2e8f0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.product-pick-img-placeholder,
.assign-product-thumb-placeholder {
  color: #64748b;
  font-size: 1rem;
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

.btn-secondary {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #334155;

  &:hover {
    background: #f1f5f9;
  }
}
</style>
