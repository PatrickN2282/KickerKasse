<!--
  DESIGN-VORLAGE V3 – Left-Sidebar Kategorien + breites Produktraster
  ====================================================================
  Vertikale Kategorieleiste links (schlanke Seitenleiste ~140 px) mit scrollbaren
  Kategorie-Schaltflächen. Rechts daneben ein 5-spaltig-breites Produktraster.
  Mehrfachauswahl möglich: mehrere Kategorien gleichzeitig aktiv.

  Alle Produktkarten-Details (Bild 60 px, Name, Preis, Bestand, Rabatt-Badge) bleiben erhalten.

  SKRIPT: identisch mit frontend/src/views/kasse/Kasse.vue – unverändert übernehmen.
-->
<template>
  <div class="kasse-container">
    <div class="kasse-products">
      <div v-if="productStore.isLoading" class="loading">Läuft...</div>
      <template v-else>
        <nav class="cat-sidebar">
          <button
            v-for="category in activeCategories"
            :key="category.id"
            class="cat-nav-btn"
            :class="{ active: expandedCategories.includes(category.id) }"
            @click="toggleCategory(category.id)"
          >
            <span class="cat-nav-name">{{ category.name }}</span>
            <span class="cat-nav-count">{{ getProductsByCategory(category.id).length }}</span>
          </button>
          <button
            v-if="productsWithoutCategory.length > 0"
            class="cat-nav-btn"
            :class="{ active: expandedCategories.includes(0) }"
            @click="toggleCategory(0)"
          >
            <span class="cat-nav-name">Ohne Kat.</span>
            <span class="cat-nav-count">{{ productsWithoutCategory.length }}</span>
          </button>
        </nav>

        <div class="product-area">
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
          <div v-else class="empty-products">Kategorie auswählen</div>
        </div>
      </template>
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
  box-shadow: 0 6px 18px rgba(24, 28, 34, 0.1);
  border: 1px solid var(--app-banner-color);
  display: flex;
  flex-direction: row;
  overflow: hidden;
}

/* ── Left category sidebar ───────────────────────────── */
.cat-sidebar {
  flex: 0 0 130px;
  width: 130px;
  background: color-mix(in srgb, var(--app-banner-color) 6%, var(--app-surface-color) 94%);
  border-right: 1px solid color-mix(in srgb, var(--app-banner-color) 20%, transparent);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: .2rem;
  padding: .5rem .35rem;

  @media (max-width: 768px) {
    flex: 0 0 auto;
    width: 100%;
    flex-direction: row;
    flex-wrap: wrap;
    border-right: none;
    border-bottom: 1px solid color-mix(in srgb, var(--app-banner-color) 20%, transparent);
    padding: .35rem;
  }
}

.cat-nav-btn {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: .5rem .5rem;
  border-radius: 8px;
  border: 1.5px solid transparent;
  background: transparent;
  cursor: pointer;
  transition: all .13s;
  text-align: left;
  gap: .1rem;

  &:hover {
    background: color-mix(in srgb, var(--app-banner-color) 10%, transparent);
  }

  &.active {
    background: var(--app-highlight-color);
    border-color: var(--app-highlight-color);
    color: var(--app-highlight-contrast);

    .cat-nav-count { color: rgba(255,255,255,.75); }
  }

  .cat-nav-name {
    font-size: .72rem;
    font-weight: 700;
    line-height: 1.2;
    color: inherit;
    word-break: break-word;
  }

  .cat-nav-count {
    font-size: .62rem;
    color: #94a3b8;
    font-weight: 500;
  }

  @media (max-width: 768px) {
    width: auto;
    flex-direction: row;
    align-items: center;
    gap: .25rem;
    padding: .25rem .55rem;

    .cat-nav-name { font-size: .7rem; }
  }
}

/* ── Product area ────────────────────────────────────── */
.product-area {
  flex: 1;
  min-width: 0;
  padding: .6rem;
  overflow-y: auto;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: .45rem;
  align-content: start;

  @media (max-width: 1400px) { grid-template-columns: repeat(4, 1fr); }
  @media (max-width: 1100px) { grid-template-columns: repeat(3, 1fr); }
  @media (max-width: 750px)  { grid-template-columns: repeat(2, 1fr); }
}

/* ── Product card ────────────────────────────────────── */
.product-btn {
  background: #fff;
  border: 1.5px solid color-mix(in srgb, var(--app-banner-color) 22%, white 78%);
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
    height: 60px;
    overflow: hidden;
    background: #eef1f7;
    flex-shrink: 0;
    position: relative;

    img { width: 100%; height: 100%; object-fit: contain; display: block; transition: transform .25s; }
  }

  .card-img-ph {
    width: 100%; height: 100%;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
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
    font-size: .72rem; font-weight: 700; line-height: 1.2; color: #111827;
  }

  .card-bottom {
    display: flex; justify-content: space-between; align-items: center; margin-top: auto;
  }

  .card-price {
    font-size: .82rem; font-weight: 800;
    color: var(--app-highlight-color);
    letter-spacing: -0.02em;
  }

  .card-stock { font-size: .63rem; color: #94a3b8; font-weight: 500; }
}

.empty-products {
  text-align: center; color: #aaa; padding: 3rem 1rem; font-size: .9rem;
}
</style>
