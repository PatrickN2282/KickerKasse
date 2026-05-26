<template>
  <div v-if="show" class="modal-overlay" @click.self="emit('close')">
    <div class="modal-dialog">

      <div class="modal-header">
        <div class="modal-header-title">
          <i class="ti ti-info-circle" />
          <h3>Help &amp; Info <span class="header-pipe">|</span> <span class="header-sub">KickerKasse</span></h3>
        </div>
        <button class="close-btn" @click="emit('close')">✕</button>
      </div>

      <div class="modal-body">
        <div class="card-grid">

          <div class="info-card">
            <i class="ti ti-device-desktop-code card-icon" />
            <p class="card-label">Projekt</p>
            <p class="card-val">KickerKasse</p>
          </div>

          <div class="info-card">
            <i class="ti ti-user card-icon" />
            <p class="card-label">Autor</p>
            <p class="card-val">Patrick Neuber</p>
          </div>

          <div class="info-card">
            <i class="ti ti-mail card-icon" />
            <p class="card-label">Kontakt</p>
            <p class="card-val">
              <a href="mailto:kickerkasse@patrick-neuber.de" target="_blank" rel="noopener noreferrer">
                kickerkasse@patrick-neuber.de
              </a>
            </p>
          </div>

          <div class="info-card">
            <i class="ti ti-brand-github card-icon" />
            <p class="card-label">Source Code</p>
            <p class="card-val">
              <a href="https://github.com/PatrickN2282/KickerKasse" target="_blank" rel="noopener noreferrer">
                github.com/PatrickN2282/KickerKasse
              </a>
            </p>
          </div>

          <div class="info-card full">
            <i class="ti ti-soccer-field card-icon" />
            <p class="card-label">Beschreibung</p>
            <p class="card-val desc">
              Privates Projekt, zugeschnitten auf die Anforderungen unseres Kickervereins.
              Vereinfacht Lagerhaltung und Kassenzugang.
            </p>
          </div>

          <div class="section-title">Features &amp; Betrieb</div>

          <div class="info-card">
            <i class="ti ti-cash-register card-icon" />
            <p class="card-label">Kassensystem</p>
            <p class="card-val desc">Mehrere wählbare Kassen-Layouts. Artikel per Klick in den Warenkorb, direkte Abrechnung per Guthaben, Voucher oder Bargeld.</p>
          </div>

          <div class="info-card">
            <i class="ti ti-users card-icon" />
            <p class="card-label">Mitgliederverwaltung</p>
            <p class="card-val desc">Mitglieder anlegen, Guthaben aufladen und Transaktionen einsehen. Bild-Upload pro Mitglied möglich.</p>
          </div>

          <div class="info-card">
            <i class="ti ti-package card-icon" />
            <p class="card-label">Produktverwaltung</p>
            <p class="card-val desc">Produkte mit Preis, Kategorie und Lagerbestand pflegen. Bestandswarnungen bei Unterschreiten eines Mindestwerts.</p>
          </div>

          <div class="info-card">
            <i class="ti ti-ticket card-icon" />
            <p class="card-label">Gutscheinsystem</p>
            <p class="card-val desc">Voucher mit festem Wert erstellen und an der Kasse einlösen. Übersicht aller aktiven und verbrauchten Gutscheine.</p>
          </div>

          <div class="info-card">
            <i class="ti ti-chart-bar card-icon" />
            <p class="card-label">Finanzen</p>
            <p class="card-val desc">Übersicht aller Einnahmen und Ausgaben. Export der Buchhaltungsdaten als CSV/Excel.</p>
          </div>

          <div class="info-card">
            <i class="ti ti-shield-lock card-icon" />
            <p class="card-label">Benutzerverwaltung &amp; Rollen</p>
            <p class="card-val desc">Rollen: Top-Admin, Admin, Manager, Kasse. Zugriffsrechte werden pro Rolle gesteuert. Session-Timer für automatischen Logout konfigurierbar.</p>
          </div>

          <div class="info-card">
            <i class="ti ti-settings card-icon" />
            <p class="card-label">Einstellungen</p>
            <p class="card-val desc">App-Name, Logo, Farben, Kassen-Layout und weitere Parameter zentral im Admin-Bereich konfigurierbar.</p>
          </div>

          <div class="info-card">
            <i class="ti ti-device-mobile card-icon" />
            <p class="card-label">PWA-Unterstützung</p>
            <p class="card-val desc">Als Progressive Web App installierbar – auch offline grundlegend nutzbar. Optimiert für Tablet- und Desktop-Betrieb.</p>
          </div>

          <div class="disclaimer">
            <strong>Hinweis:</strong> Kein TSE-fähiges oder revisionssicheres Kassensystem.
            Ziel ist die Vereinfachung von Lagerhaltung und Kassenzugangssteuerung.
            Ideen &amp; Bugs gern per Mail melden.
          </div>

        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="emit('close')">Schließen</button>
      </div>

    </div>
  </div>
</template>

<script setup>
defineProps({
  show: { type: Boolean, default: false },
})
const emit = defineEmits(['close'])
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
  width: min(620px, 100%);
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  overflow: hidden;
}

.modal-header {
  padding: 0.85rem 1.25rem;
  background: #0f766e;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;

  .ti-info-circle {
    color: #ffffff;
    font-size: 1.2rem;
    margin-right: 0.4rem;
  }
}

.modal-header-title {
  display: flex;
  align-items: center;

  h3 {
    margin: 0;
    color: #ffffff;
    font-size: 1rem;
    font-weight: 600;
  }

  .header-pipe {
    margin: 0 0.5rem;
    opacity: 0.45;
  }

  .header-sub {
    font-weight: 400;
    opacity: 0.8;
    font-size: 0.88rem;
  }
}

.close-btn {
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

  &:hover {
    background: rgba(255, 255, 255, 0.28);
  }
}

.modal-body {
  padding: 1rem 1.25rem;
  overflow-y: auto;
}

.card-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.65rem;
}

.info-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.75rem 1rem;

  &.full {
    grid-column: 1 / -1;
  }

  .card-icon {
    font-size: 1.1rem;
    color: #0f766e;
    display: block;
    margin-bottom: 0.35rem;
  }

  .card-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #94a3b8;
    margin-bottom: 0.2rem;
  }

  .card-val {
    font-size: 0.85rem;
    color: #1e293b;
    font-weight: 500;
    word-break: break-all;

    &.desc {
      font-weight: 400;
      line-height: 1.5;
    }

    a {
      color: #0f766e;
      text-decoration: none;
      font-weight: 600;

      &:hover {
        text-decoration: underline;
      }
    }
  }
}

.section-title {
  grid-column: 1 / -1;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #64748b;
  margin-top: 0.35rem;
}

.disclaimer {
  grid-column: 1 / -1;
  border-left: 3px solid #f59e0b;
  background: #fffbeb;
  border-radius: 0 10px 10px 0;
  padding: 0.65rem 0.9rem;
  font-size: 0.8rem;
  color: #92400e;
  line-height: 1.5;
}

.modal-footer {
  padding: 0.9rem 1.25rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  background: #ffffff;
  flex-shrink: 0;
}

.btn {
  border-radius: 8px;
  padding: 0.6rem 1.1rem;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.88rem;
  border: none;
}

.btn-secondary {
  background: #f8fafc;
  color: #475569;
  border: 1px solid #cbd5e1;

  &:hover {
    background: #f1f5f9;
  }
}

@media (max-width: 480px) {
  .card-grid {
    grid-template-columns: 1fr;
  }

  .info-card.full,
  .disclaimer {
    grid-column: 1;
  }
}
</style>
