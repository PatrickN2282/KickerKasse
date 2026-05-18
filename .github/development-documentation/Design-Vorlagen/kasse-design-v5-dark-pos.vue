<!--
  DESIGN-VORLAGE V5 – Dark-Mode POS
  ===================================
  Dunkles, modernes Point-of-Sale-Design. Kategorie-Chips leuchten als farbige Akzente.
  Produktkarten: dunkle Oberfläche, leuchtende Preise, Bild 65 px.
  Ideal für Low-Light-Umgebungen (Kiosk, Theke, abgedunkelter Kassenbereich).

  Alle Details (Bild, Name, Preis, Bestand, Rabatt-Badge) bleiben erhalten.

  SKRIPT: identisch mit frontend/src/views/kasse/Kasse.vue – unverändert übernehmen.
-->
<template>
  <div class="kasse-container">
    <div class="kasse-products">
      <div v-if="productStore.isLoading" class="loading">Läuft...</div>
      <div v-else class="products-section">

        <!-- Chip filter bar -->
        <div class="chip-bar">
          <button
            v-for="category in activeCategories"
            :key="category.id"
            class="chip"
            :class="{ active: expandedCategories.includes(category.id) }"
            @click="toggleCategory(category.id)"
          >
            {{ category.name }}
            <span class="chip-count">{{ getProductsByCategory(category.id).length }}</span>
          </button>
          <button
            v-if="productsWithoutCategory.length > 0"
            class="chip"
            :class="{ active: expandedCategories.includes(0) }"
            @click="toggleCategory(0)"
          >
            Ohne Kategorie
            <span class="chip-count">{{ productsWithoutCategory.length }}</span>
          </button>
        </div>

        <!-- Product grid -->
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
                  <span v-if="hasMemberPrice(product)" class="card-badge discount-badge">%</span>
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
                <span v-if="hasMemberPrice(product)" class="card-badge discount-badge">%</span>
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
/* Dark POS color tokens */
$bg-dark: #0f1117;
$surface: #1a1d26;
$surface-raised: #22263a;
$border: #2e3347;
$text: #e2e8f0;
$text-muted: #64748b;
$accent: #38bdf8;     /* sky-400 */
$accent-dim: rgba(56, 189, 248, .18);
$green: #4ade80;      /* emerald */
$amber: #fbbf24;

.kasse-container {
  display: flex;
  gap: .75rem;
  padding: .75rem;
  width: 100%; height: 100%; min-height: 0;
  background: $bg-dark;
  overflow: hidden;

  @media (max-width: 768px) { flex-direction: column; overflow-y: auto; }
}

.kasse-products {
  flex: 1 1 auto;
  min-width: 0;
  background: $surface;
  border-radius: 14px;
  padding: .7rem;
  box-shadow: 0 8px 32px rgba(0,0,0,.55);
  border: 1px solid $border;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.loading { color: $text-muted; padding: 2rem; text-align: center; }

.products-section {
  display: flex;
  flex-direction: column;
  gap: .45rem;
  height: 100%;
  min-height: 0;
}

/* ── Chip bar ─────────────────────────────────────────── */
.chip-bar {
  display: flex;
  flex-wrap: wrap;
  gap: .28rem;
  padding-bottom: .45rem;
  border-bottom: 1px solid $border;
  flex-shrink: 0;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: .25rem;
  padding: .24rem .58rem;
  border-radius: 999px;
  border: 1.5px solid $border;
  background: $surface-raised;
  color: $text-muted;
  font-size: .71rem;
  font-weight: 600;
  cursor: pointer;
  transition: all .14s;
  white-space: nowrap;

  &:hover {
    border-color: $accent;
    color: $text;
  }

  &.active {
    background: $accent-dim;
    border-color: $accent;
    color: $accent;

    .chip-count { background: rgba(56,189,248,.2); }
  }

  .chip-count {
    font-size: .6rem;
    background: rgba(255,255,255,.07);
    padding: .04rem .26rem;
    border-radius: 999px;
  }
}

/* ── Product grid ────────────────────────────────────── */
.products-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: .4rem;
  overflow-y: auto;
  flex: 1;
  align-content: start;

  @media (max-width: 1500px) { grid-template-columns: repeat(5, 1fr); }
  @media (max-width: 1200px) { grid-template-columns: repeat(4, 1fr); }
  @media (max-width: 900px)  { grid-template-columns: repeat(3, 1fr); }
  @media (max-width: 600px)  { grid-template-columns: repeat(2, 1fr); }

  &::-webkit-scrollbar { width: 5px; }
  &::-webkit-scrollbar-track { background: transparent; }
  &::-webkit-scrollbar-thumb { background: $border; border-radius: 5px; }
}

/* ── Dark product card ───────────────────────────────── */
.product-btn {
  background: $surface-raised;
  border: 1.5px solid $border;
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
    border-color: $accent;
    box-shadow: 0 3px 14px rgba(56,189,248,.15);
    transform: translateY(-1px);

    .card-img img { transform: scale(1.07); }
  }

  &:disabled { opacity: 0.3; cursor: not-allowed; }

  .card-img {
    height: 65px;
    overflow: hidden;
    background: #151820;
    flex-shrink: 0;
    position: relative;

    img { width: 100%; height: 100%; object-fit: contain; display: block; transition: transform .25s; }
  }

  .card-img-ph {
    width: 100%; height: 100%;
    display: flex; align-items: center; justify-content: center;
    font-size: 24px; opacity: .6;
  }

  .card-badge {
    position: absolute;
    top: 3px; left: 3px; z-index: 1;
    font-size: 9px; font-weight: 900;
    padding: 2px 4px; border-radius: 3px; line-height: 1.4;

    &.discount-badge { background: rgba(251,191,36,.15); color: $amber; border: 1px solid rgba(251,191,36,.3); }
  }

  .card-body {
    padding: 5px 6px 6px;
    flex: 1; display: flex; flex-direction: column; gap: 3px;
  }

  .card-name {
    font-size: .71rem; font-weight: 600; line-height: 1.2; color: $text;
  }

  .card-bottom {
    display: flex; justify-content: space-between; align-items: center; margin-top: auto;
  }

  .card-price {
    font-size: .82rem; font-weight: 800;
    color: $green;
    letter-spacing: -0.02em;
  }

  .card-stock { font-size: .62rem; color: $text-muted; font-weight: 500; }
}

.empty-products {
  text-align: center; color: $text-muted; padding: 3rem 1rem; font-size: .9rem;
}
</style>
