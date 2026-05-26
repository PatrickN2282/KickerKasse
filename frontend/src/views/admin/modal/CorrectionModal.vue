<template>
  <div
    v-if="show"
    class="modal-overlay"
    @click.self="$emit('close')"
  >
    <div class="modal-card modal-compact">
      <header class="modal-header">
        <div>
          <h3>{{ activeTab === 'members' ? 'Guthaben korrigieren' : 'Bestand korrigieren' }}</h3>
          <p class="modal-subtitle">
            {{ activeTab === 'members' && selectedMember
              ? getMemberFullName(selectedMember)
              : selectedProduct?.name || '—' }}
          </p>
        </div>
        <button
          class="close-btn"
          type="button"
          @click="$emit('close')"
        >
          ✕
        </button>
      </header>

      <div class="modal-correction-body">
        <div class="correction-subject-row">
          <template v-if="activeTab === 'members' && selectedMember">
            <div class="subject-avatar">
              <img
                v-if="selectedMember.photo_path"
                :src="`/api/members/${selectedMember.id}/photo`"
                :alt="getMemberFullName(selectedMember)"
                class="subject-photo"
              >
              <div v-else class="subject-initials">
                {{ selectedMember.first_name[0] }}{{ selectedMember.last_name[0] }}
              </div>
            </div>
            <div class="subject-meta">
              <div class="subject-name">{{ getMemberFullName(selectedMember) }}</div>
              <div class="subject-detail">Guthaben: {{ formatBalance(selectedMember.balance_cents) }}</div>
            </div>
          </template>
          <template v-else-if="activeTab === 'products' && selectedProduct">
            <div class="subject-avatar">
              <img
                v-if="selectedProduct.image_path"
                :src="`/api/products/${selectedProduct.id}/image`"
                :alt="selectedProduct.name"
                class="subject-photo"
              >
              <div v-else class="subject-initials product-icon">📦</div>
            </div>
            <div class="subject-meta">
              <div class="subject-name">{{ selectedProduct.name }}</div>
              <div class="subject-detail">{{ productMeta }}</div>
            </div>
          </template>
        </div>

        <template v-if="activeTab === 'members' && selectedMember">
          <div class="corr-form-group">
            <label>Aktueller Bestand</label>
            <input
              :value="formatBalance(selectedMember.balance_cents)"
              type="text"
              disabled
            >
          </div>
          <div class="corr-form-group">
            <label>Neuer Bestand (€)</label>
            <input
              :value="memberTargetBalanceEuro ?? ''"
              type="number"
              min="0"
              step="0.01"
              placeholder="0,00"
              @input="updateMemberTargetBalance"
            >
          </div>
          <div class="corr-form-group">
            <label>Grund der Korrektur</label>
            <input
              :value="memberCorrectionReason"
              type="text"
              maxlength="255"
              placeholder="z. B. Übertrag aus alter Kasse"
              @input="$emit('update:member-correction-reason', $event.target.value)"
            >
          </div>
          <div class="corr-preview-row">
            <span>Differenz: <strong>{{ formatBalance(memberDeltaCents) }}</strong></span>
            <span>von: <strong>{{ username || '—' }}</strong></span>
          </div>
        </template>

        <template v-else-if="activeTab === 'products' && selectedProduct">
          <div class="corr-form-group">
            <label>Aktueller Bestand</label>
            <input
              :value="selectedProduct.is_unlimited_stock ? '∞' : `${selectedProduct.stock_quantity ?? 0}`"
              type="text"
              disabled
            >
          </div>
          <div class="corr-form-group">
            <label>Neuer Bestand</label>
            <input
              :value="productTargetStock ?? ''"
              type="number"
              min="0"
              step="1"
              placeholder="0"
              @input="updateProductTargetStock"
            >
          </div>
          <div class="corr-form-group">
            <label>Grund der Korrektur</label>
            <input
              :value="productCorrectionReason"
              type="text"
              maxlength="255"
              placeholder="z. B. Inventurkorrektur"
              @input="$emit('update:product-correction-reason', $event.target.value)"
            >
          </div>
          <div class="corr-preview-row">
            <span>Differenz: <strong>{{ productDelta }}</strong></span>
            <span>von: <strong>{{ username || '—' }}</strong></span>
          </div>
        </template>
      </div>

      <footer class="modal-footer">
        <button
          class="btn btn-secondary"
          type="button"
          @click="$emit('close')"
        >
          Abbrechen / Zurück
        </button>
        <button
          v-if="activeTab === 'members'"
          class="btn btn-success"
          type="button"
          :disabled="!canSubmitMemberCorrection || isSubmitting"
          @click="$emit('submit-member')"
        >
          {{ isSubmitting ? '⏳ Speichert...' : '✓ Speichern' }}
        </button>
        <button
          v-else
          class="btn btn-success"
          type="button"
          :disabled="!canSubmitProductCorrection || isSubmitting"
          @click="$emit('submit-product')"
        >
          {{ isSubmitting ? '⏳ Speichert...' : '✓ Speichern' }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { getMemberFullName } from '@/services/member'
import { formatBalance } from '@/services/utils'

defineProps({
  show: { type: Boolean, required: true },
  activeTab: { type: String, required: true },
  selectedMember: { type: Object, default: null },
  selectedProduct: { type: Object, default: null },
  productMeta: { type: String, default: '—' },
  memberTargetBalanceEuro: { type: [Number, String], default: null },
  productTargetStock: { type: [Number, String], default: null },
  memberCorrectionReason: { type: String, default: '' },
  productCorrectionReason: { type: String, default: '' },
  memberDeltaCents: { type: Number, default: 0 },
  productDelta: { type: String, default: '—' },
  username: { type: String, default: '' },
  isSubmitting: { type: Boolean, default: false },
  canSubmitMemberCorrection: { type: Boolean, default: false },
  canSubmitProductCorrection: { type: Boolean, default: false },
})

const emit = defineEmits([
  'close',
  'submit-member',
  'submit-product',
  'update:member-target-balance-euro',
  'update:product-target-stock',
  'update:member-correction-reason',
  'update:product-correction-reason',
])

const updateMemberTargetBalance = (event) => {
  const { value } = event.target
  emit('update:member-target-balance-euro', value === '' ? null : Number(value))
}

const updateProductTargetStock = (event) => {
  const { value } = event.target
  emit('update:product-target-stock', value === '' ? null : Number(value))
}
</script>

<style scoped lang="scss">
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-card {
  --border: #e2e8f0;

  background: color-mix(in srgb, var(--app-background-color) 55%, white);
  width: 100%;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.18);
  overflow: hidden;
}

.modal-compact {
  max-width: 480px;
}

.modal-header {
  padding: 1.1rem 1.4rem;
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
}

.modal-subtitle {
  margin: 0.15rem 0 0;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.9);
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

.correction-subject-row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.subject-avatar {
  width: 52px;
  height: 52px;
  border-radius: 10px;
  overflow: hidden;
  flex-shrink: 0;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.subject-photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.subject-initials {
  font-weight: 700;
  color: #475569;
  font-size: 1rem;
}

.product-icon {
  font-size: 1.5rem;
}

.subject-meta {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.subject-name {
  font-weight: 700;
  color: #1e293b;
}

.subject-detail {
  font-size: 0.85rem;
  color: #64748b;
}

.modal-correction-body {
  padding: 1.25rem 1.4rem;
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.corr-form-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;

  label {
    font-size: 0.85rem;
    font-weight: 600;
    color: #334155;
  }

  input {
    width: 100%;
    padding: 0.55rem 0.75rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.9rem;

    &:focus {
      outline: none;
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
    }

    &:disabled {
      background: #f1f5f9;
      color: #475569;
    }
  }
}

.corr-preview-row {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #475569;
  padding: 0.2rem 0.1rem 0;
}

.modal-footer {
  padding: 1rem 1.4rem 1.2rem;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  border-top: 1px solid var(--border);
  background: color-mix(in srgb, var(--app-background-color) 45%, white);
}

.btn {
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 0.55rem 0.9rem;
  cursor: pointer;
  font-weight: 700;
  font-size: 0.88rem;
  transition: all 0.15s ease;

  &:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }
}

.btn-success {
  background: #10b981;
  color: white;

  &:hover:not(:disabled) {
    background: #059669;
  }
}

.btn-secondary {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #334155;

  &:hover:not(:disabled) {
    background: #f1f5f9;
  }
}
</style>
