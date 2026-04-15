# ✅ Voucher-System & Z-Bon-Historia - Implementierungsstand

## Phase 1: Datenbank-Modelle & Services ✅ ABGESCHLOSSEN

### Neue Dateien erstellt:

#### Models (Database Schema)
- ✅ `backend/app/models/voucher.py`
  - `Voucher` - Basis-Tabelle mit Nummernverwaltung
  - `VoucherType` enum: GIFT | PREPAID
  - `VoucherStatus` enum: CREATED | REDEEMED
  - `VoucherReason` enum: COURTESY | MARKETING | LOSS | OTHER

#### Repositories (Data Access)
- ✅ `backend/app/repositories/voucher_repository.py`
  - CRUD für Vouchers
  - Queries nach Status, Typ, Datum
  - Statistiken & Summen

#### Services (Business Logic)
- ✅ `backend/app/services/voucher_service.py`
  - `create_gift_voucher()` - GIFT ohne Zahlung
  - `create_prepaid_voucher()` - PREPAID zum Verkauf
  - `validate_voucher()` - Überprüfung vor Einlösung
  - `redeem_gift_voucher()` - Mit Transaktion (negativ)
  - `redeem_prepaid_voucher()` - Mit Null-Transaktion
  - `get_voucher_statistics()` - Statistiken

### Models aktualisiert:
- ✅ `Transaction` - Neue Transaktionstypen
  - `TransactionType.VOUCHER_SALE` - Voucher-Verkauf
  - `TransactionType.VOUCHER_REDEMPTION` - Voucher-Einlösung
  - `PaymentMethod.VOUCHER_GIFT` - GIFT-Einlösung
  - `PaymentMethod.VOUCHER_PREPAID` - PREPAID-Einlösung

### Exports aktualisiert:
- ✅ `models/__init__.py`
- ✅ `services/__init__.py`

---

## Phase 2: Backend-API-Endpoints (TODO)

### Zu implementieren:

#### Admin-Bereich (`/admin/vouchers`)
- [ ] `POST /admin/vouchers/gift` - GIFT-Voucher erstellen
  - Body: `{ value_eur: float, reason: string, description?: string }`
  - Response: Voucher mit fortlaufender Nummer
  
- [ ] `POST /admin/vouchers/prepaid` - PREPAID-Voucher erstellen
  - Body: `{ value_eur: float, description?: string }`
  - Response: Voucher mit fortlaufender Nummer

- [ ] `GET /admin/vouchers` - Liste mit Filter
  - Query: `status= (CREATED|REDEEMED)`, `type=(GIFT|PREPAID)`, `limit`, `offset`
  - Response: Paginated Voucher-Liste

- [ ] `GET /admin/vouchers/{id}` - Voucher-Details

#### Kasse-Bereich (`/transactions/voucher`)
- [ ] `POST /transactions/voucher/validate/{number}` - Voucher validieren vor Einlösung
  - Response: Voucher-Info (Type, Value, Status)
  - Error: 404 (nicht gefunden), 409 (bereits eingelöst)

- [ ] `POST /transactions/voucher/redeem` - Voucher einlösen
  - Body: `{ voucher_number: int }`
  - Response: Success mit Transaktions-ID
  - Erzeugt automatisch Transaction (GIFT= negativ, PREPAID=null)

#### Z-Bon-Daten (`/transactions/zbon`)
- [ ] Erweitere existing endpoints für Voucher-Statistiken in Z-Böns
  - Gift-Vouchers in diesem Zeitraum eingelöst: Anzahl & Betrag
  - Prepaid-Vouchers in diesem Zeitraum eingelöst: Anzahl & Betrag

---

## Phase 3: Frontend - Admin-Bereich (TODO)

### Zu implementieren:

#### New Tab: "🎫 Vouchers"
- [ ] Sub-Tab 1: "Erstellen"
  - GIFT-Voucher Formular
    - Value-Input
    - Reason-Dropdown
    - Description (optional)
    - Erstellen-Button → Zeigt fortlaufende Nummer
  
  - PREPAID-Voucher Formular
    - Value-Input
    - Description (optional)
    - Erstellen-Button → Zeigt fortlaufende Nummer

- [ ] Sub-Tab 2: "Verwaltung"
  - Table: # | Typ | Wert | Status | Erstellt | Eingelöst
  - Filter: Status, Typ
  - Export: CSV

#### Z-Böns Tab (erweitern)
- [ ] Neue Spalten für Voucher-Statistiken
  - "Gift-Vouchers eingelöst"
  - "Prepaid-Vouchers eingelöst"
  - "Voucher-Verluste"

---

## Phase 4: Frontend - Kasse-Bereich (TODO)

### Zu implementieren:

#### Bei Transaktionserstellung
- [ ] Neuer Button: "🎫 Voucher einlösen"
- [ ] Modal:
  1. Input-Feld für Voucher-Nummer
  2. Bei Eingabe: Live-Validierung
  3. Anzeige: Typ, Wert, Status
  4. Einlösen-Button (erstellt Transaktion)

---

## Phase 5: Z-Bon-Historia Tab (TODO)

### Zu implementieren:

#### New Tab: "📑 Z-Bons"
- [ ] Table mit Spalten:
  - Seq-Nr (fortlaufend)
  - Geschäftsdatum
  - Gesamtumsatz
  - Kassenbestand vorher
  - Kassenbestand nachher
  - Abschöpfung
  - Erstellt am

- [ ] Klickbar → Detail-Ansicht mit vollständigen Daten
- [ ] Filter nach Datum-Bereich
- [ ] Download-Button (HTML/PDF)

---

## Geschäftslogik - Zusammenfassung

### GIFT-Voucher:
✅ Backend-Logik fertig
```
Erstellen (Admin) → Voucher mit Nummer
Einlösen (Kasse) → Transaktion mit negativem Betrag
Z-Bon → "Gift-Vouchers: 2×5€ = -10€ (Kulanz)"
```

### PREPAID-Voucher:
✅ Backend-Logik fertig
```
Erstellen (Admin) → Voucher mit Nummer
Verkauf (Kasse) → Normale Transaction (Voucher als Produkt?)
Einlösen (Kasse) → Null-Transaktion (nur Payment-Method-Logging)
Z-Bon → "Verkauf: 100€", "Voucher-Einlösung: 30€"
```

### Z-Bon-Datenspeicherung:
✅ Struktur vorhanden (ZBonHistory)
```
- Seq-Nr (unique)
- Datum
- Zeitraum (von-bis)
- Umsatzdaten
- Kassenbestand (vorher, nachher, gezählt, Differenz)
- Ein-/Entnahmen
- Transaktionszahlen
```

---

## Nächste Schritte (empfohlene Reihenfolge):

1. **API Endpoints implementieren** (Backend)
   - Admin: Voucher CRUD
   - Kasse: Voucher-Einlösung
   - Z-Bon: Statistiken

2. **Frontend Admin** (Voucher-Verwaltung)

3. **Frontend Kasse** (Voucher-Einlösung im Modal)

4. **Frontend Finance** (Z-Böns Tab + Details)

5. **Testing & Bugfixes**

---

## Status-Überblick:

| Komponente | Status | Dateine |
|-----------|--------|---------|
| Models | ✅ Fertig | voucher.py, transaction.py |
| Repositories | ✅ Fertig | voucher_repository.py |
| Services | ✅ Fertig | voucher_service.py |
| API Endpoints | ⏳ TODO | - |
| Frontend Admin | ⏳ TODO | Admin.vue |
| Frontend Kasse | ⏳ TODO | Kasse.vue |
| Frontend Finance | ⏳ TODO | Finance.vue |
| Z-Böns Tab | ⏳ TODO | Finance.vue |
| Testing | ⏳ TODO | - |

---

**Willst du jetzt die API-Endpoints implementieren oder lieber eine andere Phase beginnen?**
