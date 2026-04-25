from datetime import datetime
import re

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.constants import INTERNAL_MATERIAL_CATEGORY_NAME
from app.models import MaterialAccountEntry, Transaction, TransactionItem


class MaterialAccountService:
    # Matches: "[Storno ]<quantity>× <product_name>"
    REASON_PATTERN = re.compile(r"^(?P<storno>Storno )?(?P<quantity>\d+)× (?P<product>.+)$")

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def is_internal_material_product(product) -> bool:
        categories = getattr(product, "categories", None) or []
        return any((getattr(category, "name", None) or "").strip() == INTERNAL_MATERIAL_CATEGORY_NAME for category in categories)

    def is_internal_material_sale_item(self, item) -> bool:
        """Return True only for sale rows explicitly marked as internal material bookings."""
        product = getattr(item, "product", None)
        return bool(product and self.is_internal_material_product(product) and getattr(item, "is_internal_material", False))

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
            if not self.is_internal_material_sale_item(item):
                continue
            product = item.product

            self.db.add(MaterialAccountEntry(
                amount_cents=self._resolve_material_amount_cents(transaction, item),
                reason=f"{item.quantity}× {product.name}",
                user_id=transaction.user_id,
                transaction_id=transaction.id,
                transaction_item_id=item.id,
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
                    transaction_item_id=entry.transaction_item_id,
                ))
            return

        # Fallback for storno transactions of older sales whose original transaction
        # has internal material items but no persisted material-account entry rows yet.
        reference_items = getattr(reference_transaction, "items", None) or []
        for item in reference_items:
            if not self.is_internal_material_sale_item(item):
                continue
            product = item.product

            self.db.add(MaterialAccountEntry(
                amount_cents=-self._resolve_material_amount_cents(reference_transaction, item),
                reason=f"Storno {item.quantity}× {product.name}",
                user_id=transaction.user_id,
                transaction_id=transaction.id,
                transaction_item_id=item.id,
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

    def get_account_summary(self) -> dict:
        entries = self.db.query(MaterialAccountEntry).options(
            joinedload(MaterialAccountEntry.user),
            joinedload(MaterialAccountEntry.transaction).joinedload(Transaction.items).joinedload(TransactionItem.product),
            joinedload(MaterialAccountEntry.transaction).joinedload(Transaction.member),
            joinedload(MaterialAccountEntry.transaction_item).joinedload(TransactionItem.product),
        ).order_by(MaterialAccountEntry.created_at.desc()).all()
        serialized_entries = []
        total_quantity = 0

        for entry in entries:
            parsed_reason = self.REASON_PATTERN.match(entry.reason or "")
            storno_marker = parsed_reason.group("storno") if parsed_reason else None
            quantity_raw = parsed_reason.group("quantity") if parsed_reason else None
            product_raw = parsed_reason.group("product") if parsed_reason else None
            quantity = int(quantity_raw) if quantity_raw else None
            product_name = product_raw.strip() if product_raw else None
            is_storno = storno_marker is not None
            total_quantity += 0 if quantity is None else quantity * (-1 if is_storno else 1)
            transaction = entry.transaction
            relevant_items = []
            if entry.transaction_item:
                relevant_items = [entry.transaction_item]
            elif transaction:
                relevant_items = [
                    transaction_item
                    for transaction_item in transaction.items
                    if self.is_internal_material_sale_item(transaction_item)
                ]

            serialized_entries.append({
                "id": entry.id,
                "amount_cents": entry.amount_cents,
                "reason": entry.reason,
                "quantity": quantity,
                "product_name": product_name,
                "entry_type": "STORNO" if is_storno else "SALE",
                "entry_type_label": "Storno" if is_storno else "Verkauf",
                "user_name": entry.user.username if entry.user else None,
                "created_at": entry.created_at,
                "receipt_number": transaction.receipt_number if transaction else None,
                "transaction": {
                    "id": transaction.id,
                    "receipt_number": transaction.receipt_number,
                    "payment_method": transaction.payment_method.value if transaction and transaction.payment_method else None,
                    "voucher_applied_cents": transaction.voucher_applied_cents if transaction else 0,
                    "balance_applied_cents": transaction.balance_applied_cents if transaction else 0,
                    "voucher_type": transaction.voucher_type if transaction else None,
                    "type": transaction.type.value if transaction and transaction.type else None,
                    "member_name": transaction.member.name if transaction and transaction.member else None,
                    "items": [
                        {
                            "id": transaction_item.id,
                            "quantity": transaction_item.quantity,
                            "unit_price_cents": transaction_item.unit_price_cents,
                            "total_price_cents": transaction_item.total_price_cents,
                            "note": transaction_item.note,
                            "product": {
                                "id": transaction_item.product.id,
                                "name": transaction_item.product.name,
                            } if transaction_item.product else None,
                        }
                        for transaction_item in relevant_items
                    ],
                } if transaction else None,
                "note": relevant_items[0].note if len(relevant_items) == 1 else None,
            })

        return {
            "total_quantity": total_quantity,
            "entries": serialized_entries,
        }
