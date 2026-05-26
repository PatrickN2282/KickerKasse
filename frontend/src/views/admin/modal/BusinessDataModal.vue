<template>
  <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card">
      <header class="modal-header">
        <div>
          <h3>Geschäftsdaten</h3>
          <p class="modal-subtitle">Diese Daten werden für Belege und Berichte verwendet.</p>
        </div>
        <button class="modal-close" @click="$emit('close')">×</button>
      </header>

      <form class="modal-form-content" @submit.prevent="$emit('save')">
        <div class="form-row">
          <div class="form-group">
            <label for="bd-name">Vereinsname</label>
            <input id="bd-name" v-model="businessData.name" type="text" placeholder="z. B. Tischfußball e.V.">
          </div>
          <div class="form-group">
            <label for="bd-tax">Steuernummer</label>
            <input id="bd-tax" v-model="businessData.taxNumber" type="text" placeholder="z. B. 12/345/67890">
          </div>
        </div>
        <div class="form-group">
          <label for="bd-street">Straße &amp; Hausnummer</label>
          <input id="bd-street" v-model="businessData.street" type="text" placeholder="z. B. Musterstraße 1">
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="bd-zip">PLZ</label>
            <input id="bd-zip" v-model="businessData.zip" type="text" placeholder="z. B. 12345">
          </div>
          <div class="form-group">
            <label for="bd-city">Ort</label>
            <input id="bd-city" v-model="businessData.city" type="text" placeholder="z. B. Musterstadt">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="bd-phone">Telefon</label>
            <input id="bd-phone" v-model="businessData.phone" type="tel" placeholder="z. B. +49 123 456789">
          </div>
          <div class="form-group">
            <label for="bd-email">E-Mail</label>
            <input id="bd-email" v-model="businessData.email" type="email" placeholder="z. B. info@verein.de">
          </div>
        </div>
        <div class="form-group">
          <label for="bd-reg">Vereinsregister (optional)</label>
          <input id="bd-reg" v-model="businessData.registrationNumber" type="text" placeholder="z. B. VR 12345 Amtsgericht Musterstadt">
        </div>

        <footer class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="$emit('close')">Abbrechen</button>
          <button type="submit" class="btn btn-success">Speichern</button>
        </footer>
      </form>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: {
    type: Boolean,
    default: false,
  },
})

const businessData = defineModel('businessData', {
  type: Object,
  required: true,
})

defineEmits(['close', 'save'])
</script>

<style scoped lang="scss">
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-card {
  background: white;
  width: 100%;
  max-width: 640px;
  max-height: 90vh;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  gap: 1rem;

  h3 {
    margin: 0;
    font-size: 1.25rem;
  }
}

.modal-subtitle {
  color: #64748b;
  margin-top: 0.25rem;
  font-size: 0.875rem;
}

.modal-form-content {
  padding: 1.5rem;
  overflow-y: auto;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  margin-bottom: 1rem;

  label {
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    margin-bottom: 0.4rem;
    color: #1e293b;
  }

  input {
    width: 100%;
    padding: 0.6rem 0.8rem;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 0.95rem;

    &:focus {
      outline: none;
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
  }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding-top: 0.5rem;
}

.modal-close {
  border: none;
  background: transparent;
  font-size: 1.6rem;
  line-height: 1;
  cursor: pointer;
  color: #6b7280;
}
</style>
