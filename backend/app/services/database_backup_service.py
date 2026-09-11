from __future__ import annotations

import hashlib
import io
import json
import logging
import stat
import zipfile
from datetime import date, datetime, time, timezone
from decimal import Decimal
from pathlib import Path, PurePosixPath
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import Table, MetaData, func, inspect, select, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import DataError, IntegrityError

from app.core.maintenance_lock import maintenance_gate
from app.services.file_service import UPLOADS_DIR
from app.services.backup_media import MediaReplacement, recovery_pending, recover_media
from app.services.audit_log_service import AuditLogService

logger = logging.getLogger(__name__)
BACKUP_FORMAT = "kickerkasse-db-backup-v2"
BACKUP_JSON_FILE = "backup.json"
MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
MAX_EXPANDED_BYTES = 512 * 1024 * 1024
MAX_JSON_BYTES = 128 * 1024 * 1024
MAX_ENTRIES = 10000
_EXCLUDED_TABLES = {"alembic_version", "schema_migrations"}


def invalid(message):
    raise HTTPException(400, message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def safe_media_name(name):
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        invalid("Ungültiger Medienpfad")
    path = PurePosixPath(name)
    if path.is_absolute() or path.as_posix() != name or any(part in {".", ".."} or part.startswith(".restore-") for part in path.parts):
        invalid("Ungültiger Medienpfad")
    # Uniform names on Linux and Windows; reject alternate streams and aliases.
    if any(part.endswith((".", " ")) or any(ord(char) < 32 or char in '<>"|?*' for char in part)
           or part.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *("COM" + str(n) for n in range(1, 10)), *("LPT" + str(n) for n in range(1, 10))}
           for part in path.parts):
        invalid("Ungültiger Medienpfad")
    return name


class DatabaseBackupService:
    def __init__(self, db: Session, uploads_dir=None):
        self.db = db
        self.engine = db.get_bind()
        self.uploads_dir = Path(uploads_dir or UPLOADS_DIR)

    def _metadata(self):
        metadata = MetaData()
        metadata.reflect(bind=self.db.connection())
        return metadata

    def _ordered_table_names(self, metadata):
        return [table.name for table in metadata.sorted_tables if table.name not in _EXCLUDED_TABLES]

    def _schema(self, metadata):
        inspector = inspect(self.db.connection())
        tables = {}
        for name in self._ordered_table_names(metadata):
            table = metadata.tables[name]
            tables[name] = {
                "columns": [{"name": col.name, "type": str(col.type), "nullable": col.nullable,
                             "default": str(col.server_default.arg) if col.server_default else None,
                             "enum_values": getattr(col.type, "enums", None)}
                            for col in table.columns],
                "primary_key": [col.name for col in table.primary_key],
                "foreign_keys": sorted([{"columns": fk["constrained_columns"], "table": fk["referred_table"],
                                          "targets": fk["referred_columns"], "options": fk.get("options", {})}
                                         for fk in inspector.get_foreign_keys(name)], key=lambda item: canonical(item)),
                "indexes": sorted([{key: item.get(key) for key in ("name", "column_names", "unique", "expressions", "dialect_options")}
                                   for item in inspector.get_indexes(name)], key=lambda item: canonical(item)),
                "checks": sorted(item["sqltext"] for item in inspector.get_check_constraints(name)),
                "unique": sorted([item["column_names"] for item in inspector.get_unique_constraints(name)]),
            }
        migrations = []
        if "schema_migrations" in metadata.tables:
            migrations = [list(row) for row in self.db.execute(text("SELECT version, step FROM schema_migrations ORDER BY version, step"))]
        return json.loads(canonical({"tables": tables, "migrations": migrations}))

    def _lock_tables(self, names, mode):
        quote = self.engine.dialect.identifier_preparer.quote
        self.db.execute(text("SET LOCAL lock_timeout = '5s'"))
        self.db.execute(text("LOCK TABLE " + ", ".join(quote(name) for name in names) + " IN " + mode + " MODE"))

    def create_backup_zip(self):
        with maintenance_gate(self.engine, exclusive=True):
            if recovery_pending(self.uploads_dir):
                invalid("Unabgeschlossene Wiederherstellung; Server zuerst neu starten")
            # Callers may have read authentication/settings. Start the snapshot afresh.
            self.db.rollback()
            try:
                metadata = self._metadata()
                names = self._ordered_table_names(metadata)
                self._lock_tables(names, "SHARE")
                exported = []
                for name in names:
                    table = metadata.tables[name]
                    query = table.select()
                    if len(table.primary_key):
                        query = query.order_by(*table.primary_key)
                    rows = [self._serialize_row(dict(row)) for row in self.db.execute(query).mappings()]
                    exported.append({"name": name, "rows": rows, "row_count": len(rows),
                                     "sha256": hashlib.sha256(canonical(rows)).hexdigest()})
                media = {}
                media_bytes = 0
                if self.uploads_dir.exists():
                    for path in sorted(self.uploads_dir.rglob("*")):
                        if path.is_symlink():
                            invalid("Medienverzeichnis enthält eine Verknüpfung")
                        if path.is_file():
                            name = path.relative_to(self.uploads_dir).as_posix()
                            if name.startswith(".restore-"):
                                continue
                            media_bytes += path.stat().st_size
                            if media_bytes > MAX_EXPANDED_BYTES or len(media) + 2 > MAX_ENTRIES:
                                invalid("Medien überschreiten die Sicherungsgrenzen")
                            media[safe_media_name(name)] = path.read_bytes()
                payload = {"format": BACKUP_FORMAT, "generated_at": datetime.now(timezone.utc).isoformat(),
                    "schema": self._schema(metadata), "tables": exported,
                    "media": [{"name": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                              for name, data in media.items()]}
                self._validate_references(exported, media)
                raw = canonical(payload)
                if len(raw) > MAX_JSON_BYTES or len(raw) + sum(map(len, media.values())) > MAX_EXPANDED_BYTES or len(media) + 1 > MAX_ENTRIES:
                    invalid("Sicherung überschreitet die unterstützte Größe")
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr(BACKUP_JSON_FILE, raw)
                    for name, data in media.items():
                        archive.writestr("media/" + name, data)
                content = buffer.getvalue()
                if len(content) > MAX_ARCHIVE_BYTES:
                    invalid("Sicherung überschreitet 256 MiB")
                self.db.commit()
                return content, f"kickerkasse-backup-{datetime.now():%Y%m%d-%H%M%S}.zip"
            except BaseException:
                self.db.rollback()
                raise

    @staticmethod
    def _read_archive(content):
        if len(content) > MAX_ARCHIVE_BYTES:
            raise HTTPException(413, "Backup-ZIP darf höchstens 256 MiB groß sein")
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                entries = archive.infolist()
                if not entries or len(entries) > MAX_ENTRIES or sum(item.file_size for item in entries) > MAX_EXPANDED_BYTES:
                    invalid("Backup überschreitet die Entpackgrenzen")
                names = [item.filename for item in entries]
                if len(set(name.casefold() for name in names)) != len(names):
                    invalid("Backup enthält doppelte Dateinamen")
                for item in entries:
                    if item.is_dir() or item.flag_bits & 1 or stat.S_ISLNK(item.external_attr >> 16):
                        invalid("Backup enthält unzulässige ZIP-Einträge")
                    if item.filename != BACKUP_JSON_FILE:
                        if not item.filename.startswith("media/"):
                            invalid("Unbekannter Eintrag im Backup")
                        safe_media_name(item.filename[6:])
                    elif item.file_size > MAX_JSON_BYTES:
                        invalid("backup.json ist zu groß")
                if BACKUP_JSON_FILE not in names:
                    invalid("backup.json fehlt")
                def unique_object(pairs):
                    result = {}
                    for key, value in pairs:
                        if key in result:
                            invalid("Doppelter JSON-Schlüssel im Backup")
                        result[key] = value
                    return result
                payload = json.loads(archive.read(BACKUP_JSON_FILE), object_pairs_hook=unique_object,
                                     parse_constant=lambda value: invalid("Ungültiger Zahlenwert"))
                if not isinstance(payload, dict) or payload.get("format") != BACKUP_FORMAT:
                    invalid("Vollständige Sicherung im Format v2 erforderlich. Alte v1- und Teilarchive werden nicht eingespielt.")
                manifest = payload.get("media")
                if not isinstance(manifest, list):
                    invalid("Medienmanifest fehlt")
                media = {}
                for item in manifest:
                    if not isinstance(item, dict):
                        invalid("Ungültiges Medienmanifest")
                    name = safe_media_name(item.get("name"))
                    if name in media or "media/" + name not in names:
                        invalid("Fehlende oder doppelte Mediendatei")
                    data = archive.read("media/" + name)
                    if len(data) != item.get("size") or hashlib.sha256(data).hexdigest() != item.get("sha256"):
                        invalid("Medienprüfsumme oder Dateigröße stimmt nicht")
                    media[name] = data
                if set(names) != {BACKUP_JSON_FILE, *("media/" + name for name in media)}:
                    invalid("ZIP-Inhalt und Medienmanifest stimmen nicht überein")
                return payload, media
        except HTTPException:
            raise
        except (ValueError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile, OSError) as exc:
            raise HTTPException(400, "Ungültige oder beschädigte Backup-ZIP") from exc

    @staticmethod
    def _validate_references(tables, media):
        fields = {"products": ("image_path",), "members": ("photo_path",),
                  "app_settings": ("logo_path", "kasse_products_background_path")}
        for table in tables:
            for row in table["rows"]:
                for field in fields.get(table["name"], ()):
                    value = row.get(field)
                    if value and safe_media_name(value) not in media:
                        invalid("Referenzierte Mediendatei fehlt: " + value)

    def _prepare_tables(self, payload, metadata):
        if payload.get("schema") != self._schema(metadata):
            invalid("Schema oder Migrationsstand passen nicht zur laufenden Installation")
        entries = payload.get("tables")
        if not isinstance(entries, list):
            invalid("Vollständiges Tabellenmanifest fehlt")
        rows = {}
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
                invalid("Ungültige Tabelle")
            name = entry["name"]
            if name in rows or name not in payload["schema"]["tables"]:
                invalid("Doppelte oder unbekannte Tabelle")
            data = entry.get("rows")
            if not isinstance(data, list) or entry.get("row_count") != len(data) or entry.get("sha256") != hashlib.sha256(canonical(data)).hexdigest():
                invalid("Tabellenprüfsumme oder Zeilenanzahl stimmt nicht")
            table = metadata.tables[name]
            if any(not isinstance(row, dict) or set(row) != set(table.c.keys()) for row in data):
                invalid("Unvollständiger Datensatz in " + name)
            try:
                rows[name] = [self._deserialize_row(row, table) for row in data]
            except (ValueError, TypeError) as exc:
                raise HTTPException(400, "Ungültiger Datentyp in " + name) from exc
        if set(rows) != set(self._ordered_table_names(metadata)):
            invalid("Backup enthält nicht alle Tabellen; aktuelle Daten wurden nicht ersetzt")
        if not any(row.get("role") == "TOP_ADMIN" and row.get("is_active") for row in rows.get("users", [])):
            invalid("Sicherung enthält keinen aktiven TopAdmin")
        # Validate foreign keys before any destructive SQL, including self references.
        for name, records in rows.items():
            for fk in payload["schema"]["tables"][name]["foreign_keys"]:
                targets = {tuple(record[col] for col in fk["targets"]) for record in rows[fk["table"]]}
                if any(all(row[col] is not None for col in fk["columns"]) and
                       tuple(row[col] for col in fk["columns"]) not in targets for row in records):
                    invalid("Ungültige Tabellenreferenz in " + name)
        return rows

    def restore_from_backup_zip(self, file_name, content, *, actor_username=None):
        if not file_name or not file_name.lower().endswith(".zip"):
            invalid("Bitte eine ZIP-Datei als Backup hochladen")
        payload, media = self._read_archive(content)
        with maintenance_gate(self.engine, exclusive=True):
            if recovery_pending(self.uploads_dir):
                invalid("Unabgeschlossene Wiederherstellung; Server zuerst neu starten")
            self.db.rollback()
            self.db.expunge_all()
            replacement = MediaReplacement(self.uploads_dir, str(uuid4()))
            committed = False
            try:
                metadata = self._metadata()
                names = self._ordered_table_names(metadata)
                self._lock_tables(names, "ACCESS EXCLUSIVE")
                rows = self._prepare_tables(payload, metadata)
                self._validate_references(payload["tables"], media)
                quote = self.engine.dialect.identifier_preparer.quote
                staging = {}
                # PostgreSQL validates types, NOT NULL, CHECK and unique constraints in
                # temporary tables BEFORE TRUNCATE. No live table is touched by this phase.
                for name in names:
                    temporary = "restore_" + uuid4().hex
                    self.db.execute(text(f"CREATE TEMP TABLE {quote(temporary)} (LIKE {quote(name)} INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES) ON COMMIT DROP"))
                    temporary_table = Table(temporary, MetaData(), autoload_with=self.db.connection())
                    if rows[name]:
                        self.db.execute(temporary_table.insert(), rows[name])
                    staging[name] = temporary
                previous_session_version = self.db.execute(text("SELECT COALESCE(MAX(session_version), 0) FROM users")).scalar()
                next_session_version = max(previous_session_version, *(row["session_version"] for row in rows["users"])) + 1
                if next_session_version > 2147483647:
                    invalid("Sitzungszähler überschreitet den unterstützten Bereich")
                replacement.prepare(media)
                self.db.execute(text("TRUNCATE TABLE " + ", ".join(quote(name) for name in names) + " RESTART IDENTITY"))
                for name in names:
                    self.db.execute(text(f"INSERT INTO {quote(name)} SELECT * FROM {quote(staging[name])}"))
                self._sync_sequences(names, metadata)
                # All pre-restore cookies are invalidated, even if user IDs coincide.
                if "users" in metadata.tables:
                    self.db.execute(text("UPDATE users SET session_version = :version"),
                                    {"version": next_session_version})
                if "password_reset_tokens" in metadata.tables:
                    self.db.execute(text("UPDATE password_reset_tokens SET used_at = CURRENT_TIMESTAMP WHERE used_at IS NULL"))
                AuditLogService(self.db).log(entity_type="database_backup", action="RESTORED",
                    entity_name=replacement.operation_id, user_username=actor_username,
                    new_value={"filename": file_name, "sha256": hashlib.sha256(content).hexdigest(),
                               "tables": len(names), "media_files": len(media)})
                replacement.apply()
                self.db.commit()
                committed = True
            except BaseException as exc:
                self.db.rollback()
                # Commit acknowledgement can be lost: read the durable marker before
                # deciding which media generation belongs to the database.
                if recovery_pending(self.uploads_dir):
                    recover_media(self.db, self.uploads_dir)
                    self.db.rollback()
                elif replacement.stage.exists():
                    replacement.cleanup()
                if isinstance(exc, (DataError, IntegrityError)):
                    raise HTTPException(400, "Backup verletzt Datenbankregeln; Wiederherstellung zurückgesetzt") from exc
                raise
            finally:
                if committed:
                    try:
                        replacement.cleanup()
                    except OSError:
                        logger.exception("Restore committed; media cleanup deferred to restart")
            return {"restored_tables": len(names), "restored_rows": sum(map(len, rows.values())),
                    "table_row_counts": {name: len(records) for name, records in rows.items()},
                    "restored_media_files": len(media)}

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
        invalid("Unbekannter Datentyp im Backup")

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
