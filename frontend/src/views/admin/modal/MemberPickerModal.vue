<template>
  <div
    v-if="show"
    class="confirmation-overlay member-picker-overlay"
  >
    <div class="kk-dialog kk-dialog--narrow">
      <div class="kk-dialog__header">
        <div>
          <h3>{{ title }}</h3>
          <p class="kk-dialog__subtitle">
            {{ searchPlaceholder }}
          </p>
        </div>
        <button
          class="kk-dialog__close"
          @click="$emit('close')"
        >
          ✕
        </button>
      </div>

      <div
        class="kk-dialog__body"
        style="gap: 0.75rem;"
      >
        <input
          :value="search"
          type="text"
          :placeholder="searchPlaceholder"
          class="kk-picker-search"
          @input="$emit('update:search', $event.target.value)"
        >

        <div class="kk-picker-list">
          <button
            v-for="entry in options"
            :key="entry.id"
            class="kk-picker-item"
            @click="$emit('select', entry)"
          >
            <div
              v-if="entry.photo_path"
              class="kk-picker-photo"
            >
              <img
                :src="`/api/members/${entry.id}/photo`"
                :alt="formatLabel(entry)"
              >
            </div>
            <div
              v-else
              class="kk-picker-photo placeholder"
            >
              👤
            </div>
            <span>{{ formatLabel(entry) }}</span>
          </button>

          <div
            v-if="!options.length"
            class="kk-picker-empty"
          >
            Keine Einträge gefunden
          </div>
        </div>
      </div>

      <div class="kk-dialog__footer">
        <button
          class="btn btn-secondary"
          @click="$emit('close')"
        >
          Abbrechen
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: { type: Boolean, required: true },
  title: { type: String, default: 'Auswählen' },
  searchPlaceholder: { type: String, default: 'Suchen...' },
  search: { type: String, default: '' },
  options: { type: Array, default: () => [] },
  formatLabel: { type: Function, default: (entry) => entry?.username || entry?.name || String(entry?.id ?? '') },
})

defineEmits(['close', 'select', 'update:search'])
</script>

<style scoped lang="scss">
.confirmation-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1500;
  padding: 1.5rem;
  overflow-y: auto;
}

.member-picker-overlay {
  z-index: 1600;
}

.kk-dialog {
  background: #ffffff;
  border-radius: 20px;
  width: min(80vw, 1100px);
  max-height: min(82vh, 900px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow:
    0 32px 64px rgba(15, 23, 42, 0.28),
    0 0 0 1px rgba(15, 23, 42, 0.06);
}

.kk-dialog--narrow {
  width: min(80vw, 560px);
}

.kk-dialog__header {
  padding: 1rem 1.4rem;
  background: #0f766e;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  flex-shrink: 0;

  h3 {
    margin: 0;
    color: #ffffff;
    font-size: 1.05rem;
    font-weight: 600;
    line-height: 1.3;
  }
}

.kk-dialog__subtitle {
  margin: 0.3rem 0 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.82rem;
}

.kk-dialog__close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
  font-size: 1rem;
  cursor: pointer;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  transition: background 0.15s;

  &:hover {
    background: rgba(255, 255, 255, 0.28);
  }
}

.kk-dialog__body {
  padding: 1.4rem;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.kk-dialog__footer {
  padding: 1rem 1.4rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.65rem;
  flex-shrink: 0;
  background: #f8fafc;
  flex-wrap: wrap;
}

.kk-picker-search {
  width: 100%;
  padding: 0.65rem 0.9rem;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 0.9rem;
  background: #f8fafc;
  transition: border-color 0.15s;

  &:focus {
    outline: none;
    border-color: #0f766e;
    background: #fff;
  }
}

.kk-picker-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  min-height: 200px;
  max-height: 400px;
}

.kk-picker-item {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  width: 100%;
  padding: 0.65rem 0.9rem;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
  cursor: pointer;
  text-align: left;
  font-size: 0.88rem;
  font-weight: 600;
  color: #1e293b;
  transition: all 0.15s;

  &:hover {
    background: #f1f5f9;
    border-color: #94a3b8;
  }
}

.kk-picker-photo {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  overflow: hidden;
  background: #e2e8f0;
  display: grid;
  place-items: center;
  flex-shrink: 0;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  &.placeholder {
    color: #94a3b8;
    font-size: 1rem;
  }
}

.kk-picker-empty {
  text-align: center;
  padding: 2rem;
  color: #94a3b8;
  font-style: italic;
  font-size: 0.9rem;
}

.btn {
  padding: 0.65rem 1.25rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;

  &:hover {
    background: #e2e8f0;
  }
}

@media (max-width: 640px) {
  .confirmation-overlay {
    padding: 0.75rem;
    align-items: flex-start;
  }

  .kk-dialog {
    width: 100%;
    max-height: calc(100dvh - 1.5rem);
    border-radius: 14px;
  }

  .kk-dialog__footer {
    flex-direction: column;

    .btn {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>
