<template>
  <div class="modal-overlay">
    <div class="modal-dialog">
      <div class="modal-header">
        <div>
          <h3>Mitglied auswählen</h3>
          <p class="subtitle">
            Mitglied für die Buchung auswählen
          </p>
        </div>
        <button
          class="close-btn"
          @click="showMemberModal = false"
        >
          ✕
        </button>
      </div>
      <div class="modal-body">
        <input
          v-model="memberSearch"
          type="text"
          placeholder="Nach Name oder Nummer suchen..."
          class="member-search-input"
        >
        <div class="member-results">
          <div
            v-if="filteredMembers.length > 0"
            class="member-grid"
          >
            <button
              v-for="member in filteredMembers"
              :key="member.id"
              class="member-card"
              @click="selectMember(member)"
            >
              <div class="member-card-img">
                <img
                  v-if="member.photo_path"
                  :src="`/api/members/${member.id}/photo`"
                  :alt="getMemberFullName(member)"
                >
                <div
                  v-else
                  class="member-card-img-placeholder"
                >
                  👤
                </div>
              </div>
              <div class="member-card-body">
                <div class="member-card-name">
                  {{ getMemberShortName(member) }}
                </div>
                <div class="member-card-balance-label">
                  Guthaben
                </div>
                <div class="member-card-balance">
                  {{ formatBalance(member.balance_cents) }}
                </div>
              </div>
            </button>
          </div>
          <div
            v-else
            class="empty-state"
          >
            Keine Mitglieder gefunden
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button
          class="btn btn-secondary"
          @click="showMemberModal = false"
        >
          Abbrechen
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue'
const { memberSearch, filteredMembers, selectMember, showMemberModal, getMemberFullName, getMemberShortName, formatBalance } = inject('kasse')
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
  z-index: 1000;
  padding: 1.25rem;
  overflow-y: auto;
}
.modal-dialog {
  background: #ffffff;
  border-radius: 16px;
  width: 650px;
  height: 650px;
  max-width: 650px;
  max-height: 650px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  overflow: hidden;
}
.modal-header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: linear-gradient(90deg, #0f766e 0%, #0ea5e9 100%);
  flex-shrink: 0;
  h3 { margin: 0; color: #ffffff; font-size: 1.1rem; }
  .subtitle { margin: 0.35rem 0 0; color: rgba(255,255,255,0.9); font-size: 0.85rem; }
}
.close-btn {
  width: 34px; height: 34px; border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.45);
  background: rgba(255,255,255,0.18);
  color: #ffffff; font-size: 1.1rem; cursor: pointer;
  display: grid; place-items: center; flex-shrink: 0;
  &:hover { background: rgba(255,255,255,0.3); }
}
.modal-body {
  padding: 1rem 1.25rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-height: 0;
  overflow: hidden;
}
.modal-footer {
  padding: 0.95rem 1.25rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  background: #ffffff;
  flex-shrink: 0;
}
.btn {
  border-radius: 8px;
  padding: 0.65rem 1rem;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.9rem;
  border: none;
}
.btn-secondary {
  background: #f8fafc;
  color: #475569;
  border: 1px solid #cbd5e1;
}
.member-search-input {
  width: 100%;
  padding: 0.6rem 0.8rem;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 0.9rem;
  box-sizing: border-box;
  flex-shrink: 0;
}
.member-results {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 0.15rem;
}
.member-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.75rem;
  align-content: start;
}
@media (max-width: 1200px) {
  .member-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }
}
@media (max-width: 900px) {
  .member-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  }
}
@media (max-width: 640px) {
  .modal-overlay {
    padding: 0.75rem;
    align-items: stretch;
  }
  .modal-dialog {
    width: 100%;
    height: auto;
    max-height: calc(100vh - 1.5rem);
  }
  .member-grid {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  }
}
.member-card {
  background: #fff;
  border: 1.5px solid color-mix(in srgb, var(--app-banner-color) 22%, white 78%);
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
  text-align: left;
  transition: all 0.18s;
  &:hover {
    border-color: var(--app-highlight-color);
    box-shadow: 0 4px 16px color-mix(in srgb, var(--app-highlight-color) 18%, transparent);
    transform: translateY(-2px);
  }
}
.member-card-img {
  width: 100%;
  aspect-ratio: 1 / 1;
  background: #eef1f7;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}
.member-card-img-placeholder { font-size: 2rem; }
.member-card-body {
  padding: 0.55rem 0.65rem 0.7rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.member-card-name {
  font-size: 0.9rem;
  font-weight: 700;
  line-height: 1.25;
  color: #111827;
  word-break: break-word;
}
.member-card-balance-label {
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #64748b;
}
.member-card-balance {
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--app-highlight-color);
}
.empty-state {
  text-align: center;
  color: #94a3b8;
  padding: 2rem;
  font-size: 0.95rem;
}
</style>
