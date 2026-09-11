from datetime import datetime
import re

from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models import MaterialAccountEntry, Member, Transaction, TransactionItem, User
from app.services.sale_pricing_service import (
    is_internal_material_product,
    resolve_catalog_unit_price_cents,
)


class MaterialAccountService:
    # Matches: "[Storno ]<quantity>× <product_name>"
    REASON_PATTERN = re.compile(r"^(?P<storno>Storno )?(?P<quantity>\d+)× (?P<product>.+)$")

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def is_internal_material_product(product) -> bool:
        return is_internal_material_product(product)

    def is_internal_material_sale_item(self, item) -> bool:
        """Return True only for sale rows explicitly marked as internal material bookings."""
        return bool(getattr(item, "is_internal_material", False))

    @staticmethod
    def _resolve_material_amount_cents(transaction: Transaction, item) -> int:
        captured = getattr(item, "internal_material_unit_value_cents", None)
        if captured is not None:
            return captured * item.quantity
        product = getattr(item, "product", None)
        if not product:
            return item.total_price_cents

        unit_price_cents = resolve_catalog_unit_price_cents(
            product,
            getattr(transaction, "member", None),
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

    @staticmethod
    def _resolve_entry_note(relevant_items: list[TransactionItem]) -> str | None:
        # Current entries reference exactly one transaction item. Older fallback data can
        # still contain multiple internal-material items on one transaction, where a single
        # top-level note would be ambiguous, so those notes stay on the item rows only.
        if len(relevant_items) != 1:
            return None
        return relevant_items[0].note

    def get_account_summary(
        self,
        *,
        search: str | None = None,
        entry_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int | None = None,
        page_size: int = 50,
    ) -> dict:
        query = self.db.query(MaterialAccountEntry)
        if entry_type == "SALE":
            query = query.filter(~MaterialAccountEntry.reason.startswith("Storno "))
        elif entry_type == "STORNO":
            query = query.filter(MaterialAccountEntry.reason.startswith("Storno "))
        if date_from is not None:
            query = query.filter(MaterialAccountEntry.created_at >= date_from)
        if date_to is not None:
            query = query.filter(MaterialAccountEntry.created_at <= date_to)
        normalized_search = (search or "").strip()
        if normalized_search:
            pattern = f"%{normalized_search}%"
            query = query.filter(or_(
                MaterialAccountEntry.reason.ilike(pattern),
                MaterialAccountEntry.user.has(User.username.ilike(pattern)),
                MaterialAccountEntry.transaction.has(or_(
                    Transaction.member_name.ilike(pattern),
                    cast(Transaction.receipt_number, String).ilike(pattern),
                    Transaction.member.has(Member.name.ilike(pattern)),
                )),
                MaterialAccountEntry.transaction_item.has(TransactionItem.note.ilike(pattern)),
            ))

        total = query.count()
        filtered_value_cents = query.with_entities(
            func.coalesce(func.sum(MaterialAccountEntry.amount_cents), 0)
        ).scalar() or 0
        reason_rows = query.with_entities(MaterialAccountEntry.reason).all()
        total_quantity = 0
        for (reason,) in reason_rows:
            parsed = self.REASON_PATTERN.match(reason or "")
            if parsed and parsed.group("quantity"):
                quantity = int(parsed.group("quantity"))
                total_quantity += -quantity if parsed.group("storno") else quantity

        entries_query = query.options(
            joinedload(MaterialAccountEntry.user),
            joinedload(MaterialAccountEntry.transaction).joinedload(Transaction.items).joinedload(TransactionItem.product),
            joinedload(MaterialAccountEntry.transaction).joinedload(Transaction.member),
            joinedload(MaterialAccountEntry.transaction_item).joinedload(TransactionItem.product),
        ).order_by(MaterialAccountEntry.created_at.desc(), MaterialAccountEntry.id.desc())
        if page is not None:
            page = max(page, 1)
            page_size = min(max(page_size, 1), 100)
            entries_query = entries_query.offset((page - 1) * page_size).limit(page_size)
        entries = entries_query.all()
        serialized_entries = []

        for entry in entries:
            parsed_reason = self.REASON_PATTERN.match(entry.reason or "")
            storno_marker = parsed_reason.group("storno") if parsed_reason else None
            quantity_raw = parsed_reason.group("quantity") if parsed_reason else None
            product_raw = parsed_reason.group("product") if parsed_reason else None
            quantity = int(quantity_raw) if quantity_raw else None
            product_name = product_raw.strip() if product_raw else None
            is_storno = storno_marker is not None
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
                "user_name": (transaction.performed_by_username if transaction else None) or (entry.user.username if entry.user else None),
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
                    "member_name": (transaction.member_name or (transaction.member.name if transaction.member else None)) if transaction else None,
                    "items": [
                        {
                            "id": transaction_item.id,
                            "quantity": transaction_item.quantity,
                            "unit_price_cents": transaction_item.unit_price_cents,
                            "total_price_cents": transaction_item.total_price_cents,
                            "note": transaction_item.note,
                            "product": {
                                "id": transaction_item.product.id,
                                "name": transaction_item.product_name or f"Altbestand – Produkt #{transaction_item.product_id}",
                            } if transaction_item.product else None,
                        }
                        for transaction_item in relevant_items
                    ],
                } if transaction else None,
                "note": self._resolve_entry_note(relevant_items),
            })

        return {
            "total_quantity": total_quantity,
            "total_value_cents": filtered_value_cents,
            "total": total,
            "page": page or 1,
            "page_size": page_size if page is not None else max(total, 1),
            "total_pages": ((total + page_size - 1) // page_size) if page is not None else (1 if total else 0),
            "entries": serialized_entries,
        }
