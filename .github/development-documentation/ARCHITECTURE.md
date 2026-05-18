# Architektur und Technologien

## 🏗️ System-Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser / Mobile                          │
│                  (Progressive Web App)                       │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3)                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │ Kasse Views │  │ Admin Views  │  │  Store (Pinia)     │ │
│  │ - Produkte  │  │ - Members    │  │  - Auth            │ │
│  │ - Bon       │  │ - Products   │  │  - Product         │ │
│  │ - Payment   │  │ - Users      │  │  - Member          │ │
│  └─────────────┘  └──────────────┘  │  - Notifications   │ │
│                                      │  - Cart            │ │
│  ┌──────────────────────────────────┴────────────────────┐ │
│  │         Service Worker / PWA Caching                  │ │
│  └──────────────────────────────────────────────────────┘ │
└──────────────────────────────┬───────────────────────────────┘
                               │ REST API
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend (FastAPI)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐ │
│  │ API Layer    │  │ Auth Layer   │  │ Session Mgmt       │ │
│  │ - Auth       │  │ - bcrypt     │  │ - Signed Cookies   │ │
│  │ - Products   │  │ - JWT        │  │ - CORS             │ │
│  │ - Members    │  │              │  │                    │ │
│  │ - Trans.     │  │              │  │                    │ │
│  └──────────────┘  └──────────────┘  └───────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Service Layer (Geschäftslogik)                       │ │
│  │  - TransactionService    - MemberService             │ │
│  │  - ProductService        - AuthService               │ │
│  │  - UserService                                        │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Repository Layer (Datenzugriff)                      │ │
│  │  - TransactionRepository - ProductRepository         │ │
│  │  - MemberRepository      - UserRepository            │ │
│  └───────────────────────────────────────────────────────┘ │
└──────────────────────────────┬───────────────────────────────┘
                               │ SQL
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL Database                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ users    │ │ members  │ │ products │ │ transactions │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
│  ┌──────────────┐ ┌────────────────────────────────────┐   │
│  │ trans_items  │ │ balance_logs                       │   │
│  └──────────────┘ └────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Datenmodell

### Users Tabelle
```sql
id (PK) | username | email | password_hash | role | is_active | created_at | updated_at
```
- **role**: ADMIN, CASHIER
- Passwörter mit bcrypt gehasht (Rounds: 12)

### Members Tabelle
```sql
id (PK) | name | email | phone | balance_cents | photo | notes | created_at | updated_at
```
- **balance_cents**: Integer, kein negativer Saldo
- Effiziente Abrechnung im Integer-Format

### Products Tabelle
```sql
id (PK) | name | description | price_cents | member_price_cents | is_discountable | stock_quantity | image | is_active | created_at | updated_at
```
- Soft-Delete via `is_active`
- Zwei Preismodelle möglich

### Transactions Tabelle
```sql
id (PK) | type | payment_method | total_amount_cents | user_id (FK) | member_id (FK) | reference_transaction_id (FK) | created_at | updated_at
```
- **type**: SALE, STORNO, RECHARGE
- **payment_method**: CASH, BALANCE
- Vollständige Nachvollziehbarkeit durch Referenzen

### TransactionItems Tabelle
```sql
id (PK) | transaction_id (FK) | product_id (FK) | quantity | unit_price_cents | total_price_cents | created_at
```
- Preis zum Verkaufszeitpunkt gespeichert

### BalanceLogs Tabelle
```sql
id (PK) | member_id (FK) | transaction_id (FK) | old_balance_cents | new_balance_cents | change_cents | reason | created_at
```
- 100% Audit Trail für Guthaben

## 🔄 Transaktionsfluss

### Verkauf (SALE)
1. Frontend: User wählt Produkte
2. Frontend: Checkout mit PaymentMethod (CASH / BALANCE)
3. Backend validates: Stock OK? Balance OK (wenn BALANCE)?
4. Backend: CREATE Transaction
5. Backend: CREATE TransactionItems
6. Backend: Stock reduzieren (DeductStock)
7. Backend: Balance reduzieren (wenn Member + BALANCE)
8. Backend: CREATE BalanceLog
9. Frontend: Bestätigung anzeigen

### Storno (STORNO)
1. Frontend: Benutzer wählt Storno für Transaction X
2. Backend: Neue Storno-Transaction erstellen (reference auf X)
3. Backend: Stock zurückbuchen
4. Backend: Balance zurückbuchen (wenn relevant)
5. Backend: BalanceLog Entry
6. Frontend: Bestätigung

### Z-Bon (Daily Summary)
1. Frontend: Admin fordert Z-Bon für Datum X an
2. Backend: Query Transactions WHERE created_at = Datum X AND type = SALE
3. Backend: Summen berechnen (CASH, BALANCE, Anzahl)
4. Frontend: Anzeigen

## 🔐 Authentifizierung & Autorisierung

### Session Flow
1. POST /api/auth/login → Request.session["user_id"] = x
2. Cookies sind "signed" mit SECRET_KEY
3. GET /api/auth/me → Check Request.session["user_id"]
4. Alle API Calls erfordern gültiges Session Cookie

### Rollen
- **ADMIN**: CRUD für Users, Products, Manual ReCharge, Z-Bon
- **CASHIER**: Nur Sales, Storno, Member auswählen

### Passwort-Sicherheit
```python
# bcrypt mit 12 rounds
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
```

## 📱 PWA Features

### Service Worker
- Cache JS/CSS/Fonts
- API Calls → keine Cache
- Offline: Zurück zu Index.html

### Manifest.json
- Installierbar auf Tablets
- `display: "standalone"`
- Offline-First-Erlebnis

## 🚀 Deployment (ohne Docker)

### Linux Systemd Service (Backend)

```ini
[Unit]
Description=Kassensoftware Backend
After=network.target postgresql.service

[Service]
Type=notify
User=kasse
WorkingDirectory=/opt/kassensoftware/backend
Environment="PATH=/opt/kassensoftware/backend/venv/bin"
ExecStart=/opt/kassensoftware/backend/venv/bin/gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

### Nginx Reverse Proxy

```nginx
upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name kasse.example.com;
    
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        proxy_pass http://localhost:5173;  # Frontend dev
        # oder: root /opt/kassensoftware/frontend/dist;
    }
}
```

---

**Technologie-Stack Summary:**
- Vue 3 (Composition API) + Vite + Pinia
- FastAPI + SQLAlchemy + Pydantic
- PostgreSQL mit Connection Pool
- bcrypt für Passwörter
- Session-basierte Auth
- PWA mit Service Worker
