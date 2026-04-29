<!--
  DESIGN-VORLAGE V4 – Tab-Ansicht pro Kategorie
  ===============================================
  Jede Kategorie ist ein horizontaler Tab ganz oben. Klick auf einen Tab zeigt
  ausschließlich die Produkte dieser Kategorie in einem breiten, vollflächigen Raster.
  Nur eine Kategorie gleichzeitig aktiv (Single-Select) – maximale Übersichtlichkeit.

  Produktkarten: Bild 65 px, Name, Preis, Bestand, Rabatt-Badge.

  SKRIPT: identisch mit frontend/src/views/kasse/Kasse.vue – unverändert übernehmen.
  Hinweis: toggleCategory muss für Single-Select angepasst werden:
    const selectTab = (id) => { expandedCategories.value = [id] }
-->
<template>
  <div class="kasse-container">
    <div class="kasse-products">
      <div v-if="productStore.isLoading" class="loading">Läuft...</div>
      <div v-else class="products-section">

        <!-- Horizontal tab bar -->
        <div class="tab-bar">
          <button
            v-for="category in activeCategories"
            :key="category.id"
            class="tab"
            :class="{ active: expandedCategories.includes(category.id) }"
            @click="toggleCategory(category.id)"
          >
            {{ category.name }}
            <span class="tab-count">{{ getProductsByCategory(category.id).length }}</span>
          </button>
          <button
            v-if="productsWithoutCategory.length > 0"
            class="tab"
            :class="{ active: expandedCategories.includes(0) }"
            @click="toggleCategory(0)"
          >
            Ohne Kategorie
            <span class="tab-count">{{ productsWithoutCategory.length }}</span>
          </button>
        </div>

        <!-- Product grid for the active tab -->
        <div v-if="hasExpandedCategory" class="products-grid">
          <template v-for="category in activeCategories" :key="category.id">
            <template v-if="expandedCategories.includes(category.id)">
              <button
                v-for="product in getProductsByCategory(category.id)"
                :key="`${category.id}-${product.id}`"
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
            </template>
          </template>
          <template v-if="expandedCategories.includes(0)">
            <button
              v-for="product in productsWithoutCategory"
              :key="`ohne-${product.id}`"
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
          </template>
        </div>

        <div v-if="!hasExpandedCategory" class="empty-products">Kategorie auswählen</div>
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
.kasse-container {
  display: flex;
  gap: .75rem;
  padding: .75rem;
  width: 100%; height: 100%; min-height: 0;
  background: var(--app-background-color);
  overflow: hidden;

  @media (max-width: 768px) { flex-direction: column; overflow-y: auto; }
}

.kasse-products {
  flex: 1 1 auto;
  min-width: 0;
  background: var(--app-surface-color);
  border-radius: 12px;
  padding: 0;
  box-shadow: 0 6px 18px rgba(24, 28, 34, 0.1);
  border: 1px solid var(--app-banner-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.products-section {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

/* ── Tab bar ─────────────────────────────────────────── */
.tab-bar {
  display: flex;
  flex-direction: row;
  overflow-x: auto;
  gap: 0;
  border-bottom: 2px solid color-mix(in srgb, var(--app-banner-color) 20%, transparent);
  flex-shrink: 0;
  padding: 0 .5rem;
  background: color-mix(in srgb, var(--app-banner-color) 5%, var(--app-surface-color) 95%);

  &::-webkit-scrollbar { height: 3px; }
  &::-webkit-scrollbar-thumb { background: var(--app-highlight-color); border-radius: 3px; }
}

.tab {
  display: inline-flex;
  align-items: center;
  gap: .35rem;
  padding: .7rem .9rem .6rem;
  border: none;
  border-bottom: 3px solid transparent;
  background: transparent;
  color: #64748b;
  font-size: .78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all .13s;
  white-space: nowrap;
  margin-bottom: -2px;

  &:hover {
    color: var(--app-banner-color);
    background: color-mix(in srgb, var(--app-banner-color) 6%, transparent);
  }

  &.active {
    color: var(--app-highlight-color);
    border-bottom-color: var(--app-highlight-color);
    background: transparent;

    .tab-count { background: color-mix(in srgb, var(--app-highlight-color) 15%, transparent); color: var(--app-highlight-color); }
  }

  .tab-count {
    font-size: .64rem;
    background: #f1f5f9;
    padding: .05rem .28rem;
    border-radius: 999px;
    font-weight: 500;
    color: #94a3b8;
  }
}

/* ── Product grid ────────────────────────────────────── */
.products-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: .45rem;
  padding: .6rem;
  overflow-y: auto;
  flex: 1;
  align-content: start;

  @media (max-width: 1400px) { grid-template-columns: repeat(5, 1fr); }
  @media (max-width: 1100px) { grid-template-columns: repeat(4, 1fr); }
  @media (max-width: 850px)  { grid-template-columns: repeat(3, 1fr); }
  @media (max-width: 600px)  { grid-template-columns: repeat(2, 1fr); }
}

/* ── Product card ────────────────────────────────────── */
.product-btn {
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  padding: 0;
  cursor: pointer;
  transition: all .14s;
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
    height: 65px;
    overflow: hidden;
    background: #f0f4fa;
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
    top: 3px; left: 3px; z-index: 1;
    font-size: 9px; font-weight: 800;
    padding: 2px 4px; border-radius: 3px; line-height: 1.4;

    &.discount-badge { background: #fffbeb; color: #d97706; }
  }

  .card-body {
    padding: 5px 6px 6px;
    flex: 1; display: flex; flex-direction: column; gap: 3px;
  }

  .card-name {
    font-size: .73rem; font-weight: 700; line-height: 1.2; color: #111827;
  }

  .card-bottom {
    display: flex; justify-content: space-between; align-items: center; margin-top: auto;
  }

  .card-price {
    font-size: .84rem; font-weight: 800;
    color: var(--app-highlight-color);
    letter-spacing: -0.02em;
  }

  .card-stock { font-size: .63rem; color: #94a3b8; font-weight: 500; }
}

.empty-products {
  text-align: center; color: #aaa; padding: 3rem 1rem; font-size: .9rem;
}
</style>
