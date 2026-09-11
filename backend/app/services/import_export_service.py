from __future__ import annotations

import json
import stat
import csv
import io
import zipfile
from pathlib import Path, PurePosixPath

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from pydantic import ValidationError
from app.schemas.data_import import IMPORT_SCHEMAS
from app.schemas.validation import MAX_INT

from app.models import (
    BalanceLog,
    Category,
    DeckelItem,
    Member,
    MemberBalanceCorrectionLog,
    Product,
    ProductStockCorrectionLog,
    Transaction,
    TransactionItem,
    User,
    product_category,
)
from app.repositories import MemberRepository
from app.services.file_service import (
    MEMBERS_DIR,
    PRODUCTS_DIR,
    delete_member_photo,
    delete_product_image,
    ensure_upload_directories,
    get_full_path,
)


SECTION_ORDER = ("categories", "products", "members")
REPLACE_ORDER = ("members", "products", "categories")
MEDIA_SECTIONS = {"products", "members"}
IMAGE_EXTENSIONS = {".avif",".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
MAX_MEDIA_SIZE = 10 * 1024 * 1024

SECTION_HEADERS = {
    "categories": [
        "dataset",
        "id",
        "name",
        "description",
        "color",
        "display_order",
        "is_active_in_kasse",
    ],
    "products": [
        "dataset",
        "id",
        "name",
        "description",
        "warengruppe",
        "price_cents",
        "member_price_cents",
        "is_discountable",
        "minimum_stock_quantity",
        "notify_on_low_stock",
        "requires_guest_list",
        "opens_small_parts_drawer",
        "stock_quantity",
        "is_unlimited_stock",
        "is_variable_price",
        "is_visible_in_kasse",
        "is_active",
        "tax_rate",
        "category_names",
    ],
    "members": [
        "dataset",
        "id",
        "member_number",
        "first_name",
        "last_name",
        "membership_number",
        "email",
        "phone",
        "notes",
        "has_discount",
        "balance_cents",
        "archived_at",
    ],
}

TRANSFER_VERSION = "2"
MAX_TRANSFER_BYTES = 128 * 1024 * 1024
MAX_EXPANDED_BYTES = 256 * 1024 * 1024
MAX_ENTRIES = 10000
MAX_ROWS = 10000
for headers in SECTION_HEADERS.values():
    headers.insert(0, "transfer_version")

SECTION_HEADER_SIGNATURES = {
    "categories": {"name", "display_order", "is_active_in_kasse"},
    "products": {"name", "price_cents", "stock_quantity"},
    "members": {"first_name", "last_name", "balance_cents"},
}


class ImportExportService:
    def __init__(self, db: Session):
        self.db = db

    def export_sections(self, sections, include_media):
        from contextlib import nullcontext
        from sqlalchemy import text
        from app.models import Base
        from app.core.maintenance_lock import maintenance_gate
        engine = self.db.get_bind()
        gate = maintenance_gate(engine, exclusive=True) if engine.dialect.name == "postgresql" else nullcontext()
        with gate:
            self.db.rollback()
            try:
                if engine.dialect.name == "postgresql":
                    quote = engine.dialect.identifier_preparer.quote
                    self.db.execute(text("SET LOCAL lock_timeout = '5s'"))
                    self.db.execute(text("LOCK TABLE " + ", ".join(quote(table.name) for table in Base.metadata.sorted_tables) + " IN SHARE MODE"))
                result = self._export_sections_unlocked(sections, include_media)
                if len(result[0]) > MAX_TRANSFER_BYTES:
                    raise HTTPException(413, "Export überschreitet 128 MiB")
                if result[1] == "application/zip":
                    with zipfile.ZipFile(io.BytesIO(result[0])) as archive:
                        self._check_archive(archive)
                self.db.commit()
                return result
            except BaseException:
                self.db.rollback()
                raise

    def _export_sections_unlocked(self, sections: list[str], include_media: bool) -> tuple[bytes, str, str]:
        normalized_sections = self._normalize_sections(sections)
        if not normalized_sections:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mindestens ein Bereich muss ausgewählt werden",
            )

        csv_payloads = {
            "categories": self._build_categories_csv(),
            "products": self._build_products_csv(),
            "members": self._build_members_csv(),
        }

        for section in normalized_sections:
            self._read_csv_rows(csv_payloads[section], section + ".csv")

        if len(normalized_sections) == 1 and not include_media:
            section = normalized_sections[0]
            return (
                csv_payloads[section],
                "text/csv; charset=utf-8",
                f"{section}.csv",
            )

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for section in normalized_sections:
                archive.writestr(f"{section}.csv", csv_payloads[section])

            if include_media:
                self._write_export_media(archive, normalized_sections)

        return buffer.getvalue(), "application/zip", "import-export.zip"

    def analyze_import(
        self,
        file_name: str,
        content: bytes,
        media_file_name: str | None = None,
        media_content: bytes | None = None,
        source_mode: str = "foreign",
        sections: list[str] | None = None,
        replace_sections: list[str] | None = None,
    ) -> dict:
        parsed_data = self._parse_data_bundle(file_name, content)
        provided_media = self._parse_external_media_bundle(media_file_name, media_content)

        detected_sections = [section for section in SECTION_ORDER if section in parsed_data["rows"]]
        supported_media_sections = [section for section in detected_sections if section in MEDIA_SECTIONS]
        embedded_media_sections = sorted(
            section for section in supported_media_sections if parsed_data["embedded_media"].get(section)
        )
        provided_media_sections = sorted(
            section for section in supported_media_sections if provided_media.get(section)
        )

        selected = self._normalize_sections(sections if sections is not None else detected_sections)
        replacing = self._normalize_sections(replace_sections or [])
        if set(selected) - set(detected_sections) or set(replacing) - set(selected):
            raise HTTPException(400, "Ungültige Bereichsauswahl")
        plan = self._plan(parsed_data["rows"], selected, replacing, source_mode)
        media = self._merge_media_entries(parsed_data["embedded_media"], provided_media)
        for section in selected:
            source_ids = {str(row.get("id")) for row in parsed_data["rows"].get(section, [])}
            for source_id in sorted(set(media.get(section, {})) - source_ids):
                plan["conflicts"].append({"section": section, "row": None, "source_id": source_id,
                    "message": f"Medien für Quell-ID {source_id} haben keinen passenden Datensatz"})
        return {
            **plan,
            "data_format": parsed_data["format"],
            "detected_sections": detected_sections,
            "row_counts": {
                section: len(parsed_data["rows"].get(section, []))
                for section in detected_sections
            },
            "supports_media_sections": supported_media_sections,
            "embedded_media_sections": embedded_media_sections,
            "provided_media_sections": provided_media_sections,
            "can_import_media": bool(embedded_media_sections or provided_media_sections),
        }

    def _import_sections_uncommitted(
        self,
        file_name: str,
        content: bytes,
        sections: list[str] | None = None,
        *,
        replace_sections: list[str] | None = None,
        import_media: bool = False,
        media_file_name: str | None = None,
        media_content: bytes | None = None,
    ) -> dict:
        parsed_data = self._parse_data_bundle(file_name, content)
        available_sections = [section for section in SECTION_ORDER if section in parsed_data["rows"]]
        selected_sections = self._normalize_sections(sections if sections is not None else available_sections)

        if not selected_sections:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Es wurden keine importierbaren Bereiche erkannt",
            )

        invalid_sections = [section for section in selected_sections if section not in available_sections]
        if invalid_sections:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Diese Bereiche sind in der Datei nicht enthalten: {', '.join(invalid_sections)}",
            )

        normalized_replace_sections = self._normalize_sections(replace_sections or [])
        invalid_replace_sections = [section for section in normalized_replace_sections if section not in selected_sections]
        if invalid_replace_sections:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Diese Bereiche können nur ersetzend importiert werden, "
                    f"wenn sie auch ausgewählt sind: {', '.join(invalid_replace_sections)}"
                ),
            )

        media_entries = self._merge_media_entries(
            parsed_data["embedded_media"],
            self._parse_external_media_bundle(media_file_name, media_content),
        ) if import_media else {}

        for section in selected_sections:
            self._validate_import_rows(section, parsed_data["rows"][section])

        plan = self._plan(parsed_data["rows"], selected_sections, normalized_replace_sections, self._source_mode)
        if plan["conflicts"]:
            raise HTTPException(409, {"message": "Importkonflikte zuerst beheben", **plan})
        deleted_media_ids = {"products": [], "members": []}

        try:
            replaced_counts = self._replace_selected_sections(normalized_replace_sections, deleted_media_ids)
            if normalized_replace_sections:
                self.db.expunge_all()

            for product_id in deleted_media_ids["products"]:
                self._remove_staged_folder("products", product_id)
            for member_id in deleted_media_ids["members"]:
                self._remove_staged_folder("members", member_id)

            results = {}
            for section in SECTION_ORDER:
                if section not in selected_sections:
                    continue

                rows = parsed_data["rows"].get(section, [])
                if section == "categories":
                    results[section] = self._import_categories(rows)
                elif section == "products":
                    results[section] = self._import_products(rows, media_entries.get("products", {}), import_media)
                elif section == "members":
                    results[section] = self._import_members(rows, media_entries.get("members", {}), import_media)

                if section in replaced_counts:
                    results[section]["replaced_deleted"] = replaced_counts[section]

            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return {
            "imported_sections": selected_sections,
            "results": results,
        }

    def _plan(self, rows_by_section, selected, replacing, source_mode):
        if source_mode not in {"foreign", "same"}:
            raise HTTPException(400, "Unbekannter Quellmodus")
        from app.models import Base
        models = {"categories": Category, "products": Product, "members": Member}
        conflicts, records = [], []
        def conflict(section, row, message):
            conflicts.append({"section": section, "row": row.get("__row_number"), "source_id": row.get("id"), "message": message})
        # Inspect all FK relationships instead of maintaining an incomplete list of
        # histories. This includes guests, deckels, vouchers, accounts and future FKs.
        for section in replacing:
            model = models[section]
            for entity in self.db.query(model).all():
                reasons = []
                if section == "categories" and entity.is_fixed:
                    continue
                if section == "members" and (entity.balance_cents or entity.role):
                    reasons.append("Guthaben oder Rolle")
                if section == "products" and entity.stock_quantity:
                    reasons.append("Lagerbestand muss zuerst ausgeglichen werden")
                for table in Base.metadata.tables.values():
                    for fk in table.foreign_keys:
                        if fk.column.table.name != model.__tablename__:
                            continue
                        if table.name == "product_category":
                            if section == "products" or "products" in replacing:
                                continue
                        if self.db.execute(table.select().where(fk.parent == entity.id).limit(1)).first():
                            reasons.append(table.name)
                if reasons:
                    conflict(section, {}, f"Ersetzen gesperrt: {entity.name} (ID {entity.id}): {', '.join(sorted(set(reasons)))}")
        categories = {category.name for category in self.db.query(Category).all()
                      if "categories" not in replacing or category.is_fixed}
        categories.update(row.get("name") for row in rows_by_section.get("categories", []) if "categories" in selected)
        initial_balance = initial_stock = 0
        for section in selected:
            model = models[section]
            seen_ids, seen_keys, seen_numbers = set(), set(), set()
            for row in rows_by_section.get(section, []):
                try:
                    self._validate_import_rows(section, [row])
                except HTTPException as exc:
                    conflict(section, row, str(exc.detail))
                    continue
                source_id = self._parse_optional_int(row.get("id"))
                name = row.get("name") if section != "members" else self._compose_member_name(row["first_name"], row["last_name"])
                key = row.get("membership_number") or name if section == "members" else name
                number = row.get("member_number") if section == "members" else None
                if (source_id and source_id in seen_ids) or key in seen_keys or (number and number in seen_numbers):
                    conflict(section, row, "Doppelte Quell-ID, Mitgliedsnummer oder fachlicher Schlüssel in der Datei")
                seen_ids.add(source_id); seen_keys.add(key)
                if number: seen_numbers.add(number)
                target = self.db.get(model, source_id) if source_mode == "same" and source_id and section not in replacing else None
                if target and target.name != name:
                    conflict(section, row, f"ID {source_id} gehört zu '{target.name}', nicht zu '{name}'")
                    target = None
                matches = [] if section in replacing else self.db.query(model).filter(model.name == name).all()
                if section == "members" and row.get("membership_number") and section not in replacing:
                    matches += self.db.query(Member).filter_by(membership_number=row["membership_number"]).all()
                if any(item.id != (target.id if target else None) for item in matches):
                    # Fixed system categories are a documented, immutable exception.
                    fixed = next((item for item in matches if section == "categories" and item.is_fixed), None)
                    if fixed:
                        target = fixed
                    else:
                        conflict(section, row, "Fachlicher Schlüssel existiert bereits; keine automatische Zusammenführung")
                if section == "categories":
                    fixed = self.db.query(Category).filter_by(name=name).first()
                    if fixed and fixed.is_fixed:
                        target = fixed
                row["__target_id"] = target.id if target else None
                if section == "members":
                    balance = int(row["balance_cents"])
                    if target:
                        if target.balance_cents != balance:
                            conflict(section, row, "Bestehendes Guthaben nur über Aufladung oder Korrektur ändern")
                        if self.db.query(User.id).filter_by(member_id=target.id).first():
                            conflict(section, row, "Verknüpftes Benutzerkonto: Änderungen über die Mitgliederverwaltung durchführen")
                        if target.member_number != self._parse_optional_int(row.get("member_number")):
                            conflict(section, row, "Bestehende interne Mitgliedsnummer darf nicht umgebucht werden")
                        incoming_archive = row.get("archived_at") or ""
                        stored_archive = str(target.archived_at) if target.archived_at else ""
                        if incoming_archive != stored_archive:
                            conflict(section, row, "Archivstatus nur über die Mitgliederverwaltung ändern")
                    else:
                        initial_balance += balance
                        if source_mode == "foreign":
                            row["member_number"] = ""
                        elif number and section not in replacing and self.db.query(Member.id).filter_by(member_number=int(number)).first():
                            conflict(section, row, "Interne Mitgliedsnummer ist bereits vergeben")
                if section == "products":
                    if target and (target.stock_quantity != int(row["stock_quantity"]) or
                                   target.is_unlimited_stock != self._parse_bool(row["is_unlimited_stock"], False)):
                        conflict(section, row, "Bestehenden Bestand und Bestandsart nur über Lagerverwaltung ändern")
                    if not target: initial_stock += int(row["stock_quantity"])
                    missing = set(self._parse_category_names(row.get("category_names"))) - categories
                    if missing:
                        conflict(section, row, "Fehlende Kategorien: " + ", ".join(sorted(missing)))
                records.append({"section": section, "row": row["__row_number"], "name": name,
                                "source_id": source_id, "target_id": target.id if target else None,
                                "action": "update" if target else "create"})
        return {"conflicts": conflicts, "records": records, "initial_balance_cents": initial_balance,
                "initial_stock_quantity": initial_stock, "source_mode": source_mode}

    def _remove_staged_folder(self, section, identifier):
        from app.services.backup_media import safe_remove
        folder = self._staged_media / section / str(identifier)
        if folder.exists():
            safe_remove(folder, self._staged_media)

    def import_sections(self, file_name, content, sections=None, *, replace_sections=None,
                        import_media=False, media_file_name=None, media_content=None,
                        source_mode="foreign", acknowledge_initial_values=False, actor_username=None):
        from contextlib import nullcontext
        from uuid import uuid4
        from sqlalchemy import text
        from app.models import Base
        from app.core.maintenance_lock import maintenance_gate
        from app.services.file_service import UPLOADS_DIR
        from app.services.backup_media import MediaReplacement, recover_media, recovery_pending
        from app.services.audit_log_service import AuditLogService
        engine = self.db.get_bind()
        gate = maintenance_gate(engine, exclusive=True) if engine.dialect.name == "postgresql" else nullcontext()
        with gate:
            self.db.rollback()
            self.db.expire_all()
            if recovery_pending(UPLOADS_DIR):
                raise HTTPException(503, "Unterbrochene Datenpflege: Server zuerst neu starten")
            replacement = None
            commit = self.db.commit
            try:
                if engine.dialect.name == "postgresql":
                    quote = engine.dialect.identifier_preparer.quote
                    self.db.execute(text("SET LOCAL lock_timeout = '5s'"))
                    self.db.execute(text("LOCK TABLE " + ", ".join(quote(table.name) for table in Base.metadata.sorted_tables) + " IN SHARE ROW EXCLUSIVE MODE"))
                parsed = self._parse_data_bundle(file_name, content)
                selected = self._normalize_sections(sections if sections is not None else list(parsed["rows"]))
                replacing = self._normalize_sections(replace_sections or [])
                if not selected or set(selected) - set(parsed["rows"]) or set(replacing) - set(selected):
                    raise HTTPException(400, "Ungültige Bereichsauswahl")
                plan = self._plan(parsed["rows"], selected, replacing, source_mode)
                if plan["conflicts"]:
                    raise HTTPException(409, {"message": "Importkonflikte zuerst beheben", **plan})
                if (plan["initial_balance_cents"] or plan["initial_stock_quantity"]) and not acknowledge_initial_values:
                    raise HTTPException(409, {"message": "Anfangsguthaben und Anfangsbestände ausdrücklich bestätigen", **plan})
                # Validate media before any database or live-media mutation.
                media = self._merge_media_entries(parsed["embedded_media"], self._parse_external_media_bundle(media_file_name, media_content))
                for section in selected:
                    ids = {str(row.get("id")) for row in parsed["rows"][section]}
                    if import_media and set(media.get(section, {})) - ids:
                        raise HTTPException(400, "Medien ohne passenden Datensatz")
                replacement = MediaReplacement(UPLOADS_DIR, str(uuid4()), entity_type="import_export", action="IMPORTED")
                existing = {}
                total = 0
                if UPLOADS_DIR.exists():
                    for path in UPLOADS_DIR.rglob("*"):
                        if path.is_symlink(): raise HTTPException(400, "Medienverknüpfung nicht zulässig")
                        if path.is_file() and not path.relative_to(UPLOADS_DIR).parts[0].startswith(".restore-"):
                            total += path.stat().st_size
                            if total > MAX_EXPANDED_BYTES: raise HTTPException(413, "Medienbestand zu groß für Datentransfer")
                            existing[path.relative_to(UPLOADS_DIR).as_posix()] = path.read_bytes()
                replacement.prepare(existing)
                self._staged_media = replacement.stage / "new"
                self._source_mode = source_mode
                self.db.commit = self.db.flush
                result = self._import_sections_uncommitted(file_name, content, selected,
                    replace_sections=replacing, import_media=import_media,
                    media_file_name=media_file_name, media_content=media_content)
                AuditLogService(self.db).log(entity_type="import_export", action="IMPORTED",
                    entity_name=replacement.operation_id, user_username=actor_username,
                    new_value={**result, "source_mode": source_mode, "initial_balance_cents": plan["initial_balance_cents"],
                               "initial_stock_quantity": plan["initial_stock_quantity"], "records": plan["records"]})
                replacement.apply()
                commit()
            except BaseException:
                self.db.rollback()
                if replacement and recovery_pending(UPLOADS_DIR):
                    recover_media(self.db, UPLOADS_DIR)
                    self.db.rollback()
                elif replacement and replacement.stage.exists():
                    replacement.cleanup()
                raise
            finally:
                self.db.commit = commit
            try:
                replacement.cleanup()
            except OSError:
                import logging
                logging.getLogger(__name__).exception("Import committed; media cleanup deferred to restart")
            return result

    def _build_categories_csv(self) -> bytes:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=SECTION_HEADERS["categories"])
        writer.writeheader()

        categories = self.db.query(Category).order_by(Category.display_order, Category.name).all()
        for category in categories:
            writer.writerow({
                "transfer_version": TRANSFER_VERSION,
                "dataset": "categories",
                "id": category.id,
                "name": category.name,
                "description": category.description or "",
                "color": category.color or "",
                "display_order": category.display_order,
                "is_active_in_kasse": self._format_bool(category.is_active_in_kasse),
            })

        return output.getvalue().encode("utf-8-sig")

    def _build_products_csv(self) -> bytes:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=SECTION_HEADERS["products"])
        writer.writeheader()

        products = self.db.query(Product).order_by(Product.name).all()
        for product in products:
            writer.writerow({
                "transfer_version": TRANSFER_VERSION,
                "dataset": "products",
                "id": product.id,
                "name": product.name,
                "description": product.description or "",
                "warengruppe": product.warengruppe or "",
                "price_cents": product.price_cents,
                "member_price_cents": "" if product.member_price_cents is None else product.member_price_cents,
                "is_discountable": self._format_bool(product.is_discountable),
                "stock_quantity": product.stock_quantity,
                "minimum_stock_quantity": product.minimum_stock_quantity,
                "notify_on_low_stock": self._format_bool(product.notify_on_low_stock),
                "requires_guest_list": self._format_bool(product.requires_guest_list),
                "opens_small_parts_drawer": self._format_bool(product.opens_small_parts_drawer),
                "is_unlimited_stock": self._format_bool(product.is_unlimited_stock),
                "is_variable_price": self._format_bool(product.is_variable_price),
                "is_visible_in_kasse": self._format_bool(product.is_visible_in_kasse),
                "is_active": self._format_bool(product.is_active),
                "tax_rate": product.tax_rate,
                "category_names": json.dumps(sorted(category.name for category in product.categories), ensure_ascii=False),
            })

        return output.getvalue().encode("utf-8-sig")

    def _build_members_csv(self) -> bytes:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=SECTION_HEADERS["members"])
        writer.writeheader()

        members = self.db.query(Member).order_by(Member.member_number, Member.last_name, Member.first_name).all()
        for member in members:
            writer.writerow({
                "transfer_version": TRANSFER_VERSION,
                "dataset": "members",
                "id": member.id,
                "member_number": member.member_number,
                "first_name": member.first_name,
                "last_name": member.last_name,
                "membership_number": member.membership_number or "",
                "email": member.email or "",
                "phone": member.phone or "",
                "notes": member.notes or "",
                "has_discount": self._format_bool(member.has_discount),
                "balance_cents": member.balance_cents,
                "archived_at": member.archived_at.isoformat() if member.archived_at else "",
            })

        return output.getvalue().encode("utf-8-sig")

    def _write_export_media(self, archive, sections):
        from app.services.file_service import get_product_original_image_path, get_member_original_photo_path
        for section, model, base, original_path in (
            ("products", Product, PRODUCTS_DIR, get_product_original_image_path),
            ("members", Member, MEMBERS_DIR, get_member_original_photo_path),
        ):
            if section not in sections:
                continue
            for entity in self.db.query(model).all():
                relative = entity.image_path if section == "products" else entity.photo_path
                main = get_full_path(relative) if relative else None
                main_stem = "image" if section == "products" else "photo"
                for stem, path in ((main_stem, main), ("original", original_path(entity.id))):
                    if path is None:
                        continue
                    try:
                        path.resolve().relative_to(base.resolve())
                    except ValueError as exc:
                        raise HTTPException(400, "Medienpfad liegt außerhalb des Bereichs") from exc
                    if path.is_symlink() or not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
                        raise HTTPException(400, "Referenzierte Mediendatei fehlt oder ist nicht unterstützt")
                    if path.stat().st_size > MAX_MEDIA_SIZE:
                        raise HTTPException(400, "Mediendatei überschreitet 10 MiB")
                    archive.writestr(f"media/{section}/{entity.id}/{stem}{path.suffix.lower()}", path.read_bytes())

    @staticmethod
    def _check_archive(archive):
        entries = archive.infolist()
        if len(entries) > MAX_ENTRIES or sum(item.file_size for item in entries) > MAX_EXPANDED_BYTES:
            raise HTTPException(413, "ZIP überschreitet die Entpackgrenzen")
        names = set()
        from app.services.database_backup_service import safe_media_name
        for item in entries:
            name = item.filename.rstrip("/")
            safe_media_name(name)
            if name.casefold() in names or item.flag_bits & 1 or stat.S_ISLNK(item.external_attr >> 16):
                raise HTTPException(400, "Doppelte oder unzulässige ZIP-Einträge")
            names.add(name.casefold())

    def _parse_data_bundle(self, file_name: str, content: bytes) -> dict:
        if len(content) > MAX_TRANSFER_BYTES:
            raise HTTPException(413, "Datendatei überschreitet 128 MiB")
        suffix = Path(file_name or "import.csv").suffix.lower()
        rows_by_section: dict[str, list[dict]] = {}
        embedded_media = {"products": {}, "members": {}}

        if suffix == ".zip":
            try:
                duplicate_sections = set()
                with zipfile.ZipFile(io.BytesIO(content)) as archive:
                    self._check_archive(archive)
                    for info in archive.infolist():
                        if info.is_dir():
                            continue
                        safe_path = self._safe_zip_path(info.filename)
                        if safe_path is None:
                            continue

                        if safe_path.parts[0] == "media":
                            self._collect_media_entry(embedded_media, safe_path, archive.read(info.filename))
                            continue

                        if safe_path.suffix.lower() != ".csv":
                            continue

                        entry_bytes = archive.read(info.filename)
                        entry_rows, section = self._read_csv_rows(entry_bytes, safe_path.name)
                        if section in rows_by_section:
                            duplicate_sections.add(section)
                            continue
                        rows_by_section[section] = entry_rows

                if duplicate_sections:
                    duplicates = ", ".join(sorted(duplicate_sections))
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Diese Bereiche sind mehrfach im Archiv enthalten: {duplicates}",
                    )
            except zipfile.BadZipFile as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Die hochgeladene ZIP-Datei ist beschädigt",
                ) from exc

            return {
                "format": "zip",
                "rows": rows_by_section,
                "embedded_media": embedded_media,
            }

        rows, section = self._read_csv_rows(content, file_name)
        rows_by_section[section] = rows
        return {
            "format": "csv",
            "rows": rows_by_section,
            "embedded_media": embedded_media,
        }

    def _parse_external_media_bundle(
        self,
        file_name: str | None,
        content: bytes | None,
    ) -> dict[str, dict[str, dict]]:
        media_entries = {"products": {}, "members": {}}
        if content is not None and len(content) > MAX_TRANSFER_BYTES:
            raise HTTPException(413, "Mediendatei überschreitet 128 MiB")
        if not file_name or content is None:
            return media_entries

        if Path(file_name).suffix.lower() != ".zip":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zusätzliche Mediadaten müssen als ZIP-Datei hochgeladen werden",
            )

        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                self._check_archive(archive)
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    safe_path = self._safe_zip_path(info.filename)
                    if safe_path is None or not safe_path.parts or safe_path.parts[0] != "media":
                        continue
                    self._collect_media_entry(media_entries, safe_path, archive.read(info.filename))
        except zipfile.BadZipFile as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Die zusätzliche Medien-Datei ist keine gültige ZIP-Datei",
            ) from exc

        return media_entries

    def _read_csv_rows(self, content: bytes, file_name: str) -> tuple[list[dict], str]:
        try:
            return self._read_csv_rows_unchecked(content, file_name)
        except csv.Error as exc:
            raise HTTPException(400, "Ungültige CSV oder zu großes CSV-Feld") from exc

    def _read_csv_rows_unchecked(self, content: bytes, file_name: str) -> tuple[list[dict], str]:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Datei '{file_name}' ist keine gültige UTF-8-CSV",
            ) from exc

        reader = csv.DictReader(io.StringIO(text))
        if len(reader.fieldnames or []) != len(set(reader.fieldnames or [])):
            raise HTTPException(400, "Doppelte CSV-Spalten")
        headers = [header.strip() for header in (reader.fieldnames or []) if header and header.strip()]
        if not headers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Datei '{file_name}' enthält keine CSV-Header",
            )

        section = self._detect_section(headers, file_name)
        if len(set(headers)) != len(headers) or set(headers) - set(SECTION_HEADERS[section]):
            raise HTTPException(400, "Doppelte oder unbekannte CSV-Spalten; Konten und Rollen werden nicht übertragen")
        rows = []
        for index, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise HTTPException(400, f"Ungültige Spaltenanzahl in Zeile {index}")
            normalized_row = {str(key).strip(): (value or "").strip() for key, value in row.items() if key is not None}
            if not any(normalized_row.values()):
                continue
            if normalized_row.get("dataset") and normalized_row["dataset"] != section:
                raise HTTPException(400, f"Falscher Bereich in Zeile {index}")
            if normalized_row.get("transfer_version", "") not in {"", "1", TRANSFER_VERSION}:
                raise HTTPException(400, "Nicht unterstützte Transfer-Version")
            normalized_row["__row_number"] = index
            normalized_row["__provided_fields"] = list(normalized_row)
            rows.append(normalized_row)
            if len(rows) > MAX_ROWS:
                raise HTTPException(413, "Höchstens 10.000 Datensätze je Bereich")

        return rows, section

    def _detect_section(self, headers: list[str], file_name: str) -> str:
        lowered_headers = {header.strip().lower() for header in headers}

        for section, signature in SECTION_HEADER_SIGNATURES.items():
            if signature.issubset(lowered_headers):
                return section

        normalized_name = Path(file_name).stem.lower()
        for section in SECTION_ORDER:
            if normalized_name == section:
                return section

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Datensatz in '{file_name}' konnte nicht erkannt werden",
        )

    def _merge_media_entries(self, *bundles: dict[str, dict[str, dict]]) -> dict[str, dict[str, dict]]:
        merged = {"products": {}, "members": {}}
        for bundle in bundles:
            for section in merged:
                for key, value in bundle.get(section, {}).items():
                    if key in merged[section]:
                        previous = merged[section][key]["files"]
                        if {item["variant"] for item in previous} & {item["variant"] for item in value["files"]}:
                            raise HTTPException(400, f"Bildvariante für {section}/{key} mehrfach geliefert")
                        merged[section][key] = {"files": [*previous, *value["files"]]}
                    else:
                        merged[section][key] = value
        return merged

    def _collect_media_entry(self, target: dict[str, dict[str, dict]], safe_path: PurePosixPath, content: bytes) -> None:
        parts = safe_path.parts
        if len(parts) != 4:
            raise HTTPException(400, "Medienpfad muss media/Bereich/Quell-ID/Datei entsprechen")
        _, section, source_key = parts[:3]
        if section not in target or not source_key:
            return

        ext = safe_path.suffix.lower()
        if ext not in IMAGE_EXTENSIONS:
            raise HTTPException(400, "Nicht unterstütztes Bildformat")
        if len(content) > MAX_MEDIA_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Mediendatei '{safe_path.name}' überschreitet "
                    f"{MAX_MEDIA_SIZE / (1024 * 1024):.0f} MB"
                ),
            )

        entry = target[section].setdefault(source_key, {"files": []})
        variant = "original" if safe_path.stem.lower() == "original" else "main"
        if any(item["variant"] == variant for item in entry["files"]):
            raise HTTPException(400, f"Mehrere Bilder derselben Variante für {section}/{source_key}")
        entry["files"].append({"filename": safe_path.name, "content": content, "variant": variant})

    def _validate_import_rows(self, section: str, rows: list[dict]):
        """Validate the complete selection before replacement or media writes."""
        schema = IMPORT_SCHEMAS[section]
        for row in rows:
            number = row["__row_number"]
            try:
                data = {}
                for name, field in schema.model_fields.items():
                    if name not in SECTION_HEADERS[section]:
                        continue
                    raw = row.get(name)
                    if raw is None or str(raw).strip() == "":
                        if field.is_required():
                            raise ValueError(f"Pflichtfeld '{name}' fehlt")
                        continue
                    if field.annotation is bool:
                        raw = self._parse_bool(raw, field.default)
                    if name == "tax_rate":
                        raw = str(raw).replace(",", ".")
                    data[name] = raw
                validated = schema.model_validate(data)
                if section == "products" and validated.is_unlimited_stock and validated.stock_quantity:
                    raise ValueError("Unbegrenzte Produkte müssen Bestand 0 haben")
                if section == "members" and validated.archived_at and validated.balance_cents:
                    raise ValueError("Archivierte Mitglieder dürfen kein Guthaben haben")
                source_id = self._parse_optional_int(row.get("id"))
                if source_id is not None and not 0 < source_id <= MAX_INT:
                    raise ValueError("'id' muss eine positive ganze Zahl sein")
                for name in self._parse_category_names(row.get("category_names")):
                    if len(name) > 120:
                        raise ValueError("Kategorienamen dürfen höchstens 120 Zeichen enthalten")
                for name, value in validated.model_dump().items():
                    if name in SECTION_HEADERS[section]:
                        row[name] = "" if value is None else str(value)
            except (ValidationError, ValueError) as exc:
                if isinstance(exc, ValidationError):
                    details = "; ".join(f"{'.'.join(map(str, e['loc'])) or 'Datensatz'}: {e['msg']}" for e in exc.errors())
                else:
                    details = str(exc)
                raise HTTPException(status_code=400, detail=f"{section}, Zeile {number}: {details}") from exc

    def _import_categories(self, rows: list[dict]) -> dict:
        created = 0
        updated = 0
        skipped_fixed = 0


        for row in rows:
            row_number = row["__row_number"]
            name = self._require_value(row, "name", row_number)
            category = None

            source_id = self._parse_optional_int(row.get("id"))
            category = self.db.get(Category, row["__target_id"]) if row.get("__target_id") else None

            if category is not None and category.is_fixed:
                skipped_fixed += 1
                continue

            if category is None:
                category = Category(name=name)
                self.db.add(category)
                created += 1
            else:
                updated += 1

            category.name = name
            category.description = self._normalize_optional_string(row.get("description"))
            category.color = self._normalize_optional_string(row.get("color"))
            category.display_order = self._parse_int(row.get("display_order"), 0, row_number, "display_order")
            category.is_active_in_kasse = self._parse_bool(row.get("is_active_in_kasse"), True)

        self.db.flush()
        return {"created": created, "updated": updated, "skipped_fixed": skipped_fixed}

    def _import_products(self, rows: list[dict], media_entries: dict[str, dict], import_media: bool) -> dict:
        created = 0
        updated = 0
        media_imported = 0

        category_map = {
            (category.name or "").strip(): category
            for category in self.db.query(Category).all()
        }


        for row in rows:
            row_number = row["__row_number"]
            name = self._require_value(row, "name", row_number)
            product = None

            source_id = self._parse_optional_int(row.get("id"))
            product = self.db.get(Product, row["__target_id"]) if row.get("__target_id") else None

            if product is None:
                product = Product(name=name, price_cents=0)
                self.db.add(product)
                created += 1
            else:
                updated += 1

            product.name = name
            product.description = self._normalize_optional_string(row.get("description"))
            product.warengruppe = self._normalize_optional_string(row.get("warengruppe"))
            product.price_cents = self._parse_int(row.get("price_cents"), 0, row_number, "price_cents")
            product.member_price_cents = self._parse_optional_int(row.get("member_price_cents"))
            product.is_discountable = self._parse_bool(row.get("is_discountable"), True)
            product.is_unlimited_stock = self._parse_bool(row.get("is_unlimited_stock"), False)
            product.stock_quantity = (
                0
                if product.is_unlimited_stock
                else self._parse_int(row.get("stock_quantity"), 0, row_number, "stock_quantity")
            )
            for field in ("minimum_stock_quantity", "notify_on_low_stock", "requires_guest_list", "opens_small_parts_drawer"):
                if field in row.get("__provided_fields", row):
                    value = row.get(field)
                    setattr(product, field, int(value) if field == "minimum_stock_quantity" else self._parse_bool(value, False))
            product.is_variable_price = self._parse_bool(row.get("is_variable_price"), False)
            product.is_visible_in_kasse = self._parse_bool(row.get("is_visible_in_kasse"), True)
            product.is_active = self._parse_bool(row.get("is_active"), True)
            product.tax_rate = self._parse_float(row.get("tax_rate"), 0.0, row_number, "tax_rate")

            category_names = self._parse_category_names(row.get("category_names"))
            product.categories = [category_map[name] for name in category_names if name in category_map]

            self.db.flush()

            if import_media and source_id is not None:
                media_entry = media_entries.get(str(source_id))
                if media_entry:
                    product.image_path = self._store_media_file("products", product.id, media_entry) or product.image_path
                    media_imported += 1

        self.db.flush()
        return {"created": created, "updated": updated, "media_imported": media_imported}

    def _import_members(self, rows: list[dict], media_entries: dict[str, dict], import_media: bool) -> dict:
        created = 0
        updated = 0
        media_imported = 0
        member_repo = MemberRepository(self.db)
        members_by_number = {
            member.member_number: member
            for member in self.db.query(Member).filter(Member.member_number.isnot(None)).all()
        }


        for row in rows:
            row_number = row["__row_number"]
            first_name = self._require_value(row, "first_name", row_number)
            last_name = self._require_value(row, "last_name", row_number)

            source_id = self._parse_optional_int(row.get("id"))
            member = self.db.get(Member, row["__target_id"]) if row.get("__target_id") else None
            member_number = self._parse_optional_int(row.get("member_number"))
            membership_number = self._normalize_optional_string(row.get("membership_number"))

            email = self._normalize_optional_string(row.get("email"))
            phone = self._normalize_optional_string(row.get("phone"))
            notes = self._normalize_optional_string(row.get("notes"))
            has_discount = self._parse_bool(row.get("has_discount"), True)
            balance_cents = self._parse_int(row.get("balance_cents"), 0, row_number, "balance_cents")

            if member is None:
                member = Member(
                    member_number=member_number or member_repo.get_next_member_number(),
                    name=self._compose_member_name(first_name, last_name),
                    first_name=first_name,
                    last_name=last_name,
                    membership_number=membership_number,
                    email=email,
                    phone=phone,
                    notes=notes,
                    has_discount=has_discount,
                    balance_cents=balance_cents,
                )
                self.db.add(member)
                self.db.flush()
                created += 1
            else:
                updated += 1

            member.first_name = first_name
            member.last_name = last_name
            member.name = self._compose_member_name(first_name, last_name)
            member.membership_number = membership_number
            member.email = email
            member.phone = phone
            member.notes = notes
            member.has_discount = has_discount
            member.balance_cents = balance_cents
            if "archived_at" in row.get("__provided_fields", row):
                from datetime import datetime
                member.archived_at = datetime.fromisoformat(row["archived_at"]) if row.get("archived_at") else None

            if member_number is not None:
                existing_member_number = members_by_number.get(member_number)
                if existing_member_number is None or existing_member_number.id == member.id:
                    member.member_number = member_number
                    members_by_number[member_number] = member

            self.db.flush()

            if import_media and source_id is not None:
                media_entry = media_entries.get(str(source_id))
                if media_entry:
                    member.photo_path = self._store_media_file("members", member.id, media_entry) or member.photo_path
                    media_imported += 1

        self.db.flush()
        return {"created": created, "updated": updated, "media_imported": media_imported}

    def _replace_selected_sections(self, sections: list[str], deleted_media_ids: dict[str, list[int]]) -> dict[str, int]:
        replaced_counts = {}
        for section in REPLACE_ORDER:
            if section not in sections:
                continue
            if section == "categories":
                replaced_counts[section] = self._replace_categories()
            elif section == "products":
                replaced_counts[section] = self._replace_products(deleted_media_ids["products"])
            elif section == "members":
                replaced_counts[section] = self._replace_members(deleted_media_ids["members"])
        return replaced_counts

    def _replace_categories(self) -> int:
        categories = self.db.query(Category).all()
        replaceable_ids = [category.id for category in categories if not category.is_fixed]
        if not replaceable_ids:
            return 0

        self.db.execute(
            product_category.delete().where(product_category.c.category_id.in_(replaceable_ids))
        )
        deleted_count = (
            self.db.query(Category)
            .filter(Category.id.in_(replaceable_ids))
            .delete(synchronize_session=False)
        )
        self.db.flush()
        return deleted_count

    def _replace_products(self, deleted_media_ids: list[int]) -> int:
        product_ids = [row[0] for row in self.db.query(Product.id).all()]
        if not product_ids:
            return 0

        referenced_transaction = (
            self.db.query(TransactionItem.id)
            .filter(TransactionItem.product_id.in_(product_ids))
            .first()
        )
        if referenced_transaction is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Produkte können nicht ersetzend importiert werden, "
                    "solange Verkaufs- oder Buchungshistorie darauf verweist."
                ),
            )

        self.db.execute(
            product_category.delete().where(product_category.c.product_id.in_(product_ids))
        )
        if self.db.query(DeckelItem.id).filter(DeckelItem.product_id.in_(product_ids)).first():
            raise HTTPException(409, "Offene Deckel verhindern den ersetzenden Produktimport")
        self.db.query(ProductStockCorrectionLog).filter(
            ProductStockCorrectionLog.product_id.in_(product_ids)
        ).delete(synchronize_session=False)
        deleted_count = (
            self.db.query(Product)
            .filter(Product.id.in_(product_ids))
            .delete(synchronize_session=False)
        )
        deleted_media_ids.extend(product_ids)
        self.db.flush()
        return deleted_count

    def _replace_members(self, deleted_media_ids: list[int]) -> int:
        member_ids = [row[0] for row in self.db.query(Member.id).all()]
        if not member_ids:
            return 0

        referenced_transaction = (
            self.db.query(Transaction.id)
            .filter(Transaction.member_id.in_(member_ids))
            .first()
        )
        if referenced_transaction is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Mitglieder können nicht ersetzend importiert werden, "
                    "solange Buchungen oder Verkäufe auf sie verweisen."
                ),
            )

        self.db.query(User).filter(User.member_id.in_(member_ids)).update(
            {User.member_id: None},
            synchronize_session=False,
        )
        self.db.query(BalanceLog).filter(BalanceLog.member_id.in_(member_ids)).delete(synchronize_session=False)
        self.db.query(MemberBalanceCorrectionLog).filter(
            MemberBalanceCorrectionLog.member_id.in_(member_ids)
        ).delete(synchronize_session=False)
        deleted_count = (
            self.db.query(Member)
            .filter(Member.id.in_(member_ids))
            .delete(synchronize_session=False)
        )
        deleted_media_ids.extend(member_ids)
        self.db.flush()
        return deleted_count

    def _store_media_file(self, section, target_id, media_entry):
        folder = self._staged_media / section / str(target_id)
        folder.mkdir(parents=True, exist_ok=True)
        main_path = None
        for item in media_entry["files"]:
            stem = "original" if item["variant"] == "original" else "image" if section == "products" else "photo"
            ext = Path(item["filename"]).suffix.lower()
            for old in folder.glob(stem + ".*"):
                old.unlink()
            (folder / (stem + ext)).write_bytes(item["content"])
            if stem != "original":
                main_path = f"{section}/{target_id}/{stem}{ext}"
        return main_path

    def _normalize_sections(self, sections: list[str] | None) -> list[str]:
        if not sections:
            return []

        normalized = []
        for section in sections:
            normalized_section = (section or "").strip().lower()
            if normalized_section not in SECTION_ORDER:
                raise HTTPException(400, "Unbekannter Import-/Exportbereich")
            if normalized_section in SECTION_ORDER and normalized_section not in normalized:
                normalized.append(normalized_section)
        return normalized

    @staticmethod
    def _format_bool(value: bool) -> str:
        return "true" if value else "false"

    @staticmethod
    def _normalize_optional_string(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @staticmethod
    def _parse_bool(value: str | None, default: bool) -> bool:
        if value is None or str(value).strip() == "":
            return default
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "ja", "y"}:
            return True
        if normalized in {"0", "false", "no", "nein", "n"}:
            return False
        raise ValueError(f"Ungültiger Wahrheitswert: {value}")

    @staticmethod
    def _parse_optional_int(value: str | None) -> int | None:
        if value is None or str(value).strip() == "":
            return None
        return int(str(value).strip())

    def _parse_int(self, value: str | None, default: int, row_number: int, field_name: str) -> int:
        if value is None or str(value).strip() == "":
            return default
        try:
            return int(str(value).strip())
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ungültiger Integer-Wert in Zeile {row_number} für '{field_name}'",
            ) from exc

    def _parse_float(self, value: str | None, default: float, row_number: int, field_name: str) -> float:
        if value is None or str(value).strip() == "":
            return default
        try:
            return float(str(value).strip().replace(",", "."))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ungültiger Zahlenwert in Zeile {row_number} für '{field_name}'",
            ) from exc

    @staticmethod
    def _parse_category_names(value: str | None) -> list[str]:
        if value is None or str(value).strip() == "":
            return []
        if str(value).lstrip().startswith("["):
            parsed = json.loads(value)
            if not isinstance(parsed, list) or any(not isinstance(name, str) or not name.strip() for name in parsed):
                raise ValueError("Kategoriezuordnung muss eine Liste von Namen sein")
            return [name.strip() for name in parsed]
        return [name.strip() for name in str(value).split("|") if name.strip()]

    @staticmethod
    def _compose_member_name(first_name: str, last_name: str) -> str:
        return " ".join(part for part in [first_name.strip(), last_name.strip()] if part)

    def _require_value(self, row: dict, field_name: str, row_number: int) -> str:
        value = self._normalize_optional_string(row.get(field_name))
        if value is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Pflichtfeld '{field_name}' fehlt in Zeile {row_number}",
            )
        return value

    @staticmethod
    def _safe_zip_path(name: str) -> PurePosixPath | None:
        try:
            path = PurePosixPath(name)
        except TypeError:
            return None
        if path.is_absolute() or ".." in path.parts:
            return None
        return path
