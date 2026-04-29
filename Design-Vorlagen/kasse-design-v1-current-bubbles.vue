<!--
  DESIGN-VORLAGE V1 – Aktuelles Layout + Bubble-Chips
  =====================================================
  Ausgangspunkt: das bisherige Kasse.vue-Layout (vertikale Kategorie-Toggle-Buttons
  neben jedem Produktgitter) – jedoch werden die schmalen Button-Säulen durch flache
  Bubble-Chips ÜBER dem jeweiligen Produktgitter ersetzt.

  Ergebnis: Jede Kategorie hat ihren eigenen Chip-Header direkt über den Produkten.
  Alle Details der Produktkarten (Bild, Name, Preis, Bestand, Rabatt-Badge) bleiben erhalten.

  SKRIPT: identisch mit frontend/src/views/kasse/Kasse.vue – unverändert übernehmen.
-->
<template>
  <div class="kasse-container">
    <div class="kasse-products">
      <div v-if="productStore.isLoading" class="loading">Läuft...</div>
      <div v-else class="products-section">

        <!-- Category: chip-header + collapsible product grid -->
        <template v-for="category in activeCategories" :key="category.id">
          <div class="category-block">
            <button
              class="cat-chip-header"
              :class="{ active: expandedCategories.includes(category.id) }"
              @click="toggleCategory(category.id)"
            >
              <span class="cat-chip-name">{{ category.name }}</span>
              <span class="cat-chip-count">{{ getProductsByCategory(category.id).length }}</span>
              <span class="cat-chip-arrow">{{ expandedCategories.includes(category.id) ? '▲' : '▼' }}</span>
            </button>
            <div v-if="expandedCategories.includes(category.id)" class="products-grid">
              <button
                v-for="product in getProductsByCategory(category.id)"
                :key="product.id"
                :disabled="isProductOutOfStock(product)"
                class="product-btn"
                @click="selectProduct(product, category.id)"
              >
                <div class="card-img">
                  <span v-if="hasMemberPrice(product)" class="card-badge discount-badge">Rabatt</span>
                  <img v-if="product.image_path && !imageErrorMap[product.id]" :src="`/api/products/${product.id}/image`" :alt="product.name" @error="onImageError(product.id)" />
                  <div v-else class="card-img-ph">🛒</div>
                </div>
                <div class="card-body">
                  <div class="card-name">{{ product.name }}</div>
                  <div class="card-bottom">
                    <span class="card-price">{{ formatPrice(getDisplayedProductPriceCents(product, category.id)) }}</span>
                    <span class="card-stock">{{ product.is_unlimited_stock ? '∞' : getAvailableStock(product) }}</span>
                  </div>
                </div>
              </button>
            </div>
          </div>
        </template>

        <!-- Products without category -->
        <template v-if="productsWithoutCategory.length > 0">
          <div class="category-block">
            <button
              class="cat-chip-header"
              :class="{ active: expandedCategories.includes(0) }"
              @click="toggleCategory(0)"
            >
              <span class="cat-chip-name">Ohne Kategorie</span>
              <span class="cat-chip-count">{{ productsWithoutCategory.length }}</span>
              <span class="cat-chip-arrow">{{ expandedCategories.includes(0) ? '▲' : '▼' }}</span>
            </button>
            <div v-if="expandedCategories.includes(0)" class="products-grid">
              <button
                v-for="product in productsWithoutCategory"
                :key="product.id"
                :disabled="isProductOutOfStock(product)"
                class="product-btn"
                @click="selectProduct(product)"
              >
                <div class="card-img">
                  <span v-if="hasMemberPrice(product)" class="card-badge discount-badge">Rabatt</span>
                  <img v-if="product.image_path && !imageErrorMap[product.id]" :src="`/api/products/${product.id}/image`" :alt="product.name" @error="onImageError(product.id)" />
                  <div v-else class="card-img-ph">🛒</div>
                </div>
                <div class="card-body">
                  <div class="card-name">{{ product.name }}</div>
                  <div class="card-bottom">
                    <span class="card-price">{{ formatPrice(product.price_cents) }}</span>
                    <span class="card-stock">{{ product.is_unlimited_stock ? '∞' : getAvailableStock(product) }}</span>
                  </div>
                </div>
              </button>
            </div>
          </div>
        </template>

        <div v-if="!hasExpandedCategory" class="empty-products">
          Kategorie auswählen
        </div>
      </div>
    </div>

    <!-- Bon-Bereich: identisch mit Kasse.vue -->
    <!-- ... (Bon-Bereich aus Kasse.vue unverändert übernehmen) ... -->
  </div>
</template>

<!-- SKRIPT: vollständig aus frontend/src/views/kasse/Kasse.vue übernehmen -->
<script setup>
// → Script-Block aus Kasse.vue 1:1 einfügen
</script>

<style scoped lang="scss">
/* ── Layout ──────────────────────────────────────────── */
.kasse-container {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  width: 100%;
  height: 100%;
  min-height: 0;
  background: var(--app-background-color);
  overflow: hidden;

  @media (max-width: 768px) {
    flex-direction: column;
    overflow-y: auto;
  }
}

.kasse-products {
  flex: 1 1 auto;
  min-width: 0;
  background: var(--app-surface-color);
  border-radius: 12px;
  padding: .85rem;
  box-shadow: 0 8px 20px rgba(24, 28, 34, 0.1);
  overflow-y: auto;
  border: 1px solid var(--app-banner-color);
}

.products-section {
  display: flex;
  flex-direction: column;
  gap: .6rem;
}

/* ── Category block: chip-header + grid ─────────────── */
.category-block {
  display: flex;
  flex-direction: column;
  gap: .4rem;
}

.cat-chip-header {
  display: inline-flex;
  align-items: center;
  gap: .45rem;
  padding: .3rem .75rem;
  border-radius: 999px;
  border: 1.5px solid color-mix(in srgb, var(--app-banner-color) 40%, transparent);
  background: transparent;
  color: var(--app-banner-color);
  font-size: .78rem;
  font-weight: 700;
  cursor: pointer;
  transition: all .14s;
  width: 100%;
  text-align: left;

  &:hover {
    background: color-mix(in srgb, var(--app-banner-color) 8%, transparent);
  }

  &.active {
    background: var(--app-highlight-color);
    border-color: var(--app-highlight-color);
    color: var(--app-highlight-contrast);

    .cat-chip-count {
      background: rgba(255,255,255,.22);
    }
  }

  .cat-chip-name {
    flex: 1;
  }

  .cat-chip-count {
    font-size: .68rem;
    background: rgba(0,0,0,.09);
    padding: .06rem .32rem;
    border-radius: 999px;
    font-weight: 500;
  }

  .cat-chip-arrow {
    font-size: .6rem;
    opacity: .7;
  }
}

.empty-products {
  text-align: center;
  color: #aaa;
  padding: 3rem 1rem;
  font-size: .95rem;
}

/* ── Product grid ────────────────────────────────────── */
.products-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: .5rem;

  @media (max-width: 1400px) { grid-template-columns: repeat(4, 1fr); }
  @media (max-width: 1100px) { grid-template-columns: repeat(3, 1fr); }
  @media (max-width: 800px)  { grid-template-columns: repeat(2, 1fr); }
  @media (max-width: 550px)  { grid-template-columns: 1fr; }
}

/* ── Product card ────────────────────────────────────── */
.product-btn {
  background: #fff;
  border: 1.5px solid color-mix(in srgb, var(--app-banner-color) 22%, white 78%);
  border-radius: 10px;
  padding: 0;
  cursor: pointer;
  transition: all .15s;
  font-family: inherit;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  text-align: left;

  &:hover:not(:disabled) {
    border-color: var(--app-highlight-color);
    box-shadow: 0 3px 12px color-mix(in srgb, var(--app-highlight-color) 18%, transparent);
    transform: translateY(-1px);

    .card-img img { transform: scale(1.08); }
  }

  &:disabled { opacity: 0.4; cursor: not-allowed; }

  .card-img {
    height: 68px;
    overflow: hidden;
    background: #eef1f7;
    flex-shrink: 0;
    position: relative;

    img { width: 100%; height: 100%; object-fit: contain; display: block; transition: transform .25s; }
  }

  .card-img-ph {
    width: 100%; height: 100%;
    display: flex; align-items: center; justify-content: center;
    font-size: 24px;
  }

  .card-badge {
    position: absolute;
    top: 3px; left: 3px;
    z-index: 1;
    font-size: 9px; font-weight: 800;
    padding: 2px 4px;
    border-radius: 3px;
    line-height: 1.4;

    &.discount-badge { background: #fffbeb; color: #d97706; }
  }

  .card-body {
    padding: 5px 7px 7px;
    flex: 1; display: flex; flex-direction: column; gap: 3px;
  }

  .card-name {
    font-size: .74rem; font-weight: 700; line-height: 1.2; color: #111827;
  }

  .card-bottom {
    display: flex; justify-content: space-between; align-items: center; margin-top: auto;
  }

  .card-price {
    font-size: .84rem; font-weight: 800;
    color: var(--app-highlight-color);
    letter-spacing: -0.02em;
  }

  .card-stock { font-size: .64rem; color: #64748b; font-weight: 500; }
}
</style>
