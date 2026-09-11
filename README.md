# 🏪 KickerKasse (Test Environment)

Webbasierte Kassensoftware für Vereine mit Kassenbetrieb, Mitgliederverwaltung, Gutschein-/Verzehrkartensystem, Z-Bon-Abschluss und rollenbasiertem Admin-Bereich.
Diese Repository-Variante ist als **Test-/Entwicklungsumgebung** gedacht und nutzt eigene Docker-Projektnamen/Ports für den Parallelbetrieb neben `KickerKasse` (ohne `-Test`).

Aktueller Stand: **Version 2.7.0**

## 🚀 Quick Start mit Docker

```bash
cp .env.example .env
# .env bearbeiten: Datenbankzugang und individuellen SECRET_KEY setzen.
docker compose up -d --build
```

In PowerShell zum Kopieren `Copy-Item .env.example .env` verwenden. Eine vorhandene `.env` beibehalten; Details für bestehende Installationen stehen unten bei „Updates und Migrationen“.

Danach:

- Frontend öffnen: http://localhost:9690
- Beim ersten Start richtet man den **TopAdmin** über den Setup-Flow ein
- Für den schnellen Kassenstart steht zusätzlich der versteckte Benutzer **„Kasse“** über den Button **„Kasse anmelden“** bereit

## 🧩 Kernfunktionen

### Kasse
- Verkauf über auswählbare, zentral bereitgestellte Kassenansichten
- Kategorien, Produktbilder und variable Preise
- Zahlungsarten **Bar** und **Mitgliedsguthaben**
- Einlösung von **Geschenk-Gutscheinen** und **Verzehrkarten**
- Deckel-Verwaltung direkt aus der Kasse
- Erfassung von internem Material mit Notiz
- Bon-/Belegnummern und laufende Warenkorb-Ansicht

#### Verbindliche Preislogik

- **Festpreisartikel:** Das Backend verwendet immer den gespeicherten Produktpreis. Ein vom Client abweichend gesendeter Preis wird nicht übernommen.
- **Mitgliedspreis:** Er gilt nur bei ausgewähltem rabattberechtigtem Mitglied, rabattfähigem Artikel und konfiguriertem Mitgliedspreis. Auch **0,00 €** ist ein gültiger Mitgliedspreis.
- **Variabler Preis:** Der Preis wird im Kassiervorgang eingegeben und serverseitig genau für diesen Verkauf bzw. die neue Deckelposition übernommen. Das ist für Spenden, MHD-Rabatte und vergleichbare Ad-hoc-Preise vorgesehen.
- **Internes Material:** Wird bei Auswahl über die reservierte Kategorie `Verbrauchsmaterial - Intern` mit **0,00 €** verkauft. Der konfigurierte reguläre bzw. berechtigte Mitgliedspreis wird ausschließlich als Wert im Materialkonto erfasst.
- Ein positiver Barzahlbetrag benötigt immer einen übermittelten gegebenen Barbetrag; ein echter 0-Euro-Vorgang ist ohne Bargeld zulässig.

Die vollständige fachliche Testmatrix mit Zahlwegen sowie Hauptkassen- und Lageröffnungen steht in [Buchungswege.md](./Buchungswege.md).

### Mitglieder
- Mitglieder anlegen, bearbeiten und optional mit Systemzugang verknüpfen
- Rabattberechtigung pro Mitglied
- Guthaben aufladen
- Mitgliedsfotos verwalten
- Rollenvergabe an Mitglieder durch den TopAdmin

### Produkte & Kategorien
- Produkte anlegen, bearbeiten, eindeutig deaktivieren und über den Statusfilter reaktivieren
- Lagerbestand und unbegrenzter Bestand
- Produktbilder inkl. Originalbild-Reset-Pfad
- Kategorien direkt am Produkt zur Strukturierung der Kasse; Warengruppen als getrenntes Auswertungsmerkmal

### Gutscheine & Verzehrkarten
- Geschenk-Gutscheine mit Grund erfassen
- Verzehrkarten in Serie vorbereiten
- Gutscheinverwaltung mit Status, Filter und serverseitigem CSV-Gesamtexport einschließlich Anfangs-/Restwert sowie Verkaufs-/Einlösungsbezug
- Vereinskonto / Gutscheinkonto für Gutscheinverluste
- Automatische Produktanlage für Verzehrkartenwerte

### Finanzen & Z-Bon
- Revisionssicherer **Z-Bon** über alle Transaktionen seit dem letzten Z-Bon
- Centgenaue, gemeinsame Berechnung für Finanzansicht, Vorschau, Abschluss, HTML, PDF und E-Mail
- Z-Bon Vorschau sowie HTML- und optionaler PDF-Export
- Z-Bon-Verlauf mit gespeicherten Abschlüssen
- Abschöpfungen und Kassenzählung
- Umsatz-, Mitglieder- und interne Konten-Ansichten (rollenabhängig)
- Materialkonto für interne Warenbewegungen
- Serverseitig gefilterte und paginierte Materialtransaktionsliste mit konsistenten Mengen-, Wert- und Trefferzahlen
- Export der gefilterten regulären Transaktionshistorie: zuerst HTML-Vorschau im Dialog, danach CSV- oder PDF-Download
- Schreibgeschützter Konsistenzbericht für historische Z-Bons unter `GET /api/transactions/zbon/audit`

### Gästeliste
- Produktübergreifende, serverseitig gefilterte und paginierte Liste im Admin-Bereich
- Datum und Uhrzeit, vollständiger Gastname, Gastgeber, Produkt/Anlass und Belegnummer auf einen Blick
- Suche über Gast, Gastgeber, Produkt und Beleg sowie Produkt- und Zeitraumfilter; Ladefehler können direkt erneut geladen werden

#### Verbindliche Kassenformel

Der im Finanzbereich angezeigte Sollbestand und der Z-Bon verwenden dieselbe Formel:

```text
Kassensoll = Anfangsbestand
           + Barzahlungen für Artikel
           + Bar-Aufladungen von Mitgliedsguthaben
           + Trinkgeld / gespendetes Wechselgeld
           + sonstige Bareinlagen
           - Barentnahmen
```

- Trinkgeld wird als Spende behandelt. Bei Barzahlungen kann ein beliebiger Teil des Rückgelds oder das gesamte Rückgeld gespendet werden; dies gilt auch für Deckel.
- Mitgliedsguthaben-Aufladungen sind Bargeldzufluss in die Kasse und erzeugen zugleich Prepaid-Guthaben auf dem Mitgliedskonto.
- Aufladungen des Vereins-/Gutscheinkontos werden weiterhin außerhalb der Kasse verrechnet und verändern das Kassensoll nicht.
- Es gibt keine Kartenzahlung.
- Der Abschlusszeitraum beginnt nach dem zuletzt erstellten Z-Bon; ein reiner Kalendertagsabschluss ist derzeit nicht aktiv.
- Historische Belege werden nicht automatisch überschrieben. Der Prüfbericht weist sichere Abweichungen aus und kennzeichnet Archive mit unzureichenden Altdaten entsprechend.
- Eine Erweiterung oder Priorisierung der vorhandenen Storno-Logik ist nicht Bestandteil dieses Release-Zyklus.

### Korrekturbuchungen
- Separate, nachvollziehbare Guthaben-Korrekturen für Mitglieder
- Separate, nachvollziehbare Bestands-Korrekturen für Produkte
- Historie mit Altwert, Neuwert, Differenz, Grund und Benutzer

### System & Oberfläche
- Session-basierte Anmeldung
- TopAdmin-Setup beim ersten Start
- Konfigurierbarer App-Name, Farben und Logo
- **Erweiterte Einstellungen** für Kassenansicht und Sitzungszeitlimit
- PWA/Installierbarkeit inklusive Icons und Manifest
- Datenpflege mit Hard-Reset für den TopAdmin
- Lokaler Hardware-Agent mit getrennt adressierbarer Haupt- und Kleinteile-Schublade

### Zweite USB-Schublade als Kleinteile-Lager

Ab Version 1.4.0 kann der lokale Hardware-Agent zwei USB-Seriell-Adapter unterscheiden:

- `main`: bisherige Hauptkassenschublade; öffnet bei einer tatsächlichen Bargeldbewegung
- `small_parts`: zusätzliche Schublade für das Kleinteile-Lager; öffnet bei der Ausgabe oder Einlagerung eines entsprechend markierten Artikels unabhängig von der Zahlungsart

Die Installation legt die persistente Zuordnung unter `/etc/default/kickerkasse-agent` an. Bevorzugt werden stabile Gerätepfade aus `/dev/serial/by-id`:

```text
KICKERKASSE_MAIN_DRAWER_DEVICE=/dev/serial/by-id/...
KICKERKASSE_SMALL_PARTS_DRAWER_DEVICE=/dev/serial/by-id/...
```

Ab Version 1.4.1 kann ein TopAdmin die Zuordnung unter `Admin → Einstellungen → Erweitert → Hardware-Service` direkt auf dem Kassen-PC vornehmen:

1. Beide USB-Adapter anschließen und den lokalen Hardware-Agenten aktualisieren.
2. Den lokalen Konfigurationscode aus dem Installationsassistenten eingeben.
3. Wenn die PWA von einem externen Server geladen wird, zunächst **Diesen Browser mit dem lokalen Agenten verbinden** wählen. Dabei wird ausschließlich der aktuelle PWA-Origin lokal freigegeben.
4. Für Hauptschublade und Kleinteile-Lager jeweils einen Adapter auswählen und über **Auswahl testen** identifizieren.
5. **Zuordnung auf diesem Client speichern** wählen. Die Änderung wird atomar unter `/etc/default/kickerkasse-agent` gespeichert und sofort aktiviert.

Der Browser kommuniziert für Erkennung, Test und Speicherung unmittelbar mit `http://127.0.0.1:8765` auf dem Vereins-PC. Der externe Kickerkasse-Server erhält weder Zugriff auf die USB-Geräte noch den lokalen Konfigurationscode. Dieser Code bleibt im Browser nur bis zum Neuladen der Seite im Arbeitsspeicher und wird nicht serverseitig gespeichert. Die Konfigurationsdatei ist nur für `root` lesbar.

In den Produktdetails aktiviert der Schalter **Kleinteile-Lager** die zusätzliche Öffnung. Das gilt für direkte Verkäufe, die Artikelausgabe auf einen Deckel und positive Bestandskorrekturen. Die technische Entscheidungsmatrix steht in [CD-Open-Logic.md](./CD-Open-Logic.md), die fachlichen End-to-End-Wege in [Buchungswege.md](./Buchungswege.md). Der Agent verhindert, dass beide logischen Schubladen versehentlich demselben Adapter zugeordnet werden. Bestehende Agent-Installationen müssen mit dem aktuellen Installationspaket aktualisiert werden, bevor der Produktschalter praktisch genutzt wird.

## 🔐 Rollen & Berechtigungen

Die vollständige und verbindliche Berechtigungsbeschreibung steht in [User-Auth.md](./User-Auth.md).

Kurzüberblick:

| Rolle | Schwerpunkt |
|---|---|
| Verkauf | Nur Kassenbetrieb |
| Manager | Operativer Admin-Zugriff auf Mitglieder, Produkte, Gutscheine, Gäste-/Materiallisten und Z-Bon |
| Admin | Zusätzliche Verwaltungsrechte inkl. Korrekturbuchungen, Benutzer, Design und direkter Abschöpfung |
| TopAdmin | Systemweite Hoheit inkl. Rollenvergabe, erweiterten Einstellungen und Hard-Reset |

Wichtige aktuelle Abgrenzungen:

- **Korrekturbuchungen**: nur **Admin** oder **TopAdmin**
- **Erweiterte Einstellungen** (Kassenansicht, Sitzungszeitlimit): nur **TopAdmin**
- **Direkte Abschöpfung außerhalb des Z-Bon-Modals**: nur **Admin** oder **TopAdmin**
- **Manager** erreicht den Admin-Bereich direkt aus der Kasse nach erfolgreichem Login

## 🧠 Authentifizierungskonzept

Es gibt zwei Arten von Systemzugängen:

1. **Direkte Benutzerkonten** in der Benutzerverwaltung
2. **Mitglieder mit verknüpftem Benutzerkonto**, sofern ihnen durch den TopAdmin eine Rolle vergeben wurde

Zusätzlich existiert der versteckte Systembenutzer **Kasse** für den direkten Start des Verkaufsmodus.

## 📁 Projektstruktur

```text
.
├── backend/                        # FastAPI Backend
│   ├── app/
│   │   ├── api/                    # REST-Endpunkte
│   │   ├── core/                   # DB, Auth, Security, Migrationen
│   │   ├── models/                 # SQLAlchemy-Modelle
│   │   ├── repositories/           # Datenzugriff
│   │   ├── schemas/                # Pydantic-Schemas
│   │   ├── services/               # Business-Logik
│   │   └── templates/              # Z-Bon-HTML-Templates
│   ├── Dockerfile
│   ├── docker-entrypoint.sh
│   ├── main.py
│   ├── requirements.txt
│   └── uploads/                    # Produktbilder / Vereinslogo (persistent)
├── frontend/                       # Vue 3 + Pinia + Vite
│   ├── src/
│   │   ├── components/             # Wiederverwendbare UI-Komponenten
│   │   ├── stores/                 # Pinia State-Management
│   │   ├── views/                  # Seiten (Admin + Kasse)
│   │   ├── services/               # API-Kommunikation
│   │   ├── router/                 # Vue Router Konfiguration
│   │   ├── styles/                 # Globale SCSS-Stylesheets
│   │   └── constants.js
│   └── public/                     # PWA-Icons, Manifest
├── .env.example                    # Vorlage für Umgebungsvariablen
├── docker-compose.yml              # Deployment-Konfiguration
├── docker-init-db.sh               # Postgres-Initialisierungsskript
├── start.ps1                       # Windows-Startskript
├── User-Auth.md                    # Verbindliche Rollenbeschreibung
├── Buchungswege.md                # Testmatrix für Preise, Zahlungen und Schubladen
└── README.md
```

## 🛠️ Tech-Stack

| Komponente | Technologie |
|---|---|
| Frontend | Vue 3, Vue Router, Pinia, Vite |
| Backend | FastAPI, SQLAlchemy |
| Datenbank | PostgreSQL |
| Styling | SCSS |
| Deployment | Docker Compose |
| App-Modus | PWA |

## 🚦 Inbetriebnahme und Vorbereitung

### Schritt 1 – Voraussetzungen

| Voraussetzung | Mindestversion |
|---|---|
| Docker | 24+ |
| Docker Compose | 2.20+ |

Ein lokal installiertes Node.js oder Python ist für den **Docker-Betrieb nicht notwendig** – alle Abhängigkeiten sind im Container enthalten.

### Schritt 2 – Umgebungsvariablen konfigurieren

```bash
cp .env.example .env
```

Passe folgende Werte in `.env` an:

| Variable | Bedeutung | Empfehlung |
|---|---|---|
| `SECRET_KEY` | Session-Verschlüsselungsschlüssel | Mindestens 32 zufällige Zeichen, **unbedingt ändern!** |
| `DATABASE_PASSWORD` | Passwort für die Postgres-Datenbank | Sicheres Passwort setzen |
| `DATABASE_USER` / `DATABASE_NAME` | Datenbankbenutzer und Datenbank | Bei vorhandenen Volumes die bisherigen Werte behalten |
| `APP_BIND_HOST` | Bind-Adresse der Webanwendung | Standard `127.0.0.1`; für bewusste LAN-Freigabe `0.0.0.0` |
| `PRODUCTION` / `COOKIE_SECURE` | Produktionsprüfung / HTTPS-Cookies | Lokal über HTTP beide `false`; hinter HTTPS beide `true` |

Einen Schlüssel erzeugen: `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Ohne lokales Python: `docker run --rm python:3.11-slim python -c "import secrets; print(secrets.token_urlsafe(48))"`. Den Wert als `SECRET_KEY` in `.env` übernehmen; die Datei enthält Zugangsdaten und gehört nicht in ein Repository. Werte mit `$` in `.env` in einfache Anführungszeichen setzen, damit Compose sie nicht interpoliert.

Compose verwendet die konfigurierten Datenbankwerte für beide Dienste. PostgreSQL bleibt ausschließlich unter `127.0.0.1:5434` erreichbar. Die Anwendung bindet standardmäßig ebenfalls nur lokal. Das Beispiel ist eine Testkonfiguration; TLS und Reverse Proxy sind darin nicht enthalten. Im Produktionsmodus verweigert die Anwendung den Start bei Platzhalterschlüssel, weniger als 32 Schlüsselzeichen oder deaktivierten sicheren Cookies. `COOKIE_SECURE=true` benötigt eine HTTPS-Verbindung im Browser.

### Schritt 3 – Anwendung starten

```bash
docker compose up -d
```

Docker lädt die nötigen Images, baut das Frontend, startet PostgreSQL und das Backend.
Die App ist danach unter **http://localhost:9690** erreichbar.

> Standardports in dieser Test-Umgebung: `9690` (App) und `5434` (PostgreSQL). Diese können über `APP_PORT_TEST` und `DB_PORT_TEST` angepasst werden (z. B. per `.env` oder Shell-Variablen vor `docker compose up -d`).

### Schritt 4 – TopAdmin einrichten (Erststart)

Beim **allerersten Start** existiert noch kein Admin-Konto.  
Rufe die Anwendung im Browser auf – du wirst automatisch in den **Setup-Flow** geleitet:

1. Vollständigen Namen für den TopAdmin eingeben
2. Benutzernamen und sicheres Passwort festlegen
3. Einrichtung abschließen → TopAdmin ist aktiv

### Schritt 5 – Grunddaten anlegen (empfohlen vor dem ersten Kasseneinsatz)

Im Admin-Bereich sollten folgende Grunddaten zuerst eingerichtet werden:

1. **Design & App-Name** (`Verwaltung → Einstellungen → Design`): Vereinslogo hochladen, App-Name und Farben anpassen
2. **Kategorien** (`Verwaltung → Kategorien`): Produktkategorien für das Kassenlayout anlegen
3. **Produkte** (`Verwaltung → Produkte`): Artikel mit Preisen, Bildern und Lagerbestand erfassen
4. **Mitglieder** (`Verwaltung → Mitglieder`): Mitglieder anlegen, optional Benutzerkonten und Rollen vergeben
5. **Kassenansicht & Sitzungszeitlimit** (`Verwaltung → Einstellungen → Erweitert`): Ansicht wählen und automatische Abmeldung konfigurieren

### Schritt 6 – Erster Kassenbetrieb

- Kassenbenutzer: Über den Button **„Kasse anmelden"** auf der Login-Seite startet der Kassenbetrieb ohne persönlichen Login
- Verwaltungsbenutzer: Mit persönlichem Konto anmelden → automatische Weiterleitung in die Verwaltung
- Kassenbericht: Am Schichtenende unter `Verwaltung → Finanzen` den Kassenbericht erstellen und ggf. exportieren

---

## 🐳 Betrieb mit Docker

### Starten
```bash
docker compose up -d
```

### Logs ansehen
```bash
docker compose logs -f kassensoftware
```

### Stoppen
```bash
docker compose down
```

### Deckel, Gutscheine und Gäste ab 1.6.9–1.6.11

- Frontend und Backend gemeinsam aktualisieren und offene Kassenansichten neu laden. Migration 1.6.10 erweitert `transactions.voucher_code` auf Text und ergänzt `voucher_redemptions`; 1.6.11 ergänzt `guest_list_entries.transaction_item_id`. Vorherige Codes und Gäste bleiben erhalten; historische Einzelbeträge und Gastpositionen werden nicht nachträglich geschätzt.
- Deckel werden ausschließlich bar bezahlt. Mitgliedsauswahl, angewendete Gutscheine/Guthaben, Gäste und Verzehrkarten gehören in den direkten Verkauf. Reguläre Artikel, variable Preise und internes Material sind auf Deckel weiterhin möglich. Nicht unterstützte historische Deckel müssen vor der Abrechnung fachlich geklärt werden.
- Deckelzahlung und Gutscheinerstellung speichern die jeweils zusammengehörenden Daten mit einem Commit. Parallele Zahlung desselben Deckels erzeugt nur eine Buchung. Die allgemeine Belegnummern- und Wiederholungsabsicherung bleibt Gegenstand der weiteren Etappen.
- Gäste stehen an der jeweiligen Bonposition: bei variablen Artikeln zuerst den Preis, dann den Namen eingeben. Namen sind vor der Zahlung sichtbar; bei einer Mengenerhöhung wird eine neue Gastangabe angefordert. Der Verkauf speichert Gäste, Zahlungsdaten und Bestand gemeinsam. Der frühere separate POST-Endpunkt `/api/guest-list/entries` ist geschlossen; GET und Gastübersicht bleiben verfügbar.
- Neue Gutscheineinlösungen enthalten eine Einzelzuordnung je Beleg und Gutschein einschließlich Teilbetrag. Derselbe Gutschein kann nicht zweimal über unterschiedliche Schreibweisen in denselben Bon aufgenommen werden.
- Abnahme und persönliche Live-Test-Schritte stehen im Etappenprotokoll 1.6.9–1.6.11 der `Projektpruefung-2026-09-06.md`.

### Zugang und Aufladung ab 1.6.7 / 1.6.8

- Frontend und Backend gemeinsam aktualisieren. Die automatische Migration ergänzt `users.session_version`, `auth_rate_limits` und erweitert `audit_logs.action`. Nach dem Update einmal neu anmelden; vorhandene Cookies ohne Sitzungsfassung werden abgelehnt.
- Passwortänderungen, erfolgreiche Resets, Rollenwechsel und Deaktivierungen widerrufen alle vorherigen Sitzungen des betroffenen Kontos sowie offene Resetlinks. Das gilt auch für verknüpfte Mitgliedskonten. Reaktivieren macht alte Sitzungen nicht wieder gültig. Eine bereits geladene Seite wird beim nächsten geschützten API-Aufruf zur Anmeldung zurückgeführt.
- Der TopAdmin-Reset ist direkt auf der Loginseite erreichbar. Für echte Resetmails müssen die vorhandenen SMTP-Einstellungen vollständig eingerichtet sein. Login- und Resetlimits sowie Hinweise für Reverse-Proxys stehen in `User-Auth.md`.
- Neue Aufladungen speichern Guthaben, Bartransaktion, Guthabenlog und Audit gemeinsam. Bei einem Fehler bleibt keine Teilaufladung bestehen. Historische Aufladungen werden nicht automatisch nachträglich zugeordnet. Sichere Wiederholung nach einem unklaren Netzwerkergebnis bleibt Aufgabe 11.
- Abnahme und offene persönliche Live-Tests: `Projektpruefung-2026-09-06.md`, Etappenprotokoll 1.6.7/1.6.8.

### Updates und Migrationen ab 1.6.5 / 1.6.6

1. Vor dem Upgrade Datenbank und Uploads sichern und die Wiederherstellung auf einer Testkopie prüfen. Frontend und Backend gemeinsam aktualisieren.
2. Bestehende `.env` ergänzen. Bei einem bisherigen unveränderten Test-Volume bleiben Benutzer, Passwort und Datenbank zunächst `kassensystem-test`. Ein geändertes `.env`-Passwort ändert **kein** Passwort innerhalb eines bereits initialisierten PostgreSQL-Volumes; eine Rotation muss separat in PostgreSQL durchgeführt werden. Volume- und Projektnamen bleiben unverändert. Das Setzen eines neuen `SECRET_KEY` beendet bestehende Anmeldungen.
3. `docker compose config --quiet` und `docker compose up -d --build` ausführen. Mit `docker compose logs -f kassensoftware` den erfolgreichen Start prüfen. Der Build stoppt bei Installationsfehlern.
4. Migrationen werden unter einer PostgreSQL-Sperre ausgeführt. `schema_migrations` dokumentiert Version, erfolgreich abgeschlossenen Schritt und Zeitpunkt. Ein fehlgeschlagener Schritt wird nicht als erledigt eingetragen; nach Klärung setzt ein Neustart dort fort. Bereits bestätigte ältere Teilschritte können bestehen bleiben. Die Prüfung von Tabellen, Spalten, Typen, Enumwerten und neuen Constraints läuft bei jedem Start; ein Fehler verhindert den Appstart auch bei lokaler Python-Ausführung.
5. Version 1.6.6 prüft vorhandene Produkt-, Mitglieder- und Kategoriedaten vor neuen Constraints. Ungültige Werte werden mit Regel und bis zu 20 IDs je Regel gemeldet. Salden oder Mengen werden **nicht** automatisch auf null gesetzt. Betroffene Daten zuerst auf der gesicherten Kopie fachlich klären und nachvollziehbar korrigieren, dann erneut starten. Das Migrationsjournal nicht löschen, um Fehler zu umgehen. Ein Rückwechsel zu altem Code entfernt die neuen Constraints nicht; für einen vollständigen Rückweg die Sicherung wiederherstellen.

Die neue Stammdatenvalidierung erlaubt Centbeträge und Mengen von 0 bis 2.147.483.647; optionale Mitgliedspreise dürfen leer oder 0 sein. Namen werden getrimmt, Pflichtfelder dürfen nicht leer oder explizit `null` sein. Beschreibung maximal 255 Zeichen, Produkt-/Kategoriename maximal 120, Mitglieder-Vor-/Nachname jeweils maximal 80 und zusammen maximal 120 Zeichen einschließlich Leerzeichen; E-Mail maximal 120, Telefon maximal 20 Zeichen. Imports verwenden dieselben Regeln und prüfen die gesamte Auswahl vor dem Schreiben. Import-Konfliktauflösung und vollständige Medienwiederherstellung bleiben eigene Aufgaben.

Produktbearbeitung verändert keine Bestandsmenge. Einlagerungen müssen positiv sein; Abgänge außerhalb eines Verkaufs gehören in die Admin-Bestandskorrektur. Ein Wechsel zwischen begrenztem und unbegrenztem Bestand erfordert Bestand 0 und wird protokolliert. Bei unbegrenzten Produkten zuerst auf begrenzt umstellen, danach einlagern. Der im geöffneten Formular angezeigte Bestand ist eine Momentaufnahme und wird beim Speichern nicht zurückgeschrieben.

### Datenbank zurücksetzen
```bash
docker compose down -v
docker compose up -d
```

## 💻 Lokale Entwicklung

### Backend

Die `.env` im Projektstamm wird auch bei Ausführung aus `backend` geladen. Für eine lokale Datenbank aus Compose zuerst `docker compose up -d postgres` im Projektstamm ausführen. Der lokale Standard ist `127.0.0.1:5434`; bei anderem veröffentlichten Port auch `DATABASE_PORT` anpassen. Eine explizite `DATABASE_URL` hat für lokale Python-Ausführung Vorrang. Unterstützte PostgreSQL-URLs werden auf den installierten Treiber `postgresql+psycopg2` normalisiert; innerhalb von Compose gelten die getrennten Variablen mit internem Host `postgres` und Port `5432`.

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Benötigte Dienste
- PostgreSQL für das Backend
- Browser mit aktivierten Cookies für Sessions

## ✅ Validierung

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

Backend:

```bash
cd backend
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest
```

Die Standardsuite verwendet isoliertes SQLite und benötigt keinen laufenden Datenbankserver. PostgreSQL-Integrationstests sind standardmäßig übersprungen. Für diese Tests `TEST_POSTGRES_URL` auf einen **separaten Testserver** mit `CREATEDB`-Berechtigung setzen und `python -m pytest tests/test_postgres_migrations.py` ausführen. Jeder Test erstellt eine eigene Datenbank mit zufälligem Namen `kickerkasse_pytest_*` und entfernt ausschließlich diese anschließend. Geprüft werden Neuinstallation, ältere Schemata, Migrationsteilfehler und Wiederholung, ungültige Altdaten, Schemadrift sowie paralleler Start und Einlagerungen.

## 🔒 Sicherheitsmerkmale

- Passwort-Hashing mit bcrypt
- Session-Cookies statt Token im Frontend
- Rollen- und Endpoint-basierte Zugriffskontrolle
- Passwort-/Credential-Bestätigung für kritische Aktionen
- Revisionsfähige Historien für Guthaben-, Bestands- und Z-Bon-relevante Vorgänge

## 📚 Weitere Dokumentation

- [User-Auth.md](./User-Auth.md) – verbindliche Rollen- und Rechteübersicht

## 🧯 Troubleshooting

### Frontend-Build oder Lint schlägt fehl
```bash
cd frontend
npm install
npm run lint
npm run build
```

### Backend erreicht die Datenbank nicht
- PostgreSQL läuft nicht oder ist unter `DATABASE_URL` nicht erreichbar
- Zugangsdaten in `.env` prüfen
- Container-/Host-Port prüfen

### Session-Probleme im Browser
- Cookies erlauben
- Browser-Cache leeren
- erneut anmelden

### Kassenabschluss und Wiederholung ab 1.6.12–1.6.13

- Frontend und Backend gemeinsam aktualisieren. Migrationen ergänzen einen gemeinsamen, transaktionalen Belegzähler, die feste Z-Bon-Zuordnung von Verkäufen/Einlagen/Entnahmen und das Vorgangsjournal. Vorhandene Belegnummern und archivierte Berichte bleiben erhalten. Frühere Buchungen werden anhand der bisherigen Abschlussgrenzen zugeordnet; spätere Abschlüsse verwenden die feste Zuordnung. Eine im Warenkorb angezeigte Nummer ist nur vorläufig.
- Der Abschluss übernimmt Ersteller aus den berechtigten Finanzpersonen (`user-…`/`member-…`) und Prüfer aus bestehenden Mitgliedern. Die API akzeptiert hierfür IDs statt freier Namen. Ein prüfendes Mitglied benötigt wie bisher keinen eigenen Finanzzugang. Namen werden serverseitig als Berichtssnapshot gespeichert. Zählwerte müssen centgenau sein; Stückzahlen ganzzahlig und nichtnegativ. Abweichungen benötigen eine Begründung.
- Buchungs-POSTs für Verkauf, Guthabenaufladung, Deckel, Gutscheine, Einlage/Entnahme und Abschluss erhalten im aktuellen Frontend eine UUID im Header `Idempotency-Key`. Die Buchung und ihre vollständige Antwort werden zusammen bestätigt. Gleiche Kennung und gleicher Inhalt liefern denselben Beleg; anderer Inhalt oder anderer Benutzer wird abgewiesen. `GET /api/transactions/operations/{kennung}` liefert nur dem ursprünglichen Benutzer das bestätigte Ergebnis.
- Bei einem Verbindungsabbruch die Buchung unverändert erneut bestätigen. Das Frontend prüft zuerst den Status und sendet nur bei noch fehlender Bestätigung dieselbe Kennung erneut. Der Hinweis „Buchung noch nicht bestätigt“ bietet zusätzlich eine Statusprüfung. Bestätigte Ergebnisse lösen beim Wiederabruf keinen weiteren Schubladenimpuls aus.
- Offene Kennungen bleiben benutzerbezogen im Sitzungsspeicher desselben Browser-Tabs erhalten, auch beim Neuladen. Dort werden keine Passwörter oder Buchungsinhalte gespeichert. Den Tab bei ungeklärtem Ausgang offen lassen; ein geschlossener Tab oder ein anderes Gerät übernimmt diese lokalen Kennungen nicht. Alte Clients ohne Header besitzen keinen Wiederholungsschutz und müssen aktualisiert werden.
- Etappe 10 bleibt auf ausdrücklichen Wunsch zurückgestellt. Die gemeinsame Abschlusskoordination ersetzt keine allgemeine Prüfung aller in dieser Etappe aufgeführten Parallelitätsszenarien.

### Historie und Mitgliederarchiv ab 1.6.14

Neue Buchungspositionen halten Warengruppe, Kategorie, Steuersatz und Materialwert zusätzlich zum Produktnamen fest. Kunden-/Kassierernamen werden bei der Buchung übernommen. Historische Auswertungen verwenden diese Werte. Für ältere Positionen fehlen manche Angaben; sie erscheinen als „Altbestand – … unbekannt“ und werden nicht mit heutigen Stammdaten ergänzt. Bereits archivierte Z-Bons werden nicht verändert.

„Archivieren“ in der Mitgliederverwaltung erhält Mitglied, Fotos und sämtliche Buchungs-, Guthaben-, Korrektur- und Gastreferenzen. Restguthaben blockiert die Archivierung und muss zuerst über die vorgesehenen, dokumentierten Wege geklärt werden. Archivierte Mitglieder sind nicht mehr für neue Verkäufe, Gäste oder Aufladungen auswählbar. Über „Archivierte Mitglieder anzeigen“ können Admins sie wiederherstellen; ein deaktivierter Systemzugang bleibt dabei deaktiviert. Mitglieder mit Systemzugang darf nur der Top-Admin archivieren/wiederherstellen; der geschützte Top-Admin selbst wird nicht archiviert.

Der bestehende DELETE-Endpunkt `/api/members/{id}` archiviert nun, statt den Datensatz physisch zu löschen. `GET /api/members?include_archived=true` ergänzt archivierte Profile für berechtigte Verwaltungsnutzer; `POST /api/members/{id}/restore` stellt ein Mitglied wieder her. Mitgliedsnummern bleiben reserviert. Migration 1.6.14 ist wiederholbar und ergänzt die benötigten Felder, ohne historische Snapshots zu schätzen.


### Vollständige Sicherung ab 2.0.0 (Etappe 15)

Die TopAdmin-Sicherung enthält Datenbank und den gesamten Upload-Bestand einschließlich Originalbildern, Mitgliederfotos, Logo und generierten Icons. Das Manifest beschreibt Tabellen, Spalten, Schlüssel, Regeln, Indizes, Enumwerte und Migrationsstand. Die Datei enthält auch Kontodaten und SMTP-Konfiguration und gehört in die geschützte Datensicherung. Fest installierte Programmdateien und Umgebungsvariablen sind weiterhin Bestandteil der Installation, nicht der Datensicherung.

Restore setzt eine gestartete PostgreSQL-Installation mit demselben Schema/Migrationsstand voraus. Leere Zielinstanzen zuerst mit derselben Anwendung initialisieren. Es gelten 256 MiB ZIP, 512 MiB entpackt, 128 MiB `backup.json` und maximal 10.000 ZIP-Einträge. Teilarchive und v1-Dateien sind nicht direkt einspielbar: Eine alte Sicherung mit ihrer damaligen Version isoliert wiederherstellen, zugehörige alte Medien ergänzen, die Instanz aktualisieren und anschließend eine vollständige v2-Sicherung erstellen. Ohne alte Medien ist ein vollständiger historischer Medienbestand nicht rekonstruierbar.

Export und Restore benötigen eine kurze Zugriffspause. Eine aktive Anfrage verhindert den Start mit HTTP 503; während der Datenpflege werden andere API-Zugriffe mit Wiederholungshinweis abgewiesen. Es erfolgt keine automatische Wiederholung einer Buchung. Alle Worker müssen denselben aktualisierten Code, dieselbe PostgreSQL-Datenbank und dasselbe Upload-Volume nutzen.

Beim Restore werden Daten zuerst in temporären PostgreSQL-Tabellen geprüft. Danach folgen Datenbank- und Medienaustausch sowie ein gemeinsamer Datenbank-/Audit-Commit. Das Upload-Verzeichnis selbst wird nicht umbenannt und bleibt mit Docker-Bind-Mounts verwendbar. Bei einem Fehler werden die alten Daten/Medien wiederhergestellt. Bei einem Prozessabbruch bleibt `.restore-state.json` mit den vorbereiteten Medien im Upload-Volume liegen. Der nächste Start entscheidet anhand des gespeicherten Auditmarkers, welche Generation gültig ist. Wenn diese Wiederanlaufprüfung scheitert, startet die Anwendung nicht; Journal und `.restore-*`-Verzeichnisse bis zur Klärung erhalten. Vollständig vorbereitete Medien benötigen vorübergehend zusätzlichen freien Speicher für alte und neue Dateien. Ein einzelner Worker-Neustart ist keine Freigabe für parallelen Betrieb verschiedener Anwendungsversionen.

Nach erfolgreichem Restore müssen sich alle Benutzer neu anmelden; vorherige Resetlinks sind ungültig. Der Scheduler wird neu geladen. Der API-Pfad für Export/Restore bleibt gleich, das Dateiformat ist bewusst inkompatibel; deshalb SemVer **2.0.0** nach Auditkorrektur **1.6.15**.

**Prüfstatus:** Etappen 14 und 15 sind implementiert, aber auf Nutzerwunsch nicht technisch geprüft. Die neuen Testdateien und die gemeinsame spätere Abnahmeliste stehen in `Projektpruefung-2026-09-06.md`. Bestehende Testergebnisse bis 1.6.14 gelten nicht als Nachweis für diese Änderungen.


### Hardware-Rückmeldungen und Mail-Automatik ab 2.3.0 (Etappen 18/19)

Nach einer gespeicherten Verkaufs- oder Deckelbuchung wertet die Kasse jedes vom Server angeforderte Schubladenziel einzeln aus. Schlägt der lokale Hardwareimpuls fehl, bleibt die Buchung erfolgreich und eine zehn Sekunden sichtbare Warnung nennt „Hauptschublade“ beziehungsweise „Kleinteile-Lager“. Der Hinweis fordert zur manuellen Prüfung auf; ein erneuter Verkauf ist keine Fehlerbehebung. Im Adminbereich werden Erreichbarkeit und Verbindungszustand zusätzlich ausgeschrieben.

Automatische Lagerwarnungen besitzen einen eigenen Schedulerjob und eine eigene Prüfzeit. Sie funktionieren bei deaktivierter Kassenbericht-Automatik, solange der allgemeine E-Mail-Versand und die Lagerwarnung aktiviert sind. Ein eigener Lagerempfänger wird bevorzugt; andernfalls gilt weiterhin der Kassenbericht-Empfänger. Ohne kritische Artikel wird der Lauf nachvollziehbar als „keine Mail erforderlich“ gespeichert.

Der automatische Kassenbericht ist ausdrücklich als Bericht für den Vortag bezeichnet und ermittelt diesen Tag in der konfigurierten Anwendungszeitzone. Letzter Zeitpunkt, Ergebnis, Meldung und Berichtstag des Kassenberichtlaufs sowie Zeitpunkt, Ergebnis und Meldung der Lagerprüfung werden dauerhaft gespeichert und nach einem Neuladen in der E-Mail-Konfiguration angezeigt. Migration 2.3.0 ergänzt diese Felder und die Lagerprüfzeit wiederholbar.

**Abnahme offen:** `backend/tests/test_stage19_mail_automation.py`, `frontend/tests/hardware-feedback.test.js` und die gemeinsame Hardware-/Mail-Abnahmeliste in `Projektpruefung-2026-09-06.md` sind nur hinterlegt. Auf Nutzerwunsch wurden keine Tests, Builds, Lint-, Docker-, Hardware-, Mail- oder Browserprüfungen ausgeführt.


### Verlässlicher Verkauf und Erststart ab 2.2.0 (Etappe 17)

Beim ersten Aufruf wird eine vorhandene Serversitzung geprüft und nicht mehr vorsorglich beendet. Ohne TopAdmin meldet der unabhängige Setup-Status sofort den Erststart und öffnet den Einrichtungsdialog. Vorübergehend noch nicht verfügbare öffentliche Einstellungen verhindern das Rendern der Loginseite nicht; der Status wird wiederholt und kann sichtbar erneut angefordert werden. Der TopAdmin wird weiterhin ausschließlich mit den im Initial-Setup eingegebenen Zugangsdaten angelegt.

Offene Warenkörbe einschließlich Kunden-, Gutschein-, Guthaben- und Barzahlungsdaten bleiben beim Neuladen im Sitzungsspeicher erhalten. Jeder Entwurf gehört zu seiner Benutzer-ID; ein Benutzerwechsel leert die sichtbare Kasse und stellt nur den eigenen Entwurf wieder her. Das Sitzungszeitlimit warnt vor dem Ablauf und meldet bei einem offenen Bon nicht automatisch ab. PWA-Updates werden angezeigt und erst ohne offenen Bon auf ausdrückliche Aktion aktiviert.

Der Verkauf sendet den angezeigten Gesamtbetrag und gegebenenfalls den gesehenen Mitgliedssaldo als Bestätigungsstand. Weichen die unter Sperre ermittelten Serverwerte ab, erfolgt keine Buchung; die Kasse übernimmt die aktuellen Preise und verlangt eine neue Bestätigung. Nach Erfolg bleibt der letzte serverbestätigte Beleg mit Endbetrag, gegebenem Bargeld und Rückgeld sichtbar. Diese Anzeige löst keinen weiteren Buchungsaufruf aus.

**Abnahme offen:** Die Regressionen in `backend/tests/test_stage17_reliability.py` und die gemeinsame Browser-/PWA-/PostgreSQL-Liste in `Projektpruefung-2026-09-06.md` sind nur hinterlegt. Auf Nutzerwunsch wurden keine Tests, Builds, Lint-, Docker- oder Browserprüfungen ausgeführt. Keine neue Datenbankmigration.


### Sicherer Stammdatentransfer ab 2.1.0 (Etappe 16)

Der Transferdialog zeigt vor dem Import je Zeile die geplante Aktion und Konflikte. Standard ist **Fremde Datenquelle**: Quell-IDs und interne Mitgliedsnummern werden nicht zur Zuordnung bestehender Datensätze verwendet. Neue Datensätze erhalten lokale IDs. Bereits vorhandene fachliche Schlüssel werden als Konflikt gemeldet. **Gleiche Installation** ist bewusst zu wählen; Aktualisierungen erfordern eine passende ID und denselben Namen. Umbenennungen und Konflikte sind vorab in der Mitglieder-/Produktverwaltung oder in der Quelldatei zu klären. Feste Systemkategorien bleiben erhalten und werden nicht überschrieben.

Bestehende Guthaben, Lagerbestände und Bestandsarten lassen sich nicht durch Import ändern. Verknüpfte Mitgliedskonten und Änderungen des Archivstatus gehören in die Mitgliederverwaltung. Beim Ersetzen schützen sämtliche im Modell definierten Fremdschlüssel die Historien, offenen Deckel, Gäste, Gutscheine und Kontobeziehungen. Kategorien mit verbleibenden Produktzuordnungen, Mitglieder mit Guthaben/Rolle und Produkte mit Bestand können nicht gelöscht werden. Neue Anfangsguthaben und Anfangsbestände werden in der Vorschau summiert und müssen ausdrücklich bestätigt werden; sie erzeugen keine Baraufladung. Nur der TopAdmin darf importieren; Admin darf weiterhin analysieren und exportieren.

CSV-Vertrag **Transfer-Version 2** ergänzt Mindestbestand, Lagerwarnung, Gastpflicht, Schubladenfunktion und den Mitglieder-Archivstatus. Kategoriezuordnungen werden als JSON-Liste gespeichert, damit Namen mit `|` erhalten bleiben. Legacy-CSV mit der bisherigen Pipe-Liste und ohne Versionsfeld bleibt lesbar; unbekannte Versionen, Spalten, doppelte Schlüssel und fehlende Zuordnungen werden abgewiesen. Konten und Rollen werden bewusst nicht übertragen. Mit Medienauswahl enthält das ZIP das verwendete Hauptbild sowie das Originalbild getrennt, einschließlich AVIF. Nicht mehr verwendete alte Bildvarianten sind kein Bestandteil des Transfers; für den gesamten Upload-Bestand dient das vollständige Backup.

Grenzen: 128 MiB je hochgeladener Datei, 256 MiB entpackt je Archiv, 10.000 ZIP-Einträge beziehungsweise Datensätze je Bereich und 10 MiB je Bild. Export und Import benötigen eine Zugriffspause. Import prüft den aktuellen Datenstand unter Sperre erneut, bereitet Medien im vorhandenen Wiederanlaufverfahren vor und bestätigt Daten mit Abschlussaudit gemeinsam. Bei Konflikten oder Fehlern wird nichts teilweise übernommen. Nach geänderter Quelle/Bereichsauswahl die Vorschau erneut analysieren.

**Abnahme offen:** `backend/tests/test_stage16_transfer.py` ist nur hinterlegt. Auf Nutzerwunsch wurden keine Tests, Builds, Lint-, Docker- oder Browserprüfungen ausgeführt. Die gemeinsame Abschlussliste einschließlich PostgreSQL-Rundlauf, Wiederanlauf, Rollenprüfung und Dialogbedienung steht in `Projektpruefung-2026-09-06.md`. Keine neue Schema-Migration in dieser Etappe.
