<template>
  <SystemCredentialModal
    :show="show"
    :title="title"
    subtitle="Zugangsdaten eingeben"
    :message="message"
    :username="username"
    :usernames="usernames"
    :allow-username-edit="allowUsernameEdit"
    :confirm-label="confirmLabel"
    :confirmation-label="confirmationLabel"
    :confirmation-placeholder="confirmationPlaceholder"
    :error="error"
    @close="$emit('close')"
    @confirm="$emit('confirm', $event)"
    @update:usernames="$emit('update:usernames', $event)"
  />
</template>

<script setup>
import SystemCredentialModal from '@/components/SystemCredentialModal.vue'

defineProps({
  show: Boolean,
  title: { type: String, default: 'Zugangsdaten bestätigen' },
  message: { type: String, default: '' },
  username: { type: String, default: '' },
  usernames: { type: Array, default: () => [] },
  allowUsernameEdit: { type: Boolean, default: false },
  confirmLabel: { type: String, default: 'Bestätigen' },
  confirmationLabel: { type: String, default: '' },
  confirmationPlaceholder: { type: String, default: '' },
  error: { type: String, default: '' },
})

defineEmits(['close', 'confirm', 'update:usernames'])
</script>
