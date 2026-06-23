from __future__ import annotations

import io
import json
import zipfile
from datetime import date, datetime, time, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import MetaData, func, inspect, select, text
from sqlalchemy.orm import Session

from app.core.database import engine as _db_engine


BACKUP_FORMAT = "kickerkasse-db-backup-v1"
BACKUP_JSON_FILE = "backup.json"

# Tables that must not be included in user-facing backups/restores.
# alembic_version tracks the current DB schema migration state; restoring
# an old value would cause Alembic to re-run already-applied migrations on
# the next application start.
_EXCLUDED_TABLES = {"alembic_version"}


class DatabaseBackupService:
    def __init__(self, db: Session):
        self.db = db
        self.engine = _db_engine

    def create_backup_zip(self) -> tuple[bytes, str]:
        metadata = MetaData()
        metadata.reflect(bind=self.engine)
        table_names = self._ordered_table_names(metadata)
        exported_tables = []

        for table_name in table_names:
            table = metadata.tables[table_name]
            rows = self.db.execute(table.select()).mappings().all()
            exported_tables.append({
                "name": table_name,
                "rows": [self._serialize_row(dict(row)) for row in rows],
            })

        payload = {
            "format": BACKUP_FORMAT,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tables": exported_tables,
        }

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(BACKUP_JSON_FILE, json.dumps(payload, ensure_ascii=False))

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"kickerkasse-db-backup-{timestamp}.zip"
        return buffer.getvalue(), filename

    def restore_from_backup_zip(self, file_name: str, content: bytes) -> dict:
        if not file_name or not file_name.lower().endswith(".zip"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bitte eine ZIP-Datei als Backup hochladen",
            )

        payload = self._read_backup_payload(content)
        if payload.get("format") != BACKUP_FORMAT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ungültiges Backup-Format",
            )

        tables_payload = payload.get("tables")
        if not isinstance(tables_payload, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Backup-Datei enthält keine gültigen Tabellen",
            )

        metadata = MetaData()
        metadata.reflect(bind=self.engine)
        table_rows = self._collect_table_rows(tables_payload)
        # Silently ignore excluded system tables that may exist in older backups.
        unknown_tables = [
            table_name
            for table_name in table_rows
            if table_name not in metadata.tables and table_name not in _EXCLUDED_TABLES
        ]
        if unknown_tables:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Backup enthält unbekannte Tabellen: {', '.join(sorted(unknown_tables))}",
            )

        ordered_tables = [name for name in self._ordered_table_names(metadata) if name in table_rows]
        if not ordered_tables:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Backup enthält keine wiederherstellbaren Tabellen",
            )

        try:
            quoted_tables = ", ".join(f'"{name}"' for name in ordered_tables)
            self.db.execute(text(f"TRUNCATE TABLE {quoted_tables} RESTART IDENTITY CASCADE"))

            restored_counts = {}
            for table_name in ordered_tables:
                rows = table_rows.get(table_name, [])
                table = metadata.tables[table_name]
                prepared_rows = [self._deserialize_row(row, table) for row in rows]
                if prepared_rows:
                    self.db.execute(table.insert(), prepared_rows)
                restored_counts[table_name] = len(prepared_rows)

            self.db.flush()
            self._sync_sequences(ordered_tables, metadata)
            self.db.commit()
            return {
                "restored_tables": len(ordered_tables),
                "restored_rows": sum(restored_counts.values()),
                "table_row_counts": restored_counts,
            }
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Backup konnte nicht wiederhergestellt werden: {str(exc)}",
            ) from exc

    @staticmethod
    def _read_backup_payload(content: bytes) -> dict:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                if BACKUP_JSON_FILE not in archive.namelist():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Backup-Datei enthält keine backup.json",
                    )
                raw = archive.read(BACKUP_JSON_FILE)
        except zipfile.BadZipFile as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Die hochgeladene Backup-Datei ist keine gültige ZIP-Datei",
            ) from exc

        try:
            parsed = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="backup.json ist ungültig",
            ) from exc

        if not isinstance(parsed, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="backup.json hat ein ungültiges Format",
            )
        return parsed

    @staticmethod
    def _collect_table_rows(tables_payload: list[dict]) -> dict[str, list[dict]]:
        table_rows: dict[str, list[dict]] = {}
        for table_entry in tables_payload:
            if not isinstance(table_entry, dict):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Backup enthält ungültige Tabellendaten",
                )
            table_name = str(table_entry.get("name") or "").strip()
            rows = table_entry.get("rows", [])
            if not table_name or not isinstance(rows, list):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Backup enthält ungültige Tabellenstruktur",
                )
            table_rows[table_name] = rows
        return table_rows

    def _ordered_table_names(self, metadata: MetaData) -> list[str]:
        inspector = inspect(self.engine)
        all_tables = set(inspector.get_table_names()) - _EXCLUDED_TABLES
        ordered = [table.name for table in metadata.sorted_tables if table.name in all_tables]
        remaining = sorted(name for name in all_tables if name not in ordered)
        return ordered + remaining

    @staticmethod
    def _serialize_row(row: dict) -> dict:
        serialized = {}
        for key, value in row.items():
            if isinstance(value, datetime):
                serialized[key] = {"__type__": "datetime", "value": value.isoformat()}
            elif isinstance(value, date):
                serialized[key] = {"__type__": "date", "value": value.isoformat()}
            elif isinstance(value, time):
                serialized[key] = {"__type__": "time", "value": value.isoformat()}
            elif isinstance(value, Decimal):
                serialized[key] = {"__type__": "decimal", "value": str(value)}
            else:
                serialized[key] = value
        return serialized

    @staticmethod
    def _deserialize_row(row: dict, table) -> dict:
        if not isinstance(row, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ungültiger Datensatz für Tabelle {table.name}",
            )

        prepared = {}
        for column in table.columns:
            if column.name not in row:
                continue
            value = row[column.name]
            if isinstance(value, dict) and value.get("__type__"):
                prepared[column.name] = DatabaseBackupService._deserialize_typed_value(value)
            else:
                prepared[column.name] = value
        return prepared

    @staticmethod
    def _deserialize_typed_value(value: dict):
        value_type = value.get("__type__")
        raw = value.get("value")
        if raw is None:
            return None
        if value_type == "datetime":
            return datetime.fromisoformat(raw)
        if value_type == "date":
            return date.fromisoformat(raw)
        if value_type == "time":
            return time.fromisoformat(raw)
        if value_type == "decimal":
            return Decimal(raw)
        return raw

    def _sync_sequences(self, table_names: list[str], metadata: MetaData) -> None:
        # All operations use self.db (the same connection/transaction as the restore) to
        # avoid opening a second connection via self.engine.  A second connection would
        # deadlock: TRUNCATE … RESTART IDENTITY holds ACCESS EXCLUSIVE locks on the
        # sequences inside the open restore transaction, and any new connection that
        # needs even a SHARE lock on those sequences (e.g. metadata reflection) would
        # block forever because PostgreSQL's deadlock detector cannot see that the
        # restore transaction is itself waiting for the reflection to complete.
        #
        # metadata was already reflected BEFORE the TRUNCATE (in restore_from_backup_zip),
        # so using it here is safe — no second connection is needed.
        for table_name in table_names:
            table = metadata.tables.get(table_name)
            # Skip tables without an 'id' column (e.g. product_category uses a composite
            # PK with no auto-increment id).
            if table is None or "id" not in table.c:
                continue

            seq_name = self.db.execute(
                text("SELECT pg_get_serial_sequence(:table_name, 'id')"),
                {"table_name": table_name},
            ).scalar()
            if not seq_name:
                continue

            max_id = self.db.execute(select(func.max(table.c.id))).scalar()
            if max_id is None:
                # For empty tables, set sequence last-value to 1 and mark is_called=False.
                # The next nextval() will then return 1.
                self.db.execute(
                    text("SELECT setval(CAST(:seq_name AS regclass), 1, false)"),
                    {"seq_name": seq_name},
                )
            else:
                self.db.execute(
                    text("SELECT setval(CAST(:seq_name AS regclass), :value, true)"),
                    {"seq_name": seq_name, "value": int(max_id)},
                )
