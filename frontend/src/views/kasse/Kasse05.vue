<template>
  <div class="kasse-container">
    <div class="kasse-products">
      <div v-if="productStore.isLoading" class="loading">Läuft...</div>
      <div v-else class="products-section">

        <template
          v-for="(category, index) in activeCategories"
          :key="category.id"
        >
          <hr v-if="index > 0" class="category-separator" />
          <div class="category-row">
            <button
              class="cat-btn"
              :class="{ 'cat-btn--expanded': expandedCategories.includes(category.id) }"
              :style="getCategoryChipStyle(category, expandedCategories.includes(category.id))"
              @click="toggleCategory(category.id)"
            >
              <span class="cat-name">{{ category.name }}</span>
              <span v-if="!expandedCategories.includes(category.id)" class="cat-count">{{ getProductsByCategory(category.id).length }}</span>
            </button>
            <div
              v-if="expandedCategories.includes(category.id)"
              class="category-products"
            >
              <div class="products-grid">
                <button
                  v-for="product in getProductsByCategory(category.id)"
                  :key="product.id"
                  :disabled="isProductOutOfStock(product)"
                  class="product-btn"
                  :class="{ 'product-btn--oos': isProductOutOfStock(product) }"
                  :style="getCategoryCardStyle(category)"
                  @click="selectProduct(product, category.id)"
                >
                  <div class="card-img">
                    <span v-if="hasMemberPrice(product)" class="card-badge discount-badge">%</span>
                    <span class="card-badge stock-badge" :class="{ 'stock-badge--in': !isProductOutOfStock(product), 'stock-badge--out': isProductOutOfStock(product) }">{{ product.is_unlimited_stock ? '∞' : getAvailableStock(product) }}</span>
                    <img v-if="product.image_path && !imageErrorMap[product.id]" :src="`/api/products/${product.id}/image`" :alt="product.name" @error="onImageError(product.id)" />
                    <div v-else class="card-img-ph">🛒</div>
                  </div>
                  <div class="card-body">
                    <div class="card-name">{{ product.name }}</div>
                    <div class="card-bottom">
                      <span class="card-price">{{ formatPrice(getDisplayedProductPriceCents(product, category.id)) }}</span>
                    </div>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </template>

        <template v-if="productsWithoutCategory.length > 0">
          <hr v-if="activeCategories.length > 0" class="category-separator" />
          <div class="category-row">
            <button
              class="cat-btn"
              :class="{ 'cat-btn--expanded': expandedCategories.includes(0) }"
              @click="toggleCategory(0)"
            >
              <span class="cat-name">Ohne Kategorie</span>
              <span v-if="!expandedCategories.includes(0)" class="cat-count">{{ productsWithoutCategory.length }}</span>
            </button>
            <div
              v-if="expandedCategories.includes(0)"
              class="category-products"
            >
              <div class="products-grid">
                <button
                  v-for="product in productsWithoutCategory"
                  :key="product.id"
                  :disabled="isProductOutOfStock(product)"
                  class="product-btn"
                  :class="{ 'product-btn--oos': isProductOutOfStock(product) }"
                  @click="selectProduct(product)"
                >
                  <div class="card-img">
                    <span v-if="hasMemberPrice(product)" class="card-badge discount-badge">%</span>
                    <span class="card-badge stock-badge" :class="{ 'stock-badge--in': !isProductOutOfStock(product), 'stock-badge--out': isProductOutOfStock(product) }">{{ product.is_unlimited_stock ? '∞' : getAvailableStock(product) }}</span>
                    <img v-if="product.image_path && !imageErrorMap[product.id]" :src="`/api/products/${product.id}/image`" :alt="product.name" @error="onImageError(product.id)" />
                    <div v-else class="card-img-ph">🛒</div>
                  </div>
                  <div class="card-body">
                    <div class="card-name">{{ product.name }}</div>
                    <div class="card-bottom">
                      <span class="card-price">{{ formatPrice(product.price_cents) }}</span>
                    </div>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </template>

        <div v-if="!hasExpandedCategory" class="empty-products">
          Kategorie auswählen
        </div>

      </div>
    </div>

    <div
      class="kasse-resizer"
      @mousedown="startResizing"
    ></div>

    <div class="kasse-bon" :style="bonPanelStyle">
      <div class="bon-content">
        <div class="receipt-number-banner">
          Beleg: <strong>#{{ nextReceiptNumber || '-' }}</strong>
        </div>
        <div class="bon-items">
          <div
            v-for="item in cartStore.items"
            :key="item.line_id"
            class="bon-item"
          >
            <div class="item-name">
              <span>{{ item.product_name }}</span>
              <span v-if="item.note" class="item-note-preview">{{ item.note }}</span>
            </div>
            <div class="item-controls">
              <button @click="changeCartItemQuantity(item, item.quantity - 1)" class="btn-qty">−</button>
              <input
                v-model.number="item.quantity"
                type="number"
                min="1"
                @change="changeCartItemQuantity(item, item.quantity)"
                class="qty-input"
              />
              <button @click="changeCartItemQuantity(item, item.quantity + 1)" class="btn-qty">+</button>
            </div>
            <div class="item-price">{{ formatPrice(item.total_price_cents) }}</div>
            <button @click="cartStore.removeItem(item.line_id)" class="btn-remove">✕</button>
          </div>
        </div>

        <div v-if="cartStore.items.length === 0" class="empty-bon">
          Keine Artikel im Bon
        </div>

        <div class="bon-total">
          <div v-for="voucher in cartStore.appliedVouchers" :key="voucher.voucher_number" class="total-row voucher-row">
            <div class="total-label">
              Gutscheineinlösung
              <small>{{ voucher.voucher_number }}</small>
            </div>
            <div class="total-amount">-{{ formatPrice(voucher.applied_amount_cents) }}</div>
          </div>
          <div v-if="hasAppliedBalance" class="total-row voucher-row">
            <div class="total-label">
              Mitgliedsguthaben
              <small>{{ selectedMemberName }}</small>
            </div>
            <div class="total-amount">-{{ formatPrice(balanceAppliedAmount) }}</div>
          </div>
          <div class="total-row grand-total">
            <div class="total-label">Zu zahlen:</div>
            <div class="total-amount">{{ formatPrice(cartStore.getTotalAmount()) }}</div>
          </div>
        </div>

        <div v-if="hasAppliedVoucher || hasAppliedBalance" class="voucher-applied-card">
          <div class="applied-discounts">
            <div v-for="voucher in cartStore.appliedVouchers" :key="voucher.voucher_number" class="applied-discount-line">
              <div>
                <strong>🎫 Gutschein aktiv</strong>
                <div class="voucher-applied-hint">
                  {{ voucher.message }}
                </div>
              </div>
              <button @click="removeAppliedVoucher(voucher.voucher_number)" class="btn-remove-voucher">
                Entfernen
              </button>
            </div>
            <div v-if="hasAppliedBalance" class="applied-discount-line">
              <div>
                <strong>💳 Mitgliedsguthaben aktiv</strong>
                <div class="voucher-applied-hint">
                  {{ selectedMemberName }}: {{ formatBalance(balanceAppliedAmount) }} angerechnet
                </div>
              </div>
              <button @click="removeAppliedBalance" class="btn-remove-voucher">
                Entfernen
              </button>
            </div>
          </div>
        </div>

        <div class="member-selection-bottom">
          <div class="bon-quick-actions">
            <button
              @click="selectCustomer"
              class="btn btn-info"
            >
              {{ cartStore.selectedMemberId ? 'Mitglied wechseln' : '+ Mitglied auswählen' }}
            </button>
            <button
              v-if="appSettingsStore.settings.deckel_enabled"
              @click="openDeckelOverview"
              class="btn-deckel-inline"
              :disabled="cartStore.items.length === 0 && deckelList.length === 0"
              title="Bon als Deckel speichern oder vorhandenen Deckel öffnen"
            >
              <span v-if="activeDeckelCount > 0" class="deckel-badge-inline">{{ activeDeckelCount }}</span>
              Deckel erstellen
            </button>
          </div>

          <div v-if="cartStore.selectedMemberId" class="member-card">
            <div class="member-card-header">
              <div v-if="selectedMember && selectedMember.photo_path" class="member-avatar">
                <img :src="`/api/members/${cartStore.selectedMemberId}/photo`" :alt="selectedMemberName" />
              </div>
              <div v-else class="member-avatar-placeholder">
                👤
              </div>
              <div class="member-card-info">
                <div class="member-name">{{ selectedMemberName }}</div>
                <div class="member-balance-display">
                  Guthaben: {{ formatBalance(selectedMemberBalance) }}
                </div>
              </div>
            </div>
            <button
               @click="() => {
                 cartStore.selectedMemberId = null;
                 cartStore.selectedMemberHasDiscount = false;
                 cartStore.removeBalanceDiscount();
                 cartStore.recalculatePrices();
               }"
              class="btn-change"
            >
              Mitglied entfernen
            </button>
          </div>

          <div class="payment-section">
            <div class="payment-buttons">
              <button
                @click="openPaymentConfirmation('CASH')"
                :disabled="cartStore.items.length === 0"
                class="payment-btn payment-btn--cash"
              >
                💰 Zahlen - BAR
              </button>

              <button
                @click="openPaymentConfirmation('BALANCE')"
                :disabled="!cartStore.selectedMemberId || cartStore.items.length === 0 || selectedMemberBalance <= 0"
                :style="getPaymentButtonStyle('BALANCE')"
                class="payment-btn payment-btn--balance"
              >
                💳 Guthaben nutzen
              </button>

              <button
                @click="openVoucherModal"
                :disabled="cartStore.items.length === 0"
                class="payment-btn voucher-btn"
              >
                🎫 Gutschein / Verzehrkarte
              </button>
            </div>
          </div>
          <div class="bon-secondary-actions">
            <button @click="cartStore.clear()" class="btn-cancel" title="Kassiervorgang abbrechen">
              Bon abbrechen
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Components -->
    <MemberModal v-if="showMemberModal" />
    <PaymentModal v-if="showPaymentConfirmModal" />
    <VoucherModal v-if="showVoucherModal" />
    <DeckelCreateModal v-if="showDeckelCreateModal" />
    <DeckelOverviewModal v-if="showDeckelOverviewModal" />
    <DeckelDetailsModal v-if="showDeckelDetailsModal && activeDeckel" />
    <InternalMaterialNoteModal v-if="showInternalMaterialNoteModal && pendingInternalMaterialProduct" />
    <VariablePriceModal v-if="showVariablePriceModal && pendingVariablePriceProduct" />
  </div>
</template>

<script setup>
import { provide } from 'vue'
import useKasse from './useKasse.js'
import { useAppSettingsStore } from '@/stores/appSettings'
import MemberModal from './modal/MemberModal.vue'
import PaymentModal from './modal/PaymentModal.vue'
import VoucherModal from './modal/VoucherModal.vue'
import DeckelCreateModal from './modal/DeckelCreateModal.vue'
import DeckelOverviewModal from './modal/DeckelOverviewModal.vue'
import DeckelDetailsModal from './modal/DeckelDetailsModal.vue'
import InternalMaterialNoteModal from './modal/InternalMaterialNoteModal.vue'
import VariablePriceModal from './modal/VariablePriceModal.vue'

const appSettingsStore = useAppSettingsStore()
const kasse = useKasse()
provide('kasse', kasse)

const {
  productStore,
  cartStore,
  showMemberModal,
  showPaymentConfirmModal,
  showVoucherModal,
  showDeckelCreateModal,
  showDeckelOverviewModal,
  showDeckelDetailsModal,
  showInternalMaterialNoteModal,
  showVariablePriceModal,
  pendingVariablePriceProduct,
  pendingInternalMaterialProduct,
  activeDeckel,
  imageErrorMap,
  onImageError,
  activeCategories,
  expandedCategories,
  hasExpandedCategory,
  productsWithoutCategory,
  getCategoryChipStyle,
  getCategoryCardStyle,
  getProductsByCategory,
  toggleCategory,
  isProductOutOfStock,
  hasMemberPrice,
  getAvailableStock,
  getDisplayedProductPriceCents,
  formatPrice,
  formatBalance,
  selectProduct,
  nextReceiptNumber,
  bonPanelStyle,
  startResizing,
  balanceAppliedAmount,
  hasAppliedVoucher,
  hasAppliedBalance,
  selectedMemberName,
  selectedMember,
  selectedMemberBalance,
  removeAppliedVoucher,
  removeAppliedBalance,
  selectCustomer,
  openPaymentConfirmation,
  openVoucherModal,
  getPaymentButtonStyle,
  deckelList,
  activeDeckelCount,
  openDeckelOverview,
  changeCartItemQuantity,
} = kasse
</script>

<style scoped lang="scss">

/* =========================================================================
   DESIGN KONFIGURATION (Hier kannst du die wichtigsten Werte anpassen)
   ========================================================================= */
.kasse-container {
  --kasse-spacing-outer: 0.5rem;          /* Abstand Container zum Rand (vorher 1rem) */
  --kasse-spacing-panels: 0.5rem;         /* Inneres Padding der Hauptpanels (Produkte) */
  --kasse-spacing-bon: 0.55rem;           /* Inneres Padding des Bon-Bereichs (kompakter) */
  --kasse-spacing-bon-items: 0.3rem;      /* Padding für Bon-Listeneinträge */
  --kasse-resizer-width: 6px;             /* Breite des Trenners (vorher 12px) */
  --kasse-bg-opacity: 85%;                /* Deckkraft der weißen Hintergründe (Transparenz) */

  display: flex;
  gap: 0;                                 /* Abstand zwischen Produkt- und Bonbereich entfernt */
  padding: var(--kasse-spacing-outer);
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
  /* Hintergrund mit 85% Transparenz */
  background-color: color-mix(in srgb, var(--kasse-area-background-color, var(--app-surface-color)) var(--kasse-bg-opacity), transparent);
  --kasse-products-background-overlay: color-mix(
    in srgb,
    transparent var(--kasse-products-background-opacity, 100%),
    var(--kasse-area-background-color, var(--app-surface-color))
  );
  background-image:
    linear-gradient(
      var(--kasse-products-background-overlay),
      var(--kasse-products-background-overlay)
    ),
    var(--kasse-products-background-image, none);
  background-size: var(--kasse-products-background-size, 100%);
  background-repeat: no-repeat;
  background-position: center;
  border-radius: 12px;
  padding: var(--kasse-spacing-panels);
  box-shadow: 0 8px 20px rgba(24, 28, 34, 0.1);
  overflow-y: auto;
  border: 1px solid var(--app-banner-color);
}

.kasse-resizer {
  width: var(--kasse-resizer-width);
  margin: 0 3px; /* small horizontal breathing room on both sides */
  border-radius: 999px;
  background: var(--app-highlight-color);
  cursor: col-resize;
  flex: 0 0 var(--kasse-resizer-width);
  align-self: stretch;
  transition: background 0.2s ease;

  &:hover {
    opacity: 0.85;
  }

  @media (max-width: 768px) {
    display: none;
  }
}

.kasse-bon {
  flex: 0 0 420px;
  display: flex;
  flex-direction: column;
  width: 420px;
  min-width: 320px;
  max-width: min(70vw, 720px);
  /* Hintergrund mit 85% Transparenz */
  background: color-mix(in srgb, var(--app-surface-color) var(--kasse-bg-opacity), transparent);
  border-radius: 8px;
  padding: var(--kasse-spacing-bon);
  box-shadow: 0 10px 24px rgba(24, 28, 34, 0.14);
  overflow-y: auto;
  border: 1px solid var(--app-banner-color);

  h2 {
    margin: 0 0 1rem 0;
    color: var(--app-banner-color);
    font-size: 1.3rem;
  }

  @media (max-width: 768px) {
    width: 100%;
    min-width: 0;
    max-width: 100%;
    flex-basis: auto !important;
  }
}

.products-section {
  display: flex;
  flex-direction: column;
  gap: .5rem;
}

/* ── Category separator ───────────────────────────────── */
.category-separator {
  border: none;
  border-top: 1px solid color-mix(in srgb, var(--app-banner-color) 25%, transparent);
  margin: .15rem 0;
  padding: 1px 0;
}

/* ── Category row ─────────────────────────────────────── */
.category-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: .75rem;
  /* Keine min-height — eingeklappte Zeilen sollen kompakt sein */
}

/* Expandierte Zeile bekommt die Mindesthöhe der Produktkarten */
.category-row:has(.cat-btn--expanded) {
  min-height: 116px;
}

/* ── Kategorie-Blase: gemeinsame Basis ───────────────── */
.cat-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;

  background: var(--app-banner-color);
  color: var(--app-banner-contrast);
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  text-align: center;
  transition: opacity .18s, background .18s, border-color .18s;

  &:hover { opacity: .82; }

  /* ── Eingeklappt: horizontale Pille, kippt in den Kartenbereich ── */
  &:not(.cat-btn--expanded) {
    flex-direction: row;
    width: auto;
    height: 28px;         /* flache horizontale Pille */
    padding: 2px .65rem;

    .cat-name {
      writing-mode: horizontal-tb;
      transform: none;
      font-size: .85rem;
      line-height: 1;
      letter-spacing: 0.03em;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 180px;   /* ab hier kürzen */
      display: block;
    }

    .cat-count {
      font-size: .8rem;
      opacity: .75;
      font-weight: 500;
      flex-shrink: 0;
      writing-mode: horizontal-tb;
    }
  }

  /* ── Expandiert: schmale vertikale Leiste, volle Zeilenhöhe ──── */
  &.cat-btn--expanded {
    flex-direction: column;
    width: 28px;
    align-self: stretch;  /* volle Höhe der category-row */
    padding: .4rem .1rem;
    background: var(--app-highlight-color);
    color: var(--app-highlight-contrast);

    .cat-name {
      writing-mode: vertical-rl;
      transform: rotate(180deg);
      text-orientation: mixed;
      font-size: .8rem;
      line-height: 1;
      letter-spacing: 0.05em;
      overflow: hidden;
      text-overflow: ellipsis;
      max-height: 90px;
      white-space: nowrap;
      display: block;
      text-align: center;
    }

    .cat-count {
      font-size: .7rem;
      opacity: .75;
      font-weight: 500;
      flex-shrink: 0;
      writing-mode: horizontal-tb;
      transform: none;
    }
  }
}

.category-products {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center; /* Produktkarten vertikal zentriert */
}

.empty-products {
  text-align: center;
  color: #aaa;
  padding: 3rem 1rem;
  font-size: .95rem;
}

.products-grid {
  display: grid;
  width: 100%;
  grid-template-columns: repeat(7, 1fr); /* Default für große Bildschirme (>1280px) */
  gap: .65rem;

  @media (max-width: 1280px) {
    grid-template-columns: repeat(6, 1fr);
  }

  @media (max-width: 1100px) {
    grid-template-columns: repeat(5, 1fr);
  }

  @media (max-width: 900px) {
    grid-template-columns: repeat(4, 1fr);
  }

  @media (max-width: 700px) {
    grid-template-columns: repeat(3, 1fr);
  }

  @media (max-width: 500px) {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* ── Product card ─────────────────────────────────────── */
.product-btn {
  background: #fff;
  border: 1.5px solid color-mix(in srgb, var(--app-banner-color) 22%, white 78%);
  border-radius: 10px;
  padding: 0;
  cursor: pointer;
  transition: all .18s;
  text-align: center;
  font-family: inherit;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;

  &:hover:not(:disabled) {
    border-color: var(--app-highlight-color);
    box-shadow: 0 4px 16px color-mix(in srgb, var(--app-highlight-color) 18%, transparent);
    transform: translateY(-2px);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .card-img {
    height: 80px;
    overflow: hidden;
    background: #eef1f7;
    flex-shrink: 0;
    position: relative;

    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
      transition: none;
    }
  }

  .card-img-ph {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
  }

  .card-badge {
    position: absolute;
    top: 5px;
    z-index: 1;
    font-weight: 800;
    padding: 2px 5px;
    border-radius: 4px;
    letter-spacing: 0.04em;
    line-height: 1.4;

    &.discount-badge {
      left: 5px;
      font-size: 10px;
      background: #fffbeb;
      color: #d97706;
    }

    &.stock-badge {
      right: 5px;
      font-size: 11px;
      background: #e2e8f0;
      color: #475569;

      &.stock-badge--in {
        background: #dcfce7;
        color: #15803d;
      }

      &.stock-badge--out {
        background: #fee2e2;
        color: #b91c1c;
      }
    }
  }

  .card-body {
    padding: 4px 6px; /* Reduziert von 7px 8px */
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .card-name {
    font-size: .8rem;
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
    font-size: .9rem;
    font-weight: 800;
    color: var(--app-highlight-color);
    letter-spacing: -0.02em;
    margin: 0 auto; /* Zentriert den Preis, da Stock entfernt wurde */
  }

}

/* OOS diagonal red bar overlay */
.product-btn--oos {
  &::after {
    content: '';
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(
      -45deg,
      transparent,
      transparent 8px,
      rgba(239, 68, 68, 0.28) 8px,
      rgba(239, 68, 68, 0.28) 14px
    );
    pointer-events: none;
    z-index: 3;
    border-radius: inherit;
  }
}

.member-info {
  background: color-mix(in srgb, var(--app-background-color) 55%, white 45%);
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  border-left: 4px solid var(--app-highlight-color);

  .member-name {
    font-weight: 600;
    color: var(--app-highlight-color);
    margin-bottom: 0.35rem;
  }

  .member-balance {
    color: #666;
    margin-bottom: 0.35rem;
  }

  .btn-small {
    background: white;
    border: 1px solid #ddd;
    padding: 0.4rem 0.8rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85rem;

    &:hover {
      background: #d5dae0;
    }
  }
}

.bon-content {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
  flex: 1;
  overflow: hidden;
}

.payment-section {
  flex-shrink: 0;
  margin-top: 0.65rem;

  .payment-buttons {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-template-rows: repeat(2, minmax(0, 1fr));
    gap: 0.5rem;

    .payment-btn {
      flex: 1;
      font-size: 0.88rem;
      padding: 0.62rem;
      border-radius: 6px;
      font-weight: 600;
      transition: all 0.2s;
      border: none;
      cursor: pointer;
      text-align: center;

      &:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      &:hover:not(:disabled) {
        transform: translateY(-1px);
        box-shadow: 0 3px 7px rgba(0, 0, 0, 0.16);
      }

      &.active {
        box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.3);
        transform: scale(1.02);
      }

      &.voucher-btn {
        background: var(--app-banner-color);
        color: var(--app-banner-contrast);
      }

      &.payment-btn--cash {
        grid-column: 1 / 2;
        grid-row: 1 / 3;
        background: #2e7d32;
        color: #ffffff;
      }

      &.payment-btn--balance {
        grid-column: 2 / 3;
        grid-row: 1 / 2;
      }

      &.voucher-btn {
        grid-column: 2 / 3;
        grid-row: 2 / 3;
      }
    }
  }
}

.bon-secondary-actions {
  flex-shrink: 0;
  margin-top: 0.45rem;
}

.bon-items {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #cfcfcf;
  border-radius: 4px;
  padding: 0.35rem;
  background: #e7e7e7;
  min-height: 50px;
}

.bon-item {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  padding: var(--kasse-spacing-bon-items);
  background: white;
  border-radius: 4px;
  margin-bottom: 0.35rem;

  .item-name {
    flex: 1;
    font-weight: 500;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .item-note-preview {
    font-size: 0.75rem;
    color: #5b6470;
    font-weight: 400;
    white-space: normal;
  }

  .item-controls {
    display: flex;
    gap: 0.3rem;
    align-items: center;

    button {
      width: 28px;
      height: 28px;
      border: 1px solid #ddd;
      background: white;
      cursor: pointer;
      border-radius: 4px;
      font-size: 0.9rem;

      &:hover {
        background: #f0f0f0;
      }
    }
  }

  .qty-input {
    width: 40px;
    border: 1px solid #ddd;
    border-radius: 4px;
    text-align: center;
    font-size: 0.9rem;
    padding: 0.3rem;
  }

  .item-price {
    font-weight: 600;
    min-width: 70px;
    text-align: right;
    color: var(--app-highlight-color);
  }

  .btn-remove {
    background: #ffebee;
    color: #c62828;
    border: none;
    border-radius: 4px;
    width: 28px;
    height: 28px;
    cursor: pointer;
    font-weight: bold;
    font-size: 0.9rem;

    &:hover {
      background: #ffcdd2;
    }
  }
}

.empty-bon {
  text-align: center;
  color: #999;
  padding: 2rem 1rem;
  font-size: 0.95rem;
}

.bon-total {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  padding: 0.6rem;
  background: color-mix(in srgb, var(--app-background-color) 65%, white 35%);
  border-radius: 4px;

  .total-label {
    font-weight: 600;
  }

  .total-amount {
    color: var(--app-highlight-color);
    font-weight: bold;
    font-size: 1.1rem;
  }
}

.receipt-number-banner {
  margin-bottom: 0.75rem;
  padding: 0.4rem 0.6rem; /* Reduziert von 0.65rem 0.85rem */
  background: color-mix(in srgb, var(--app-banner-color) 12%, white 88%);
  border-radius: 8px;
  color: var(--app-banner-color);
  font-weight: 600;
  text-align: center;
}

.total-row {
  display: flex;
  justify-content: space-between;
  gap: 0.7rem;
  width: 100%;
}

.grand-total {
  padding-top: 0.55rem;
  border-top: 1px solid color-mix(in srgb, var(--app-banner-color) 25%, white 75%);

  .total-amount {
    font-size: 1.3rem;
  }
}

.voucher-row {
  color: var(--app-highlight-color);

  small {
    display: block;
    color: #5d646d;
    font-weight: 500;
  }
}

.voucher-applied-card {
  display: flex;
  gap: 0.7rem;
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  background: color-mix(in srgb, var(--app-highlight-color) 12%, white 88%);
  border: 1px solid color-mix(in srgb, var(--app-highlight-color) 30%, white 70%);
}

.applied-discounts {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
}

.applied-discount-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.7rem;
}

.voucher-applied-hint {
  color: #4f555d;
  font-size: 0.85rem;
}

.btn-remove-voucher {
  border: 1px solid color-mix(in srgb, var(--app-highlight-color) 35%, white 65%);
  background: #eef1f4;
  color: var(--app-highlight-color);
  border-radius: 6px;
  padding: 0.45rem 0.75rem;
  cursor: pointer;
}

.member-selection-bottom {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;

  .bon-quick-actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.5rem;

    .btn {
      width: 100%;
      padding: 0.65rem;
      font-size: 0.9rem;
    }
  }

  .member-selector {
    width: 100%;

    .full-width {
      width: 100%;
    }
  }

  .member-card {
    background: #eef1f4;
    border: 2px solid var(--app-banner-color);
    border-radius: 8px;
    padding: 0.6rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 0;

    .member-card-header {
      display: flex;
      gap: 0.75rem;
      align-items: center;

      .member-avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        overflow: hidden;
        border: 2px solid var(--app-banner-color);
        flex-shrink: 0;

        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      }

      .member-avatar-placeholder {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: #e3f2fd;
        border: 2px solid var(--app-banner-color);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        flex-shrink: 0;
      }

      .member-card-info {
        flex: 1;
        min-width: 0;

        .member-name {
          font-weight: 600;
          color: #333;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .member-balance-display {
          font-size: 0.85rem;
          color: var(--app-highlight-color);
          font-weight: 600;
        }
      }
    }

    .btn-change {
      width: 100%;
      padding: 0.35rem;
      background: white;
      border: 1px solid var(--app-banner-color);
      color: var(--app-banner-color);
      border-radius: 4px;
      cursor: pointer;
      font-weight: 600;
      font-size: 0.85rem;
      transition: all 0.2s;
      margin-bottom: 0;

      &:hover {
        background: color-mix(in srgb, var(--app-banner-color) 10%, white 90%);
      }
    }
  }

  .payment-section {
    width: 100%;

    .payment-buttons {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      grid-template-rows: repeat(2, minmax(0, 1fr));
      gap: 0.5rem;

      .payment-btn {
        flex: 1;
        font-size: 0.88rem;
        padding: 0.62rem;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s;
        border: none;
        cursor: pointer;
        text-align: center;

        &:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        &:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 3px 7px rgba(0, 0, 0, 0.16);
        }

        &.payment-btn--cash {
          grid-column: 1 / 2;
          grid-row: 1 / 3;
        }

        &.payment-btn--balance {
          grid-column: 2 / 3;
          grid-row: 1 / 2;
        }

        &.voucher-btn {
          grid-column: 2 / 3;
          grid-row: 2 / 3;
        }
      }
    }
  }
}

.member-selection {
  display: none;
}

.btn-cancel,
.btn-deckel-inline {
  width: 100%;
  min-height: 46px;
  padding: 0.62rem 0.85rem;
  border-radius: 10px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 700;
  transition: all 0.2s;

  &:hover {
    transform: translateY(-1px);
  }

  &:active {
    transform: scale(0.95);
  }
}

.btn-deckel-inline {
  background: linear-gradient(135deg, #e7edf5, #d6e0eb);
  color: #334155;
  border: 1px solid #b8c6d8;
  display: inline-flex;
  position: relative;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 0.35rem;
  text-align: center;
  line-height: 1.2;

  &:hover {
    background: linear-gradient(135deg, #dde7f1, #cad7e5);
    border-color: #9fb2c8;
    color: #1f2937;
  }
}

.deckel-badge-inline {
  position: absolute;
  top: 0.35rem;
  right: 0.45rem;
  min-width: 1.25rem;
  height: 1.25rem;
  padding: 0 0.25rem;
  border-radius: 999px;
  background: var(--app-highlight-color, #0f766e);
  color: var(--app-highlight-contrast, #ffffff);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 800;
  line-height: 1;
  box-shadow: 0 3px 9px rgba(15, 23, 42, 0.16);
}

.btn-cancel {
  background: linear-gradient(135deg, #f87171, #dc2626);
  color: #fff7f7;
  border: 2px solid #b91c1c;
}

.btn-cancel:hover {
  background: linear-gradient(135deg, #ef4444, #b91c1c);
  border-color: #991b1b;
  color: #ffffff;
}

/* Modals styles unchanged - remaining CSS keeps existing definitions */
.issued-voucher-panel {
  margin-top: 1rem;
  h4 { margin-bottom: 0.75rem; }
}

.issued-voucher-box {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  border-radius: 10px;
  background: linear-gradient(135deg, #dcfce7, #bbf7d0);
  border: 1px solid #22c55e;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.4);
}

.issued-voucher-number {
  font-size: 1.25rem;
  font-weight: 800;
  color: #166534;
  text-align: center;
  font-family: monospace;
}

.issued-voucher-alert {
  margin-top: 0.45rem;
  padding: 0.9rem 1rem;
  border-radius: 10px;
  border: 2px solid #ef4444;
  background: linear-gradient(135deg, #fef2f2, #fee2e2);
}

.issued-voucher-note {
  margin: 0;
  color: #991b1b;
  font-weight: 700;
}

.btn {
  padding: 0.6rem;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &:not(:disabled):hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
}

.btn-success {
  background-color: #4caf50;
  color: white;

  &:not(:disabled):hover {
    background-color: #45a049;
  }
}

.btn-danger {
  background-color: #f44336;
  color: white;

  &:not(:disabled):hover {
    background-color: #da190b;
  }
}

.btn-info {
  background-color: var(--app-banner-color);
  color: var(--app-banner-contrast);

  &:not(:disabled):hover {
    opacity: 0.9;
  }
}

.btn-subtle {
  background-color: #f5f5f5;
  color: #666;
  border: 1px solid #ddd;
  font-size: 0.85rem;

  &:not(:disabled):hover {
    background-color: #e0e0e0;
    border-color: #999;
  }
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;

  .modal-content {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    width: 90%;
    max-width: 400px;
    max-height: 80vh;
    overflow-y: auto;

    h3 {
      margin-top: 0;
      color: #333;
    }

    .form-input {
      width: 100%;
      padding: 0.6rem;
      border: 1px solid #ddd;
      border-radius: 4px;
      margin-bottom: 1rem;
      font-size: 0.9rem;
    }

    &.member-modal {
      width: min(75vw, 1200px);
      max-width: 1200px;
      max-height: 75vh;
    }

    &.payment-modal {
      max-width: 560px;

      .cash-payment-fields {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.7rem;
        margin-bottom: 1rem;

        label {
          font-weight: 600;
          color: #334155;
        }

        .form-input {
          margin-bottom: 0;
          margin-top: 0.5rem;
        }
      }
    }

    &.voucher-modal {
      max-width: 500px;

      .voucher-input {
        text-transform: uppercase;
        font-family: monospace;
        letter-spacing: 0.1em;
      }

      .step {
        animation: fadeIn 0.2s;
      }

      .validation-result {
        border: 2px solid #ddd;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;

        h4 {
          margin-top: 0;
          margin-bottom: 1rem;
        }

        &.valid {
          background: #d4edda;
          border-color: #c3e6cb;
          color: #155724;

          h4 {
            color: #155724;
          }
        }

        &.invalid {
          background: #f8d7da;
          border-color: #f5c6cb;
          color: #721c24;

          h4 {
            color: #721c24;
          }
        }
      }

      .voucher-details {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 1rem;
        font-size: 0.9rem;

        tr {
          border-bottom: 1px solid rgba(0, 0, 0, 0.1);
        }

        td {
          padding: 0.35rem;

          &:first-child {
            color: #666;
            font-weight: 500;
            width: 100px;
          }

          &:last-child {
            text-align: right;
          }
        }
      }

      .success-message {
        background: #d4edda;
        border: 2px solid #c3e6cb;
        border-radius: 8px;
        padding: 1.5rem;
        color: #155724;
        margin-bottom: 1.5rem;

        h4 {
          margin-top: 0;
          margin-bottom: 1rem;
          color: #155724;
        }
      }

      .info-text {
        font-size: 0.85rem;
        color: #666;
        margin: 0;
        padding: 0.35rem;
        background: #f9f9f9;
        border-radius: 4px;
      }

      .error-message {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 4px;
        color: #721c24;
        padding: 0.6rem;
        margin-bottom: 1rem;
        font-size: 0.9rem;
      }

      .button-group {
        display: flex;
        gap: 0.75rem;
        justify-content: flex-end;

        button {
          flex: 1;
        }
      }
    }

    &.internal-material-note-modal {
      max-width: 460px;

      textarea.form-input {
        min-height: 110px;
        resize: vertical;
      }
    }
  }
}

.btn-confirm-payment {
  background: #2e7d32;
  color: #fff;
  box-shadow: 0 0 0 2px rgba(46, 125, 50, 0.2);

  &.selected {
    box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.24), 0 0 16px rgba(46, 125, 50, 0.45);
  }

  &:not(:disabled):hover {
    background: #256a29;
  }
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
}

.member-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
  max-height: 60vh;
  overflow-y: auto;
}

.member-item {
  background: white;
  border: 2px solid #ddd;
  padding: 0.6rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: center;
  text-align: left;

  &:hover {
    background: #f0f0f0;
    border-color: var(--app-banner-color);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .member-photo {
    width: 84px;
    height: 84px;
    border-radius: 50%;
    overflow: hidden;
    background: #e0e0e0;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }

  .member-photo-placeholder {
    font-size: 2rem;
  }

  .member-info-box {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    width: 100%;
    align-items: center;

    .member-number-badge {
      font-size: 0.72rem;
      color: var(--app-banner-color);
      font-weight: 600;
    }

    .member-name-modal {
      font-weight: 600;
      color: #333;
      text-align: center;
    }

    .balance {
      font-size: 0.85rem;
      color: #666;
    }
  }

  .balance {
    color: var(--app-highlight-color);
    font-weight: 600;
  }
}

.payment-method-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
  padding: 0.45rem 0.85rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--app-banner-color) 12%, white 88%);
  color: var(--app-banner-color);
  font-weight: 600;
}

.payment-summary-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 280px;
  overflow-y: auto;
  margin-bottom: 1rem;
}

.payment-summary-item,
.payment-summary-totals .total-row {
  display: flex;
  justify-content: space-between;
  gap: 0.7rem;
}

.payment-summary-item {
  padding: 0.65rem 0.75rem;
  border-radius: 6px;
  background: #f5f5f5;

  .payment-summary-copy {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    min-width: 0;

    small {
      color: #5b6470;
      font-size: 0.75rem;
      white-space: normal;
    }
  }
}

.deckel-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.deckel-list-item {
  width: 100%;
  border: 1px solid #d7dde4;
  border-radius: 8px;
  padding: 0.9rem;
  background: #fff;
  display: flex;
  justify-content: space-between;
  gap: 0.7rem;
  align-items: center;
  text-align: left;
  cursor: pointer;
}

.deckel-actions-inline {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.payment-summary-totals {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.payment-summary-totals .modal-grand-total {
  margin-top: 0.35rem;
  padding: 0.95rem 1rem;
  align-items: center;
  border: 2px solid color-mix(in srgb, var(--app-highlight-color) 30%, var(--app-banner-color) 70%);
  border-radius: 10px;
  background: color-mix(in srgb, var(--app-highlight-color) 10%, white 90%);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);

  span,
  strong {
    color: var(--app-banner-color);
  }

  span {
    font-size: 0.9rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  strong {
    font-size: 1.7rem;
    font-weight: 800;
  }
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #999;
}
</style>
