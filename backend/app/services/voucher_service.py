"""Service for Voucher operations"""
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
from app.models import Voucher, VoucherType, VoucherStatus, VoucherReason, Transaction, TransactionType, PaymentMethod, ClubAccountEntry
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.voucher_repository import VoucherRepository
import logging

logger = logging.getLogger(__name__)


class VoucherService:
    """Business logic for Vouchers"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = VoucherRepository(db)

    def _get_club_account_balance_cents(self) -> int:
        return (
            self.db.query(func.coalesce(func.sum(ClubAccountEntry.amount_cents), 0))
            .scalar()
            or 0
        )

    def create_gift_voucher(self, value_cents: int, reason: str, created_by_user_id: int, description: str = None) -> Voucher:
        """
        Create a GIFT voucher (ohne Zahlung)
        
        Args:
            value_cents: Value in cents
            reason: Reason (DYP_SIEGER, PROMOTION)
            created_by_user_id: User who created this
            description: Optional description
            
        Returns:
            Created Voucher with number
        """
        # Validate reason
        try:
            reason_enum = VoucherReason(reason)
        except ValueError:
            raise ValueError(f"Invalid reason: {reason}")

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

        logger.info(f"Created GIFT voucher #{voucher.voucher_number}: {value_cents/100:.2f}€ ({reason})")
        return voucher

    def create_prepaid_voucher(self, value_cents: int, created_by_user_id: int, description: str = None) -> Voucher:
        """
        Create a PREPAID voucher (wird später gekauft)
        
        Args:
            value_cents: Value in cents
            created_by_user_id: User who created this
            description: Optional description
            
        Returns:
            Created Voucher with number
        """
        voucher = self.repository.create(
            voucher_type=VoucherType.PREPAID,
            value_cents=value_cents,
            created_by_user_id=created_by_user_id,
            description=description,
        )

        TransactionRepository(self.db).create(
            type=TransactionType.VOUCHER_SALE,
            payment_method=PaymentMethod.CASH,
            total_amount_cents=value_cents,
            user_id=created_by_user_id,
            items=[],
            voucher_code=self._format_voucher_identifier(voucher),
            voucher_type=VoucherType.PREPAID.value,
        )

        logger.info(f"Created PREPAID voucher #{voucher.voucher_number}: {value_cents/100:.2f}€")
        return voucher

    def _format_voucher_identifier(self, voucher: Voucher) -> str:
        """Get display identifier for voucher"""
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
        """Calculate applicable voucher amount for the current cart."""
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
        """Create a user-facing validation message for the current cart state."""
        if cart_total_cents is None or cart_total_cents <= 0:
            return "Voucher is valid"

        if cart_context["covers_cart_total"]:
            remainder = cart_context["remaining_value_cents"]
            if remainder > 0:
                return (
                    f"Voucher deckt den Warenkorb ab. "
                    f"Restwert von {remainder / 100:.2f}€ bleibt erhalten."
                )
            return "Voucher deckt den Warenkorb vollständig ab."

        return f"Voucher reduziert den Warenkorb um {cart_context['applicable_amount_cents'] / 100:.2f}€."

    def get_redeemable_voucher(self, voucher_number: str) -> Voucher:
        """Load a voucher and ensure it can still be redeemed."""
        voucher = self.repository.get_by_number(voucher_number)

        if not voucher:
            raise ValueError(f"Voucher #{voucher_number} not found")

        if voucher.status == VoucherStatus.REDEEMED:
            raise ValueError(f"Voucher #{voucher_number} already redeemed")

        if self._get_available_value_cents(voucher) <= 0:
            raise ValueError(f"Voucher #{voucher_number} has no remaining value")

        return voucher

    def validate_voucher(self, voucher_number: str, cart_total_cents: Optional[int] = None) -> dict:
        """
        Validate a voucher before redemption
        
        Args:
            voucher_number: Voucher number to validate
            
        Returns:
            Dict with voucher details and status
            
        Raises:
            ValueError if voucher not found or already redeemed
        """
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

        if voucher.status == VoucherStatus.REDEEMED:
            redeemed_str = voucher.redeemed_at.strftime('%d.%m.%Y %H:%M') if voucher.redeemed_at else "unknown time"
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
        """Update an existing voucher before redemption."""
        voucher = self.repository.get_by_id(voucher_id)
        if not voucher:
            raise ValueError(f"Voucher {voucher_id} not found")

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
        """
        Redeem a GIFT voucher
        
        Creates a negative transaction (loss)
        
        Args:
            voucher_number: Voucher number
            user_id: User who redeems it
            
        Returns:
            Redeemed Voucher
        """
        voucher = self.repository.get_by_number(voucher_number)
        
        if not voucher:
            raise ValueError(f"Voucher #{voucher_number} not found")

        if voucher.voucher_type != VoucherType.GIFT:
            raise ValueError(f"Voucher #{voucher_number} is not a GIFT voucher")

        if voucher.status == VoucherStatus.REDEEMED:
            raise ValueError(f"Voucher #{voucher_number} already redeemed")

        # Create transaction for GIFT voucher (negative amount = loss)
        transaction = Transaction(
            type=TransactionType.VOUCHER_REDEMPTION,
            payment_method=PaymentMethod.VOUCHER_GIFT,
            total_amount_cents=-self._get_available_value_cents(voucher),  # Negative = loss
            user_id=redeemed_by,
            member_id=member_id,
        )
        self.db.add(transaction)
        self.db.flush()  # Get transaction ID without committing

        # Mark voucher as redeemed
        self.repository.redeem(voucher.id, redeemed_by, transaction.id)

        logger.info(f"Redeemed GIFT voucher #{voucher_number} ({self._get_available_value_cents(voucher)/100:.2f}€) in transaction {transaction.id}")
        return transaction

    def redeem_prepaid_voucher(self, voucher_number: str, redeemed_by: int, member_id: Optional[int] = None) -> Transaction:
        """
        Redeem a PREPAID voucher
        
        Creates a null transaction (only payment method, no amount change)
        
        Args:
            voucher_number: Voucher number
            user_id: User who redeems it
            
        Returns:
            Redeemed Voucher
        """
        voucher = self.repository.get_by_number(voucher_number)
        
        if not voucher:
            raise ValueError(f"Voucher #{voucher_number} not found")

        if voucher.voucher_type != VoucherType.PREPAID:
            raise ValueError(f"Voucher #{voucher_number} is not a PREPAID voucher")

        if voucher.status == VoucherStatus.REDEEMED:
            raise ValueError(f"Voucher #{voucher_number} already redeemed")

        # Create transaction for PREPAID voucher (null amount = just payment method logging)
        transaction = Transaction(
            type=TransactionType.VOUCHER_REDEMPTION,
            payment_method=PaymentMethod.VOUCHER_PREPAID,
            total_amount_cents=0,  # Null transaction
            user_id=redeemed_by,
            member_id=member_id,
        )
        self.db.add(transaction)
        self.db.flush()

        # Mark voucher as redeemed
        self.repository.redeem(voucher.id, redeemed_by, transaction.id)

        logger.info(f"Redeemed PREPAID voucher #{voucher_number} in transaction {transaction.id}")
        return transaction

    def get_voucher_statistics(self, start_date: date, end_date: date) -> dict:
        """
        Get voucher statistics for a date range
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dict with statistics
        """
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
            reason="Vereinskonto aufgeladen",
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
