<template>
  <div
    v-if="show"
    class="confirmation-overlay member-picker-overlay"
  >
    <div class="confirmation-dialog member-picker-dialog">
      <h3>{{ pickerTitle }}</h3>
      <input
        v-model="localSearch"
        type="text"
        :placeholder="pickerSearchPlaceholder"
        class="form-input member-search-input"
      >
      <div class="member-picker-list">
        <button
          v-for="entry in filteredPickerOptions"
          :key="entry.id"
          class="member-picker-item"
          @click="$emit('select', entry)"
        >
          <div
            v-if="entry.photo_path"
            class="member-picker-photo"
          >
            <img
              :src="`/api/members/${entry.id}/photo`"
              :alt="formatPickerLabel(entry)"
            >
          </div>
          <div
            v-else
            class="member-picker-photo placeholder"
          >
            👤
          </div>
          <span>{{ formatPickerLabel(entry) }}</span>
        </button>
        <div
          v-if="!filteredPickerOptions.length"
          class="empty member-picker-empty"
        >
          Keine Einträge gefunden
        </div>
      </div>
      <div class="confirmation-buttons">
        <button
          class="btn btn-secondary"
          @click="$emit('close')"
        >
          Abbrechen / Zurück
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  show: { type: Boolean, required: true },
  pickerTitle: { type: String, default: '' },
  pickerSearchPlaceholder: { type: String, default: 'Suchen...' },
  filteredPickerOptions: { type: Array, default: () => [] },
  memberSearch: { type: String, default: '' },
  formatPickerLabel: { type: Function, required: true },
})

const emit = defineEmits(['close', 'select', 'update:memberSearch'])

const localSearch = ref(props.memberSearch)

watch(localSearch, (val) => {
  emit('update:memberSearch', val)
})

watch(() => props.memberSearch, (val) => {
  if (val !== localSearch.value) localSearch.value = val
})
</script>

<style scoped lang="scss">
.confirmation-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1500;
}

.member-picker-overlay {
  z-index: 1600;
}

.confirmation-dialog {
  background: #dde2e8;
  border-radius: 8px;
  padding: 2rem;
  max-width: 400px;
  width: min(100%, 520px);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  text-align: center;

  h3 {
    margin: 0 0 0.75rem 0;
    color: #333;
  }

  p {
    margin: 0 0 1.5rem 0;
    color: #666;
  }
}

.member-picker-dialog {
  max-width: 520px;
}

.form-input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.member-search-input {
  width: 100%;
  margin-bottom: 1rem;
}

.member-picker-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 360px;
  overflow-y: auto;
  margin-bottom: 1rem;
}

.member-picker-item {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  width: 100%;
  padding: 0.75rem 0.9rem;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  background: #f8fafc;
  cursor: pointer;
  text-align: left;
  font-weight: 600;
  color: #1e293b;
  transition: all 0.2s;

  &:hover {
    background: #eef2f7;
    border-color: #94a3b8;
  }
}

.member-picker-photo {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  overflow: hidden;
  background: #cbd5e1;
  display: grid;
  place-items: center;
  flex-shrink: 0;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  &.placeholder {
    color: #475569;
    font-size: 1.1rem;
  }
}

.member-picker-empty {
  margin: 0;
  padding: 1rem 0;
}

.confirmation-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-secondary {
  background: #f5f5f5;
  color: #666;
  border: 1px solid #ddd;

  &:hover {
    background: #e0e0e0;
  }
}
</style>
