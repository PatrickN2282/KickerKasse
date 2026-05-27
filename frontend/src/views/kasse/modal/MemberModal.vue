<template>
  <div class="modal-overlay">
    <div class="modal-dialog modal-dialog--fullsize">
      <div class="modal-header">
        <div class="modal-header-title">
          <h3>Mitglied auswählen <span class="header-pipe">|</span> <span class="header-sub">Mitglied für die Buchung auswählen</span></h3>
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
            v-if="sortedMembers.length > 0"
            class="member-grid"
          >
            <button
              v-for="member in sortedMembers"
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
                <div
                  v-if="member.balance_cents && member.balance_cents !== 0"
                  class="balance-badge"
                >
                  💰 {{ formatBalance(member.balance_cents) }}
                </div>
              </div>
              <div class="member-card-body">
                <div class="member-card-name">
                  {{ getMemberShortName(member) }}
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
import { inject, computed } from 'vue'
const { memberSearch, filteredMembers, selectMember, showMemberModal, getMemberFullName, getMemberShortName, formatBalance } = inject('kasse')

const sortedMembers = computed(() =>
  [...filteredMembers.value].sort((a, b) =>
    (a.last_name ?? '').localeCompare(b.last_name ?? '', 'de')
  )
)
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
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  overflow: hidden;
}
.modal-dialog--fullsize {
  width: 85vw !important;
  max-width: 85vw !important;
  height: 85vh !important;
  max-height: 85vh !important;
}
.modal-header {
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(90deg, #0f766e 0%, #0ea5e9 100%);
  flex-shrink: 0;
}
.modal-header-title {
  display: flex;
  align-items: center;
  min-width: 0;
  h3 {
    margin: 0;
    color: #ffffff;
    font-size: 1.05rem;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .header-pipe {
    margin: 0 0.5rem;
    opacity: 0.5;
  }
  .header-sub {
    font-weight: 400;
    opacity: 0.88;
    font-size: 0.92rem;
  }
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
  grid-template-columns: repeat(6, 1fr);
  grid-auto-rows: 200px;
  gap: 0.5rem;
  align-content: start;
}
@media (max-width: 900px) {
  .modal-overlay {
    padding: 0.75rem;
    align-items: stretch;
  }
  .modal-dialog--fullsize {
    width: 100% !important;
    height: auto !important;
    max-height: calc(100vh - 1.5rem) !important;
    max-width: 100% !important;
  }
  .member-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    grid-auto-rows: 160px;
  }
}
.member-card {
  background: #fff;
  border: 1.5px solid color-mix(in srgb, var(--app-banner-color) 22%, white 78%);
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
  text-align: center;
  transition: all 0.18s;
  height: 200px;
  &:hover {
    border-color: var(--app-highlight-color);
    box-shadow: 0 4px 14px color-mix(in srgb, var(--app-highlight-color) 18%, transparent);
    transform: translateY(-2px);
  }
}
.member-card-img {
  width: 100%;
  height: 85%;
  flex-shrink: 0;
  background: #eef1f7;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}
.member-card-img-placeholder { font-size: 1.8rem; }
.balance-badge {
  position: absolute;
  bottom: 6px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 255, 255, 0.92);
  color: var(--app-highlight-color);
  font-size: 1.0rem;
  font-weight: 700;
  padding: 0.25rem 0.6rem;
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  white-space: nowrap;
  backdrop-filter: blur(2px);
  border: 1px solid rgba(255, 255, 255, 0.5);
}
.member-card-body {
  padding: 0.1rem 0.2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 0;
}
.member-card-name {
  font-size: 1.1rem;
  font-weight: 700;
  line-height: 1.2;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
  text-align: center;
}
.empty-state {
  text-align: center;
  color: #94a3b8;
  padding: 2rem;
  font-size: 0.95rem;
}
</style>
