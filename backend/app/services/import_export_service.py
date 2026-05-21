from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path, PurePosixPath

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

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
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
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
        "stock_quantity",
        "is_unlimited_stock",
        "is_variable_price",
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
    ],
}

SECTION_HEADER_SIGNATURES = {
    "categories": {"name", "display_order", "is_active_in_kasse"},
    "products": {"name", "price_cents", "stock_quantity"},
    "members": {"first_name", "last_name", "balance_cents"},
}


class ImportExportService:
    def __init__(self, db: Session):
        self.db = db

    def export_sections(self, sections: list[str], include_media: bool) -> tuple[bytes, str, str]:
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

        return {
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

    def import_sections(
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
        selected_sections = self._normalize_sections(sections or available_sections)

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

        deleted_media_ids = {"products": [], "members": []}

        try:
            replaced_counts = self._replace_selected_sections(normalized_replace_sections, deleted_media_ids)
            if normalized_replace_sections:
                self.db.expunge_all()

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

        for product_id in deleted_media_ids["products"]:
            delete_product_image(product_id)
        for member_id in deleted_media_ids["members"]:
            delete_member_photo(member_id)

        return {
            "imported_sections": selected_sections,
            "results": results,
        }

    def _build_categories_csv(self) -> bytes:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=SECTION_HEADERS["categories"])
        writer.writeheader()

        categories = self.db.query(Category).order_by(Category.display_order, Category.name).all()
        for category in categories:
            writer.writerow({
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
                "dataset": "products",
                "id": product.id,
                "name": product.name,
                "description": product.description or "",
                "warengruppe": product.warengruppe or "",
                "price_cents": product.price_cents,
                "member_price_cents": "" if product.member_price_cents is None else product.member_price_cents,
                "is_discountable": self._format_bool(product.is_discountable),
                "stock_quantity": product.stock_quantity,
                "is_unlimited_stock": self._format_bool(product.is_unlimited_stock),
                "is_variable_price": self._format_bool(product.is_variable_price),
                "is_active": self._format_bool(product.is_active),
                "tax_rate": product.tax_rate,
                "category_names": "|".join(sorted(category.name for category in product.categories)),
            })

        return output.getvalue().encode("utf-8-sig")

    def _build_members_csv(self) -> bytes:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=SECTION_HEADERS["members"])
        writer.writeheader()

        members = self.db.query(Member).order_by(Member.member_number, Member.last_name, Member.first_name).all()
        for member in members:
            writer.writerow({
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
            })

        return output.getvalue().encode("utf-8-sig")

    def _write_export_media(self, archive: zipfile.ZipFile, sections: list[str]) -> None:
        if "products" in sections:
            products = self.db.query(Product).filter(Product.image_path.isnot(None)).order_by(Product.id).all()
            for product in products:
                file_path = get_full_path(product.image_path)
                if file_path and file_path.exists():
                    archive.writestr(
                        f"media/products/{product.id}/{file_path.name}",
                        file_path.read_bytes(),
                    )

        if "members" in sections:
            members = self.db.query(Member).filter(Member.photo_path.isnot(None)).order_by(Member.id).all()
            for member in members:
                file_path = get_full_path(member.photo_path)
                if file_path and file_path.exists():
                    archive.writestr(
                        f"media/members/{member.id}/{file_path.name}",
                        file_path.read_bytes(),
                    )

    def _parse_data_bundle(self, file_name: str, content: bytes) -> dict:
        suffix = Path(file_name or "import.csv").suffix.lower()
        rows_by_section: dict[str, list[dict]] = {}
        embedded_media = {"products": {}, "members": {}}

        if suffix == ".zip":
            try:
                duplicate_sections = set()
                with zipfile.ZipFile(io.BytesIO(content)) as archive:
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
        if not file_name or content is None:
            return media_entries

        if Path(file_name).suffix.lower() != ".zip":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zusätzliche Mediadaten müssen als ZIP-Datei hochgeladen werden",
            )

        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
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
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Datei '{file_name}' ist keine gültige UTF-8-CSV",
            ) from exc

        reader = csv.DictReader(io.StringIO(text))
        headers = [header.strip() for header in (reader.fieldnames or []) if header and header.strip()]
        if not headers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Datei '{file_name}' enthält keine CSV-Header",
            )

        section = self._detect_section(headers, file_name)
        rows = []
        for index, row in enumerate(reader, start=2):
            normalized_row = {str(key).strip(): (value or "").strip() for key, value in row.items() if key is not None}
            if not any(normalized_row.values()):
                continue
            normalized_row["__row_number"] = index
            rows.append(normalized_row)

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
                merged[section].update(bundle.get(section, {}))
        return merged

    def _collect_media_entry(self, target: dict[str, dict[str, dict]], safe_path: PurePosixPath, content: bytes) -> None:
        parts = safe_path.parts
        if len(parts) < 4:
            return
        _, section, source_key = parts[:3]
        if section not in target or not source_key:
            return

        ext = safe_path.suffix.lower()
        if ext not in IMAGE_EXTENSIONS:
            return
        if len(content) > MAX_MEDIA_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Mediendatei '{safe_path.name}' überschreitet "
                    f"{MAX_MEDIA_SIZE / (1024 * 1024):.0f} MB"
                ),
            )

        target[section][source_key] = {
            "filename": safe_path.name,
            "content": content,
        }

    def _import_categories(self, rows: list[dict]) -> dict:
        created = 0
        updated = 0
        skipped_fixed = 0

        existing_category_ids = {c[0] for c in self.db.query(Category.id).all()}

        for row in rows:
            row_number = row["__row_number"]
            name = self._require_value(row, "name", row_number)
            category = None

            source_id = self._parse_optional_int(row.get("id"))
            if source_id is not None and source_id in existing_category_ids:
                category = self.db.query(Category).filter(Category.id == source_id).first()
            if category is None:
                category = self.db.query(Category).filter(Category.name == name).first()

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

        existing_product_ids = {p[0] for p in self.db.query(Product.id).all()}

        for row in rows:
            row_number = row["__row_number"]
            name = self._require_value(row, "name", row_number)
            product = None

            source_id = self._parse_optional_int(row.get("id"))
            if source_id is not None and source_id in existing_product_ids:
                product = self.db.query(Product).filter(Product.id == source_id).first()
            if product is None:
                product = self.db.query(Product).filter(Product.name == name).first()

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
            product.is_variable_price = self._parse_bool(row.get("is_variable_price"), False)
            product.is_active = self._parse_bool(row.get("is_active"), True)
            product.tax_rate = self._parse_float(row.get("tax_rate"), 0.0, row_number, "tax_rate")

            category_names = self._parse_category_names(row.get("category_names"))
            product.categories = [category_map[name] for name in category_names if name in category_map]

            self.db.flush()

            if import_media and source_id is not None:
                media_entry = media_entries.get(str(source_id))
                if media_entry:
                    product.image_path = self._store_media_file("products", product.id, media_entry)
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

        existing_member_ids = {m[0] for m in self.db.query(Member.id).all()}

        for row in rows:
            row_number = row["__row_number"]
            first_name = self._require_value(row, "first_name", row_number)
            last_name = self._require_value(row, "last_name", row_number)

            member = None
            source_id = self._parse_optional_int(row.get("id"))
            if source_id is not None and source_id in existing_member_ids:
                member = self.db.query(Member).filter(Member.id == source_id).first()

            member_number = self._parse_optional_int(row.get("member_number"))
            membership_number = self._normalize_optional_string(row.get("membership_number"))

            if member is None and member_number is not None:
                member = members_by_number.get(member_number)
            if member is None and membership_number:
                member = self.db.query(Member).filter(Member.membership_number == membership_number).first()

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

            if member_number is not None:
                existing_member_number = members_by_number.get(member_number)
                if existing_member_number is None or existing_member_number.id == member.id:
                    member.member_number = member_number
                    members_by_number[member_number] = member

            self.db.flush()

            if import_media and source_id is not None:
                media_entry = media_entries.get(str(source_id))
                if media_entry:
                    member.photo_path = self._store_media_file("members", member.id, media_entry)
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
        product_ids = [product_id for (product_id,) in self.db.query(Product.id).all()]
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
        self.db.query(DeckelItem).filter(DeckelItem.product_id.in_(product_ids)).delete(synchronize_session=False)
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
        member_ids = [member_id for (member_id,) in self.db.query(Member.id).all()]
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

    def _store_media_file(self, section: str, target_id: int, media_entry: dict) -> str:
        ensure_upload_directories()

        filename = media_entry["filename"]
        content = media_entry["content"]
        ext = Path(filename).suffix.lower()
        if ext not in IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dateiformat '{ext}' wird für Medien nicht unterstützt",
            )

        base_name = "image" if section == "products" else "photo"
        folder = (PRODUCTS_DIR if section == "products" else MEMBERS_DIR) / str(target_id)
        folder.mkdir(parents=True, exist_ok=True)

        for existing_file in folder.glob(f"{base_name}.*"):
            existing_file.unlink(missing_ok=True)

        target_path = folder / f"{base_name}{ext}"
        target_path.write_bytes(content)
        return f"{section}/{target_id}/{base_name}{ext}"

    def _normalize_sections(self, sections: list[str] | None) -> list[str]:
        if not sections:
            return []

        normalized = []
        for section in sections:
            normalized_section = (section or "").strip().lower()
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
        return str(value).strip().lower() in {"1", "true", "yes", "ja", "y"}

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
