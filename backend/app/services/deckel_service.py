from collections import defaultdict

from sqlalchemy.orm import Session, joinedload

from app.models import Deckel, DeckelItem, Product
from app.repositories import ProductRepository
from app.services.sale_pricing_service import resolve_sale_unit_price_cents


class DeckelService:
    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)

    def list_deckel(self) -> list[Deckel]:
        return self.db.query(Deckel).options(
            joinedload(Deckel.items).joinedload(DeckelItem.product)
        ).order_by(Deckel.updated_at.desc(), Deckel.id.desc()).all()

    def get_deckel(self, deckel_id: int, *, lock: bool = False) -> Deckel | None:
        if lock:
            locked = self.db.query(Deckel).filter_by(id=deckel_id).populate_existing().with_for_update().first()
            if not locked:
                return None
        return self.db.query(Deckel).options(
            joinedload(Deckel.items).joinedload(DeckelItem.product)
        ).filter(Deckel.id == deckel_id).populate_existing().first()

    def get_reserved_quantities(self, exclude_deckel_id: int | None = None) -> dict[int, int]:
        query = self.db.query(DeckelItem)
        if exclude_deckel_id is not None:
            query = query.filter(DeckelItem.deckel_id != exclude_deckel_id)

        reserved: dict[int, int] = defaultdict(int)
        for item in query.all():
            reserved[item.product_id] += item.quantity
        return dict(reserved)

    def validate_item_stock(self, items: list[dict], *, exclude_deckel_id: int | None = None) -> None:
        reserved_quantities = self.get_reserved_quantities(exclude_deckel_id=exclude_deckel_id)
        requested_quantities: dict[int, int] = defaultdict(int)

        for item in items:
            requested_quantities[item["product_id"]] += item["quantity"]

        for product_id, requested_quantity in requested_quantities.items():
            product = self.product_repo.get_by_id(product_id)
            if not product:
                raise ValueError(f"Produkt {product_id} nicht gefunden")

            if product.is_unlimited_stock:
                continue

            available_quantity = max(product.stock_quantity - reserved_quantities.get(product_id, 0), 0)
            if requested_quantity > available_quantity:
                raise ValueError(
                    f"Unzureichender Bestand für Produkt {product.name} "
                    f"({requested_quantity} angefordert, {available_quantity} verfügbar)"
                )

    @staticmethod
    def _merge_item_payload(items: list[dict]) -> list[dict]:
        merged: dict[tuple[int, int, bool, str], dict] = {}
        for item in items:
            note = (item.get("note") or "").strip()
            key = (
                item["product_id"],
                item["unit_price_cents"],
                bool(item.get("is_internal_material", False)),
                note,
            )
            if key not in merged:
                merged[key] = {
                    "product_id": item["product_id"],
                    "quantity": 0,
                    "unit_price_cents": item["unit_price_cents"],
                    "is_internal_material": bool(item.get("is_internal_material", False)),
                    "note": note or None,
                }
            merged[key]["quantity"] += item["quantity"]

        return list(merged.values())

    def _resolve_new_item_prices(self, items: list[dict]) -> list[dict]:
        for product_id in sorted({item["product_id"] for item in items}):
            self.product_repo.get_by_id_for_update(product_id)
        priced_items = []
        for item in items:
            product = self.product_repo.get_by_id(item["product_id"])
            if not product:
                raise ValueError(f"Produkt {item['product_id']} nicht gefunden")
            if not product.is_active:
                raise ValueError(f"Produkt {product.name} ist inaktiv")

            from app.services.voucher_service import VoucherService
            if product.requires_guest_list or VoucherService.get_prepaid_value_from_product(product) is not None:
                raise ValueError("Gastartikel und Verzehrkarten bitte direkt über den normalen Verkauf abrechnen.")
            priced_items.append({
                **item,
                "unit_price_cents": resolve_sale_unit_price_cents(
                    product,
                    item["unit_price_cents"],
                    is_internal_material=bool(item.get("is_internal_material", False)),
                ),
            })
        return priced_items

    def create_deckel(self, name: str, created_by_user_id: int, items: list[dict]) -> Deckel:
        normalized_name = (name or "").strip()
        if not normalized_name:
            raise ValueError("Bitte einen Deckelnamen eingeben")
        if not items:
            raise ValueError("Ein Deckel benötigt mindestens einen Artikel")

        merged_items = self._merge_item_payload(self._resolve_new_item_prices(items))
        self.validate_item_stock(merged_items)

        deckel = Deckel(name=normalized_name, created_by_user_id=created_by_user_id)
        self.db.add(deckel)
        self.db.flush()

        for item in merged_items:
            deckel.items.append(DeckelItem(
                product_id=item["product_id"],
                quantity=item["quantity"],
                unit_price_cents=item["unit_price_cents"],
                total_price_cents=item["quantity"] * item["unit_price_cents"],
                is_internal_material=bool(item.get("is_internal_material", False)),
                note=item.get("note"),
            ))

        self.db.commit()
        return self.get_deckel(deckel.id)

    def append_items(self, deckel_id: int, items: list[dict]) -> Deckel:
        deckel = self.get_deckel(deckel_id, lock=True)
        if not deckel:
            raise ValueError("Deckel nicht gefunden")
        if not items:
            raise ValueError("Keine Artikel zum Buchen vorhanden")

        existing_quantities: dict[int, int] = defaultdict(int)
        for existing_item in deckel.items:
            existing_quantities[existing_item.product_id] += existing_item.quantity

        merged_new_items = self._merge_item_payload(self._resolve_new_item_prices(items))
        combined_items = []
        for product_id, quantity in existing_quantities.items():
            unit_price = next(
                (item.unit_price_cents for item in deckel.items if item.product_id == product_id),
                0,
            )
            combined_items.append({
                "product_id": product_id,
                "quantity": quantity,
                "unit_price_cents": unit_price,
                "is_internal_material": any(
                    item.product_id == product_id and item.is_internal_material
                    for item in deckel.items
                ),
            })
        combined_items.extend(merged_new_items)

        self.validate_item_stock(combined_items, exclude_deckel_id=deckel.id)

        for item in merged_new_items:
            target_item = next(
                (
                    existing_item for existing_item in deckel.items
                    if existing_item.product_id == item["product_id"]
                    and existing_item.unit_price_cents == item["unit_price_cents"]
                    and existing_item.is_internal_material == bool(item.get("is_internal_material", False))
                    and (existing_item.note or None) == (item.get("note") or None)
                ),
                None,
            )
            if target_item:
                target_item.quantity += item["quantity"]
                target_item.total_price_cents = target_item.quantity * target_item.unit_price_cents
                continue

            deckel.items.append(DeckelItem(
                product_id=item["product_id"],
                quantity=item["quantity"],
                unit_price_cents=item["unit_price_cents"],
                total_price_cents=item["quantity"] * item["unit_price_cents"],
                is_internal_material=bool(item.get("is_internal_material", False)),
                note=item.get("note"),
            ))

        self.db.commit()
        return self.get_deckel(deckel.id)

    def delete_deckel(self, deckel_id: int) -> bool:
        deckel = self.get_deckel(deckel_id, lock=True)
        if not deckel:
            return False
        self.db.delete(deckel)
        self.db.commit()
        return True

    def settle(self, deckel_id, user, cash_received_cents, tip_cents=0):
        from app.services.transaction_service import TransactionService
        from app.services.material_account_service import MaterialAccountService
        from app.services.audit_log_service import AuditLogService
        from app.services.voucher_service import VoucherService
        try:
            deckel = self.get_deckel(deckel_id, lock=True)
            if not deckel:
                raise LookupError("Deckel nicht gefunden oder bereits abgerechnet")
            if not deckel.items:
                raise ValueError("Ein leerer Deckel kann nicht abgerechnet werden")
            for product_id in sorted({item.product_id for item in deckel.items}):
                product = self.product_repo.get_by_id_for_update(product_id)
                if not product:
                    raise ValueError("Ein Deckelprodukt fehlt")
                if product.requires_guest_list or VoucherService.get_prepaid_value_from_product(product) is not None:
                    raise ValueError("Dieser alte Deckel enthält Gastartikel oder Verzehrkarten und muss vor der Abrechnung fachlich geklärt werden.")
            items = [{"product_id": i.product_id, "product_name": i.product.name,
                      "quantity": i.quantity, "unit_price_cents": i.unit_price_cents,
                      "is_internal_material": i.is_internal_material, "note": i.note} for i in deckel.items]
            self.validate_item_stock(items, exclude_deckel_id=deckel.id)
            total = sum(i["quantity"] * i["unit_price_cents"] for i in items)
            service = TransactionService(self.db)
            change = service.validate_cash_payment("CASH", total, tip_cents, cash_received_cents)
            transaction = service.create_sale_transaction(user_id=user.id, performed_by_username=user.username,
                total_amount_cents=total, payment_method="CASH", items=items, tip_cents=tip_cents,
                cash_received_cents=cash_received_cents, change_given_cents=change, commit=False)
            for item in items:
                if not self.product_repo.deduct_stock(item["product_id"], item["quantity"], commit=False):
                    raise ValueError("Bestand hat sich geändert; Deckel wurde nicht abgerechnet")
            MaterialAccountService(self.db).record_sale_transaction(transaction)
            AuditLogService(self.db).log(entity_type="deckel", entity_id=deckel.id, entity_name=deckel.name,
                action="SETTLED", user_username=user.username, new_value={"transaction_id": transaction.id, "total_amount_cents": total})
            self.db.delete(deckel)
            self.db.commit()
            self.db.refresh(transaction)
            return transaction
        except Exception:
            self.db.rollback()
            raise
