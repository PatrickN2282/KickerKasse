<template>
  <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-card modal-compact">
      <header class="modal-header">
        <div>
          <h3>{{ editingUserId ? 'Benutzer bearbeiten' : 'Neuen Benutzer anlegen' }}</h3>
          <p class="modal-subtitle">Direkte Benutzerkonten verwalten.</p>
        </div>
        <button class="modal-close" @click="$emit('close')">×</button>
      </header>

      <form class="modal-compact-layout" @submit.prevent="$emit('save')">
        <div class="modal-scroller">
          <section class="form-section">
            <h4>Kontodaten</h4>
            <div class="form-row">
              <div class="form-group">
                <label for="username">Benutzername*</label>
                <input
                  id="username"
                  :value="username"
                  type="text"
                  required
                  @input="$emit('update:username', $event.target.value)"
                >
              </div>

              <div class="form-group">
                <label for="email">E-Mail</label>
                <input
                  id="email"
                  :value="email"
                  type="email"
                  @input="$emit('update:email', $event.target.value)"
                >
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="role">Rolle*</label>
                <select
                  id="role"
                  :value="role"
                  required
                  @change="$emit('update:role', $event.target.value)"
                >
                  <option value="VERKAUF">Verkauf</option>
                  <option value="MANAGER">Manager</option>
                  <option value="ADMIN">Admin</option>
                </select>
              </div>

              <div class="form-group">
                <label for="password">{{ editingUserId ? 'Neues Passwort' : 'Passwort*' }}</label>
                <input
                  id="password"
                  :value="passwordValue"
                  type="password"
                  minlength="8"
                  :required="!editingUserId"
                  placeholder="Mindestens 8 Zeichen"
                  @input="$emit('update:password-value', $event.target.value)"
                >
                <small class="help-text">
                  {{ editingUserId
                    ? 'Leer lassen, wenn das bestehende Passwort unverändert bleiben soll.'
                    : 'Passwort wird für den ersten Login benötigt.' }}
                </small>
              </div>
            </div>
          </section>
        </div>

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
defineProps({
  show: { type: Boolean, required: true },
  editingUserId: { type: [Number, String], default: null },
  username: { type: String, default: '' },
  email: { type: String, default: '' },
  passwordValue: { type: String, default: '' },
  role: { type: String, default: 'VERKAUF' },
})

defineEmits(['close', 'save', 'update:username', 'update:email', 'update:password-value', 'update:role'])
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
  --border: #e2e8f0;
  --primary: #3b82f6;
  --success: #10b981;

  background: white;
  width: 100%;
  max-height: calc(100vh - 2rem);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.modal-compact {
  max-width: 680px;
}

.modal-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;

  h3 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: #1e293b;
  }

  .modal-subtitle {
    margin: 0.15rem 0 0 0;
    font-size: 0.85rem;
    color: #64748b;
  }
}

.modal-compact-layout {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-scroller {
  padding: 1.5rem;
  overflow-y: auto;
  max-height: calc(85vh - 120px);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-section {
  margin-bottom: 0;

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
  gap: 0.75rem;
}

.form-group {
  margin-bottom: 1rem;

  label {
    display: block;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 0.35rem;
    color: #334155;
  }

  input,
  select {
    width: 100%;
    padding: 0.55rem 0.75rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.9rem;
    color: #0f172a;

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

.btn {
  padding: 0.55rem 1.1rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-size: 0.9rem;
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
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: #6b7280;
  padding: 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border);
  background: #f8fafc;
}

@media (max-width: 600px) {
  .modal-card {
    min-height: auto;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .btn {
    width: 100%;
  }
}
</style>
