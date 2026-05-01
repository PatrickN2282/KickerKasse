<template>
  <div v-if="show" class="modal">
    <div class="modal-content member-modal">
      <h3>Mitglied auswählen</h3>
      <input
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        type="text"
        placeholder="Nach Name oder Nummer suchen..."
        class="form-input"
      />
      <div v-if="members.length > 0" class="member-grid">
        <button
          v-for="member in members"
          :key="member.id"
          @click="$emit('select', member)"
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
        <button @click="$emit('close')" class="btn btn-danger">
          Abbrechen / Zurück
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { getMemberFullName, getMemberShortName } from '@/services/member'
import { formatBalance } from '@/services/utils'

defineProps({
  show: Boolean,
  members: { type: Array, default: () => [] },
  modelValue: { type: String, default: '' },
})

defineEmits(['update:modelValue', 'select', 'close'])
</script>

<style scoped lang="scss">
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

.empty-bon {
  text-align: center;
  color: #999;
  padding: 2rem 1rem;
  font-size: 0.95rem;
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

.btn-danger {
  background-color: #f44336;
  color: white;

  &:not(:disabled):hover {
    background-color: #da190b;
  }
}
</style>
