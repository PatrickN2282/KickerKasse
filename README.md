# 🏪 KickerKasse

Webbasierte Kassensoftware für Vereine mit Kassenbetrieb, Mitgliederverwaltung, Gutschein-/Verzehrkartensystem, Z-Bon-Abschluss und rollenbasiertem Admin-Bereich.

## 🚀 Quick Start mit Docker

```bash
docker compose up -d
```

Danach:

- Frontend öffnen: http://localhost:8000
- Beim ersten Start richtet man den **TopAdmin** über den Setup-Flow ein
- Für den schnellen Kassenstart steht zusätzlich der versteckte Benutzer **„Kasse“** über den Button **„Kasse anmelden“** bereit

## 🧩 Kernfunktionen

### Kasse
- Verkauf über mehrere Kassenlayouts
- Kategorien, Produktbilder und variable Preise
- Zahlungsarten **Bar** und **Mitgliedsguthaben**
- Einlösung von **Geschenk-Gutscheinen** und **Verzehrkarten**
- Deckel-Verwaltung direkt aus der Kasse
- Erfassung von internem Material mit Notiz
- Bon-/Belegnummern und laufende Warenkorb-Ansicht

### Mitglieder
- Mitglieder anlegen, bearbeiten und optional mit Systemzugang verknüpfen
- Rabattberechtigung pro Mitglied
- Guthaben aufladen
- Mitgliedsfotos verwalten
- Rollenvergabe an Mitglieder durch den TopAdmin

### Produkte & Kategorien
- Produkte anlegen, bearbeiten, deaktivieren und löschen
- Lagerbestand und unbegrenzter Bestand
- Produktbilder inkl. Originalbild-Reset-Pfad
- Kategorien zur Strukturierung der Kasse

### Gutscheine & Verzehrkarten
- Geschenk-Gutscheine mit Grund erfassen
- Verzehrkarten in Serie vorbereiten
- Gutscheinverwaltung mit Status, Filter und CSV-Export
- Vereinskonto / Gutscheinkonto für Gutscheinverluste
- Automatische Produktanlage für Verzehrkartenwerte

### Finanzen & Z-Bon
- Revisionssicherer **Z-Bon** über alle Transaktionen seit dem letzten Z-Bon
- Z-Bon Vorschau und HTML-Export
- Z-Bon-Verlauf mit gespeicherten Abschlüssen
- Abschöpfungen und Kassenzählung
- Umsatz-, Mitglieder- und interne Konten-Ansichten (rollenabhängig)
- Materialkonto für interne Warenbewegungen

### Korrekturbuchungen
- Separate, nachvollziehbare Guthaben-Korrekturen für Mitglieder
- Separate, nachvollziehbare Bestands-Korrekturen für Produkte
- Historie mit Altwert, Neuwert, Differenz, Grund und Benutzer

### System & Oberfläche
- Session-basierte Anmeldung
- TopAdmin-Setup beim ersten Start
- Konfigurierbarer App-Name, Farben und Logo
- **Ext. Settings** für Kassenlayout und Session-Timer
- PWA/Installierbarkeit inklusive Icons und Manifest
- Datenpflege mit Hard-Reset für den TopAdmin

## 🔐 Rollen & Berechtigungen

Die vollständige und verbindliche Berechtigungsbeschreibung steht in [User-Auth.md](./User-Auth.md).

Kurzüberblick:

| Rolle | Schwerpunkt |
|---|---|
| Verkauf | Nur Kassenbetrieb |
| Manager | Operativer Admin-Zugriff auf Mitglieder, Produkte, Gutscheine und Z-Bon |
| Admin | Zusätzliche Verwaltungsrechte inkl. Korrekturbuchungen, Benutzer, Design und direkter Abschöpfung |
| TopAdmin | Systemweite Hoheit inkl. Rollenvergabe, Ext. Settings und Hard-Reset |

Wichtige aktuelle Abgrenzungen:

- **Korrekturbuchungen**: nur **Admin** oder **TopAdmin**
- **Ext. Settings** (Kassenlayout, Session-Timer): nur **TopAdmin**
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

> ⚠️ **Wichtig:** Starte die App niemals produktiv ohne einen individuellen `SECRET_KEY`!

### Schritt 3 – Anwendung starten

```bash
docker compose up -d
```

Docker lädt die nötigen Images, baut das Frontend, startet PostgreSQL und das Backend.
Die App ist danach unter **http://localhost:9190** erreichbar.

> Der Standard-Port ist `9190`. Dieser kann in `docker-compose.yml` unter `ports` angepasst werden.

### Schritt 4 – TopAdmin einrichten (Erststart)

Beim **allerersten Start** existiert noch kein Admin-Konto.  
Rufe die Anwendung im Browser auf – du wirst automatisch in den **Setup-Flow** geleitet:

1. Vollständigen Namen für den TopAdmin eingeben
2. Benutzernamen und sicheres Passwort festlegen
3. Einrichtung abschließen → TopAdmin ist aktiv

### Schritt 5 – Grunddaten anlegen (empfohlen vor dem ersten Kasseneinsatz)

Im Admin-Bereich sollten folgende Grunddaten zuerst eingerichtet werden:

1. **Design & App-Name** (`Admin → Design`): Vereinslogo hochladen, App-Name und Farben anpassen
2. **Kategorien** (`Admin → Kategorien`): Produktkategorien für die Kassenlayouts anlegen
3. **Produkte** (`Admin → Produkte`): Artikel mit Preisen, Bildern und Lagerbestand erfassen
4. **Mitglieder** (`Admin → Mitglieder`): Mitglieder anlegen, optional Benutzerkonten und Rollen vergeben
5. **Kassenlayout & Session-Timer** (`Admin → Ext. Settings`): Layout wählen und optionalen Automations-Timer konfigurieren

### Schritt 6 – Erster Kassenbetrieb

- Kassenbenutzer: Über den Button **„Kasse anmelden"** auf der Login-Seite startet der Kassenbetrieb ohne persönlichen Login
- Admin-Benutzer: Mit persönlichem Konto anmelden → automatische Weiterleitung in den Admin-Bereich
- Z-Bon: Am Schichtenende unter `Admin → Finanzen` den Z-Bon erstellen und ggf. exportieren

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

### Datenbank zurücksetzen
```bash
docker compose down -v
docker compose up -d
```

## 💻 Lokale Entwicklung

### Backend
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
python -m pytest
```

Hinweis: Die Backend-Tests benötigen eine erreichbare PostgreSQL-Datenbank passend zur Backend-Konfiguration.

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
