# Implementierungsplan: Z-Bon-Historie & Voucher-System

## Phase 1: Z-Bon-Historie & Cash Management Integration

### 1.1 Backend - API Endpoints (transaction.py)
- ✅ GET `/transactions/zbon/history` - Liste aller Z-Böns mit Pagination
- ✅ GET `/transactions/zbon/history/{seq_number}` - Detailansicht eines Z-Bons
- ✅ GET `/transactions/cash/balance` - Aktueller Kassenbestand
- ✅ POST `/transactions/zbon/save` - Z-Bon speichern nach Erstellung

### 1.2 Frontend - Finance-Tab "Z-Böns"
- Neue Tab: "📑 Z-Böns" (neben "Z-Bon")
- Table mit Spalten:
  - Seq-Nr (fortlaufend)
  - Datum
  - Gesamtumsatz
  - Kassenstand vorher
  - Kassenstand nachher
  - Abschöpfung
- Clickable Zeile → Detailansicht
- Filter nach Datum-Bereich

### 1.3 Database
- ✅ Bereits vorhanden: ZBonHistory, CashEntry, CashBalance

---

## Phase 2: Voucher-System

### 2.1 Database Models (New)

#### Voucher (base table)
```
- id (PK)
- voucher_number (unique, laufend)
- voucher_type (GIFT | PREPAID) - enum
- status (CREATED | REDEEMED) - enum
- value_cents (Betrag)
- description (optional)
- created_by_user_id (FK)
- created_at
- redeemed_by_user_id (FK, null wenn nicht eingelöst)
- redeemed_at (null wenn nicht eingelöst)
- redeemed_in_transaction_id (FK, null wenn nicht eingelöst)
```

#### VoucherReason (nur für GIFT)
```
- id (PK)
- reason (VARCHAR) - "Kulanz", "Marketing", "Verlust"
```

### 2.2 Transaction-Model Extensions
Neue PaymentMethod Enums:
- `VOUCHER_GIFT` - Einlösung eines Gift-Vouchers
- `VOUCHER_PREPAID` - Einlösung eines Prepaid-Vouchers (bereits als "VOUCHER_PREPAID_PURCHASE" bei Verkauf)

Neue TransactionType:
- `VOUCHER_SALE` - Verkauf eines Prepaid-Vouchers
- `VOUCHER_REDEMPTION` - Einlösung eines Vouchers

### 2.3 Backend - Services

#### VoucherService
- `create_gift_voucher(value, reason)` → erzeugt GIFT-Voucher ohne Transaktion
- `create_prepaid_voucher(value, description)` → erzeugt Voucher (wird später gekauft)
- `redeem_voucher(voucher_number, user_id)` → Voucher einlösen
- `get_voucher_by_number(number)` → Lookup mit Validierung
- `get_vouchers_by_status(status)` → Liste

#### VoucherRepository
- CRUD-Operationen
- Query nach Status, Typ, Datum

### 2.4 Backend - API Endpoints

#### Admin-Bereich
- `POST /admin/vouchers/gift` - Neuen Gift-Voucher erzeugen
- `POST /admin/vouchers/prepaid` - Neuen Prepaid-Voucher erzeugen
- `GET /admin/vouchers` - Liste mit Filter (Status, Typ, Datum)
- `GET /admin/vouchers/{id}` - Detail

#### Kasse-Bereich
- `POST /transactions/voucher/redeem` - Voucher einlösen (mit Nummern-Eingabe)
- `GET /transactions/voucher/validate/{number}` - Voucher-Validierung vor Einlösung

### 2.5 Z-Bon Integration

#### Im Z-Bon anzeigen:
```
VOUCHER-STATISTIKEN:
- Gift-Voucher eingelöst: 2 × 5,00€ = 10,00€ (Kulanz)
- Prepaid-Voucher eingelöst: 3 × 10,00€ = 30,00€

UMSATZ-ANPASSUNGEN:
- Bruttoumsatz (BAR) ohne Vouchers: XXX,XX€
- Bruttoumsatz (GUTHABEN) ohne Vouchers: XXX,XX€
- Verluste (Gift-Vouchers): -10,00€
```

---

## Phase 3: Frontend - Admin-Bereich

### 3.1 New Tab: "🎫 Vouchers"
- Zwei Sub-Tabs: "Erstellen" | "Verwaltung"

#### Erstellen-Tab:
- Gift-Voucher: 
  - Wert-Input
  - Grund-Dropdown (Kulanz, Marketing, Verlust)
  - Erstellen-Button → Zeigt Nummer
  
- Prepaid-Voucher (wird bei normaler Verkauf-Transaktion als Produkt erstellt)

#### Verwaltung-Tab:
- Table: Nummer | Typ | Wert | Status | Erstellt am | Eingelöst am
- Filter nach Status (Aktiv/Eingelöst)
- Export-Funktion (CSV)

### 3.2 Kasse-Bereich - Voucher einlösen
- Neues Modal/Dialog "Voucher einlösen"
- Input: Voucher-Nummer nur
- Bei Eingabe: Validierung + Anzeige (Typ, Wert, Status)
- Einlösen-Button → Transaktion erzeugen

---

## Phase 4: Testing & Validation

- Unit Tests für VoucherService
- Integration Tests für Transaction-Voucher
- Z-Bon-Rendering mit Voucher-Daten testen
- Geschäftslogik-Tests (z.B.: kann GIFT nicht 2x eingelöst werden)

---

## Abhängigkeiten & Reihenfolge

1. **Models erstellen** (Voucher Table)
2. **Services & Repositories** (VoucherService, VoucherRepository)
3. **API Endpoints** (Admin + Kasse)
4. **Z-Bon Integration** (Service, Template)
5. **Frontend** (Admin + Kasse)
6. **Testing**

---

## Geschäftslogik-Details

### GIFT-Voucher:
- Keine Transaction beim Erstellen
- Beim Einlösen: 
  - Status → REDEEMED
  - Neue Transaction: type=VOUCHER_REDEMPTION, payment_method=VOUCHER_GIFT
  - Betrag negativ (Verlust)
  - Im Z-Bon: nicht in normal Umsatz, sondern in "Voucher-Verluste"

### PREPAID-Voucher:
- Bei Kauf: Transaction type=VOUCHER_SALE, payment_method=CASH/BALANCE
- Beim Einlösen:
  - Status → REDEEMED
  - Neue Transaction: type=VOUCHER_REDEMPTION, payment_method=VOUCHER_PREPAID
  - Nulltransaktion (Betrag = 0)
  - Im Z-Bon: Verkauf im Umsatz, Einlösung als Zahlungsmittel-Statistik
