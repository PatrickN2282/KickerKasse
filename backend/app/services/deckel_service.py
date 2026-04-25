from collections import defaultdict

from sqlalchemy.orm import Session, joinedload

from app.models import Deckel, DeckelItem, Product
from app.repositories import ProductRepository


class DeckelService:
    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)

    def list_deckel(self) -> list[Deckel]:
        return self.db.query(Deckel).options(
            joinedload(Deckel.items).joinedload(DeckelItem.product)
        ).order_by(Deckel.updated_at.desc(), Deckel.id.desc()).all()

    def get_deckel(self, deckel_id: int) -> Deckel | None:
        return self.db.query(Deckel).options(
            joinedload(Deckel.items).joinedload(DeckelItem.product)
        ).filter(Deckel.id == deckel_id).first()

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

    def create_deckel(self, name: str, created_by_user_id: int, items: list[dict]) -> Deckel:
        normalized_name = (name or "").strip()
        if not normalized_name:
            raise ValueError("Bitte einen Deckelnamen eingeben")
        if not items:
            raise ValueError("Ein Deckel benötigt mindestens einen Artikel")

        merged_items = self._merge_item_payload(items)
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
        deckel = self.get_deckel(deckel_id)
        if not deckel:
            raise ValueError("Deckel nicht gefunden")
        if not items:
            raise ValueError("Keine Artikel zum Buchen vorhanden")

        existing_quantities: dict[int, int] = defaultdict(int)
        for existing_item in deckel.items:
            existing_quantities[existing_item.product_id] += existing_item.quantity

        merged_new_items = self._merge_item_payload(items)
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
        deckel = self.get_deckel(deckel_id)
        if not deckel:
            return False
        self.db.delete(deckel)
        self.db.commit()
        return True
