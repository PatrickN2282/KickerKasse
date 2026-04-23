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

    @staticmethod
    def _resolve_material_amount_cents(transaction: Transaction, item) -> int:
        product = getattr(item, "product", None)
        if not product:
            return item.total_price_cents

        unit_price_cents = (
            product.member_price_cents
            if transaction.member_id and product.member_price_cents is not None
            else product.price_cents
        )
        return item.quantity * unit_price_cents

    def record_sale_transaction(self, transaction: Transaction) -> None:
        for item in transaction.items:
            product = getattr(item, "product", None)
            if not product or not self.is_internal_material_product(product):
                continue

            self.db.add(MaterialAccountEntry(
                amount_cents=self._resolve_material_amount_cents(transaction, item),
                reason=f"{item.quantity}× {product.name}",
                user_id=transaction.user_id,
                transaction_id=transaction.id,
            ))

    def record_storno_transaction(self, transaction: Transaction) -> None:
        reference_transaction = getattr(transaction, "reference_transaction", None)
        if not reference_transaction:
            return

        original_entries = self.db.query(MaterialAccountEntry).filter(
            MaterialAccountEntry.transaction_id == reference_transaction.id
        ).all()

        if original_entries:
            for entry in original_entries:
                self.db.add(MaterialAccountEntry(
                    amount_cents=-entry.amount_cents,
                    reason=f"Storno {entry.reason}",
                    user_id=transaction.user_id,
                    transaction_id=transaction.id,
                ))
            return

        # Fallback for storno transactions of older sales whose original transaction
        # has internal material items but no persisted material-account entry rows yet.
        reference_items = getattr(reference_transaction, "items", None) or []
        for item in reference_items:
            product = getattr(item, "product", None)
            if not product or not self.is_internal_material_product(product):
                continue

            self.db.add(MaterialAccountEntry(
                amount_cents=-self._resolve_material_amount_cents(reference_transaction, item),
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
