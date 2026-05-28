<template>
  <div v-if="show" class="modal-overlay" @click.self="emit('close')">
    <div class="modal-dialog">

      <div class="modal-header">
        <div class="modal-header-title">
          <span class="header-icon">ℹ️</span>
          <h3>Help &amp; Info <span class="header-pipe">|</span> <span class="header-sub">KickerKasse</span></h3>
        </div>
        <button class="close-btn" @click="emit('close')">✕</button>
      </div>

      <div class="modal-body">

        <table class="meta-table">
          <tbody>
            <tr>
              <td><span class="meta-icon">👤</span> Autor</td>
              <td>Patrick Neuber</td>
            </tr>
            <tr>
              <td><span class="meta-icon">✉️</span> E-Mail</td>
              <td>
                <a href="mailto:kickerkasse@patrick-neuber.de" target="_blank" rel="noopener noreferrer">
                  kickerkasse@patrick-neuber.de
                </a>
              </td>
            </tr>
            <tr>
              <td><span class="meta-icon">💻</span> GitHub</td>
              <td>
                <a href="https://github.com/PatrickN2282/KickerKasse" target="_blank" rel="noopener noreferrer">
                  github.com/PatrickN2282/KickerKasse
                </a>
              </td>
            </tr>
            <tr>
              <td><span class="meta-icon">🧪</span> Tester</td>
              <td>Carsten Heine <span class="tester-role">– Fehler-finden &amp; QM</span></td>
            </tr>
          </tbody>
        </table>

        <div class="features-section">
          <p class="section-label">Features</p>
          <ul class="feature-list">
            <li v-for="feat in features" :key="feat.label" class="feature-item">
              <div class="feat-icon">
                <span>{{ feat.icon }}</span>
              </div>
              <div>
                <p class="feat-name">{{ feat.label }}</p>
                <p class="feat-desc">{{ feat.desc }}</p>
              </div>
            </li>
          </ul>
        </div>

        <div class="disclaimer">
          <span class="disclaimer-icon">⚠️</span>
          <span>
            Kein TSE-fähiges oder revisionssicheres Kassensystem. Ziel ist die Vereinfachung von
            Lagerhaltung und Kassenzugang. Ideen &amp; Bugs gern per Mail melden.
          </span>
        </div>

      </div>

      <div class="modal-footer">
        <button class="btn btn-donate" @click="emit('donate'); emit('close')">💛 Spenden</button>
        <button class="btn btn-secondary" @click="emit('close')">Schließen</button>
        <a class="btn btn-primary" href="mailto:kickerkasse@patrick-neuber.de">
          ✉️ Kontakt
        </a>
      </div>

    </div>
  </div>
</template>

<script setup>
defineProps({
  show: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'donate'])

const features = [
  { icon: '🖥️', label: 'Kassensystem',          desc: 'Mehrere Layouts, Warenkorb, Abrechnung per Guthaben, Voucher oder Bargeld' },
  { icon: '👥', label: 'Mitgliederverwaltung',  desc: 'Guthaben, Transaktionen, Bild-Upload pro Mitglied' },
  { icon: '📦', label: 'Produktverwaltung',     desc: 'Preis, Kategorie, Lagerbestand mit Mindestmengen-Warnung' },
  { icon: '🎟️', label: 'Gutscheinsystem',       desc: 'Voucher erstellen, einlösen, Übersicht aktiver und verbrauchter Codes' },
  { icon: '📊', label: 'Finanzen',              desc: 'Einnahmen/Ausgaben-Übersicht, Export als CSV/Excel' },
  { icon: '🔐', label: 'Rollen & Rechte',       desc: 'Top-Admin, Admin, Manager, Kasse – Session-Timer konfigurierbar' },
  { icon: '📱', label: 'PWA',                   desc: 'Installierbar, offline-fähig, optimiert für Tablet & Desktop' },
]
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
  padding: 1.25rem;
  overflow-y: auto;
}

.modal-dialog {
  background: #ffffff;
  border-radius: 20px;
  width: min(560px, 100%);
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  overflow: hidden;
}

/* Header */
.modal-header {
  padding: 0.85rem 1.2rem;
  background: #0f766e;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.modal-header-title {
  display: flex;
  align-items: center;
  gap: 8px;

  .header-icon {
    font-size: 1rem;
  }

  h3 {
    margin: 0;
    color: #ffffff;
    font-size: 0.95rem;
    font-weight: 600;
  }

  .header-pipe {
    opacity: 0.35;
    margin: 0 3px;
  }

  .header-sub {
    font-weight: 400;
    opacity: 0.75;
    font-size: 0.85rem;
  }
}

.close-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
  font-size: 0.9rem;
  cursor: pointer;
  display: grid;
  place-items: center;
  flex-shrink: 0;

  &:hover {
    background: rgba(255, 255, 255, 0.24);
  }
}

/* Body */
.modal-body {
  padding: 1rem 1.2rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Meta-Tabelle */
.meta-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;

  tr {
    border-bottom: 1px solid #f1f5f9;

    &:last-child {
      border-bottom: none;
    }
  }

  td {
    padding: 0.5rem 0;
    vertical-align: middle;

    &:first-child {
      color: #64748b;
      display: flex;
      align-items: center;
      gap: 6px;
      width: 110px;
      white-space: nowrap;
      padding-top: 0.6rem;
    }

    &:last-child {
      color: #1e293b;
      font-weight: 500;
      word-break: break-all;

      a {
        color: #0f766e;
        text-decoration: none;

        &:hover {
          text-decoration: underline;
        }
      }
    }
  }
}

.meta-icon {
  font-size: 0.9rem;
}

.tester-role {
  font-weight: 400;
  color: #64748b;
  font-size: 0.8rem;
}

/* Feature-Liste */
.features-section {
  .section-label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94a3b8;
    margin-bottom: 0.5rem;
    padding-top: 0.25rem;
    border-top: 1px solid #f1f5f9;
  }
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f8fafc;
  font-size: 0.84rem;

  &:last-child {
    border-bottom: none;
  }
}

.feat-icon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  margin-top: 1px;
  font-size: 0.9rem;
}

.feat-name {
  font-weight: 600;
  color: #1e293b;
  line-height: 1.3;
  margin: 0 0 2px;
}

.feat-desc {
  font-size: 0.78rem;
  color: #64748b;
  line-height: 1.4;
  margin: 0;
}

/* Disclaimer */
.disclaimer {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 10px;
  padding: 0.65rem 0.85rem;
  font-size: 0.78rem;
  color: #92400e;
  line-height: 1.5;
}

.disclaimer-icon {
  font-size: 0.95rem;
  flex-shrink: 0;
  margin-top: 1px;
}

/* Footer */
.modal-footer {
  padding: 0.8rem 1.2rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  background: #ffffff;
  flex-shrink: 0;
}

.btn {
  border-radius: 8px;
  padding: 0.55rem 1rem;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.85rem;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  text-decoration: none;
}

.btn-secondary {
  background: #f8fafc;
  color: #475569;
  border: 1px solid #cbd5e1;

  &:hover {
    background: #f1f5f9;
  }
}

.btn-primary {
  background: #0f766e;
  color: #ffffff;
  border: none;

  &:hover {
    background: #0d6460;
  }
}

.btn-donate {
  background: #fef9c3;
  color: #92400e;
  border: 1px solid #fde68a;
  margin-right: auto;

  &:hover {
    background: #fef08a;
  }
}
</style>
