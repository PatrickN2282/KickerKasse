<!--
  DESIGN-VORLAGE V2 – Ultra-Kompakt / Maximale Dichte
  =====================================================
  Maximale Produktanzahl auf dem Bildschirm: kleine Text-Kacheln ohne Bild-Bereich.
  Preis, Bestand und Rabatt-Badge bleiben sichtbar. Produkte werden als dichte
  kleine Rechtecke dargestellt – ideal für Displays mit vielen Artikeln.

  Kategorie-Filter: horizontal scrollbare Bubble-Chips ganz oben.

  SKRIPT: identisch mit frontend/src/views/kasse/Kasse.vue – unverändert übernehmen.
-->
<template>
  <div class="kasse-container">
    <div class="kasse-products">
      <div v-if="productStore.isLoading" class="loading">Läuft...</div>
      <div v-else class="products-section">

        <!-- Bubble-Chip filter -->
        <div class="chip-bar">
          <button
            v-for="category in activeCategories"
            :key="category.id"
            class="chip"
            :class="{ active: expandedCategories.includes(category.id) }"
            @click="toggleCategory(category.id)"
          >
            {{ category.name }}
            <span class="chip-badge">{{ getProductsByCategory(category.id).length }}</span>
          </button>
          <button
            v-if="productsWithoutCategory.length > 0"
            class="chip"
            :class="{ active: expandedCategories.includes(0) }"
            @click="toggleCategory(0)"
          >
            Ohne Kategorie
            <span class="chip-badge">{{ productsWithoutCategory.length }}</span>
          </button>
        </div>

        <!-- Dense tile grid -->
        <div v-if="hasExpandedCategory" class="products-grid">
          <template v-for="category in activeCategories" :key="category.id">
            <template v-if="expandedCategories.includes(category.id)">
              <button
                v-for="product in getProductsByCategory(category.id)"
                :key="`${category.id}-${product.id}`"
                :disabled="isProductOutOfStock(product)"
                class="product-tile"
                @click="selectProduct(product, category.id)"
              >
                <span v-if="hasMemberPrice(product)" class="tile-badge">%</span>
                <div class="tile-name">{{ product.name }}</div>
                <div class="tile-footer">
                  <span class="tile-price">{{ formatPrice(getDisplayedProductPriceCents(product, category.id)) }}</span>
                  <span class="tile-stock">{{ product.is_unlimited_stock ? '∞' : getAvailableStock(product) }}</span>
                </div>
              </button>
            </template>
          </template>
          <template v-if="expandedCategories.includes(0)">
            <button
              v-for="product in productsWithoutCategory"
              :key="`ohne-${product.id}`"
              :disabled="isProductOutOfStock(product)"
              class="product-tile"
              @click="selectProduct(product)"
            >
              <span v-if="hasMemberPrice(product)" class="tile-badge">%</span>
              <div class="tile-name">{{ product.name }}</div>
              <div class="tile-footer">
                <span class="tile-price">{{ formatPrice(product.price_cents) }}</span>
                <span class="tile-stock">{{ product.is_unlimited_stock ? '∞' : getAvailableStock(product) }}</span>
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
  border-radius: 10px;
  padding: .6rem;
  box-shadow: 0 4px 14px rgba(24, 28, 34, 0.09);
  border: 1px solid var(--app-banner-color);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.products-section {
  display: flex;
  flex-direction: column;
  gap: .4rem;
  height: 100%;
  min-height: 0;
}

/* ── Chip bar ─────────────────────────────────────────── */
.chip-bar {
  display: flex;
  flex-wrap: wrap;
  gap: .25rem;
  padding-bottom: .4rem;
  border-bottom: 1px solid color-mix(in srgb, var(--app-banner-color) 16%, transparent);
  flex-shrink: 0;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: .25rem;
  padding: .2rem .55rem;
  border-radius: 999px;
  border: 1.5px solid color-mix(in srgb, var(--app-banner-color) 35%, transparent);
  background: transparent;
  color: var(--app-banner-color);
  font-size: .7rem;
  font-weight: 600;
  cursor: pointer;
  transition: all .13s;
  white-space: nowrap;

  &:hover { background: color-mix(in srgb, var(--app-banner-color) 8%, transparent); }

  &.active {
    background: var(--app-highlight-color);
    border-color: var(--app-highlight-color);
    color: var(--app-highlight-contrast);

    .chip-badge { background: rgba(255,255,255,.22); }
  }

  .chip-badge {
    font-size: .6rem;
    background: rgba(0,0,0,.09);
    padding: .04rem .26rem;
    border-radius: 999px;
  }
}

/* ── Dense tile grid ─────────────────────────────────── */
.products-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: .3rem;
  overflow-y: auto;
  flex: 1;
  align-content: start;

  @media (max-width: 1500px) { grid-template-columns: repeat(7, 1fr); }
  @media (max-width: 1200px) { grid-template-columns: repeat(6, 1fr); }
  @media (max-width: 950px)  { grid-template-columns: repeat(5, 1fr); }
  @media (max-width: 700px)  { grid-template-columns: repeat(4, 1fr); }
  @media (max-width: 480px)  { grid-template-columns: repeat(3, 1fr); }
}

/* ── Compact tile ────────────────────────────────────── */
.product-tile {
  position: relative;
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 7px;
  padding: .4rem .45rem .38rem;
  cursor: pointer;
  transition: all .13s;
  font-family: inherit;
  display: flex;
  flex-direction: column;
  gap: .2rem;
  text-align: left;
  min-height: 52px;

  &:hover:not(:disabled) {
    border-color: var(--app-highlight-color);
    background: color-mix(in srgb, var(--app-highlight-color) 5%, white 95%);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px color-mix(in srgb, var(--app-highlight-color) 16%, transparent);
  }

  &:disabled { opacity: 0.38; cursor: not-allowed; }

  .tile-badge {
    position: absolute;
    top: 2px; right: 2px;
    background: #fef3c7;
    color: #d97706;
    font-size: 8px;
    font-weight: 900;
    border-radius: 3px;
    padding: 1px 3px;
    line-height: 1.3;
  }

  .tile-name {
    font-size: .69rem;
    font-weight: 700;
    line-height: 1.15;
    color: #111827;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    flex: 1;
  }

  .tile-footer {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: .2rem;
    flex-shrink: 0;
  }

  .tile-price {
    font-size: .76rem;
    font-weight: 800;
    color: var(--app-highlight-color);
    letter-spacing: -0.02em;
  }

  .tile-stock {
    font-size: .6rem;
    color: #94a3b8;
    font-weight: 500;
  }
}

.empty-products {
  text-align: center;
  color: #aaa;
  padding: 3rem 1rem;
  font-size: .9rem;
}
</style>
