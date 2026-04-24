"""Service for Voucher operations"""
from datetime import date
from typing import Optional
import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    ClubAccountEntry,
    PaymentMethod,
    Product,
    Transaction,
    TransactionType,
    Voucher,
    VoucherReason,
    VoucherStatus,
    VoucherType,
)
from app.repositories.product_repository import ProductRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.voucher_repository import VoucherRepository

logger = logging.getLogger(__name__)


class VoucherService:
    """Business logic for Vouchers"""

    PREPAID_PRODUCT_MARKER = "VERZEHRKARTE:"
    DEFAULT_PREPAID_VALUE_CENTS = 1000

    def __init__(self, db: Session):
        self.db = db
        self.repository = VoucherRepository(db)
        self.product_repository = ProductRepository(db)

    @classmethod
    def build_prepaid_product_name(cls, value_cents: int) -> str:
        if value_cents == cls.DEFAULT_PREPAID_VALUE_CENTS:
            return "Verzehrkarte"
        return f"Verzehrkarte {value_cents / 100:.2f} €".replace(".", ",")

    @classmethod
    def build_prepaid_product_description(cls, value_cents: int) -> str:
        return f"{cls.PREPAID_PRODUCT_MARKER}{value_cents}"

    @classmethod
    def get_prepaid_value_from_product(cls, product: Product | None) -> int | None:
        description = (getattr(product, "description", None) or "").strip()
        if not description.startswith(cls.PREPAID_PRODUCT_MARKER):
            return None
        try:
            return int(description.split(":", 1)[1])
        except (IndexError, ValueError):
            return None

    def get_or_create_prepaid_product(self, value_cents: int) -> Product:
        marker = self.build_prepaid_product_description(value_cents)
        prepaid_product = self.db.query(Product).filter(Product.description == marker).first()
        if prepaid_product:
            prepaid_product.name = self.build_prepaid_product_name(value_cents)
            prepaid_product.price_cents = value_cents
            prepaid_product.member_price_cents = None
            prepaid_product.is_discountable = False
            prepaid_product.is_active = True
            self.db.flush()
            return prepaid_product

        prepaid_product = Product(
            name=self.build_prepaid_product_name(value_cents),
            description=marker,
            price_cents=value_cents,
            member_price_cents=None,
            is_discountable=False,
            stock_quantity=0,
            is_active=True,
        )
        self.db.add(prepaid_product)
        self.db.flush()
        return prepaid_product

    def _get_club_account_balance_cents(self) -> int:
        return (
            self.db.query(func.coalesce(func.sum(ClubAccountEntry.amount_cents), 0)).scalar()
            or 0
        )

    def create_gift_voucher(self, value_cents: int, reason: str, created_by_user_id: int, description: str = None) -> Voucher:
        try:
            reason_enum = VoucherReason(reason)
        except ValueError as exc:
            raise ValueError(f"Invalid reason: {reason}") from exc

        voucher = self.repository.create(
            voucher_type=VoucherType.GIFT,
            value_cents=value_cents,
            created_by_user_id=created_by_user_id,
            reason=reason_enum,
            description=description,
        )

        self.db.add(ClubAccountEntry(
            amount_cents=-value_cents,
            reason=f"Geschenk-Gutschein {self._format_voucher_identifier(voucher)} erstellt",
            user_id=created_by_user_id,
            voucher_id=voucher.id,
        ))
        self.db.commit()
        self.db.refresh(voucher)

        logger.info("Created GIFT voucher #%s: %.2f€ (%s)", voucher.voucher_number, value_cents / 100, reason)
        return voucher

    def create_prepaid_vouchers(
        self,
        value_cents: int,
        created_by_user_id: int,
        quantity: int = 1,
        description: str = None,
    ) -> tuple[list[Voucher], Product]:
        if quantity <= 0:
            raise ValueError("Anzahl muss größer als 0 sein")

        prepaid_product = self.get_or_create_prepaid_product(value_cents)
        created_vouchers: list[Voucher] = []

        for _ in range(quantity):
            created_vouchers.append(self.repository.create(
                voucher_type=VoucherType.PREPAID,
                value_cents=value_cents,
                created_by_user_id=created_by_user_id,
                description=description,
            ))

        prepaid_product.stock_quantity += quantity
        self.db.commit()
        self.db.refresh(prepaid_product)
        for voucher in created_vouchers:
            self.db.refresh(voucher)

        logger.info(
            "Created %s PREPAID vouchers with %.2f€ and increased stock of %s",
            quantity,
            value_cents / 100,
            prepaid_product.name,
        )
        return created_vouchers, prepaid_product

    def ensure_prepaid_stock(self, requested_quantities_by_value: dict[int, int]) -> None:
        for value_cents, quantity in requested_quantities_by_value.items():
            available = self.repository.get_unsold_prepaid_by_value(value_cents, quantity)
            if len(available) < quantity:
                raise ValueError(
                    f"Es sind nicht genügend unverkaufte Verzehrkarten mit {value_cents / 100:.2f}€ vorhanden"
                )

    def issue_prepaid_vouchers_for_sale(
        self,
        transaction: Transaction,
        sold_quantities_by_value: dict[int, int],
        sold_by_user_id: int,
    ) -> tuple[list[Voucher], Voucher | None]:
        issued_vouchers: list[Voucher] = []
        if not sold_quantities_by_value:
            return issued_vouchers, self.repository.get_next_unsold_prepaid()

        for value_cents, quantity in sold_quantities_by_value.items():
            vouchers = self.repository.get_unsold_prepaid_by_value(value_cents, quantity)
            if len(vouchers) < quantity:
                raise ValueError(
                    f"Es sind nicht genügend unverkaufte Verzehrkarten mit {value_cents / 100:.2f}€ vorhanden"
                )

            for voucher in vouchers:
                voucher.sold_by_user_id = sold_by_user_id
                voucher.sold_in_transaction_id = transaction.id
                voucher.sold_at = transaction.created_at
                issued_vouchers.append(voucher)

        self.db.flush()
        next_unsold = self.repository.get_next_unsold_prepaid()
        return issued_vouchers, next_unsold

    def get_next_unissued_prepaid_voucher_number(self) -> str | None:
        next_voucher = self.repository.get_next_unsold_prepaid()
        if not next_voucher:
            return None
        return self.format_voucher_identifier(next_voucher)

    def format_voucher_identifier(self, voucher: Voucher | None) -> str | None:
        if not voucher:
            return None
        return self._format_voucher_identifier(voucher)

    def _format_voucher_identifier(self, voucher: Voucher) -> str:
        if voucher.voucher_code:
            return voucher.voucher_code
        year = voucher.created_at.year if voucher.created_at else date.today().year
        return f"V-{year}-{str(voucher.voucher_number).zfill(3)}"

    @staticmethod
    def _get_available_value_cents(voucher: Voucher) -> int:
        if voucher.remaining_value_cents is None:
            return voucher.value_cents
        return voucher.remaining_value_cents

    def _build_cart_context(self, voucher: Voucher, cart_total_cents: Optional[int] = None) -> dict:
        available_value_cents = self._get_available_value_cents(voucher)

        if cart_total_cents is None:
            return {
                "applicable_amount_cents": available_value_cents,
                "remaining_value_cents": 0,
                "covers_cart_total": True,
            }

        applicable_amount_cents = min(available_value_cents, max(cart_total_cents, 0))
        remaining_value_cents = max(available_value_cents - applicable_amount_cents, 0)
        covers_cart_total = available_value_cents >= cart_total_cents

        return {
            "applicable_amount_cents": applicable_amount_cents,
            "remaining_value_cents": remaining_value_cents,
            "covers_cart_total": covers_cart_total,
        }

    def _build_validation_message(self, cart_context: dict, cart_total_cents: Optional[int]) -> str:
        if cart_total_cents is None or cart_total_cents <= 0:
            return "Voucher is valid"

        if cart_context["covers_cart_total"]:
            remainder = cart_context["remaining_value_cents"]
            if remainder > 0:
                return f"Voucher deckt den Warenkorb ab. Restwert von {remainder / 100:.2f}€ bleibt erhalten."
            return "Voucher deckt den Warenkorb vollständig ab."

        return f"Voucher reduziert den Warenkorb um {cart_context['applicable_amount_cents'] / 100:.2f}€."

    def get_redeemable_voucher(self, voucher_number: str) -> Voucher:
        voucher = self.repository.get_by_number(voucher_number)

        if not voucher:
            raise ValueError(f"Voucher #{voucher_number} not found")
        if voucher.voucher_type == VoucherType.PREPAID and not voucher.sold_at:
            raise ValueError(f"Voucher #{voucher_number} wurde noch nicht ausgegeben")
        if voucher.status == VoucherStatus.REDEEMED:
            raise ValueError(f"Voucher #{voucher_number} already redeemed")
        if self._get_available_value_cents(voucher) <= 0:
            raise ValueError(f"Voucher #{voucher_number} has no remaining value")

        return voucher

    def validate_voucher(self, voucher_number: str, cart_total_cents: Optional[int] = None) -> dict:
        voucher = self.repository.get_by_number(voucher_number)

        if not voucher:
            return {
                "valid": False,
                "voucher_number": str(voucher_number),
                "voucher_type": "",
                "value_cents": 0,
                "status": "NOT_FOUND",
                "message": f"Voucher {voucher_number} not found",
                "reason": None,
                "applicable_amount_cents": 0,
                "remaining_value_cents": 0,
                "covers_cart_total": False,
            }

        if voucher.voucher_type == VoucherType.PREPAID and not voucher.sold_at:
            return {
                "valid": False,
                "voucher_number": self._format_voucher_identifier(voucher),
                "voucher_type": voucher.voucher_type.value,
                "value_cents": 0,
                "status": "NOT_SOLD",
                "message": "Diese Verzehrkarte wurde noch nicht ausgegeben",
                "reason": voucher.reason.value if voucher.reason else None,
                "applicable_amount_cents": 0,
                "remaining_value_cents": 0,
                "covers_cart_total": False,
            }

        if voucher.status == VoucherStatus.REDEEMED:
            redeemed_str = voucher.redeemed_at.strftime("%d.%m.%Y %H:%M") if voucher.redeemed_at else "unknown time"
            return {
                "valid": False,
                "voucher_number": self._format_voucher_identifier(voucher),
                "voucher_type": voucher.voucher_type.value,
                "value_cents": 0,
                "status": voucher.status.value,
                "message": f"Voucher already redeemed on {redeemed_str}",
                "reason": voucher.reason.value if voucher.reason else None,
                "applicable_amount_cents": 0,
                "remaining_value_cents": 0,
                "covers_cart_total": False,
            }

        cart_context = self._build_cart_context(voucher, cart_total_cents)
        message = self._build_validation_message(cart_context, cart_total_cents)

        return {
            "valid": True,
            "voucher_number": self._format_voucher_identifier(voucher),
            "voucher_type": voucher.voucher_type.value,
            "value_cents": self._get_available_value_cents(voucher),
            "status": voucher.status.value,
            "message": message,
            "reason": voucher.reason.value if voucher.reason else None,
            **cart_context,
        }

    def update_voucher(
        self,
        voucher_id: int,
        value_cents: int,
        reason: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Voucher:
        voucher = self.repository.get_by_id(voucher_id)
        if not voucher:
            raise ValueError(f"Voucher {voucher_id} not found")

        if voucher.voucher_type == VoucherType.PREPAID and voucher.sold_at:
            raise ValueError("Ausgegebene Verzehrkarten können nicht mehr bearbeitet werden")
        if voucher.status != VoucherStatus.CREATED or (voucher.redeemed_amount_cents or 0) > 0:
            raise ValueError("Bereits genutzte Gutscheine können nicht mehr bearbeitet werden")
        if voucher.voucher_type == VoucherType.GIFT and not reason:
            raise ValueError("Gift-Gutscheine benötigen einen Grund")

        if voucher.voucher_type == VoucherType.PREPAID:
            reason = None

        return self.repository.update(
            voucher_id,
            value_cents=value_cents,
            reason=VoucherReason(reason) if reason else None,
            description=description,
        )

    def redeem_gift_voucher(self, voucher_number: str, redeemed_by: int, member_id: Optional[int] = None) -> Transaction:
        voucher = self.repository.get_by_number(voucher_number)

        if not voucher:
            raise ValueError(f"Voucher #{voucher_number} not found")
        if voucher.voucher_type != VoucherType.GIFT:
            raise ValueError(f"Voucher #{voucher_number} is not a GIFT voucher")
        if voucher.status == VoucherStatus.REDEEMED:
            raise ValueError(f"Voucher #{voucher_number} already redeemed")

        transaction = Transaction(
            type=TransactionType.VOUCHER_REDEMPTION,
            payment_method=PaymentMethod.VOUCHER_GIFT,
            total_amount_cents=-self._get_available_value_cents(voucher),
            user_id=redeemed_by,
            member_id=member_id,
        )
        self.db.add(transaction)
        self.db.flush()

        self.repository.redeem(voucher.id, redeemed_by, transaction.id)

        logger.info(
            "Redeemed GIFT voucher #%s (%.2f€) in transaction %s",
            voucher_number,
            self._get_available_value_cents(voucher) / 100,
            transaction.id,
        )
        return transaction

    def redeem_prepaid_voucher(self, voucher_number: str, redeemed_by: int, member_id: Optional[int] = None) -> Transaction:
        voucher = self.repository.get_by_number(voucher_number)

        if not voucher:
            raise ValueError(f"Voucher #{voucher_number} not found")
        if voucher.voucher_type != VoucherType.PREPAID:
            raise ValueError(f"Voucher #{voucher_number} is not a PREPAID voucher")
        if not voucher.sold_at:
            raise ValueError(f"Voucher #{voucher_number} wurde noch nicht ausgegeben")
        if voucher.status == VoucherStatus.REDEEMED:
            raise ValueError(f"Voucher #{voucher_number} already redeemed")

        transaction = Transaction(
            type=TransactionType.VOUCHER_REDEMPTION,
            payment_method=PaymentMethod.VOUCHER_PREPAID,
            total_amount_cents=0,
            user_id=redeemed_by,
            member_id=member_id,
        )
        self.db.add(transaction)
        self.db.flush()

        self.repository.redeem(voucher.id, redeemed_by, transaction.id)

        logger.info("Redeemed PREPAID voucher #%s in transaction %s", voucher_number, transaction.id)
        return transaction

    def get_voucher_statistics(self, start_date: date, end_date: date) -> dict:
        gift_created = self.repository.count_by_type_and_status(VoucherType.GIFT, VoucherStatus.CREATED)
        gift_redeemed_count = self.repository.count_by_type_and_status(VoucherType.GIFT, VoucherStatus.REDEEMED)
        gift_redeemed_value = self.repository.sum_redeemed_by_type_and_date(VoucherType.GIFT, start_date, end_date)

        prepaid_created = self.repository.count_by_type_and_status(VoucherType.PREPAID, VoucherStatus.CREATED)
        prepaid_redeemed_count = self.repository.count_by_type_and_status(VoucherType.PREPAID, VoucherStatus.REDEEMED)
        prepaid_redeemed_value = self.repository.sum_redeemed_by_type_and_date(VoucherType.PREPAID, start_date, end_date)

        return {
            "gift": {
                "created": gift_created,
                "redeemed": gift_redeemed_count,
                "redeemed_value_cents": gift_redeemed_value,
                "redeemed_value_eur": gift_redeemed_value / 100.0,
            },
            "prepaid": {
                "created": prepaid_created,
                "redeemed": prepaid_redeemed_count,
                "redeemed_value_cents": prepaid_redeemed_value,
                "redeemed_value_eur": prepaid_redeemed_value / 100.0,
            },
        }

    def get_club_account_summary(self) -> dict:
        entries = self.db.query(ClubAccountEntry).order_by(ClubAccountEntry.created_at.desc()).all()
        balance_cents = sum(entry.amount_cents for entry in entries)
        return {
            "balance_cents": balance_cents,
            "entries": [
                {
                    "id": entry.id,
                    "amount_cents": entry.amount_cents,
                    "reason": entry.reason,
                    "user_name": entry.user.username if entry.user else None,
                    "created_at": entry.created_at,
                }
                for entry in entries
            ],
        }

    def top_up_club_account(self, amount_cents: int, user_id: int) -> dict:
        transaction = TransactionRepository(self.db).create(
            type=TransactionType.RECHARGE,
            payment_method=PaymentMethod.CASH,
            total_amount_cents=amount_cents,
            user_id=user_id,
            items=[],
        )
        entry = ClubAccountEntry(
            amount_cents=amount_cents,
            reason="Materialkonto aufgeladen",
            user_id=user_id,
            transaction_id=transaction.id,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return {
            "entry_id": entry.id,
            "transaction_id": transaction.id,
            "balance_cents": self._get_club_account_balance_cents(),
        }
