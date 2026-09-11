<template>
  <div v-if="show" class="modal-overlay">
    <div class="modal-card">
      <header class="modal-header">
        <div>
          <h3>📋 Gästeliste</h3>
          <p class="modal-subtitle">Bitte trage den Namen des Gastes ein.</p>
        </div>
        <button type="button" class="close-btn" @click="$emit('cancel')">✕</button>
      </header>

      <div class="modal-body">
        <div v-if="entries.length === 0" class="empty-state">
          <p>Keine Einträge vorhanden.</p>
        </div>

        <div v-else>
          <div
            v-for="(entry, index) in entries"
            :key="index"
            class="guest-entry"
          >
            <div class="guest-entry-header">
              <span class="product-label">{{ entry.productName }}</span>
              <span v-if="entries.length > 1" class="entry-count">{{ index + 1 }} / {{ entries.length }}</span>
            </div>

            <!-- 1. Besucher: Name des Gastes (mit optionaler Autovervollständigung aus bekannten Gästen) -->
            <div class="input-group">
              <label :for="`known-guest-${index}`">Bekannter Gast</label>
              <select
                :id="`known-guest-${index}`"
                v-model="entry.selectedKnownGuest"
                class="guest-select"
                :disabled="knownGuests.length === 0"
                @change="applyKnownGuest(entry)"
              >
                <option value="">
                  {{ knownGuests.length ? 'Aus Gästeliste auswählen' : 'Keine bekannten Gäste vorhanden' }}
                </option>
                <option
                  v-for="guest in knownGuests"
                  :key="guest.guest_name"
                  :value="guest.guest_name"
                >
                  {{ guest.short_display_name }}
                </option>
              </select>
            </div>

            <div class="name-grid">
              <div class="input-group">
                <label :for="`guest-first-name-${index}`">Vorname *</label>
                <input
                  :id="`guest-first-name-${index}`"
                  v-model.trim="entry.guestFirstName"
                  type="text"
                  class="guest-name-input"
                  placeholder="Vorname"
                  autocomplete="off"
                >
              </div>

              <div class="input-group">
                <label :for="`guest-last-name-${index}`">Nachname</label>
                <input
                  :id="`guest-last-name-${index}`"
                  v-model.trim="entry.guestLastName"
                  type="text"
                  class="guest-name-input"
                  placeholder="Nachname"
                  autocomplete="off"
                >
              </div>
            </div>

            <!-- 2. Gast von: optionale Zuordnung zu einem Mitglied, unterhalb des Besuchernamens -->
            <div class="input-group">
              <label :for="`guest-member-${index}`">Gast von (optional)</label>
              <select
                :id="`guest-member-${index}`"
                v-model="entry.memberId"
                class="guest-select"
                :disabled="memberOptions.length === 0"
              >
                <option :value="null">
                  {{ memberOptions.length ? 'Kein Mitglied auswählen' : 'Keine Mitglieder vorhanden' }}
                </option>
                <option
                  v-for="member in memberOptions"
                  :key="member.id"
                  :value="member.id"
                >
                  {{ getMemberLabel(member) }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <!-- Ladehinweis für Vorschläge -->
        <div v-if="isLoadingKnownGuests" class="loading-guests">
          <small>⏳ Bekannte Gäste werden geladen...</small>
        </div>
      </div>

      <footer class="modal-footer">
        <button type="button" class="btn btn-secondary" @click="$emit('cancel')">Abbrechen</button>
        <button
          type="button"
          class="btn btn-success"
          :disabled="!allEntriesFilled"
          @click="handleConfirm"
        >
          ✓ Bestätigen
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import apiService from '@/services/api'
import { useMemberStore } from '@/stores/member'
import { getMemberFullName, getMemberShortName } from '@/services/member'

const props = defineProps({
  show: { type: Boolean, required: true },
  products: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(['confirm', 'cancel'])

const memberStore = useMemberStore()
const entries = ref([])
const knownGuests = ref([])
const isLoadingKnownGuests = ref(false)
const memberOptions = computed(() => (
  [...memberStore.members].sort((a, b) => getMemberFullName(a).localeCompare(getMemberFullName(b), 'de'))
))

const getMemberLabel = (member) => getMemberShortName(member) || getMemberFullName(member) || `Mitglied ${member.id}`

const productSignature = computed(() => (
  (props.products || [])
    .map(p => `${p.productId}:${p.quantity ?? 1}`)
    .join('|')
))

const buildEntries = () => {
  if (!props.products || props.products.length === 0) {
    entries.value = []
    return
  }
  const rows = []
  for (const p of props.products) {
    const count = p.quantity ?? 1
    for (let i = 0; i < count; i++) {
      rows.push({
        productId: p.productId,
        productName: p.productName,
        memberId: null,
        guestFirstName: '',
        guestLastName: '',
        selectedKnownGuest: '',
      })
    }
  }
  entries.value = rows
}

const getShortDisplayName = (guestFirstName, guestLastName) => {
  const normalizedLastName = (guestLastName || '').trim()
  return normalizedLastName.length > 0
    ? `${guestFirstName} ${normalizedLastName.charAt(0)}.`
    : guestFirstName
}

const normalizeKnownGuest = (guest) => {
  if (!guest) return null

  if (typeof guest === 'string') {
    const name = guest.trim()
    if (!name) return null
    const [guestFirstName, ...rest] = name.split(/\s+/)
    const guestLastName = rest.join(' ').trim()
    return {
      guest_name: name,
      guest_first_name: guestFirstName,
      guest_last_name: guestLastName || null,
      short_display_name: getShortDisplayName(guestFirstName, guestLastName),
    }
  }

  const guestFirstName = (guest.guest_first_name || '').trim()
  const guestLastName = (guest.guest_last_name || '').trim()
  const guestName = (guest.guest_name || `${guestFirstName} ${guestLastName}`).trim()
  if (!guestFirstName || !guestName) return null

  return {
    guest_name: guestName,
    guest_first_name: guestFirstName,
    guest_last_name: guestLastName || null,
    short_display_name: guest.short_display_name || getShortDisplayName(guestFirstName, guestLastName),
  }
}

const ensureMemberOptions = async () => {
  if (memberStore.members.length > 0 || memberStore.isLoading) {
    return
  }
  try {
    await memberStore.getMemberSelection()
  } catch (error) {
    console.error('Failed to load members for guest list modal:', error)
  }
}

const loadKnownGuests = async () => {
  if (!props.products || props.products.length === 0) {
    knownGuests.value = []
    return
  }

  isLoadingKnownGuests.value = true
  try {
    const productIds = [...new Set(props.products.map(p => p.productId))]
    const results = await Promise.all(
      productIds.map(id => apiService.get('/guest-list/guests', { params: { product_id: id } }))
    )
    const merged = []
    const seen = new Set()
    for (const response of results) {
      for (const rawGuest of (response.data || [])) {
        const normalizedGuest = normalizeKnownGuest(rawGuest)
        if (!normalizedGuest) continue
        const key = normalizedGuest.guest_name.toLowerCase()
        if (seen.has(key)) continue
        seen.add(key)
        merged.push(normalizedGuest)
      }
    }
    merged.sort((a, b) => a.short_display_name.localeCompare(b.short_display_name, 'de'))
    knownGuests.value = merged
  } catch (error) {
    console.error('Failed to load known guests:', error)
    knownGuests.value = []
  } finally {
    isLoadingKnownGuests.value = false
  }
}

const applyKnownGuest = (entry) => {
  const guest = knownGuests.value.find(item => item.guest_name === entry.selectedKnownGuest)
  if (!guest) return
  entry.guestFirstName = guest.guest_first_name
  entry.guestLastName = guest.guest_last_name || ''
}

watch(
  () => ({ show: props.show, signature: productSignature.value }),
  (current, previous) => {
    if (!current.show) {
      entries.value = []
      knownGuests.value = []
      isLoadingKnownGuests.value = false
      return
    }

    if (!previous?.show || previous.signature !== current.signature) {
      buildEntries()
      ensureMemberOptions()
      loadKnownGuests()
    }
  },
  { immediate: true }
)

const allEntriesFilled = computed(() => (
  entries.value.length > 0
  && entries.value.every(e => Number.isInteger(e.productId) && e.productId > 0 && e.guestFirstName?.trim().length > 0)
))

const toGuestName = (entry) => `${entry.guestFirstName} ${entry.guestLastName || ''}`.trim()

const handleConfirm = () => {
  if (!allEntriesFilled.value) return
  emit('confirm', entries.value.map(e => ({
    productId: e.productId,
    memberId: e.memberId || null,
    guestFirstName: e.guestFirstName.trim(),
    guestLastName: (e.guestLastName || '').trim(),
    guestName: toGuestName(e),
  })))
}
</script>

<style scoped lang="scss">
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
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
  max-width: 480px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  max-height: 90vh;
}

.modal-header {
  padding: 1rem 1.2rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  background: linear-gradient(90deg, #0f766e 0%, #0ea5e9 100%);
  flex-shrink: 0;

  h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #ffffff;
  }

  .modal-subtitle {
    margin: 0.25rem 0 0;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.9);
  }
}

.close-btn {
  background: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 6px;
  color: white;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.9rem;
  flex-shrink: 0;

  &:hover {
    background: rgba(255, 255, 255, 0.25);
  }
}

.modal-body {
  padding: 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.empty-state {
  text-align: center;
  padding: 2rem 1rem;
  color: #999;
  font-size: 0.95rem;
}

.guest-entry {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.9rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.guest-entry-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-label {
  font-weight: 600;
  font-size: 0.9rem;
  color: #334155;
}

.entry-count {
  font-size: 0.78rem;
  color: #94a3b8;
  font-weight: 500;
}

.name-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.6rem;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;

  label {
    font-size: 0.82rem;
    font-weight: 600;
    color: #64748b;
  }
}

.guest-name-input,
.guest-select {
  width: 100%;
  padding: 0.55rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.95rem;
  outline: none;
  transition: border-color 0.15s;
  box-sizing: border-box;

  &:focus {
    border-color: #0ea5e9;
    box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.15);
  }
}

.guest-name-input {
  &::placeholder {
    color: #94a3b8;
  }
}

.loading-guests {
  text-align: center;
  color: #64748b;
  font-size: 0.85rem;
  padding: 0.5rem;
}

.modal-footer {
  padding: 0.9rem 1.2rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  flex-shrink: 0;
}

.btn {
  padding: 0.55rem 1.1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: opacity 0.15s;

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

.btn-success {
  background: #16a34a;
  color: white;

  &:hover:not(:disabled) {
    background: #15803d;
  }
}

@media (max-width: 540px) {
  .name-grid {
    grid-template-columns: 1fr;
  }
}
</style>
