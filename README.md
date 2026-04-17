# 🏪 Kassensoftware

Webbasierte Kassensoftware für Vereine und kleine Handelsbetriebe mit Echtzeit-Verkaufsverfolgung, Mitgliederverwaltung und detaillierter Finanzberichtserstattung.

## 🚀 Quick Start mit Docker

```bash
# 1. Voraussetzungen: Docker & Docker Compose installieren
# https://docs.docker.com/get-docker/

# 2. Repository klonen/entpacken

# 3. Container starten
docker-compose up -d

# 4. Öffne http://localhost:8000 im Browser
# Login: admin / admin123  oder  Kasse1 / Kasse1123
```

## 📋 Für Anfänger

Vollständige Anleitung siehe: [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md)

## ✨ Features

### 🛒 Verkaufssystem (Kasse)
- Artikel aus Katalog hinzufügen
- Mitgliederverwaltung mit Guthaben
- Zahlungsarten: Bargeld oder Guthaben
- Echtzeit-Preisberechnung für Mitglieder
- Bon-Anzeige mit Tagesbelegnummern

### 👥 Mitgliederverwaltung
- CRUD für Mitglieder
- Profilfotos hochladen
- Guthaben-Management
- Historie aller Transaktionen

### 📦 Bestandsverwaltung
- Artikel hinzufügen/bearbeiten
- Zwei Preismodelle (Normal + Mitglieder-Preis)
- Bestand verwalten
- Artikel-Bilder hochladen

### 💰 Finanzbereich
- Z-Bon (Tagesabrechnung)
- Transaktionshistorie filtern
- Umsatzstatistiken (täglich/wöchentlich)
- Mitglied-Statistiken
- Top-Produkte übersicht

### 👤 Benutzerverwaltung
- Admin-, Kassenmitglied- & Kassierer-Rollen
- Passwort-Hashing (bcrypt)
- Session-basierte Authentifizierung
- Passwort-Bestätigung für kritische Aktionen (z. B. Guthaben aufbuchen, Z-Bon erstellen)

### 🎨 Branding & Design
- Konfigurierbare Hintergrund-, Banner- und Highlight-Farbe
- Austauschbares Logo für Header, Login, Favicon und PWA-Icons

### 📱 Cross-Platform
- Progressive Web App (PWA)
- Responsive Design
- Installierbar auf Mobil-Geräten
- Install-Button im UI, sobald der Browser die Installation anbietet

## 🛠️ Tech-Stack

| Komponente | Technologie |
|-----------|-------------|
| Backend | FastAPI 0.104.1 |
| Server | Uvicorn 0.24.0 |
| ORM | SQLAlchemy 2.0.49 |
| Datenbank | PostgreSQL 15 |
| Frontend | Vue.js 3.3.8 |
| State | Pinia 2.1.6 |
| Build | Vite 5.0.7 |
| Container | Docker & Docker Compose |

## 📁 Projektstruktur

```
.
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/               # REST API Endpunkte
│   │   ├── models/            # SQLAlchemy Models
│   │   ├── services/          # Business Logic
│   │   ├── repositories/      # Datenzugriff
│   │   ├── schemas/           # Pydantic Schemas
│   │   └── core/              # Config, DB, Security
│   ├── requirements.txt        # Python Dependencies
│   ├── main.py                # FastAPI App
│   └── Dockerfile             # Docker Image
├── frontend/                   # Vue.js Frontend (PWA)
│   ├── src/
│   │   ├── components/        # Vue Components
│   │   ├── views/             # Page Views
│   │   ├── stores/            # Pinia State Stores
│   │   ├── services/          # API Client
│   │   └── styles/            # SCSS Styling
│   ├── package.json
│   ├── vite.config.js
│   └── public/                # Static Assets
├── docker-compose.yml         # Container Orchestration
├── .env                       # Environment Configuration
└── DOCKER_QUICKSTART.md       # Anfänger-Anleitung
```

## 📖 Dokumentation

- **[DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md)** - Schritt-für-Schritt Anleitung für Anfänger
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technische Architektur
- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - Feature & Überblick

## 🔐 Sicherheit

- Passwörter: bcrypt 12-Rounds
- Sessions: Signed Cookies
- CORS: Production-ready (nur für Entwicklung aktiv)
- Environment-basierte Secrets
- Keine sensitiven Daten in Code

## 🐳 Docker

### Installation
Siehe [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md#docker-installation)

### Container starten
```bash
docker-compose up -d
```

### Logs anschauen
```bash
docker-compose logs -f kassensoftware
```

### Container stoppen
```bash
docker-compose down
```

### Datenbank zurücksetzen
```bash
docker-compose down -v              # -v löscht auch Volumes
docker-compose up -d                # Neustart erstellt frische DB
```

## 🔧 Umgebungsvariablen (.env)

| Variable | Standard | Beschreibung |
|----------|----------|-------------|
| `DATABASE_URL` | PostgreSQL URL | Datenbankverbindung |
| `SECRET_KEY` | change-me | Session-Encryption Key (MUSS ändern!) |
| `PRODUCTION` | false | Production-Modus (CORS deaktiviert) |

## 📱 Standard-Benutzer

Bei Docker-Start werden automatisch erstellt:

| Benutzer | Passwort | Rolle |
|----------|----------|-------|
| `admin` | admin123 | Admin |
| `Kasse1` | Kasse1123 | Kassierer |

## 🐛 Troubleshooting

**Container starten nicht?**
- `docker-compose logs` anschauen
- Port 8000 oder 5432 belegt? → `.env` anpassen

**Datenbank-Fehler?**
- `docker-compose down -v` (Volumes löschen)
- `docker-compose up -d` (Neustart mit fresh DB)

**Frontend zeigt Fehler?**
- Browser Cache löschen (Ctrl+Shift+R)
- Browser Console (F12) für Details checken

## 📝 Lizenz

Weitere Infos siehe [LICENSE](LICENSE) (falls vorhanden)

## 📧 Support

Bei Fragen oder Problemen: Dokumentation lesen oder Logs checken

- Node.js 18+
- PostgreSQL 12+
- Git

#### Windows
```powershell
# PowerShell (Admin)
python --version    # >= 3.11
node --version      # >= 18
npm --version       # >= 9
```

#### Linux/macOS
```bash
python3 --version   # >= 3.11
node --version      # >= 18
npm --version       # >= 9
```

### 1. PostgreSQL Setup

#### Windows (WSL2 oder native PostgreSQL)

```powershell
# PostgreSQL Windows-Installer: https://www.postgresql.org/download/windows/
# Nach Installation: psql sollte verfügbar sein

# Datenbank und Benutzer erstellen
$env:PGPASSWORD='postgres'  # Default Admin-PW
psql -U postgres -h localhost

# In psql console:
CREATE USER kassensystem WITH PASSWORD 'kassensystem';
CREATE DATABASE kassensystem OWNER kassensystem;
ALTER ROLE kassensystem SET client_encoding TO 'utf8';
ALTER ROLE kassensystem SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE kassensystem TO kassensystem;
\q
```

#### Linux (Ubuntu/Debian)

```bash
# Installation
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# PostgreSQL starten und aktivieren
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Datenbank und Benutzer erstellen
sudo -u postgres psql << EOF
CREATE USER kassensystem WITH PASSWORD 'kassensystem';
CREATE DATABASE kassensystem OWNER kassensystem;
ALTER ROLE kassensystem SET client_encoding TO 'utf8';
ALTER ROLE kassensystem SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE kassensystem TO kassensystem;
\q
EOF

# Verbindung testen
psql -U kassensystem -d kassensystem -h localhost
```

#### macOS (Homebrew)

```bash
# Installation
brew install postgresql@14

# Server starten
brew services start postgresql@14

# Datenbank erstellen
createuser -P kassensystem   # Passwort: kassensystem
createdb -O kassensystem kassensystem

# Verbindung testen
psql -U kassensystem -d kassensystem -h localhost
```

### 2. Backend Setup

```bash
# Repository klonen
cd Kassensoftware
cd backend

# Virtual Environment erstellen
python -m venv venv

# Environment aktivieren
# Windows:
venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Environment-Variablen konfigurieren
# .env.example zu .env kopieren und anpassen
cp .env.example .env

# Editor öffnen und DATABASE_URL überprüfen:
# DATABASE_URL=postgresql://kassensystem:kassensystem@localhost:5432/kassensystem
```

**Inhalt `.env`:**
```env
# Backend Configuration
DATABASE_URL=postgresql://kassensystem:kassensystem@localhost:5432/kassensystem
SECRET_KEY=your-secret-key-here-minimum-32-chars-for-production

# Frontend Configuration
VITE_API_URL=http://localhost:8000/api
```

### 3. Frontend Setup

```bash
cd ../frontend

# Abhängigkeiten installieren
npm install

# Optional: Umgebungsvariablen überprüfen
# In .env oder vite.config.js:
# VITE_API_URL sollte auf Backend zeigen
```

### 4. Admin-Benutzer erstellen (Optional)

```bash
# Im Backend-Verzeichnis:
source venv/bin/activate  # oder venv\Scripts\Activate.ps1 auf Windows

python create_admin.py
# Folgen Sie den Prompts zur Eingabe von Benutzername, E-Mail und Passwort
```

---

## 🚀 Betrieb

### Entwicklung (Lokale Maschine)

#### Backend starten

```bash
cd backend

# Aktivieren Sie das Virtual Environment
# Windows:
venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Server mit Auto-Reload starten
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Oder unter Windows alternative Ports (falls 8000 blockiert):
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

**Output sollte etwa so aussehen:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

#### Frontend starten (neues Terminal)

```bash
cd frontend

# Development Server starten
npm run dev

# Output:
# ➜  Local:   http://localhost:5173/
```

#### Im Browser öffnen

```
http://localhost:5173
```

Login mit Standardbenutzer:
- **Username**: admin
- **Passwort**: admin (Standard, sollte in Production geändert werden)

### Windows Batch-Skripte (Vereinfacht)

**Backend starten:**
```batch
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend starten:**
```batch
cd frontend
npm run dev
```

### Ports

| Service | Port | Beschreibung |
|---------|------|-------------|
| Backend API | 8000 (oder 8001) | FastAPI Uvicorn Server |
| Frontend | 5173 | Vite Dev Server |
| PostgreSQL | 5432 | Datenbank |

---

## 📖 Nutzung

### 1. Login

1. Unter `http://localhost:5173` im Browser öffnen
2. Mit Admin-Benutzer anmelden

### 2. Verkauf durchführen (Kasse)

1. **Menü**: Click "Kasse" (Verkaufen)
2. **Artikel hinzufügen**: 
   - Click "Artikel hinzufügen"
   - Artikel aus Liste wählen
   - Menge eingeben
3. **Kunde** (Optional):
   - Click "Mitglied auswählen"
   - Mitglied wählen (Guthaben-Rabatt wird automatisch angewendet)
4. **Zahlung**:
   - "💰 BAR" für Bargeld oder "💳 Guthaben" für Mitglied-Zahlung
   - Bestätigung anzeigen
5. **Bon-Anzeige**:
   - Belegnummer und Artikel sichtbar
   - Nach Checkout neue Belegnummer generiert

### 3. Mitglieder verwalten

1. **Admin-Bereich** → "Mitglieder"
2. **Neue Mitglied**:
   - Click "Mitglied anlegen"
   - Name, E-Mail, Telefon eingeben
   - Optionales Profilfoto upload
3. **Guthaben aufladen**:
   - Click auf Mitglied
   - "Guthaben aufladen" input
   - Betrag eingeben und speichern

### 4. Artikel verwalten

1. **Admin-Bereich** → "Artikel"
2. **Neuer Artikel**:
   - Click "Artikel anlegen"
   - Name, Beschreibung eingeben
   - Normalpreis und Mitglieder-Preis
   - Bestand setzen
   - Bild hochladen (optional)
3. **Bestand aktualisieren**:
   - Click auf Artikel
   - Bestand ändern und speichern

### 5. Finanzberichte ansehen

1. **Admin-Bereich** → "Finanzstatistik"
2. **Z-Bon** (Tagesabrechnung):
   - Datum wählen
   - Umsatz nach Zahlungsart (BAR/Guthaben)
   - Transaktionsliste mit expandierbaren Artikeln
3. **Transaktionshistorie**:
   - Datum-Bereich und Zahlungsart filtern
   - Details pro Verkauf anzeigen
4. **Umsatzstatistik**:
   - Wochenübersicht, Monatlich
   - Top Produkte
5. **Mitglied-Statistik**:
   - Anzahl Mitglieder
   - Aktive diese Woche
   - Gesamtes Guthaben
   - Top Spender

### 6. Benutzer verwalten

1. **Admin-Bereich** → "Teams"
2. **Neuer Benutzer**:
   - Click "Benutzer einladen"
   - Benutzername, E-Mail
   - Rolle: ADMIN oder CASHIER
3. **Aktivieren/Deaktivieren**:
   - Toggle "Aktiv" Checkbox

---

## 🔌 API-Dokumentation

### Authentication

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin"
}

# Response: 200 OK
# Set-Cookie: session=<signed_cookie>
```

### Transactions API

#### Verkauf erstellen
```http
POST /api/transactions/create
Content-Type: application/json
Cookie: session=<cookie>

{
  "member_id": 1,
  "payment_method": "BALANCE",
  "items": [
    {
      "product_id": 5,
      "quantity": 2
    }
  ]
}

# Response: 201 Created
{
  "id": 42,
  "receipt_number": 123,
  "total_amount_cents": 500,
  "member": {"id": 1, "name": "Max Mustermann"},
  "items": [...]
}
```

#### Tagesstatistiken
```http
GET /api/transactions/daily-stats?date=2024-04-11
Cookie: session=<cookie>

# Response: 200 OK
{
  "cash_total": 5000,
  "balance_total": 2000,
  "total_amount": 7000,
  "transaction_count": 15,
  "transactions": [
    {
      "id": 42,
      "receipt_number": 123,
      "total_amount_cents": 500,
      "payment_method": "BALANCE",
      "member": {"name": "Max"},
      "items": [...]
    }
  ]
}
```

### Members API

```http
GET /api/members
GET /api/members/{id}
POST /api/members
PUT /api/members/{id}
GET /api/members/statistics

POST /api/members/{id}/recharge?amount_cents=5000
```

### Products API

```http
GET /api/products
GET /api/products/{id}
POST /api/products
PUT /api/products/{id}
GET /api/products/{id}/image
POST /api/products/{id}/image (multipart/form-data)
```

**Vollständige API-Dokumentation** sind in der Swagger-UI unter `http://localhost:8000/docs` verfügbar.

---

## 🏗️ Architektur

### Datenmodell

```
┌─────────────┐     ┌────────────────┐     ┌──────────────┐
│   users     │────▶│  transactions  │◀────│  members     │
│             │     │                │     │              │
│ - id        │     │ - id           │     │ - id         │
│ - username  │     │ - type         │     │ - name       │
│ - password  │     │ - payment_*    │     │ - balance_*  │
│ - role      │     │ - total_*      │     │ - photo      │
└─────────────┘     │ - user_id (FK) │     └──────────────┘
                    │ - member_id    │
                    │ - created_at   │     ┌──────────────┐
                    └────────┬───────┘     │  products    │
                             │            │              │
                             │            │ - id         │
                             ▼            │ - name       │
                    ┌──────────────────┐   │ - price_*    │
                    │ transaction_items│   │ - stock      │
                    │                  │   │ - image      │
                    │ - id             │   │ - is_active  │
                    │ - trans_id (FK)  │──▶└──────────────┘
                    │ - product_id (FK)│
                    │ - quantity       │
                    │ - unit_price_*   │
                    └──────────────────┘
                           │
                           ▼
                    ┌──────────────────┐
                    │ balance_logs     │
                    │ (Audit-Trail)    │
                    │ - member_id (FK) │
                    │ - old_balance    │
                    │ - new_balance    │
                    │ - reason         │
                    │ - created_at     │
                    └──────────────────┘
```

### Schichten-Architektur

```
┌──────────────────────────────────────┐
│  Vue 3 Frontend (Kasse, Admin, etc.) │
├──────────────────────────────────────┤
│  Pinia Stores (Auth, Cart, Member)   │
├──────────────────────────────────────┤
│  Axios HTTP Client                   │
├──────────────────────────────────────┤
│  FastAPI REST API Routes             │
├──────────────────────────────────────┤
│  Service Layer (Business Logic)      │
├──────────────────────────────────────┤
│  Repository Layer (Data Access)      │
├──────────────────────────────────────┤
│  SQLAlchemy ORM Models               │
├──────────────────────────────────────┤
│  PostgreSQL Database                 │
└──────────────────────────────────────┘
```

---

## 🔒 Sicherheit

- **Passwort-Hashing**: bcrypt mit 12 Runden
- **Authentifizierung**: Session-Cookies (signed mit SECRET_KEY)
- **CORS**: Konfiguriert für Frontend-Origin
- **Input-Validierung**: Pydantic-Schemas auf allen Endpoints
- **SQL-Injection**: SQLAlchemy ORM verhindert direkte SQL-Injections
- **Audit-Trail**: BalanceLogs für alle Guthaben-Änderungen

---

## 🐛 Troubleshooting

### Port 8000 blockiert (Windows)

```powershell
# Prozess auf Port 8000 finden
netstat -ano | findstr :8000

# Prozess beenden (ersetzen Sie PID)
taskkill /PID <PID> /F

# Oder: Alternativer Port verwenden
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8001

# Frontend muss entsprechend konfiguriert werden:
# .env: VITE_API_URL=http://localhost:8001/api
```

### Database Connection Error

```
psycopg2.OperationalError: could not connect to server
```

**Lösungen:**
1. PostgreSQL läuft? `psql -U kassensystem -d kassensystem`
2. Passwort korrekt in `.env`?
3. DATABASE_URL korrekt? `postgresql://user:pass@host:port/db`
4. Firewall blockiert Port 5432?

### CSRF / Session Fehler

```
Authentication failed
```

**Lösungen:**
1. Cookies aktiviert im Browser?
2. `SECRET_KEY` in `.env` gesetzt?
3. Browser-Konsole prüfen (DevTools → Network)
4. Cookies löschen und erneut anmelden

### Module Import Error

```
ModuleNotFoundError: No module named 'fastapi'
```

**Lösung:**
```bash
# Virtual Environment korrekt aktiviert?
which python  # Linux/macOS - sollte venv zeigen
python -m pip list  # requirements.txt-Pakete sichtbar?

# Wenn nicht:
pip install -r requirements.txt --upgrade
```

### Frontend zeigt "Cannot find module"

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

---

## 📚 Weitere Dokumentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Detaillierte technische Architektur
- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)**: Projektstruktur & Dateiorganisation
- **[SETUP.md](SETUP.md)**: Ausführliche Setup-Anleitung (Linux-fokussiert)
- **[WINDOWS_SETUP.md](WINDOWS_SETUP.md)**: Windows-spezifische Anleitung

---

## 🤝 Support & Kontakt

Bei Fragen oder Problemen:
1. Checklist im Troubleshooting-Bereich durchgehen
2. Log-Ausgaben im Terminal prüfen
3. Browser-Konsole (F12) auf Fehler prüfen
4. Database-Verbindung testen: `psql -U kassensystem -d kassensystem`

---

## 📄 Lizenz

[Lizenz hier einfügen, z.B. MIT, GPL, etc.]

---

**Versionshistorie:**
- v1.0.0 (Apr 2026): Initiale Release
  - Vollständiges Kassensystem mit Verkauf
  - Mitglieder- und Bestandsverwaltung
  - Finanzberichte (Z-Bon, Statistiken)
  - PWA für mobile Geräte
