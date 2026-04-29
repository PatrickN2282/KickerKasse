<!--
  DESIGN-VORLAGE V6 – Kategorie-Abschnitte inline (immer sichtbar, scrollbar)
  ==============================================================================
  Alle Kategorien sind gleichzeitig sichtbar als farbige Abschnitts-Header.
  Darunter die Produkte in einer kompakten Reihe. Kein Auf-/Zuklappen – alles
  auf einmal durchsrollbar. Ideal wenn viele kleine Sortimente übersichtlich
  auf einer Seite dargestellt werden sollen.

  Kategorie-Header: flacher farbiger Streifen mit Namen und Produktanzahl.
  Produktkarten: kompaktes Layout mit Bild 55 px, Name, Preis, Bestand, Badge.

  SKRIPT: identisch mit frontend/src/views/kasse/Kasse.vue – unverändert übernehmen.
  Hinweis: expandedCategories muss alle Kategorien enthalten (alle aufgeklappt).
-->
<template>
  <div class="kasse-container">
    <div class="kasse-products">
      <div v-if="productStore.isLoading" class="loading">Läuft...</div>
      <div v-else class="products-scroll">

        <!-- Category sections always visible -->
        <section
          v-for="category in activeCategories"
          :key="category.id"
          class="cat-section"
        >
          <header class="cat-header">
            <span class="cat-header-name">{{ category.name }}</span>
            <span class="cat-header-count">{{ getProductsByCategory(category.id).length }} Artikel</span>
          </header>
          <div class="products-grid">
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
        </section>

        <!-- Products without category -->
        <section v-if="productsWithoutCategory.length > 0" class="cat-section">
          <header class="cat-header">
            <span class="cat-header-name">Ohne Kategorie</span>
            <span class="cat-header-count">{{ productsWithoutCategory.length }} Artikel</span>
          </header>
          <div class="products-grid">
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
        </section>

      </div>
    </div>

    <!-- Bon-Bereich: identisch mit Kasse.vue -->
    <!-- ... (Bon-Bereich aus Kasse.vue unverändert übernehmen) ... -->
  </div>
</template>

<!-- SKRIPT: vollständig aus frontend/src/views/kasse/Kasse.vue übernehmen -->
<script setup>
// → Script-Block aus Kasse.vue 1:1 einfügen
// Hinweis: in onMounted alle Kategorien zu expandedCategories hinzufügen
// (expandedCategories.value = categories.value.map(c => c.id))
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
  overflow: hidden;
}

.products-scroll {
  height: 100%;
  overflow-y: auto;
  padding: .5rem .6rem;
  display: flex;
  flex-direction: column;
  gap: .9rem;
}

/* ── Category section ────────────────────────────────── */
.cat-section {
  display: flex;
  flex-direction: column;
  gap: .4rem;
}

.cat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: .28rem .6rem;
  background: color-mix(in srgb, var(--app-highlight-color) 10%, var(--app-surface-color) 90%);
  border-left: 3px solid var(--app-highlight-color);
  border-radius: 0 6px 6px 0;

  .cat-header-name {
    font-size: .76rem;
    font-weight: 700;
    color: var(--app-highlight-color);
    letter-spacing: .02em;
    text-transform: uppercase;
  }

  .cat-header-count {
    font-size: .65rem;
    color: #94a3b8;
    font-weight: 500;
  }
}

/* ── Product grid ────────────────────────────────────── */
.products-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: .38rem;

  @media (max-width: 1500px) { grid-template-columns: repeat(6, 1fr); }
  @media (max-width: 1200px) { grid-template-columns: repeat(5, 1fr); }
  @media (max-width: 950px)  { grid-template-columns: repeat(4, 1fr); }
  @media (max-width: 700px)  { grid-template-columns: repeat(3, 1fr); }
  @media (max-width: 480px)  { grid-template-columns: repeat(2, 1fr); }
}

/* ── Product card ────────────────────────────────────── */
.product-btn {
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  padding: 0;
  cursor: pointer;
  transition: all .13s;
  font-family: inherit;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  text-align: left;

  &:hover:not(:disabled) {
    border-color: var(--app-highlight-color);
    box-shadow: 0 2px 10px color-mix(in srgb, var(--app-highlight-color) 16%, transparent);
    transform: translateY(-1px);

    .card-img img { transform: scale(1.06); }
  }

  &:disabled { opacity: 0.4; cursor: not-allowed; }

  .card-img {
    height: 55px;
    overflow: hidden;
    background: #f0f4fa;
    flex-shrink: 0;
    position: relative;

    img { width: 100%; height: 100%; object-fit: contain; display: block; transition: transform .22s; }
  }

  .card-img-ph {
    width: 100%; height: 100%;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
  }

  .card-badge {
    position: absolute;
    top: 2px; left: 2px; z-index: 1;
    font-size: 8px; font-weight: 900;
    padding: 1px 3px; border-radius: 3px; line-height: 1.4;

    &.discount-badge { background: #fffbeb; color: #d97706; }
  }

  .card-body {
    padding: 4px 5px 5px;
    flex: 1; display: flex; flex-direction: column; gap: 2px;
  }

  .card-name {
    font-size: .67rem; font-weight: 700; line-height: 1.15; color: #111827;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  .card-bottom {
    display: flex; justify-content: space-between; align-items: center; margin-top: auto;
  }

  .card-price {
    font-size: .76rem; font-weight: 800;
    color: var(--app-highlight-color);
    letter-spacing: -0.02em;
  }

  .card-stock { font-size: .6rem; color: #94a3b8; font-weight: 500; }
}

.loading {
  text-align: center; color: #aaa; padding: 2rem;
}
</style>
