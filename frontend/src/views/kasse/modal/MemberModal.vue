<template>
  <div class="modal-overlay">
    <div class="modal-dialog">
      <div class="modal-header">
        <div>
          <h3>Mitglied auswählen</h3>
          <p class="subtitle">Mitglied für die Buchung auswählen</p>
        </div>
        <button class="close-btn" @click="showMemberModal = false">✕</button>
      </div>
      <div class="modal-body">
        <input
          v-model="memberSearch"
          type="text"
          placeholder="Nach Name oder Nummer suchen..."
          class="member-search-input"
        />
        <div v-if="filteredMembers.length > 0" class="member-grid">
          <button
            v-for="member in filteredMembers"
            :key="member.id"
            @click="selectMember(member)"
            class="member-card"
          >
            <div class="member-card-img">
              <img
                v-if="member.photo_path"
                :src="`/api/members/${member.id}/photo`"
                :alt="getMemberFullName(member)"
              />
              <div v-else class="member-card-img-placeholder">👤</div>
            </div>
            <div class="member-card-body">
              <div class="member-card-name">{{ getMemberShortName(member) }}</div>
              <div class="member-card-balance">{{ formatBalance(member.balance_cents) }}</div>
            </div>
          </button>
        </div>
        <div v-else class="empty-state">Keine Mitglieder gefunden</div>
      </div>
      <div class="modal-footer">
        <button @click="showMemberModal = false" class="btn btn-secondary">
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
}
.modal-dialog {
  background: #ffffff;
  border-radius: 16px;
  width: 100%;
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
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
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
}
.member-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 0.6rem;
  overflow-y: auto;
  flex: 1;
}
.member-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
  transition: border-color 0.15s, box-shadow 0.15s;
  &:hover {
    border-color: #0ea5e9;
    box-shadow: 0 2px 8px rgba(14, 165, 233, 0.15);
  }
}
.member-card-img {
  width: 100%;
  aspect-ratio: 1 / 1;
  background: #e2e8f0;
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
  padding: 0.4rem 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
.member-card-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.member-card-balance {
  font-size: 0.85rem;
  font-weight: 700;
  color: #059669;
}
.empty-state {
  text-align: center;
  color: #94a3b8;
  padding: 2rem;
  font-size: 0.95rem;
}
</style>
