<template>
  <div v-if="show" class="modal-overlay">
    <div class="modal-card">
      <header class="modal-header">
        <div>
          <h3>📋 Gäste heute</h3>
          <p class="modal-subtitle">
            {{ totalCount }} Einträge
          </p>
        </div>
        <button type="button" class="close-btn" @click="$emit('close')">✕</button>
      </header>

      <div class="modal-body">
        <div v-if="groups.length === 0" class="empty-state">
          <p>Heute sind keine Gäste eingetragen.</p>
        </div>

        <section v-for="group in groups" :key="group.product_id" class="product-group">
          <div class="group-header">
            <span class="product-label">{{ group.product_name }}</span>
            <span class="entry-count">{{ group.entries.length }}</span>
          </div>

          <div class="entries-list">
            <div v-for="entry in group.entries" :key="entry.id" class="entry-row">
              <div class="entry-main">
                <strong>{{ entry.guest_name }}</strong>
                <small v-if="entry.member_name">Gast von: {{ entry.member_name }}</small>
              </div>
              <div class="entry-meta">{{ formatDate(entry.created_at) }}</div>
            </div>
          </div>
        </section>
      </div>

      <footer class="modal-footer">
        <button type="button" class="btn btn-secondary" @click="$emit('close')">Schließen</button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

defineEmits(['close'])

const props = defineProps({
  show: { type: Boolean, required: true },
  groups: { type: Array, default: () => [] },
})

const totalCount = computed(() => (
  (props.groups || []).reduce((sum, group) => sum + (group.entries?.length || 0), 0)
))

const formatDate = (dateString) => {
  if (!dateString) return '—'
  const date = new Date(dateString)
  return date.toLocaleTimeString('de-DE', {
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped lang="scss">
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
  padding: 1rem;
}

.modal-card {
  background: white;
  width: 100%;
  max-width: 780px;
  max-height: 90vh;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.15);
}

.modal-header,
.modal-footer {
  padding: 1rem 1.2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.modal-header {
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(90deg, #0f766e 0%, #0ea5e9 100%);

  h3,
  .modal-subtitle {
    color: #fff;
    margin: 0;
  }

  .modal-subtitle {
    margin-top: 0.25rem;
    font-size: 0.85rem;
    opacity: 0.9;
  }
}

.close-btn {
  background: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 6px;
  color: white;
  width: 28px;
  height: 28px;
  cursor: pointer;
}

.modal-body {
  padding: 1.2rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.empty-state {
  text-align: center;
  color: #64748b;
  padding: 2rem 1rem;
}

.product-group {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.9rem 1rem;
  background: #f8fafc;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.product-label {
  font-weight: 600;
  color: #334155;
}

.entry-count {
  background: #e2e8f0;
  color: #334155;
  border-radius: 999px;
  padding: 0.15rem 0.55rem;
  font-size: 0.8rem;
}

.entries-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.entry-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.65rem 0.75rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.entry-main {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.entry-main small,
.entry-meta {
  color: #64748b;
  font-size: 0.82rem;
}

.modal-footer {
  border-top: 1px solid #e2e8f0;
  justify-content: flex-end;
}

// Bislang fehlten hier eigene Button-Stile, wodurch der "Schließen"-Button unstyled
// (Browser-Default) dargestellt wurde. Angleichung an das Button-Erscheinungsbild von
// GuestListModal.vue und den übrigen Kasse-Modals.
.btn {
  padding: 0.55rem 1.1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: opacity 0.15s, background 0.15s;

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;

  &:hover:not(:disabled) {
    background: #e2e8f0;
  }
}

@media (max-width: 640px) {
  .entry-row {
    flex-direction: column;
    gap: 0.25rem;
  }

  .modal-card {
    max-height: 100vh;
    border-radius: 0;
  }

  .btn {
    width: 100%;
  }
}
</style>
