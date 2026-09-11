<template>
  <aside
    v-if="entries.length"
    class="pending-bookings"
    aria-live="polite"
  >
    <strong>Buchung noch nicht bestätigt</strong>
    <p>Bei einem Verbindungsabbruch die Buchung unverändert erneut bestätigen. Ihr Status wird vor einer Wiederholung geprüft.</p>
    <div
      v-for="entry in entries"
      :key="entry.key"
    >
      <button
        type="button"
        :disabled="busy"
        @click="check(entry)"
      >
        Status prüfen
      </button>
      <span>{{ entry.key.slice(0, 8) }}</span>
    </div>
    <p v-if="message">
      {{ message }}
    </p>
    <button
      v-if="confirmed"
      type="button"
      @click="accept"
    >
      Bestätigung übernehmen
    </button>
  </aside>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { pendingBookings } from '@/services/api'
import { useCartStore } from '@/stores/cart'
const entries = ref([])
const message = ref('')
const confirmed = ref(null)
const busy = ref(false)
const cart = useCartStore()
const refresh = () => { entries.value = pendingBookings.list() }
const check = async entry => {
  busy.value = true
  confirmed.value = null
  try {
    const result = await pendingBookings.resolve(entry)
    message.value = `Buchung bestätigt${result.receipt_number ? `: Beleg #${result.receipt_number}` : ''}. Die Bestätigung kann jetzt übernommen werden.`
    confirmed.value = entry
  } catch (error) {
    message.value = error.response?.status === 404
      ? 'Noch keine Bestätigung vorhanden. Die ursprüngliche Buchung unverändert erneut versuchen.'
      : error.response?.data?.detail || 'Status derzeit nicht erreichbar. Bitte später erneut prüfen.'
  } finally { busy.value = false }
}
const accept = () => {
  if (confirmed.value.path === '/transactions/sale') cart.clear()
  pendingBookings.acknowledge(confirmed.value)
  confirmed.value = null
  message.value = ''
  // Reload stock, balances, deckel and archive from the committed database state.
  window.location.reload()
}
onMounted(() => { refresh(); window.addEventListener('pending-bookings-changed', refresh) })
onUnmounted(() => window.removeEventListener('pending-bookings-changed', refresh))
</script>

<style scoped>
.pending-bookings { margin: 1rem; padding: 1rem; border: 2px solid #996600; border-radius: 8px; background: #fff4d6; color: #332200; }
.pending-bookings button { margin: .4rem .75rem .4rem 0; min-height: 44px; padding: .5rem 1rem; }
</style>
