# Voucher System - Docker Deployment Guide

## Overview
Das Gutschein-System (`vouchers` Tabelle) wird bei jedem Docker-Container-Start automatisch initialisiert und aktualisiert.

## Startup-Prozess (Guaranteed bei jedem Container-Start)

### 1. Docker Container Start (`docker-compose up`)
- Container `kassensoftware` wird gestartet
- Wartet auf `postgres` Container (health-check)
- Führt `docker-entrypoint.sh` aus

### 2. Entrypoint Script (`backend/docker-entrypoint.sh`)
```bash
⏳ STEP 1: Waiting for database connection...
   └─ Versucht Datenbankverbindung bis zu 30x
   
🔄 STEP 2: Running database migrations...
   └─ Ruft `run_migrations()` auf
   
🚀 STEP 3: Starting Kassensoftware with uvicorn...
   └─ Startet FastAPI Server
```

### 3. Database Migration (`app/core/db_migration.py`)
Die Migration läuft in 3 Schritten:

#### Schritt 1: Tabellen erstellen
```python
Base.metadata.create_all(bind=engine)
```
- Erstellt ALLE Tabellen mit aktuellen Definitions aus den Models
- Inklusive `vouchers` Tabelle mit:
  - `voucher_code` VARCHAR(20) UNIQUE (nullable=True)
  - `voucher_number` INTEGER UNIQUE
  - Alle weiteren Spalten

#### Schritt 2: Enum-Typen aktualisieren
```sql
-- Überprüft voucherreason enum
SELECT enumlabel FROM pg_enum WHERE enumtypid = ...
-- Falls UPDATE nötig: Recreates enum mit korrekten Werten
-- DYP_SIEGER, PROMOTION
```

#### Schritt 3: Fehlende Spalten hinzufügen
```sql
-- Für alle bestehenden Vouchers ohne voucher_code:
UPDATE vouchers 
SET voucher_code = 'V-2026-' || LPAD(CAST(voucher_number AS TEXT), 3, '0') 
WHERE voucher_code IS NULL
```

## Garantien

✅ **Bei neuem Container:**
- `vouchers` Tabelle wird mit allen Spalten inkl. `voucher_code` erstellt
- Alle Enums werden mit korrekten Werten erstellt

✅ **Bei existierendem Container:**
- `voucher_code` Spalte wird hinzugefügt (falls nicht existiert)
- Alte Gutscheine werden mit Codes gefüllt (V-2026-001, V-2026-002, etc.)
- Enums werden aktualisiert (falls nötig)

✅ **Migration ist idempotent:**
- Mehrfaches Ausführen verursacht keine Fehler
- Bereits existierende Spalten werden übersprungen
- Bereits gesetzte Codes werden nicht überschrieben

## Verifikation nach Startup

### Option 1: Docker Logs prüfen
```bash
docker logs kassensoftware-app | grep -A50 "DATABASE MIGRATION"
```

Erwartet:
```
======================================================================
DATABASE MIGRATION STARTED
======================================================================
✓ Step 1: Creating/verifying tables...
  → All tables created/verified
✓ Step 2: Updating enum types...
  → Enum types checked
✓ Step 3: Adding missing columns...
  → Missing columns added
======================================================================
✓ DATABASE MIGRATION COMPLETED SUCCESSFULLY
======================================================================
```

### Option 2: Manuelles Verifikations-Skript
```bash
# Im Backend-Container:
docker exec kassensoftware-app python check_migration.py

# Output zeigt:
# - Alle Tabellen existieren
# - voucher_code Spalte existiert
# - Alle Enums haben korrekten Werte
# - Anzahl Gutscheine mit/ohne Codes
```

### Option 3: Direkt in PostgreSQL
```bash
# Verbindung zur DB:
psql -h localhost -p 5433 -U kassensystem -d kassensystem

# Spalte überprüfen:
\d vouchers

# Gutscheine anschauen:
SELECT id, voucher_number, voucher_code FROM vouchers LIMIT 5;

# Enums überprüfen:
SELECT typname, enumlabel 
FROM pg_type 
JOIN pg_enum ON pg_type.oid = pg_enum.enumtypid 
WHERE typname = 'voucherreason';
```

## Troubleshooting

### Problem: "V-2026-undefined" in UI
**Symptom:** Neue Gutscheine zeigen "V-2026-undefined"

**Ursachen:**
1. Migration hat nicht gelaufen → `voucher_code` Spalte fehlt
2. Neuer Gutschein wurde ohne Code erstellt

**Lösung:**
1. Container-Logs prüfen: `docker logs kassensoftware-app`
2. Migration manuell erneut laufen: `docker restart kassensoftware-app`
3. Nach Restart: Check mit `check_migration.py`

### Problem: "voucherreason enum does not exist"
**Symptom:** Fehler beim Erstellen von GIFT-Gutscheinen

**Ursache:** Enum wurde nicht korrekt erstellt

**Lösung:**
1. Container neu starten: `docker restart kassensoftware-app`
2. Migration wird neu laufen und Enum erstellen

### Problem: "duplicate key value violates unique constraint"
**Symptom:** Fehler beim Erstellen von neuen Gutscheinen

**Ursachen:**
1. Mehrere NULL voucher_codes (PostgreSQL: NULL != NULL, aber UNIQUE erlaubt mehrfach NULL)
2. Im Fehlerfall: Repository schreibt duplicate codes

**Lösung:**
1. Container Logs prüfen
2. Manuelle SQL-Bereinigung (mit Vorsicht!):
   ```sql
   -- Zeige duplikaten:
   SELECT voucher_code, COUNT(*) 
   FROM vouchers 
   GROUP BY voucher_code 
   HAVING COUNT(*) > 1;
   
   -- Regeneriere Codes (wenn nötig):
   UPDATE vouchers 
   SET voucher_code = 'V-2026-' || LPAD(CAST(id AS TEXT), 3, '0')
   WHERE voucher_code IS NULL;
   ```

## Änderungen für Deployment

Falls es Probleme gibt und manuell angepasst werden soll:

### 1. Migration Logik ändern
Datei: `backend/app/core/db_migration.py`
- Methode `_add_missing_columns()`
- Ändert wie `voucher_code` erstellt/gefüllt wird

### 2. Model Spalten-Definition
Datei: `backend/app/models/voucher.py`
- Spalte `voucher_code` Definition
- Constraints wie UNIQUE, nullable

### 3. Repository Logik
Datei: `backend/app/repositories/voucher_repository.py`
- Methode `create()`
- Garantiert dass voucher_code vor commit gesetzt ist

### 4. Pydantic Fallback
Datei: `backend/app/schemas/voucher.py`
- Validator `fallback_voucher_code()`
- Generiert Code aus ID wenn DB-Spalte NULL ist

## Best Practices

✅ **DO:**
- Container beim Deployment neu starten
- Logs nach Start überprüfen
- Migration-Verifikations-Skript verwenden
- Enum-Werte in Code mit DB synchron halten

❌ **DON'T:**
- DB-Spalten manuell löschen
- Enum-Werte manuell ändern (in SQLzuerst!)
- `voucher_code` auf alten Gutscheinen manipulieren
- Migration-Skript direkt in DB-Dumps importieren

## Zusammenfassung

Das Gutschein-System ist **vollständig automatisiert** für Docker-Deployment:

1. ✅ Migration läuft beim Container-Start
2. ✅ Tabellen werden erstellt
3. ✅ Fehlende Spalten werden hinzugefügt
4. ✅ Enums werden aktualisiert
5. ✅ Alte Gutscheine bekommen Codes
6. ✅ Neue Gutscheine generieren Codes automatisch
7. ✅ Frontend hat Fallback für undefined codes

**Keine manuellen DB-Operationen nötig!**
