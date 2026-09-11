<template>
  <div
    v-if="show"
    class="help-overlay"
    @click.self="closeModal"
  >
    <section
      class="help-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="help-title"
    >
      <header class="help-header">
        <button
          v-if="activeFeature"
          type="button"
          class="header-action back-action"
          aria-label="Zurück zur Funktionsübersicht"
          @click="showOverview"
        >
          <span aria-hidden="true">←</span>
        </button>

        <div class="header-copy">
          <span class="header-icon" aria-hidden="true">
            {{ activeFeature?.icon || 'ℹ️' }}
          </span>
          <div>
            <p class="header-eyebrow">
              {{ activeFeature ? 'Funktionsdetails' : 'Hilfe & Informationen' }}
            </p>
            <h2 id="help-title">
              {{ activeFeature?.label || 'Alles Wichtige an einem Ort' }}
            </h2>
          </div>
        </div>

        <button
          type="button"
          class="header-action close-action"
          aria-label="Hilfe und Informationen schließen"
          @click="closeModal"
        >
          <span aria-hidden="true">✕</span>
        </button>
      </header>

      <main class="help-body">
        <Transition name="page" mode="out-in">
          <div v-if="!activeFeature" key="overview" class="overview-page">
            <section class="about-card" aria-labelledby="about-title">
              <div class="about-heading">
                <span aria-hidden="true">💬</span>
                <div>
                  <p class="section-kicker">Projekt & Kontakt</p>
                  <h3 id="about-title">Hilfe, Feedback oder Fehler melden</h3>
                </div>
                <span class="version-badge">Version {{ appVersion }}</span>
              </div>
              <div class="about-grid">
                <div>
                  <span>Autor</span>
                  <strong>Patrick Neuber</strong>
                </div>
                <div>
                  <span>Qualitätssicherung</span>
                  <strong>Carsten Heine</strong>
                </div>
                <div>
                  <span>E-Mail</span>
                  <a href="mailto:kickerkasse@patrick-neuber.de">
                    kickerkasse@patrick-neuber.de
                  </a>
                </div>
                <div>
                  <span>Quellcode</span>
                  <a
                    href="https://github.com/PatrickN2282/KickerKasse"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    GitHub-Projekt öffnen ↗
                  </a>
                </div>
              </div>
            </section>

            <section aria-labelledby="feature-overview-title">
              <div class="section-heading">
                <div>
                  <p class="section-kicker">Funktionsübersicht</p>
                  <h3 id="feature-overview-title">Was KickerKasse abdeckt</h3>
                </div>
                <p class="section-hint">Pfeil auswählen für mehr Details</p>
              </div>

              <div class="feature-grid">
                <button
                  v-for="feature in features"
                  :key="feature.id"
                  type="button"
                  class="feature-card"
                  :aria-label="`${feature.label}: mehr erfahren`"
                  @click="openFeature(feature.id)"
                >
                  <span class="feature-icon" aria-hidden="true">{{ feature.icon }}</span>
                  <span class="feature-copy">
                    <strong>{{ feature.label }}</strong>
                    <span>{{ feature.summary }}</span>
                  </span>
                  <span class="more-arrow" aria-hidden="true">›</span>
                </button>
              </div>
            </section>

          </div>

          <article v-else :key="activeFeature.id" class="detail-page">
            <section class="detail-intro">
              <span class="detail-icon" aria-hidden="true">{{ activeFeature.icon }}</span>
              <div>
                <p class="section-kicker">{{ activeFeature.kicker }}</p>
                <h3>{{ activeFeature.headline }}</h3>
                <p>{{ activeFeature.intro }}</p>
              </div>
            </section>

            <div class="detail-sections">
              <section
                v-for="section in activeFeature.sections"
                :key="section.title"
                class="detail-section"
              >
                <div class="detail-section-heading">
                  <span aria-hidden="true">{{ section.icon }}</span>
                  <h4>{{ section.title }}</h4>
                </div>
                <p v-if="section.text" class="detail-text">{{ section.text }}</p>
                <ul v-if="section.items?.length">
                  <li v-for="item in section.items" :key="item">{{ item }}</li>
                </ul>
              </section>
            </div>

            <aside v-if="activeFeature.note" class="info-note">
              <span aria-hidden="true">💡</span>
              <p>{{ activeFeature.note }}</p>
            </aside>
          </article>
        </Transition>
      </main>

      <footer class="help-footer">
        <aside class="notice-card notice-card--footer">
          <span class="notice-icon" aria-hidden="true">⚠️</span>
          <div>
            <strong>Wichtiger Hinweis</strong>
            <p>
              KickerKasse ist kein TSE-fähiges oder rechtlich revisionssicheres
              Kassensystem. Es unterstützt den vereinsinternen Kassen- und Lagerbetrieb,
              ersetzt aber keine steuerliche oder rechtliche Prüfung.
            </p>
          </div>
        </aside>
        <div class="help-footer-actions">
          <button type="button" class="btn btn-donate" @click="donate">
            <span aria-hidden="true">💛</span>
            Spenden
          </button>
          <button
            v-if="activeFeature"
            type="button"
            class="btn btn-secondary"
            @click="showOverview"
          >
            ← Zur Übersicht
          </button>
          <button type="button" class="btn btn-secondary" @click="closeModal">
            Schließen
          </button>
          <a class="btn btn-primary" href="mailto:kickerkasse@patrick-neuber.de">
            <span aria-hidden="true">✉️</span>
            Kontakt
          </a>
        </div>
      </footer>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import packageInfo from '../../package.json'

const props = defineProps({
  show: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'donate'])

const appVersion = packageInfo.version
const activeFeatureId = ref(null)

const features = [
  {
    id: 'checkout',
    icon: '🖥️',
    label: 'Kasse & Zahlungen',
    summary: 'Warenkorb, Preislogik, Barzahlung, Guthaben und Spenden',
    kicker: 'Schneller Kassenbetrieb',
    headline: 'Verkaufen und sicher abrechnen',
    intro: 'Die Kassenansicht verbindet Produktauswahl, Warenkorb und alle unterstützten Zahlungswege in einem geführten Ablauf.',
    sections: [
      {
        icon: '🛒',
        title: 'Verkauf',
        items: [
          'Mehrere Kassenlayouts für Tablet und Desktop',
          'Produktauswahl über Kategorien, Bilder und Verfügbarkeitsanzeige',
          'Laufende Belegnummer, Mengenänderung und übersichtlicher Warenkorb',
          'Gästelistenpflichtige Artikel erfassen die Gastdaten direkt beim Hinzufügen',
        ],
      },
      {
        icon: '🏷️',
        title: 'Preislogik',
        items: [
          'Festpreise werden serverseitig aus den Produktdaten ermittelt',
          'Mitgliedspreise gelten nur bei Rabattberechtigung und rabattfähigem Artikel; auch 0,00 € ist zulässig',
          'Variable Preise werden beim Kassieren eingegeben, etwa für Spenden oder MHD-Rabatte',
          'Internes Material wird mit 0,00 € verkauft und getrennt bewertet',
        ],
      },
      {
        icon: '💶',
        title: 'Zahlungswege',
        items: [
          'Barzahlung mit gegebenem Betrag und automatisch berechnetem Rückgeld',
          'Vollständige oder teilweise Nutzung von Mitgliedsguthaben',
          'Einlösung von Geschenk-Gutscheinen und Verzehrkarten',
          'Frei wählbare Spende aus dem Wechselgeld, auch beim Deckel',
        ],
      },
    ],
    note: 'Eine Hauptkassenöffnung wird nur angefordert, wenn tatsächlich Bargeld bewegt wird.',
  },
  {
    id: 'members',
    icon: '👥',
    label: 'Mitglieder & Guthaben',
    summary: 'Stammdaten, Fotos, Rabatte, Guthaben und Benutzerverknüpfung',
    kicker: 'Mitgliederverwaltung',
    headline: 'Mitglieder und Zugänge gemeinsam pflegen',
    intro: 'Mitgliedsdaten, Rabattstatus, Guthaben und optionale Systemzugänge werden zentral verwaltet.',
    sections: [
      {
        icon: '👤',
        title: 'Stammdaten',
        items: [
          'Vor- und Nachname, Mitgliedsnummer, Kontaktangaben und Notizen',
          'Mitgliedsfoto für eine schnelle Auswahl an der Kasse',
          'Suche und übersichtliche Bearbeitung im Admin-Bereich',
        ],
      },
      {
        icon: '💳',
        title: 'Guthaben und Rabatt',
        items: [
          'Rabattberechtigung je Mitglied aktivieren oder deaktivieren',
          'Guthaben bar aufladen und in der Kasse vollständig oder teilweise einsetzen',
          'Nachvollziehbare Guthabenhistorie und gesonderte Korrekturbuchungen für Admins',
        ],
      },
      {
        icon: '🔗',
        title: 'Verknüpfte Konten',
        items: [
          'Mitglieder mit Rolle können einen eigenen Systemzugang erhalten',
          'Rollenvergabe an Mitglieder erfolgt ausschließlich durch den TopAdmin',
          'Direkte Benutzerkonten und verknüpfte Mitgliedskonten bleiben unterscheidbar',
        ],
      },
    ],
  },
  {
    id: 'products',
    icon: '📦',
    label: 'Produkte & Lager',
    summary: 'Artikel, Kategorien, Bilder, Bestände und Warnschwellen',
    kicker: 'Sortiment und Bestand',
    headline: 'Produkte passend zum Vereinsbetrieb konfigurieren',
    intro: 'Produkte lassen sich flexibel bepreisen, kategorisieren und mit oder ohne physische Bestandsführung betreiben.',
    sections: [
      {
        icon: '🧾',
        title: 'Produktdaten',
        items: [
          'Regulärer Preis, optionaler Mitgliedspreis und variable Preisangabe',
          'Mehrere Kategorien, Produktbeschreibung und Produktbild',
          'Artikel aktivieren, deaktivieren oder löschen',
          'Sonderoptionen für Gästeliste, internes Material und Kleinteile-Lager',
        ],
      },
      {
        icon: '📊',
        title: 'Bestandsführung',
        items: [
          'Geführter Lagerbestand oder unbegrenzte Verfügbarkeit',
          'Mindestbestand mit optionaler Warnung',
          'Deckel reservieren Ware, damit sie nicht doppelt verkauft wird',
          'Bestandskorrekturen protokollieren Altwert, Neuwert, Grund und Benutzer',
        ],
      },
      {
        icon: '🔄',
        title: 'Datenübernahme',
        items: [
          'Import und Export von Produkten, Kategorien und Mitgliederdaten',
          'Bestehende Installationen werden durch additive Datenbankanpassungen weitergeführt',
        ],
      },
    ],
  },
  {
    id: 'vouchers',
    icon: '🎟️',
    label: 'Gutscheine & Verzehrkarten',
    summary: 'Erstellen, vorbereiten, verkaufen, einlösen und auswerten',
    kicker: 'Flexible Voucher',
    headline: 'Guthaben verschenken oder als Verzehrkarte ausgeben',
    intro: 'Geschenk-Gutscheine und vorproduzierte Verzehrkarten besitzen getrennte Abläufe, werden an der Kasse aber einheitlich eingelöst.',
    sections: [
      {
        icon: '🎁',
        title: 'Geschenk-Gutscheine',
        items: [
          'Gutschein mit Wert, Grund und eindeutigem Code erstellen',
          'Vollständige oder teilweise Einlösung im Warenkorb',
          'Status und Restwert in der Verwaltung nachvollziehen',
        ],
      },
      {
        icon: '🎫',
        title: 'Verzehrkarten',
        items: [
          'Serien mit festen Werten vorbereiten und verwalten',
          'Passende Verkaufsprodukte und Bestände automatisch anlegen',
          'Ausgabe beim Verkauf und spätere Einlösung sauber trennen',
        ],
      },
      {
        icon: '📋',
        title: 'Verwaltung',
        items: [
          'Filter für aktive, eingelöste und verbrauchte Codes',
          'CSV-Export der Gutscheinübersicht',
          'Gesondertes Gutscheinkonto für nachvollziehbare Verlust- und Korrekturwerte',
        ],
      },
    ],
  },
  {
    id: 'operations',
    icon: '📋',
    label: 'Deckel & Gästeliste',
    summary: 'Offene Bons, Reservierungen und chronologische Gastdaten',
    kicker: 'Abläufe im Vereinsheim',
    headline: 'Offene Vorgänge und Gäste im Blick behalten',
    intro: 'Deckel verschieben die Bezahlung auf später; die Gästeliste dokumentiert erforderliche Gastangaben direkt zum Verkauf.',
    sections: [
      {
        icon: '🧾',
        title: 'Deckel',
        items: [
          'Deckel benennen, mit Artikeln anlegen und später erweitern',
          'Festpreise werden serverseitig geprüft, variable Preise als Buchungspreis gespeichert',
          'Bestände bleiben bis zur Barabrechnung für den Deckel reserviert',
          'Der beim Buchen gespeicherte Preis bleibt als nachvollziehbarer Snapshot erhalten',
        ],
      },
      {
        icon: '👤',
        title: 'Gäste erfassen',
        items: [
          'Gastname und optionaler Gastgeber werden beim betreffenden Artikel abgefragt',
          'Die Anzahl der Gastdatensätze wird an die verkaufte Artikelmenge gekoppelt',
        ],
      },
      {
        icon: '🗂️',
        title: 'Gästeliste im Admin-Bereich',
        items: [
          'Produktübergreifende, chronologische Anzeige mit Datum und Uhrzeit',
          'Gast, Gastgeber, Produkt oder Anlass sowie Belegnummer auf einen Blick',
          'Freitextsuche und zusätzlicher Produktfilter',
        ],
      },
    ],
  },
  {
    id: 'finance',
    icon: '📊',
    label: 'Finanzen & Z-Bon',
    summary: 'Transaktionen, Konten, Kassenzählung und Abschlüsse',
    kicker: 'Nachvollziehbare Finanzen',
    headline: 'Kassenbewegungen prüfen und Zeiträume abschließen',
    intro: 'Finanzansicht und Z-Bon verwenden dieselbe centgenaue Berechnung für den jeweils offenen Zeitraum.',
    sections: [
      {
        icon: '🧮',
        title: 'Kassensoll',
        items: [
          'Anfangsbestand plus Barverkäufe, Guthabenaufladungen, Trinkgeld und Bareinlagen',
          'Barentnahmen und Abschöpfungen werden abgezogen',
          'Guthaben- und Gutscheineinlösungen erzeugen keinen zusätzlichen Bargeldfluss',
        ],
      },
      {
        icon: '🧾',
        title: 'Z-Bon',
        items: [
          'Vorschau für den Zeitraum seit dem letzten Abschluss',
          'Kassenzählung, Differenzbegründung und vorgemerkte Abschöpfung',
          'Gespeicherter Verlauf sowie HTML-, PDF- und E-Mail-Ausgabe',
          'Lesender Konsistenzbericht für historische Abschlüsse',
        ],
      },
      {
        icon: '📄',
        title: 'Transaktionen und Export',
        items: [
          'Reguläre Transaktionshistorie mit Filtern',
          'Zuerst formatierte HTML-Vorschau im Dialog',
          'Anschließender CSV- oder PDF-Download der gefilterten Liste',
          'Rollenabhängige Ansichten für Mitglieder-, Gutschein- und Materialkonto',
        ],
      },
    ],
    note: 'Es gibt derzeit keine Kartenzahlung. Unterstützt werden Bargeld, Mitgliedsguthaben und Voucher.',
  },
  {
    id: 'material',
    icon: '🧰',
    label: 'Verbrauchsmaterial & Schubladen',
    summary: 'Interne 0-Euro-Buchungen und getrennte Hardware-Ziele',
    kicker: 'Material und Hardware',
    headline: 'Interne Ausgabe und physische Zugriffe sauber trennen',
    intro: 'Interne Materialwerte, Bargeldbewegungen und Lagerzugriffe folgen getrennten Regeln und bleiben dadurch nachvollziehbar.',
    sections: [
      {
        icon: '🧩',
        title: 'Internes Verbrauchsmaterial',
        items: [
          'Auswahl über die reservierte Kategorie „Verbrauchsmaterial - Intern“',
          'Verkauf und Belegposition immer mit 0,00 €',
          'Separater Materialkontowert zum regulären oder berechtigten Mitgliedspreis',
          'Optionale Notiz, Menge, Artikel, Beleg und buchender Benutzer bleiben gespeichert',
        ],
      },
      {
        icon: '🗃️',
        title: 'Materialliste',
        items: [
          'Eigene Admin-Seite für Manager, Admin und TopAdmin',
          'Filterbare Transaktionsliste mit Datum, Wert, Notiz und Belegbezug',
          'Das interne Materialkonto selbst bleibt Admin und TopAdmin vorbehalten',
        ],
      },
      {
        icon: '🔌',
        title: 'Hauptkasse und Kleinteile-Lager',
        items: [
          'Die Hauptschublade öffnet nur bei tatsächlicher Bargeldbewegung',
          'Das Kleinteile-Lager öffnet bei Ausgabe oder Einlagerung entsprechend markierter Artikel',
          'Bei Deckeln erfolgt die Lageröffnung bei der Warenausgabe, nicht erneut bei der Bezahlung',
          'Der lokale Hardware-Agent ordnet beide Ziele getrennten USB-Adaptern zu',
        ],
      },
    ],
  },
  {
    id: 'roles',
    icon: '🔐',
    label: 'Rollen & Administration',
    summary: 'Verkauf, Manager, Admin, TopAdmin und Systemeinstellungen',
    kicker: 'Zugriff nach Aufgabe',
    headline: 'Jede Rolle sieht nur die vorgesehenen Funktionen',
    intro: 'Das Berechtigungssystem trennt den reinen Kassenbetrieb von operativer Verwaltung und systemweiten Einstellungen.',
    sections: [
      {
        icon: '🛒',
        title: 'Verkauf',
        items: [
          'Kassenbetrieb, Gutscheine, Guthaben, Deckel, Gäste und internes Material',
          'Kein Zugriff auf den Admin-Bereich',
          'Optionaler versteckter Direktlogin „Kasse“ für den schnellen Start',
        ],
      },
      {
        icon: '🛠️',
        title: 'Manager und Admin',
        items: [
          'Manager: operative Verwaltung, Gäste-/Materiallisten und Z-Bon',
          'Admin: zusätzlich Korrekturen, Benutzer, Konten, Transaktionsexport und Einstellungen',
          'Sensible Aktionen bleiben passwortgeschützt und rollenabhängig',
        ],
      },
      {
        icon: '🛡️',
        title: 'TopAdmin',
        items: [
          'Initiales Setup, Rollenvergabe und vollständige Systemhoheit',
          'Erweiterte Einstellungen für Kassenansicht, Sitzungszeitlimit, E-Mail und lokalen Hardware-Service',
          'Datenpflege, Backup/Restore, Audit-Log und Hard-Reset',
          'Zentrale Steuerung des Kassen-Direktlogins',
        ],
      },
    ],
  },
  {
    id: 'system',
    icon: '📱',
    label: 'PWA, Design & Betrieb',
    summary: 'Installierbare Oberfläche, Branding, Backups und lokaler Agent',
    kicker: 'Flexibler Einsatz',
    headline: 'Auf Tablet und Desktop als Web-App betreiben',
    intro: 'KickerKasse ist für den lokalen Vereins-PC ebenso geeignet wie für einen extern bereitgestellten Server mit lokalem Kassenclient.',
    sections: [
      {
        icon: '📲',
        title: 'Progressive Web App',
        items: [
          'Installierbare, responsive Oberfläche für Tablet und Desktop',
          'App-Name, Farben und Vereinslogo konfigurierbar',
          'Kassenansicht und Sitzungszeitlimit durch den TopAdmin einstellbar',
          'Für serverseitige Buchungen ist eine Verbindung zum KickerKasse-Backend erforderlich',
        ],
      },
      {
        icon: '💾',
        title: 'Daten und Betrieb',
        items: [
          'PostgreSQL-Datenbank mit automatischen, additiven Schema-Erweiterungen',
          'Datenbank-Backups können exportiert, wiederhergestellt und per E-Mail versendet werden',
          'Import/Export unterstützt den Umzug von Stamm- und Bestandsdaten',
          'Audit-Log dokumentiert relevante administrative Änderungen',
        ],
      },
      {
        icon: '🖨️',
        title: 'Lokaler Hardware-Agent',
        items: [
          'Der Browser spricht den Agenten auf dem Kassen-PC direkt an',
          'USB-Geräte und Konfigurationscode werden nicht an einen externen Server weitergegeben',
          'Externe PWA-Origins müssen einmal lokal mit dem Agenten gekoppelt werden',
        ],
      },
    ],
  },
]

const activeFeature = computed(() => (
  features.find(feature => feature.id === activeFeatureId.value) || null
))

const openFeature = (featureId) => {
  activeFeatureId.value = featureId
}

const showOverview = () => {
  activeFeatureId.value = null
}

const closeModal = () => {
  showOverview()
  emit('close')
}

const donate = () => {
  showOverview()
  emit('donate')
  emit('close')
}

const handleKeydown = (event) => {
  if (!props.show || event.key !== 'Escape') return
  if (activeFeature.value) {
    showOverview()
    return
  }
  closeModal()
}

watch(() => props.show, (isVisible) => {
  if (isVisible) showOverview()
})

onMounted(() => window.addEventListener('keydown', handleKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', handleKeydown))
</script>

<style scoped lang="scss">
.help-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: grid;
  place-items: center;
  padding: 1.25rem;
  overflow-y: auto;
  background:
    radial-gradient(circle at 15% 10%, rgba(20, 184, 166, 0.2), transparent 32%),
    rgba(15, 23, 42, 0.68);
  backdrop-filter: blur(6px);
}

.help-dialog {
  width: min(860px, 100%);
  max-height: min(90vh, 900px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f8fafc;
  border: 1px solid rgba(255, 255, 255, 0.65);
  border-radius: 22px;
  box-shadow: 0 28px 70px rgba(15, 23, 42, 0.38);
}

.help-header {
  min-height: 68px;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) 42px;
  align-items: center;
  gap: 0.75rem;
  padding: 0.72rem 1rem;
  color: #ffffff;
  background:
    linear-gradient(125deg, rgba(255, 255, 255, 0.08), transparent 45%),
    linear-gradient(135deg, #0f766e, #115e59);
  flex-shrink: 0;
}

.header-copy {
  grid-column: 2;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-icon {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  font-size: 1.15rem;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 12px;
}

.header-eyebrow,
.section-kicker {
  margin: 0;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.header-eyebrow {
  color: rgba(255, 255, 255, 0.68);
}

.header-copy h2 {
  margin: 0.12rem 0 0;
  overflow: hidden;
  font-size: 1.08rem;
  font-weight: 750;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-action {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  padding: 0;
  color: #ffffff;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.26);
  border-radius: 11px;
  cursor: pointer;
  transition: background 160ms ease, transform 160ms ease;

  &:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-1px);
  }

  &:focus-visible {
    outline: 3px solid rgba(253, 230, 138, 0.8);
    outline-offset: 2px;
  }
}

.back-action {
  grid-column: 1;
  grid-row: 1;
  font-size: 1.25rem;
}

.close-action {
  grid-column: 3;
  grid-row: 1;
}

.help-body {
  min-height: 0;
  padding: 1rem;
  overflow-y: auto;
  scrollbar-color: #94a3b8 transparent;
}

.overview-page,
.detail-page {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.section-kicker {
  color: #0f766e;
}

.version-badge {
  flex-shrink: 0;
  padding: 0.38rem 0.65rem;
  color: #0f766e;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid #99f6e4;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 750;
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.7rem;

  h3 {
    margin: 0.18rem 0 0;
    color: #1e293b;
    font-size: 1.05rem;
  }
}

.section-hint {
  margin: 0;
  color: #94a3b8;
  font-size: 0.72rem;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.65rem;
}

.feature-card {
  min-width: 0;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) 28px;
  align-items: center;
  gap: 0.75rem;
  padding: 0.7rem 0.75rem;
  text-align: left;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(15, 23, 42, 0.025);
  transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;

  &:hover {
    border-color: #5eead4;
    box-shadow: 0 9px 20px rgba(15, 118, 110, 0.1);
    transform: translateY(-2px);

    .more-arrow {
      color: #ffffff;
      background: #0f766e;
      transform: translateX(2px);
    }
  }

  &:focus-visible {
    outline: 3px solid rgba(20, 184, 166, 0.28);
    outline-offset: 2px;
  }
}

.feature-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  font-size: 1.1rem;
  background: #f0fdfa;
  border: 1px solid #ccfbf1;
  border-radius: 12px;
}

.feature-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.18rem;

  strong {
    color: #1e293b;
    font-size: 0.88rem;
  }

  span {
    color: #64748b;
    font-size: 0.75rem;
    line-height: 1.4;
  }
}

.more-arrow {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  color: #0f766e;
  background: #ecfdf5;
  border-radius: 50%;
  font-size: 1.35rem;
  line-height: 1;
  transition: color 160ms ease, background 160ms ease, transform 160ms ease;
}

.about-card {
  padding: 0.72rem 0.85rem;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 15px;
}

.about-heading {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f1f5f9;

  > span {
    font-size: 1.1rem;
  }

  h3 {
    margin: 0.12rem 0 0;
    color: #1e293b;
    font-size: 0.92rem;
  }

  .version-badge {
    margin-left: auto;
  }
}

.about-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.55rem 0.85rem;
  padding-top: 0.55rem;

  > div {
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.12rem;
  }

  span {
    color: #94a3b8;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  strong,
  a {
    overflow: hidden;
    color: #334155;
    font-size: 0.8rem;
    font-weight: 650;
    text-decoration: none;
    text-overflow: ellipsis;
  }

  a {
    color: #0f766e;

    &:hover {
      text-decoration: underline;
    }
  }
}

.notice-card,
.info-note {
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
  padding: 0.85rem 1rem;
  border-radius: 13px;
}

.notice-card {
  color: #92400e;
  background: #fffbeb;
  border: 1px solid #fde68a;

  strong {
    display: block;
    margin-bottom: 0.18rem;
    font-size: 0.8rem;
  }

  p {
    margin: 0;
    font-size: 0.76rem;
    line-height: 1.5;
  }
}

.notice-icon {
  flex-shrink: 0;
}

.detail-intro {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.15rem 1.2rem;
  background: linear-gradient(135deg, #ecfdf5, #f0fdfa);
  border: 1px solid #a7f3d0;
  border-radius: 16px;

  h3 {
    margin: 0.2rem 0 0.35rem;
    color: #134e4a;
    font-size: 1.25rem;
  }

  p:last-child {
    margin: 0;
    color: #3f625f;
    font-size: 0.86rem;
    line-height: 1.55;
  }
}

.detail-icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  font-size: 1.35rem;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid #99f6e4;
  border-radius: 14px;
}

.detail-sections {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
}

.detail-section {
  padding: 1rem;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;

  ul {
    display: flex;
    flex-direction: column;
    gap: 0.48rem;
    margin: 0;
    padding: 0 0 0 1.05rem;
  }

  li {
    padding-left: 0.1rem;
    color: #526174;
    font-size: 0.76rem;
    line-height: 1.48;

    &::marker {
      color: #14b8a6;
    }
  }
}

.detail-section-heading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.72rem;
  padding-bottom: 0.6rem;
  border-bottom: 1px solid #f1f5f9;

  span {
    font-size: 0.95rem;
  }

  h4 {
    margin: 0;
    color: #1e293b;
    font-size: 0.86rem;
  }
}

.detail-text {
  margin: 0 0 0.7rem;
  color: #64748b;
  font-size: 0.78rem;
  line-height: 1.5;
}

.info-note {
  color: #155e75;
  background: #ecfeff;
  border: 1px solid #a5f3fc;

  p {
    margin: 0;
    font-size: 0.78rem;
    line-height: 1.5;
  }
}

.help-footer {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.85rem;
  padding: 0.7rem 1.15rem;
  background: #ffffff;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.notice-card--footer {
  min-width: 0;
  padding: 0.55rem 0.7rem;

  strong {
    margin-bottom: 0.08rem;
  }

  p {
    font-size: 0.7rem;
    line-height: 1.35;
  }
}

.help-footer-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.55rem;
}

.btn {
  min-height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  padding: 0.55rem 0.9rem;
  border-radius: 9px;
  font-size: 0.78rem;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  transition: filter 150ms ease, transform 150ms ease;

  &:hover {
    filter: brightness(0.98);
    transform: translateY(-1px);
  }

  &:focus-visible {
    outline: 3px solid rgba(20, 184, 166, 0.25);
    outline-offset: 2px;
  }
}

.btn-secondary {
  color: #475569;
  background: #f8fafc;
  border: 1px solid #cbd5e1;
}

.btn-primary {
  color: #ffffff;
  background: #0f766e;
  border: 1px solid #0f766e;
}

.btn-donate {
  color: #92400e;
  background: #fef9c3;
  border: 1px solid #fde68a;
}

.page-enter-active,
.page-leave-active {
  transition: opacity 140ms ease, transform 140ms ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateX(8px);
}

.page-leave-to {
  opacity: 0;
  transform: translateX(-8px);
}

@media (max-width: 720px) {
  .help-overlay {
    padding: 0;
  }

  .help-dialog {
    width: 100%;
    max-height: 100dvh;
    min-height: 100dvh;
    border: 0;
    border-radius: 0;
  }

  .help-body {
    padding: 1rem;
  }

  .feature-grid,
  .detail-sections {
    grid-template-columns: 1fr;
  }

  .section-hint {
    display: none;
  }

  .about-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .detail-intro {
    flex-direction: column;
  }
}

@media (max-width: 520px) {
  .help-header {
    grid-template-columns: 38px minmax(0, 1fr) 38px;
    padding-inline: 0.75rem;
  }

  .header-icon {
    display: none;
  }

  .help-footer {
    grid-template-columns: 1fr;
    padding: 0.75rem;
  }

  .help-footer-actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .notice-card--footer p {
    font-size: 0.66rem;
  }

  .about-grid {
    grid-template-columns: 1fr;
  }

  .feature-card {
    grid-template-columns: 38px minmax(0, 1fr) 28px;
  }

  .feature-icon {
    width: 38px;
    height: 38px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .feature-card,
  .more-arrow,
  .header-action,
  .btn,
  .page-enter-active,
  .page-leave-active {
    transition: none;
  }
}
</style>
