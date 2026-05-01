<template>
  <div v-if="show" class="user-modal modal-overlay" @click.self="$emit('close')">
    <div class="modal-card modal-card-form">
      <header class="modal-header">
        <div>
          <h3>{{ editingUserId ? 'Benutzer bearbeiten' : 'Neuen Benutzer anlegen' }}</h3>
          <p class="modal-subtitle">Direkte Benutzerkonten nutzen eigene Zugangsdaten und sind nicht an ein Mitglied gebunden.</p>
        </div>
        <button class="modal-close" @click="$emit('close')">×</button>
      </header>

      <form class="modal-form-content" @submit.prevent="handleSubmit">
        <section class="form-section">
          <h4>Kontodaten</h4>
          <div class="form-row">
            <div class="form-group">
              <label for="user-username">Benutzername*</label>
              <input id="user-username" v-model="localForm.username" type="text" required>
            </div>

            <div class="form-group">
              <label for="user-email">E-Mail</label>
              <input id="user-email" v-model="localForm.email" type="email">
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="user-role">Rolle*</label>
              <select id="user-role" v-model="localForm.role" required>
                <option value="VERKAUF">Verkauf</option>
                <option value="MANAGER">Manager</option>
                <option value="ADMIN">Admin</option>
              </select>
            </div>

            <div class="form-group">
              <label for="user-password">{{ editingUserId ? 'Neues Passwort' : 'Passwort*' }}</label>
              <input
                id="user-password"
                v-model="localForm.password"
                type="password"
                minlength="8"
                :required="!editingUserId"
                placeholder="Mindestens 8 Zeichen"
              >
              <small class="help-text">
                {{ editingUserId
                  ? 'Leer lassen, wenn das bestehende Passwort unverändert bleiben soll.'
                  : 'Passwort wird für den ersten Login benötigt.' }}
              </small>
            </div>
          </div>
        </section>

        <footer class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="$emit('close')">Abbrechen</button>
          <button type="submit" class="btn btn-success">
            {{ editingUserId ? 'Änderungen speichern' : 'Benutzer anlegen' }}
          </button>
        </footer>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  show: { type: Boolean, required: true },
  editingUserId: { type: [Number, String], default: null },
  initialFormData: {
    type: Object,
    default: () => ({ username: '', email: '', password: '', role: 'VERKAUF' }),
  },
})

const emit = defineEmits(['close', 'save'])

const localForm = ref({ username: '', email: '', password: '', role: 'VERKAUF' })

watch(() => props.initialFormData, (val) => {
  if (val) localForm.value = { ...val }
}, { immediate: true, deep: true })

const handleSubmit = () => {
  emit('save', { ...localForm.value })
}
</script>

<style scoped lang="scss">
.user-modal {
  --primary: #3b82f6;
  --success: #10b981;
  --border: #e2e8f0;
}

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
  max-width: 900px;
  max-height: 90vh;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.modal-card-form {
  max-width: 760px;
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border);
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

.form-section {
  margin-bottom: 2rem;

  h4 {
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
  }
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

  input,
  select {
    width: 100%;
    padding: 0.6rem 0.8rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.95rem;

    &:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
  }
}

.help-text {
  display: block;
  margin-top: 0.4rem;
  font-size: 0.75rem;
  color: #64748b;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid var(--border);
}

.btn {
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.btn-success {
  background: var(--success);
  color: white;
}

.btn-secondary {
  background: #e2e8f0;
  color: #475569;
}

.modal-close {
  border: none;
  background: transparent;
  font-size: 1.6rem;
  line-height: 1;
  cursor: pointer;
  color: #6b7280;
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
