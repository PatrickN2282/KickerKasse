<template>
  <div v-if="show" class="modal-overlay" @click.self="emit('close')">
    <div class="modal-dialog">
      <div class="modal-header">
        <div>
          <h3>💛 Projekt unterstützen</h3>
          <p class="subtitle">Vielen Dank für deine Wertschätzung</p>
        </div>
        <button class="close-btn" @click="emit('close')">✕</button>
      </div>
      <div class="modal-body">
        <img
          :src="donationQrUrl"
          alt="Spenden-QR-Code"
          class="donation-qr"
        >
        <p class="donation-hint">
          Wenn dir KickerKasse hilft, freuen wir uns über eine kleine Spende für die Zeit und Mühe,
          die in dieses Projekt geflossen ist.
          Der QR-Code verweist direkt auf PayPal – einfach scannen und einen kleinen Betrag hinterlassen. Danke! 🙏
        </p>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" @click="emit('close')">Schließen</button>
        <a
          href="https://www.paypal.com/donate/?hosted_button_id=64BS2U8G43M5U"
          target="_blank"
          rel="noopener noreferrer"
          class="btn btn-primary"
        >
          Jetzt spenden
        </a>
      </div>
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

const emit = defineEmits(['close'])
const donationBannerUrl = '/api/app-settings/donation-banner'
const donationQrUrl = '/api/app-settings/donation-qr'
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
  z-index: 1200;
  padding: 1rem;
}

.modal-dialog {
  background: #ffffff;
  border-radius: 16px;
  width: 100%;
  max-width: 420px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  overflow: hidden;
}

.modal-header {
  padding: 0.9rem 1.1rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: linear-gradient(90deg, #0f766e 0%, #0ea5e9 100%);
  flex-shrink: 0;

  h3 {
    margin: 0;
    color: #ffffff;
    font-size: 1rem;
  }

  .subtitle {
    margin: 0.25rem 0 0;
    color: rgba(255, 255, 255, 0.9);
    font-size: 0.8rem;
  }
}

.close-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.45);
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
  font-size: 1rem;
  cursor: pointer;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.modal-body {
  padding: 0.9rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.donation-banner {
  width: 100%;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  object-fit: cover;
  max-height: 140px;
}

.donation-qr {
  width: min(220px, 100%);
  align-self: center;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.donation-hint {
  margin: 0;
  font-size: 0.9rem;
  color: #334155;
  line-height: 1.35;
}

.modal-footer {
  padding: 0.85rem 1.1rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  gap: 0.6rem;
  justify-content: flex-end;
  background: #ffffff;
  flex-shrink: 0;
}

.btn {
  border-radius: 8px;
  padding: 0.6rem 0.9rem;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.85rem;
  border: none;
  text-decoration: none;
}

.btn-primary {
  background: linear-gradient(90deg, #0f766e 0%, #0ea5e9 100%);
  color: #fff;
}

.btn-secondary {
  background: #f8fafc;
  color: #475569;
  border: 1px solid #cbd5e1;
}
</style>
