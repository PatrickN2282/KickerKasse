from datetime import datetime
import re

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.constants import INTERNAL_MATERIAL_CATEGORY_NAME
from app.models import ClubAccountEntry, MaterialAccountEntry, Transaction


class MaterialAccountService:
    CLUB_ACCOUNT_REASON_PREFIX = "Verbrauchsmaterial intern:"
    # Matches: "[Storno ]<quantity>× <product_name>"
    REASON_PATTERN = re.compile(r"^(?P<storno>Storno )?(?P<quantity>\d+)× (?P<product>.+)$")

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
            self.db.add(ClubAccountEntry(
                amount_cents=-self._resolve_material_amount_cents(transaction, item),
                reason=f"{self.CLUB_ACCOUNT_REASON_PREFIX} {item.quantity}× {product.name}",
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
            original_club_entries = self.db.query(ClubAccountEntry).filter(
                ClubAccountEntry.transaction_id == reference_transaction.id,
                ClubAccountEntry.reason.like(f"{self.CLUB_ACCOUNT_REASON_PREFIX}%"),
            ).all()
            for entry in original_entries:
                self.db.add(MaterialAccountEntry(
                    amount_cents=-entry.amount_cents,
                    reason=f"Storno {entry.reason}",
                    user_id=transaction.user_id,
                    transaction_id=transaction.id,
                ))
            for entry in original_club_entries:
                self.db.add(ClubAccountEntry(
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

    def get_account_summary(self) -> dict:
        entries = self.db.query(MaterialAccountEntry).order_by(MaterialAccountEntry.created_at.desc()).all()
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
                    "payment_method": transaction.payment_method.value if transaction and transaction.payment_method else None,
                    "voucher_applied_cents": transaction.voucher_applied_cents if transaction else 0,
                    "balance_applied_cents": transaction.balance_applied_cents if transaction else 0,
                    "voucher_type": transaction.voucher_type if transaction else None,
                    "type": transaction.type.value if transaction and transaction.type else None,
                } if transaction else None,
            })

        return {
            "total_quantity": total_quantity,
            "entries": serialized_entries,
        }
