<template>
  <div class="kasse-container">
    <div class="kasse-products">
      <div v-if="productStore.isLoading" class="loading">Läuft...</div>
      <div v-else class="products-section">

        <!-- One row per category: narrow toggle button + product grid side by side -->
        <template
          v-for="(category, index) in activeCategories"
          :key="category.id"
        >
          <hr v-if="index > 0" class="category-separator" />
          <div class="category-row">
            <button
              class="cat-btn"
              :class="{ active: expandedCategories.includes(category.id) }"
              :style="getCategoryChipStyle(category, expandedCategories.includes(category.id))"
              @click="toggleCategory(category.id)"
            >
              <span class="cat-name">{{ category.name }}</span>
              <span class="cat-count">{{ getProductsByCategory(category.id).length }}</span>
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
                  :style="getCategoryCardStyle(category)"
                  @click="selectProduct(product, category.id)"
                >
                  <div class="card-img">
                    <span v-if="hasMemberPrice(product)" class="card-badge discount-badge">Rabatt</span>
                    <img v-if="product.image_path && !imageErrorMap[product.id]" :src="`/api/products/${product.id}/image`" :alt="product.name" @error="onImageError(product.id)" />
                    <div v-else class="card-img-ph">🛒</div>
                  </div>
                  <div class="card-body">
                    <div class="card-name">{{ product.name }}</div>
                    <div class="card-price">{{ formatPrice(getDisplayedProductPriceCents(product, category.id)) }}</div>
                    <div class="card-stock">{{ product.is_unlimited_stock ? '∞' : getAvailableStock(product) }}</div>
                    <!-- /div -->
                  </div>
                </button>
              </div>
            </div>
          </div>
        </template>

        <!-- Products without category -->
        <template v-if="productsWithoutCategory.length > 0">
          <hr v-if="activeCategories.length > 0" class="category-separator" />
          <div class="category-row">
            <button
              class="cat-btn"
              :class="{ active: expandedCategories.includes(0) }"
              @click="toggleCategory(0)"
            >
              <span class="cat-name">Ohne Kategorie</span>
              <span class="cat-count">{{ productsWithoutCategory.length }}</span>
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
                    <div class="card-price">{{ formatPrice(product.price_cents) }}</div>
                    <div class="card-stock">{{ product.is_unlimited_stock ? '∞' : getAvailableStock(product) }}</div>
                    <!-- /div-->
                  </div>
                </button>
              </div>
            </div>
          </div>
        </template>

        <!-- Hint shown when no category is expanded -->
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
        <!-- Top section: Items -->
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
          <div class="total-row">
            <div class="total-label">Zwischensumme:</div>
            <div class="total-amount">{{ formatPrice(cartSubtotal) }}</div>
          </div>
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

        <!-- Bottom section: Member selection -->
        <div class="member-selection-bottom">
          <div v-if="!cartStore.selectedMemberId" class="member-selector">
            <button
              @click="selectCustomer"
              class="btn btn-info full-width"
            >
              + Mitglied auswählen
            </button>
          </div>

          <div v-else class="member-card">
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
              Wechseln
            </button>
          </div>

          <!-- Payment buttons at bottom -->
          <div class="payment-section">
            <div class="payment-buttons">
              <button
                @click="openPaymentConfirmation('CASH')"
                :disabled="cartStore.items.length === 0"
                :style="getPaymentButtonStyle('CASH')"
                class="payment-btn"
              >
                💰 Zahlen - BAR
              </button>

              <button
                @click="openPaymentConfirmation('BALANCE')"
                :disabled="!cartStore.selectedMemberId || cartStore.items.length === 0 || selectedMemberBalance <= 0"
                :style="getPaymentButtonStyle('BALANCE')"
                class="payment-btn"
              >
                💳 Guthaben nutzen
              </button>

              <button
                @click="openVoucherModal"
                :disabled="cartStore.items.length === 0"
                class="payment-btn voucher-btn"
              >
                🎫 Gutschein
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

      <div class="deckel-section">
        <button @click="openDeckelOverview" class="btn-deckel" :disabled="cartStore.items.length === 0 && deckelList.length === 0" title="Bon als Deckel speichern oder vorhandenen Deckel öffnen">
          <span v-if="activeDeckelCount > 0" class="deckel-badge">{{ activeDeckelCount }}</span>
          <span>Deckel - Gastteam</span>
          <span>Ligaspiel</span>
        </button>
      </div>
    </div>

    <!-- Member Selection Modal -->
    <div v-if="showMemberModal" class="modal">
      <div class="modal-content member-modal">
        <h3>Mitglied auswählen</h3>
        <input
          v-model="memberSearch"
          type="text"
          placeholder="Nach Name oder Nummer suchen..."
          class="form-input"
        />
        <div v-if="filteredMembers.length > 0" class="member-grid">
          <button
            v-for="member in filteredMembers"
            :key="member.id"
            @click="selectMember(member)"
            class="member-item"
          >
            <div v-if="member.photo_path" class="member-photo">
              <img :src="`/api/members/${member.id}/photo`" :alt="getMemberFullName(member)" />
            </div>
            <div v-else class="member-photo member-photo-placeholder">👤</div>
            <div class="member-info-box">
              <div class="member-number-badge">Nr. {{ member.member_number }}</div>
              <div class="member-name-modal">{{ getMemberShortName(member) }}</div>
              <div class="balance">{{ formatBalance(member.balance_cents) }}</div>
            </div>
          </button>
        </div>
        <div v-else class="empty-bon">Keine Mitglieder gefunden</div>
        <div class="modal-actions">
          <button @click="showMemberModal = false" class="btn btn-danger">
            Abbrechen / Zurück
          </button>
        </div>
      </div>
    </div>

    <div v-if="showPaymentConfirmModal" class="modal">
      <div class="modal-content payment-modal">
        <template v-if="paymentResult">
          <h3>Verkauf abgeschlossen</h3>
          <p class="info-text">Der Verkauf wurde erfolgreich gebucht.</p>
          <div v-if="paymentResult.issued_prepaid_voucher_numbers?.length" class="issued-voucher-panel">
            <h4>💳 Verzehrkarten ausgegeben</h4>
            <div class="issued-voucher-box">
              <div v-for="voucherNumber in paymentResult.issued_prepaid_voucher_numbers" :key="voucherNumber" class="issued-voucher-number">
                {{ voucherNumber }}
              </div>
            </div>
            <div class="issued-voucher-alert">
              <p class="issued-voucher-note">
                Nummer auf der Verzehrkarte notieren - Einlösung ohne Nummer nicht möglich
              </p>
            </div>
          </div>
          <div class="modal-actions">
            <button @click="closePaymentConfirmation" class="btn btn-confirm-payment" :class="{ selected: true }">
              Fertig
            </button>
          </div>
        </template>
        <template v-else>
          <h3>{{ paymentSource === 'deckel' ? 'Deckel abrechnen' : 'Zahlung bestätigen' }}</h3>
          <div class="payment-method-chip">
            {{ getPaymentMethodLabel(pendingPaymentMethod) }}
          </div>
          <div class="payment-summary-list">
            <div v-for="item in paymentSummaryItems" :key="item.line_id || `${paymentSource}-${item.product_id}-${item.unit_price_cents}-${item.is_internal_material ? 'internal' : 'regular'}`" class="payment-summary-item">
              <div class="payment-summary-copy">
                <span>{{ item.quantity }}× {{ item.product_name }}</span>
                <small v-if="item.note">{{ item.note }}</small>
              </div>
              <strong>{{ formatPrice(item.total_price_cents) }}</strong>
            </div>
          </div>
          <div class="payment-summary-totals">
            <div class="total-row">
              <span>Zwischensumme</span>
              <strong>{{ formatPrice(paymentSubtotal) }}</strong>
            </div>
            <div v-if="paymentSource === 'cart' && hasAppliedVoucher" class="total-row">
              <span>Gutscheine</span>
              <strong>-{{ formatPrice(voucherAppliedAmount) }}</strong>
            </div>
            <div v-if="paymentSource === 'cart' && hasAppliedBalance" class="total-row">
              <span>Mitgliedsguthaben</span>
              <strong>-{{ formatPrice(balanceAppliedAmount) }}</strong>
            </div>
            <div v-if="paymentSource === 'cart' && pendingPaymentMethod === 'BALANCE'" class="total-row">
              <span>Mitglied</span>
              <strong>{{ selectedMemberName }}</strong>
            </div>
            <div v-if="paymentSource === 'deckel'" class="total-row">
              <span>Deckel</span>
              <strong>{{ activePaymentDeckel?.name }}</strong>
            </div>
            <div class="total-row grand-total modal-grand-total">
              <span>Zu zahlen</span>
              <strong>{{ formatPrice(paymentTotal) }}</strong>
            </div>
          </div>
          <div v-if="pendingPaymentMethod === 'CASH'" class="cash-payment-fields">
            <label>
              Bar gegeben
              <input
                ref="cashGivenInput"
                v-model="cashGiven"
                type="number"
                min="0"
                step="0.01"
                class="form-input"
                @keyup.enter="confirmPayment"
              />
            </label>
            <label>
              Rückgeld
              <input :value="cashChangeDisplay" type="text" class="form-input" readonly />
            </label>
          </div>
          <div class="modal-actions">
            <button @click="confirmPayment" class="btn btn-confirm-payment" :class="{ selected: true }" :disabled="processingPayment">
              {{ processingPayment ? '⏳ Wird verarbeitet...' : 'Bestätigen' }}
            </button>
            <button @click="closePaymentConfirmation" class="btn btn-danger" :disabled="processingPayment">
              Abbrechen / Zurück
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- Voucher Redemption Modal -->
    <div v-if="showVoucherModal" class="modal">
      <div class="modal-content voucher-modal">
        <h3>🎫 Gutschein einlösen</h3>

        <!-- Step 1: Input Voucher Number -->
        <div v-if="!voucherValidated" class="step">
          <input
            v-model="voucherNumber"
            type="text"
            :placeholder="`Gutscheinnummer eingeben (z. B. ${voucherPrefix}001)`"
            class="form-input voucher-input"
            @keyup.enter="validateVoucher"
            autocomplete="off"
          />

          <div v-if="voucherError" class="error-message">
            ❌ {{ voucherError }}
          </div>

          <div class="button-group">
            <button
              @click="validateVoucher"
              :disabled="!hasValidVoucherInput || validatingVoucher"
              class="btn btn-primary"
            >
              {{ validatingVoucher ? '⏳ Wird überprüft...' : '✓ Überprüfen' }}
            </button>
            <button @click="closeVoucherModal" class="btn btn-secondary">
              Abbrechen / Zurück
            </button>
          </div>
        </div>

        <!-- Step 2: Show Validation Result -->
        <div v-else-if="voucherValidation && !voucherRedeemed" class="step">
          <div
            :class="['validation-result', voucherValidation.valid ? 'valid' : 'invalid']"
          >
            <h4>{{ voucherValidation.valid ? '✅ Gültig' : '❌ Ungültig' }}</h4>
            <table class="voucher-details">
              <tr>
                <td>Nummer:</td>
                <td><strong>{{ voucherValidation.voucher_number }}</strong></td>
              </tr>
              <tr>
                <td>Typ:</td>
                <td>{{ voucherValidation.voucher_type === 'GIFT' ? '🎁 Gutschein' : '💳 Verzehrkarte' }}</td>
              </tr>
              <tr>
                <td>Wert:</td>
                <td><strong>{{ (voucherValidation.value_cents / 100).toFixed(2) }}€</strong></td>
              </tr>
              <tr v-if="voucherValidation.valid && cartSubtotal > 0">
                <td>Anrechnung:</td>
                <td><strong>{{ (voucherValidation.applicable_amount_cents / 100).toFixed(2) }}€</strong></td>
              </tr>
              <tr v-if="voucherValidation.valid && voucherValidation.remaining_value_cents > 0">
                <td>Restwert:</td>
                <td>{{ (voucherValidation.remaining_value_cents / 100).toFixed(2) }}€</td>
              </tr>
              <tr v-if="getExpiredStatusLabel(voucherValidation)">
                <td>Status:</td>
                <td>
                  {{ getExpiredStatusLabel(voucherValidation) }}
                </td>
              </tr>
              <tr v-if="voucherValidation.reason">
                <td>Grund:</td>
                <td>{{ formatVoucherReason(voucherValidation.reason) }}</td>
              </tr>
            </table>
            <p v-if="voucherValidation.message" class="info-text">
              ℹ️ {{ voucherValidation.message }}
            </p>
          </div>

          <div class="button-group">
            <button
              v-if="voucherValidation.valid"
              @click="redeemVoucher"
              :disabled="redeemingVoucher"
              class="btn"
              :class="voucherValidation.covers_cart_total ? 'btn-success' : 'btn-primary'"
            >
              {{ voucherActionLabel }}
            </button>
            <button @click="handleVoucherSecondaryAction" class="btn btn-secondary">
              Abbrechen / Zurück
            </button>
          </div>
        </div>

        <!-- Step 3: Success Message -->
        <div v-else-if="voucherRedeemed" class="step">
          <div class="success-message">
            <h4>✅ Gutschein eingelöst!</h4>
            <table class="voucher-details">
              <tr>
                <td>Nummer:</td>
                <td><strong>{{ voucherRedeemed.voucher_number }}</strong></td>
              </tr>
              <tr>
                <td>Typ:</td>
                <td>{{ voucherRedeemed.voucher_type === 'GIFT' ? '🎁 Gutschein' : '💳 Verzehrkarte' }}</td>
              </tr>
              <tr>
                <td>Wert:</td>
                <td><strong>{{ (voucherRedeemed.value_cents / 100).toFixed(2) }}€</strong></td>
              </tr>
            </table>
            <p class="info-text">
              {{ voucherRedeemed.message }}
            </p>
          </div>

          <div class="button-group">
            <button @click="closeVoucherModal" class="btn btn-primary">
              ✓ Fertig
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showDeckelCreateModal" class="modal">
      <div class="modal-content voucher-modal">
        <h3>📒 Neuen Deckel anlegen</h3>
        <p class="info-text">Der aktuelle Bon wird unter einem Namen zwischengespeichert und kann später bar bezahlt werden.</p>
        <input
          v-model="deckelName"
          type="text"
          placeholder="Name des Deckels"
          class="form-input voucher-input"
          @keyup.enter="createDeckel"
        />
        <div class="button-group">
          <button @click="createDeckel" :disabled="!deckelName.trim() || cartStore.items.length === 0" class="btn btn-primary">
            ✓ Speichern
          </button>
          <button @click="closeDeckelCreateModal" class="btn btn-secondary">
            Abbrechen / Zurück
          </button>
        </div>
      </div>
    </div>

    <div v-if="showDeckelOverviewModal" class="modal">
      <div class="modal-content voucher-modal deckel-overview-modal">
        <h3>📒 Deckelübersicht</h3>
        <p class="info-text">Vorhandene Deckel können eingesehen, mit dem aktuellen Bon erweitert oder direkt bar abgerechnet werden.</p>
        <div v-if="deckelList.length === 0" class="empty-bon">Keine gespeicherten Deckel vorhanden</div>
        <div v-else class="deckel-list">
          <button
            v-for="deckel in deckelList"
            :key="deckel.id"
            class="deckel-list-item"
            @click="openDeckelDetails(deckel)"
          >
            <div>
              <strong>{{ deckel.name }}</strong>
              <div>{{ deckel.items.length }} Positionen · {{ formatPrice(deckel.total_amount_cents) }}</div>
            </div>
            <div class="deckel-actions-inline" @click.stop>
              <button class="btn btn-primary" :disabled="cartStore.items.length === 0" @click="bookCurrentCartToDeckel(deckel)">
                Buchen
              </button>
              <button class="btn btn-info" @click="openDeckelForPayment(deckel)">
                Zahlen
              </button>
            </div>
          </button>
        </div>
        <div class="button-group">
          <button @click="openDeckelCreateModalFromOverview" :disabled="cartStore.items.length === 0" class="btn btn-primary">
            + Neuen Deckel anlegen
          </button>
          <button @click="closeDeckelOverviewModal" class="btn btn-secondary">
            Schließen
          </button>
        </div>
      </div>
    </div>

    <div v-if="showDeckelDetailsModal && activeDeckel" class="modal">
      <div class="modal-content payment-modal">
        <h3>📒 Deckel: {{ activeDeckel.name }}</h3>
        <p class="info-text">Hier sehen Sie alle bisher gebuchten Artikel und können den Deckel direkt bar abrechnen.</p>
        <div class="payment-summary-list">
          <div v-for="item in activeDeckel.items" :key="`deckel-${item.id || item.product_id}-${item.unit_price_cents}`" class="payment-summary-item">
            <div class="payment-summary-copy">
              <span>{{ item.quantity }}× {{ item.product_name }}</span>
              <small v-if="item.note">{{ item.note }}</small>
            </div>
            <strong>{{ formatPrice(item.total_price_cents) }}</strong>
          </div>
        </div>
        <div class="payment-summary-totals">
          <div class="total-row grand-total">
            <span>Gesamt</span>
            <strong>{{ formatPrice(activeDeckel.total_amount_cents) }}</strong>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="openDeckelPaymentConfirmation(activeDeckel)" class="btn btn-confirm-payment" :class="{ selected: true }">
            💰 Zahlen - BAR
          </button>
          <button @click="closeDeckelDetailsModal" class="btn btn-danger">
            Abbrechen / Zurück
          </button>
        </div>
      </div>
    </div>

    <div v-if="showInternalMaterialNoteModal && pendingInternalMaterialProduct" class="modal">
      <div class="modal-content internal-material-note-modal">
        <h3>Notiz für internes Material</h3>
        <p class="info-text">
          Optional können Sie eine Notiz für
          <strong>{{ pendingInternalMaterialProduct.name }}</strong>
          hinterlegen.
        </p>
        <textarea
          v-model.trim="internalMaterialNote"
          class="form-input"
          rows="4"
          maxlength="500"
          placeholder="z. B. Einsatzort, Zweck oder Ansprechpartner"
        ></textarea>
        <div class="modal-actions">
          <button @click="confirmInternalMaterialSelection" class="btn btn-confirm-payment" :class="{ selected: true }">
            Artikel hinzufügen
          </button>
          <button @click="closeInternalMaterialNoteModal" class="btn btn-danger">
            Abbrechen / Zurück
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useProductStore } from '@/stores/product'
import { useMemberStore } from '@/stores/member'
import { useCartStore } from '@/stores/cart'
import { useNotificationStore } from '@/stores/notification'
import { useAuthStore } from '@/stores/auth'
import { formatPrice, formatBalance } from '@/services/utils'
import { getMemberFullName, getMemberShortName, getMemberSearchText } from '@/services/member'
import apiService from '@/services/api'

const productStore = useProductStore()
const memberStore = useMemberStore()
const cartStore = useCartStore()
const notificationStore = useNotificationStore()
const authStore = useAuthStore()
const INTERNAL_MATERIAL_CATEGORY_NAME = 'Verbrauchsmaterial - Intern'

const showMemberModal = ref(false)
const showPaymentConfirmModal = ref(false)
const showInternalMaterialNoteModal = ref(false)
const memberSearch = ref('')
const pendingPaymentMethod = ref(null)
const processingPayment = ref(false)
const paymentResult = ref(null)
const expandedCategories = ref([])
const categories = ref([])
const bonWidth = ref(420)
const nextReceiptNumber = ref(null)
const cashGiven = ref('')
const cashGivenInput = ref(null)
const imageErrorMap = ref({})

const onImageError = (productId) => {
  imageErrorMap.value[productId] = true
}

// Voucher redemption
const showVoucherModal = ref(false)
const voucherNumber = ref('')
const voucherValidation = ref(null)
const voucherValidated = ref(false)
const voucherRedeemed = ref(null)
const voucherError = ref(null)
const validatingVoucher = ref(false)
const redeemingVoucher = ref(false)
const showDeckelCreateModal = ref(false)
const showDeckelOverviewModal = ref(false)
const showDeckelDetailsModal = ref(false)
const deckelName = ref('')
const deckelList = ref([])
const activeDeckel = ref(null)
const paymentSource = ref('cart')
const activePaymentDeckel = ref(null)
const pendingInternalMaterialProduct = ref(null)
const internalMaterialNote = ref('')

const voucherReasonLabels = {
  DYP_SIEGER: 'DYP-Sieger',
  PROMOTION: 'Promotion',
}
const voucherPrefix = `V-${new Date().getFullYear()}-`
const normalizedVoucherPrefix = voucherPrefix.toUpperCase()

const isInternalMaterialSale = (product, categoryId = null) => (
  !!categoryId && !!product?.categories?.some(category => (
    category.id === categoryId && category.name === INTERNAL_MATERIAL_CATEGORY_NAME
  ))
)

const getDisplayedProductPriceCents = (product, categoryId = null) => (
  isInternalMaterialSale(product, categoryId)
    ? 0
    : ((cartStore.selectedMemberId && cartStore.selectedMemberHasDiscount && product.member_price_cents)
        ? product.member_price_cents
        : product.price_cents)
)

const loadCategories = async () => {
  try {
    const response = await apiService.get('/categories?only_active=true')
    categories.value = response.data
    // Auto-expand categories that have products
    expandedCategories.value = []
    categories.value.forEach(category => {
      const productsInCategory = getProductsByCategory(category.id)
      if (productsInCategory.length > 0) {
        expandedCategories.value.push(category.id)
      }
    })
    // Also expand "Ohne Kategorie" if there are products without categories
    if (productsWithoutCategory.value.length > 0) {
      expandedCategories.value.push(0)
    }
    console.log('[Kasse] Categories loaded:', categories.value)
    console.log('[Kasse] Auto-expanded categories:', expandedCategories.value)
  } catch (err) {
    console.error('[Kasse] Failed to load categories:', err)
  }
}


/**
 * Returns '#1e293b' (dark) or '#ffffff' (light) depending on the
 * perceived luminance of the hex background color.
 */
const getContrastTextColor = (hex) => {
  if (!hex) return '#1e293b'
  const clean = hex.replace('#', '')
  if (clean.length < 6) return '#1e293b'
  const r = parseInt(clean.slice(0, 2), 16)
  const g = parseInt(clean.slice(2, 4), 16)
  const b = parseInt(clean.slice(4, 6), 16)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.5 ? '#1e293b' : '#ffffff'
}

const getCategoryChipStyle = (category, isActive) => {
  if (!category.color) return {}
  const textColor = getContrastTextColor(category.color)
  if (isActive) {
    return {
      background: category.color,
      borderColor: category.color,
      color: textColor,
    }
  }
  return {
    borderColor: category.color,
    color: category.color,
  }
}

const getCategoryCardStyle = (category) => {
  if (!category || !category.color) return {}
  return { borderColor: category.color }
}

const toggleCategory = (categoryId) => {
  const idx = expandedCategories.value.indexOf(categoryId)
  if (idx > -1) {
    expandedCategories.value.splice(idx, 1)
  } else {
    expandedCategories.value.push(categoryId)
  }
}

const getProductsByCategory = (categoryId) => {
  if (categoryId === 0) {
    return productsWithoutCategory.value
  }
  return productStore.products.filter(p =>
    p.categories && p.categories.some(c => c.id === categoryId)
  )
}

const activeCategories = computed(() => {
  return categories.value
    .filter(category => (
      category.is_active_in_kasse
      && (
        category.name !== INTERNAL_MATERIAL_CATEGORY_NAME
        || getProductsByCategory(category.id).length > 0
      )
    ))
    .sort((a, b) => a.display_order - b.display_order)
})

const productsWithoutCategory = computed(() => {
  return productStore.products.filter(p => !p.categories || p.categories.length === 0)
})

const selectedMemberName = computed(() => {
  const member = memberStore.members.find(m => m.id === cartStore.selectedMemberId)
  return getMemberShortName(member)
})

const selectedMemberBalance = computed(() => {
  const member = memberStore.members.find(m => m.id === cartStore.selectedMemberId)
  console.log(`[Kasse] Balance for member ${cartStore.selectedMemberId}:`, member?.balance_cents)
  return member?.balance_cents || 0
})

const selectedMember = computed(() => {
  return memberStore.members.find(m => m.id === cartStore.selectedMemberId) || null
})

const hasExpandedCategory = computed(() => expandedCategories.value.length > 0)

const cartSubtotal = computed(() => cartStore.getSubtotalAmount())
const voucherAppliedAmount = computed(() => cartStore.getVoucherAppliedAmount())
const balanceAppliedAmount = computed(() => cartStore.getBalanceAppliedAmount())
const hasAppliedVoucher = computed(() => cartStore.appliedVouchers.length > 0)
const hasAppliedBalance = computed(() => balanceAppliedAmount.value > 0)
const activeDeckelCount = computed(() => deckelList.value.length)
const paymentSummaryItems = computed(() => paymentSource.value === 'deckel'
  ? (activePaymentDeckel.value?.items || [])
  : cartStore.items
)
const paymentSubtotal = computed(() => paymentSource.value === 'deckel'
  ? (activePaymentDeckel.value?.total_amount_cents || 0)
  : cartSubtotal.value
)
const paymentTotal = computed(() => paymentSource.value === 'deckel'
  ? (activePaymentDeckel.value?.total_amount_cents || 0)
  : cartStore.getTotalAmount()
)
const cashChangeDisplay = computed(() => {
  const value = Number(cashGiven.value || 0)
  const change = Math.max(Math.round((value * 100) - paymentTotal.value), 0)
  return formatPrice(change)
})
const voucherActionLabel = computed(() => {
  if (redeemingVoucher.value) {
    return '⏳ Wird verarbeitet...'
  }

  return voucherValidation.value?.covers_cart_total
    ? '✓ Kauf abschließen'
    : '✓ Als Rabatt anwenden'
})
const hasValidVoucherInput = computed(() => {
  const normalizedVoucher = voucherNumber.value.trim().toUpperCase()
  return normalizedVoucher !== '' && normalizedVoucher !== normalizedVoucherPrefix
})

const bonPanelStyle = computed(() => ({
  width: `${bonWidth.value}px`,
  flexBasis: `${bonWidth.value}px`,
}))

const filteredMembers = computed(() => {
  const search = memberSearch.value.trim().toLowerCase()

  if (!search) {
    return memberStore.members
  }

  return memberStore.members.filter((member) => {
    return getMemberSearchText(member).includes(search)
  })
})

const getDeckelReservedQuantity = (productId, excludeDeckelId = null) => {
  return deckelList.value.reduce((sum, deckel) => {
    if (excludeDeckelId && deckel.id === excludeDeckelId) {
      return sum
    }
    return sum + deckel.items
      .filter(item => item.product_id === productId)
      .reduce((itemSum, item) => itemSum + item.quantity, 0)
  }, 0)
}

const getCartReservedQuantity = (productId, excludeLineId = null) => {
  return cartStore.items.reduce((sum, item) => {
    if (item.product_id !== productId || item.line_id === excludeLineId) {
      return sum
    }

    return sum + item.quantity
  }, 0)
}

const hasMemberPrice = (product) => product.member_price_cents !== null && product.member_price_cents !== undefined

const showProductBadge = (product) => hasMemberPrice(product) || product.is_unlimited_stock

const getAvailableStock = (product, excludeDeckelId = null, excludeLineId = null) => {
  if (product.is_unlimited_stock) {
    return Number.POSITIVE_INFINITY
  }

  return Math.max(
    (product.stock_quantity || 0)
      - getDeckelReservedQuantity(product.id, excludeDeckelId)
      - getCartReservedQuantity(product.id, excludeLineId),
    0
  )
}

const isProductOutOfStock = (product) => !product.is_unlimited_stock && getAvailableStock(product) === 0

const getStockLabel = (product) => (
  product.is_unlimited_stock
    ? 'Unbegrenzt verfügbar'
    : `Verfügbar: ${getAvailableStock(product)}`
)

const selectProduct = (product, categoryId = null) => {
  if (isInternalMaterialSale(product, categoryId)) {
    pendingInternalMaterialProduct.value = {
      ...product,
      is_internal_material: true,
    }
    internalMaterialNote.value = ''
    showInternalMaterialNoteModal.value = true
    return
  }

  const result = cartStore.addItem({
    ...product,
    is_internal_material: false,
  }, getAvailableStock(product))
  if (!result.success) {
    notificationStore.error(`Nur ${getAvailableStock(product)} Einheiten von ${product.name} verfügbar`)
  }
}

const closeInternalMaterialNoteModal = () => {
  showInternalMaterialNoteModal.value = false
  pendingInternalMaterialProduct.value = null
  internalMaterialNote.value = ''
}

const confirmInternalMaterialSelection = () => {
  if (!pendingInternalMaterialProduct.value) {
    return
  }

  const product = pendingInternalMaterialProduct.value
  const result = cartStore.addItem({
    ...product,
    note: internalMaterialNote.value,
  }, getAvailableStock(product))

  if (!result.success) {
    notificationStore.error(`Nur ${getAvailableStock(product)} Einheiten von ${product.name} verfügbar`)
    return
  }

  closeInternalMaterialNoteModal()
}

const changeCartItemQuantity = (item, quantity) => {
  const product = productStore.products.find(productEntry => productEntry.id === item.product_id)
  const maxQuantity = product ? getAvailableStock(product, null, item.line_id) : item.quantity
  const result = cartStore.updateItemQuantity(item.line_id, quantity, maxQuantity)
  if (!result.success && result.quantity > 0) {
    notificationStore.error(`Nur ${maxQuantity} Einheiten von ${item.product_name} verfügbar`)
  }
}

const selectCustomer = () => {
  showMemberModal.value = true
}

const validatePaymentMethod = (method) => {
  if (method === 'BALANCE') {
    if (!cartStore.selectedMemberId) {
      notificationStore.error('Bitte wählen Sie ein Mitglied aus')
      return false
    }

    if (selectedMemberBalance.value <= 0) {
      notificationStore.error('Das Mitglied hat kein Guthaben')
      return false
    }

  }

  return true
}

const applyPartialBalanceAndContinue = ({ notify = false } = {}) => {
  const currentlyAppliedBalance = cartStore.getBalanceAppliedAmount()
  const remainingMemberBalance = Math.max(selectedMemberBalance.value - currentlyAppliedBalance, 0)
  const remainingTotal = cartStore.getTotalAmount()

  if (cartStore.selectedMemberId && remainingMemberBalance > 0 && remainingMemberBalance < remainingTotal) {
    cartStore.applyBalanceDiscount(currentlyAppliedBalance + remainingMemberBalance)

    if (notify) {
      notificationStore.success('Verfügbares Mitgliedsguthaben wurde als Rabatt auf den Warenkorb angerechnet')
    }
  }

  openPaymentConfirmation('CASH')
}

const openPaymentConfirmation = (method, options = {}) => {
  const nextSource = options.source || 'cart'
  if (nextSource === 'cart' && !validatePaymentMethod(method)) {
    return
  }

  paymentSource.value = nextSource
  activePaymentDeckel.value = options.deckel || null
  pendingPaymentMethod.value = method
  showPaymentConfirmModal.value = true
  paymentResult.value = null
  cashGiven.value = method === 'CASH' ? (paymentTotal.value / 100).toFixed(2) : ''
  nextTick(() => {
    if (method === 'CASH') {
      cashGivenInput.value?.focus()
      cashGivenInput.value?.select?.()
    }
  })
}

const closePaymentConfirmation = () => {
  if (processingPayment.value) {
    return
  }

  showPaymentConfirmModal.value = false
  pendingPaymentMethod.value = null
  cashGiven.value = ''
  paymentResult.value = null
  paymentSource.value = 'cart'
  activePaymentDeckel.value = null
}

const confirmPayment = async () => {
  if (!pendingPaymentMethod.value) {
    return
  }

  if (pendingPaymentMethod.value === 'CASH') {
    const givenCents = Math.round(Number(cashGiven.value || 0) * 100)
    if (givenCents < paymentTotal.value) {
      notificationStore.error('Der gegebene Barbetrag reicht nicht aus')
      return
    }
  }

  processingPayment.value = true
  const transaction = await handlePaymentAndCheckout(pendingPaymentMethod.value)
  processingPayment.value = false

  if (transaction?.appliedBalanceOnly) {
    closePaymentConfirmation()
    return
  }

  if (transaction) {
    if (transaction.issued_prepaid_voucher_numbers?.length) {
      paymentResult.value = transaction
      return
    }
    closePaymentConfirmation()
  }
}

const handlePaymentAndCheckout = async (method) => {
  if (paymentSource.value === 'deckel') {
    return handleDeckelPayment()
  }

  if (!validatePaymentMethod(method)) {
    return false
  }

  if (method === 'BALANCE' && selectedMemberBalance.value < cartStore.getTotalAmount()) {
    applyPartialBalanceAndContinue({ notify: true })
    return { appliedBalanceOnly: true }
  }

  cartStore.paymentMethod = method
  return handleCheckout()
}

const selectMember = (member) => {
  cartStore.removeBalanceDiscount()
  cartStore.selectedMemberId = member.id
  cartStore.selectedMemberHasDiscount = !!member.has_discount
  cartStore.recalculatePrices()  // Update prices to member prices
  showMemberModal.value = false
}

const openVoucherModal = () => {
  resetVoucherState()
  showVoucherModal.value = true
}

const validateVoucher = async () => {
  const normalizedVoucher = voucherNumber.value.trim().toUpperCase()
  if (!normalizedVoucher || normalizedVoucher === normalizedVoucherPrefix) return

  voucherNumber.value = normalizedVoucher

  validatingVoucher.value = true
  voucherError.value = null
  voucherValidation.value = null

  try {
    const response = await apiService.post('/transactions/voucher/validate', {
      voucher_number: voucherNumber.value,
      cart_total_cents: cartStore.getTotalAmount(),
    })
    voucherValidation.value = response.data
    voucherValidated.value = true
    console.log('[Kasse] Voucher validated:', response.data)
  } catch (error) {
    const detail = error.response?.data?.detail || error.message || 'Fehler bei der Validierung'
    voucherError.value = detail
    voucherValidated.value = false
    console.error('[Kasse] Voucher validation failed:', error)
  } finally {
    validatingVoucher.value = false
  }
}

const redeemVoucher = async () => {
  if (!voucherValidation.value || !voucherValidation.value.valid) return

  redeemingVoucher.value = true
  voucherError.value = null

  try {
    const appliedVoucher = {
      voucher_number: voucherValidation.value.voucher_number,
      voucher_type: voucherValidation.value.voucher_type,
      value_cents: voucherValidation.value.value_cents,
      applied_amount_cents: voucherValidation.value.applicable_amount_cents,
      message: voucherValidation.value.message,
    }

    cartStore.applyVoucher(appliedVoucher)

    if (voucherValidation.value.covers_cart_total) {
      voucherRedeemed.value = appliedVoucher
      cartStore.paymentMethod = 'CASH'
      const successMessage = voucherValidation.value.remaining_value_cents > 0
        ? 'Verkauf mit Gutschein abgeschlossen. Restguthaben bleibt erhalten.'
        : 'Verkauf mit Gutschein abgeschlossen'
      await handleCheckout(successMessage)
      closeVoucherModal()
      return
    }

    voucherRedeemed.value = {
      ...appliedVoucher,
      message: voucherValidation.value.remaining_value_cents > 0
        ? `Gutschein ${voucherValidation.value.voucher_number} wurde übernommen. Restguthaben bleibt erhalten.`
        : `Gutschein ${voucherValidation.value.voucher_number} wurde als Rabatt übernommen.`,
    }
    notificationStore.success(`Gutschein ${voucherValidation.value.voucher_number} als Rabatt übernommen`)
    closeVoucherModal()
    applyPartialBalanceAndContinue({ notify: true })
  } catch (error) {
    const detail = error.response?.data?.detail || error.message || 'Fehler bei der Einlösung'
    voucherError.value = detail
    console.error('[Kasse] Voucher redemption failed:', error)
  } finally {
    redeemingVoucher.value = false
  }
}

const resetVoucherState = () => {
  voucherNumber.value = voucherPrefix
  voucherValidation.value = null
  voucherValidated.value = false
  voucherRedeemed.value = null
  voucherError.value = null
}

const closeVoucherModal = () => {
  resetVoucherState()
  showVoucherModal.value = false
}

const backToVoucherInput = () => {
  resetVoucherState()
  showVoucherModal.value = true
}

const handleVoucherSecondaryAction = () => {
  if (voucherValidation.value?.valid) {
    backToVoucherInput()
    return
  }

  closeVoucherModal()
}

const removeAppliedVoucher = (voucherNumber) => {
  cartStore.removeVoucher(voucherNumber)
  notificationStore.success('Gutschein aus dem Bon entfernt')
}

const removeAppliedBalance = () => {
  cartStore.removeBalanceDiscount()
  notificationStore.success('Mitgliedsguthaben aus dem Bon entfernt')
}

const serializeCartItems = () => {
  return cartStore.items.map(item => ({
    product_id: item.product_id,
    quantity: item.quantity,
    unit_price_cents: item.unit_price_cents,
    is_internal_material: item.is_internal_material,
    note: item.note,
  }))
}

const loadDeckelList = async () => {
  try {
    const response = await apiService.get('/deckel')
    deckelList.value = response.data
    if (activeDeckel.value) {
      activeDeckel.value = deckelList.value.find(deckel => deckel.id === activeDeckel.value.id) || null
    }
    if (activePaymentDeckel.value) {
      activePaymentDeckel.value = deckelList.value.find(deckel => deckel.id === activePaymentDeckel.value.id) || null
    }
  } catch (error) {
    console.error('[Kasse] Failed to load deckel:', error)
    notificationStore.error(error.response?.data?.detail || 'Deckel konnten nicht geladen werden')
  }
}

const closeDeckelCreateModal = () => {
  showDeckelCreateModal.value = false
  deckelName.value = ''
}

const openDeckelCreateModalFromOverview = () => {
  closeDeckelOverviewModal()
  showDeckelCreateModal.value = true
}

const closeDeckelOverviewModal = () => {
  showDeckelOverviewModal.value = false
}

const closeDeckelDetailsModal = () => {
  showDeckelDetailsModal.value = false
  activeDeckel.value = null
}

const openDeckelOverview = async () => {
  await loadDeckelList()
  if (deckelList.value.length === 0) {
    if (cartStore.items.length === 0) {
      notificationStore.error('Keine gespeicherten Deckel vorhanden')
      return
    }
    showDeckelCreateModal.value = true
    return
  }

  showDeckelOverviewModal.value = true
}

const openDeckelDetails = (deckel) => {
  activeDeckel.value = deckel
  showDeckelDetailsModal.value = true
}

const openDeckelForPayment = (deckel) => {
  openDeckelDetails(deckel)
}

const createDeckel = async () => {
  try {
    const response = await apiService.post('/deckel', {
      name: deckelName.value,
      items: serializeCartItems(),
    })
    cartStore.clear()
    closeDeckelCreateModal()
    await Promise.all([loadDeckelList(), productStore.getProducts(), loadNextReceiptNumber()])
    notificationStore.success(`Deckel "${response.data.name}" gespeichert`)
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Deckel konnte nicht gespeichert werden')
  }
}

const bookCurrentCartToDeckel = async (deckel) => {
  try {
    await apiService.post(`/deckel/${deckel.id}/book`, {
      items: serializeCartItems(),
    })
    cartStore.clear()
    await Promise.all([loadDeckelList(), productStore.getProducts()])
    notificationStore.success(`Bon auf Deckel "${deckel.name}" gebucht`)
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Bon konnte nicht auf den Deckel gebucht werden')
  }
}

const openDeckelPaymentConfirmation = (deckel) => {
  activePaymentDeckel.value = deckel
  closeDeckelDetailsModal()
  closeDeckelOverviewModal()
  openPaymentConfirmation('CASH', { source: 'deckel', deckel })
}

const handleDeckelPayment = async () => {
  if (!activePaymentDeckel.value) {
    return null
  }

  try {
    const response = await apiService.post(`/deckel/${activePaymentDeckel.value.id}/pay`)
    notificationStore.success(`Deckel "${activePaymentDeckel.value.name}" wurde bezahlt`)
    await Promise.all([productStore.getProducts(), memberStore.getMembers(), loadDeckelList(), loadNextReceiptNumber()])
    return response.data
  } catch (error) {
    notificationStore.error(error.response?.data?.detail || 'Deckel konnte nicht abgerechnet werden')
    return null
  }
}

const clampBonWidth = (width) => {
  const minWidth = 340
  const maxWidth = Math.min(window.innerWidth * 0.7, 720)
  bonWidth.value = Math.min(Math.max(width, minWidth), maxWidth)
}

const BON_RESIZE_OFFSET = 16

const stopResizing = () => {
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  window.removeEventListener('mousemove', handleResize)
  window.removeEventListener('mouseup', stopResizing)
}

const handleResize = (event) => {
  const nextWidth = window.innerWidth - event.clientX - BON_RESIZE_OFFSET
  clampBonWidth(nextWidth)
}

const startResizing = (event) => {
  if (window.innerWidth <= 768) {
    return
  }

  event.preventDefault()
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  window.addEventListener('mousemove', handleResize)
  window.addEventListener('mouseup', stopResizing)
}

const formatVoucherReason = (reason) => {
  if (!reason) return '-'
  return voucherReasonLabels[reason] || reason
}

const getExpiredStatusLabel = (voucher) => {
  if (voucher?.status === 'EXPIRED') {
    return '⏰ Abgelaufen'
  }
  return ''
}

const getPaymentMethodLabel = (method) => {
  if (paymentSource.value === 'deckel') {
    return '💰 Zahlung in Bar'
  }
  if (method === 'BALANCE') {
    return selectedMemberBalance.value >= cartStore.getTotalAmount()
      ? '💳 Zahlung mit Guthaben'
      : '💳 Guthaben als Rabatt anwenden'
  }

  return '💰 Zahlung in Bar'
}

const loadNextReceiptNumber = async () => {
  try {
    const response = await apiService.get('/transactions/next-receipt-number')
    nextReceiptNumber.value = response.data.receipt_number
  } catch (error) {
    console.error('[Kasse] Failed to load next receipt number:', error)
  }
}

const handleCheckout = async (successMessage = 'Verkauf abgeschlossen') => {
  try {
    console.log('[Kasse] Starting checkout...')
    const transaction = await cartStore.checkout(authStore.user.id)
    console.log('[Kasse] Checkout successful, transaction:', transaction)
    notificationStore.success(successMessage)
    // Reload members to update balances
    await Promise.all([memberStore.getMembers(), productStore.getProducts(), loadNextReceiptNumber(), loadDeckelList()])
    return transaction
  } catch (err) {
    console.error('[Kasse] Checkout failed:', err)
    const errorMessage = err.response?.data?.detail || err.message || 'Fehler bei der Abrechnung'
    console.error('[Kasse] Showing error notification:', errorMessage)
    notificationStore.error(errorMessage)
    return null
  }
}

const getPaymentButtonStyle = (method) => {
  const balance = selectedMemberBalance.value
  const total = cartStore.getTotalAmount()
  const hasMember = !!cartStore.selectedMemberId

  console.log(`[Kasse] Button style for ${method}: hasMember=${hasMember}, balance=${balance}, total=${total}`)

  // No member selected - only BAR button is green
  if (!hasMember) {
    if (method === 'CASH') {
      return { background: 'var(--app-highlight-color)', color: 'var(--app-highlight-contrast)' }
    } else {
      return { background: '#999', color: 'white', cursor: 'not-allowed' }
    }
  }

  // Member selected - check balance
  const hasEnoughBalance = balance >= total
  console.log(`[Kasse] HasEnoughBalance: ${hasEnoughBalance} (${balance} >= ${total})`)

  if (method === 'CASH') {
    return { background: 'var(--app-highlight-color)', color: 'var(--app-highlight-contrast)' }
  } else {
    if (balance > 0) {
      return { background: 'var(--app-banner-color)', color: 'var(--app-banner-contrast)' }
    } else {
      return { background: '#ccc', color: '#999', cursor: 'not-allowed' }
    }
  }
}

// Watch für Member-Updates
watch(
  () => memberStore.members,
  (newMembers) => {
    if (newMembers && newMembers.length > 0) {
      const selectedMem = newMembers.find(m => m.id === cartStore.selectedMemberId)
      if (selectedMem) {
        console.log('[Kasse] Members updated, selected member balance is now:', selectedMem.balance_cents)
      }
    }
  },
  { deep: true }
)

onMounted(async () => {
  await productStore.getProducts()
  await memberStore.getMembers()
  await loadCategories()
  await loadDeckelList()
  await loadNextReceiptNumber()
  clampBonWidth(bonWidth.value)
  console.log('[Kasse] Initial members loaded:', memberStore.members.length)
})

onBeforeUnmount(() => {
  stopResizing()
})
</script>

<style scoped lang="scss">
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
  padding: 1rem;
  box-shadow: 0 8px 20px rgba(24, 28, 34, 0.1);
  overflow-y: auto;
  border: 1px solid var(--app-banner-color);
}

.kasse-resizer {
  width: 12px;
  margin: 0 0.5rem;
  border-radius: 999px;
  background: var(--app-highlight-color);
  cursor: col-resize;
  flex: 0 0 12px;
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
  background: var(--app-surface-color);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 10px 24px rgba(24, 28, 34, 0.14);
  overflow-y: auto;
  border: 1px solid var(--app-banner-color);
  border-left: 5px solid var(--app-highlight-color);

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
}

/* ── Category row: narrow toggle + products side by side ─ */
.category-row {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: .75rem;
}

/* ── Category toggle button (always compact/narrow) ────── */
.cat-btn {
  flex-shrink: 0;
  /* So schmal wie möglich – nur Padding + Schrift */
  width: 26px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;   /* Text startet unten */
  padding: .5rem .2rem;
  background: var(--app-banner-color);
  color: var(--app-banner-contrast);
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  text-align: center;
  transition: opacity .18s, background .18s, border-color .18s;
  gap: 4px;
  align-self: stretch;

  &:hover {
    opacity: .82;
  }

  &.active {
    background: var(--app-highlight-color);
    color: var(--app-highlight-contrast);
  }

  .cat-name {
    /* vertical-rl + rotate(180deg) = Text läuft von UNTEN nach OBEN */
    writing-mode: vertical-rl;
    transform: rotate(180deg);
    text-orientation: mixed;
    font-size: .68rem;
    line-height: 1;
    letter-spacing: 0.05em;
    overflow: hidden;
    /* Kein max-height – wächst mit dem Inhalt */
  }

  .cat-count {
    font-size: .6rem;
    opacity: .75;
    font-weight: 500;
    flex-shrink: 0;
    writing-mode: horizontal-tb;
    transform: none;
  }
}

.category-products {
  flex: 1;
  min-width: 0;
  margin-bottom: .75rem;
}

.empty-products {
  text-align: center;
  color: #aaa;
  padding: 3rem 1rem;
  font-size: .95rem;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: .65rem;

  @media (max-width: 1400px) {
    grid-template-columns: repeat(4, 1fr);
  }

  @media (max-width: 1100px) {
    grid-template-columns: repeat(3, 1fr);
  }

  @media (max-width: 800px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
}

/* ── Product card ─────────────────────────────────────── */
.product-btn {
  background: #fff;
  border: 1.5px solid color-mix(in srgb, var(--app-banner-color) 22%, white 78%);
  border-radius: 12px;
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
      /* "contain" sorgt dafür, dass das Bild komplett angezeigt wird */
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
    left: 5px;
    z-index: 1;
    font-size: 10px;
    font-weight: 800;
    padding: 2px 5px;
    border-radius: 4px;
    letter-spacing: 0.04em;
    line-height: 1.4;

    &.discount-badge {
      background: #fffbeb;
      color: #d97706;
    }
  }

  .card-body {
    padding: 7px 8px 8px;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .card-name {
    font-size: 1.0rem;
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
  }

  .card-stock {
    font-size: .72rem;
    color: #64748b;
    font-weight: 500;

    /* Fügt den Text "Verfügbar: " vor den Inhalt der Klasse ein */
    &::before {
      content: "Lager: ";
    }
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
    margin-bottom: 0.5rem;
  }

  .member-balance {
    color: #666;
    margin-bottom: 0.5rem;
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
  gap: 1rem;
  flex: 1;
  overflow: hidden;
}

.payment-section {
  flex-shrink: 0;
  margin-top: 1.5rem;

  .payment-buttons {
    display: flex;
    flex-direction: row;
    gap: 0.75rem;

    .payment-btn {
      flex: 1;
      font-size: 0.95rem;
      padding: 0.8rem;
      border-radius: 6px;
      font-weight: 600;
      transition: all 0.2s;
      border: none;
      cursor: pointer;

      &:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      &:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
      }

      &.active {
        box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.3);
        transform: scale(1.02);
      }

      &.voucher-btn {
        background: var(--app-banner-color);
        color: var(--app-banner-contrast);
      }
    }
  }
}

.bon-secondary-actions {
  flex-shrink: 0;
  margin-top: 0.75rem;
}

.bon-items {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #cfcfcf;
  border-radius: 4px;
  padding: 0.5rem;
  background: #e7e7e7;
  min-height: 50px;
}

.bon-item {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  padding: 0.75rem;
  background: white;
  border-radius: 4px;
  margin-bottom: 0.5rem;

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
  padding: 0.75rem;
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
  padding: 0.65rem 0.85rem;
  background: color-mix(in srgb, var(--app-banner-color) 12%, white 88%);
  border-radius: 8px;
  color: var(--app-banner-color);
  font-weight: 600;
  text-align: center;
}

.total-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
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
  gap: 1rem;
  padding: 0.85rem 1rem;
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
  gap: 1rem;
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
    padding: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 0.75rem;

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
      padding: 0.5rem;
      background: white;
      border: 1px solid var(--app-banner-color);
      color: var(--app-banner-color);
      border-radius: 4px;
      cursor: pointer;
      font-weight: 600;
      font-size: 0.85rem;
      transition: all 0.2s;
      margin-bottom: 0.75rem;

      &:hover {
        background: color-mix(in srgb, var(--app-banner-color) 10%, white 90%);
      }
    }
  }

  .payment-section {
    width: 100%;

    .payment-buttons {
      display: flex;
      flex-direction: row;
      gap: 0.75rem;

      .payment-btn {
        flex: 1;
        font-size: 0.95rem;
        padding: 0.8rem;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s;
        border: none;
        cursor: pointer;

        &:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        &:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
      }
    }
  }
}

.member-selection {
  display: none;
}

.deckel-section {
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid color-mix(in srgb, var(--app-banner-color) 18%, white 82%);
}

.btn-deckel,
.btn-cancel {
  width: 100%;
  min-height: 60px;
  padding: 0.95rem 1.35rem;
  border-radius: 12px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 700;
  transition: all 0.2s;

  &:hover {
    transform: translateY(-1px);
  }

  &:active {
    transform: scale(0.95);
  }
}

.btn-deckel {
  background: linear-gradient(135deg, #e7edf5, #d6e0eb);
  color: #334155;
  border: 1px solid #b8c6d8;
  display: flex;
  position: relative;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 0.1rem;
  text-align: center;
  line-height: 1.2;

  &:hover {
    background: linear-gradient(135deg, #dde7f1, #cad7e5);
    border-color: #9fb2c8;
    color: #1f2937;
  }
}

.deckel-badge {
  position: absolute;
  top: 0.55rem;
  right: 0.7rem;
  min-width: 1.5rem;
  height: 1.5rem;
  padding: 0 0.35rem;
  border-radius: 999px;
  background: var(--app-highlight-color, #0f766e);
  color: var(--app-highlight-contrast, #ffffff);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 800;
  line-height: 1;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.18);
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

.issued-voucher-panel {
  margin-top: 1rem;

  h4 {
    margin-bottom: 0.75rem;
  }
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
  margin-top: 0.75rem;
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
  padding: 0.75rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
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
      padding: 0.75rem;
      border: 1px solid #ddd;
      border-radius: 4px;
      margin-bottom: 1rem;
      font-size: 1rem;
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
        gap: 1rem;
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
          padding: 0.5rem;

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
        padding: 0.5rem;
        background: #f9f9f9;
        border-radius: 4px;
      }

      .error-message {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 4px;
        color: #721c24;
        padding: 0.75rem;
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
  padding: 0.75rem;
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
      font-size: 0.8rem;
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
  gap: 1rem;
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
  gap: 1rem;
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
    font-size: 1rem;
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
