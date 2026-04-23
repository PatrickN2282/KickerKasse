from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.constants import INTERNAL_MATERIAL_CATEGORY_NAME
from app.models import MaterialAccountEntry, Transaction


class MaterialAccountService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def is_internal_material_product(product) -> bool:
        categories = getattr(product, "categories", None) or []
        return any((getattr(category, "name", None) or "").strip() == INTERNAL_MATERIAL_CATEGORY_NAME for category in categories)

    def record_sale_transaction(self, transaction: Transaction) -> None:
        for item in transaction.items:
            product = getattr(item, "product", None)
            if not product or not self.is_internal_material_product(product):
                continue

            self.db.add(MaterialAccountEntry(
                amount_cents=item.total_price_cents,
                reason=f"{item.quantity}× {product.name}",
                user_id=transaction.user_id,
                transaction_id=transaction.id,
            ))

    def record_storno_transaction(self, transaction: Transaction) -> None:
        reference_items = getattr(transaction.reference_transaction, "items", None) or []
        for item in reference_items:
            product = getattr(item, "product", None)
            if not product or not self.is_internal_material_product(product):
                continue

            self.db.add(MaterialAccountEntry(
                amount_cents=-item.total_price_cents,
                reason=f"Storno {item.quantity}× {product.name}",
                user_id=transaction.user_id,
                transaction_id=transaction.id,
            ))

    def get_period_total_cents(
        self,
        period_start: datetime | None,
        period_end: datetime,
    ) -> int:
        query = self.db.query(func.coalesce(func.sum(MaterialAccountEntry.amount_cents), 0)).filter(
            MaterialAccountEntry.created_at <= period_end
        )
        if period_start:
            query = query.filter(MaterialAccountEntry.created_at > period_start)
        return query.scalar() or 0
