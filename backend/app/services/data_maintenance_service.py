import shutil

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.constants import (
    INTERNAL_MATERIAL_CATEGORY_DESCRIPTION,
    INTERNAL_MATERIAL_CATEGORY_DISPLAY_ORDER,
    INTERNAL_MATERIAL_CATEGORY_NAME,
)
from app.models import (
    AuditLog,
    AppSettings,
    BalanceLog,
    CashBalance,
    CashEntry,
    Category,
    ClubAccountEntry,
    Deckel,
    DeckelItem,
    MaterialAccountEntry,
    Member,
    MemberBalanceCorrectionLog,
    Product,
    ProductStockCorrectionLog,
    Transaction,
    TransactionItem,
    User,
    Voucher,
    ZBonHistory,
    product_category,
)
from app.services.file_service import APP_SETTINGS_DIR, delete_member_photo, delete_product_image


_TABLES_WITH_SEQUENCES = [
    "transactions",
    "transaction_items",
    "vouchers",
    "members",
    "users",
    "products",
    "categories",
    "balance_logs",
    "cash_entries",
    "cash_balances",
    "club_account_entries",
    "material_account_entries",
    "deckel",
    "deckel_items",
    "zbon_history",
    "product_stock_correction_logs",
    "member_balance_correction_logs",
    "audit_logs",
    "app_settings",
]


class DataMaintenanceService:
    """Maintenance operations for privileged admin cleanup flows."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _build_fixed_internal_material_category() -> Category:
        return Category(
            name=INTERNAL_MATERIAL_CATEGORY_NAME,
            description=INTERNAL_MATERIAL_CATEGORY_DESCRIPTION,
            is_active_in_kasse=True,
            display_order=INTERNAL_MATERIAL_CATEGORY_DISPLAY_ORDER,
        )

    def _reset_sequences(self) -> None:
        """Reset all auto-increment sequences for tables cleared during hard reset."""
        for table in _TABLES_WITH_SEQUENCES:
            self.db.execute(
                text(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), 1, false)"
                )
            )

    def get_stats(self) -> dict:
        """Return current row counts for the main data tables."""
        return {
            "transactions": self.db.query(Transaction.id).count(),
            "members": self.db.query(Member.id).count(),
            "users": self.db.query(User.id).count(),
            "products": self.db.query(Product.id).count(),
            "categories": self.db.query(Category.id).count(),
            "vouchers": self.db.query(Voucher.id).count(),
            "audit_log_entries": self.db.query(AuditLog.id).count(),
        }

    def hard_reset(self) -> dict:
        member_ids = [member_id for (member_id,) in self.db.query(Member.id).all()]
        product_ids = [product_id for (product_id,) in self.db.query(Product.id).all()]

        self.db.execute(product_category.delete())
        self.db.query(BalanceLog).delete(synchronize_session=False)
        self.db.query(ClubAccountEntry).delete(synchronize_session=False)
        self.db.query(MaterialAccountEntry).delete(synchronize_session=False)
        self.db.query(CashEntry).delete(synchronize_session=False)
        self.db.query(CashBalance).delete(synchronize_session=False)
        self.db.query(ZBonHistory).delete(synchronize_session=False)
        self.db.query(Voucher).delete(synchronize_session=False)
        self.db.query(DeckelItem).delete(synchronize_session=False)
        self.db.query(Deckel).delete(synchronize_session=False)
        self.db.query(TransactionItem).delete(synchronize_session=False)
        self.db.query(Transaction).delete(synchronize_session=False)
        self.db.query(User).update({User.member_id: None}, synchronize_session=False)
        deleted_users = self.db.query(User).delete(synchronize_session=False)
        self.db.query(MemberBalanceCorrectionLog).delete(synchronize_session=False)
        self.db.query(Member).delete(synchronize_session=False)
        self.db.query(ProductStockCorrectionLog).delete(synchronize_session=False)
        self.db.query(Product).delete(synchronize_session=False)
        self.db.query(Category).delete(synchronize_session=False)
        self.db.query(AuditLog).delete(synchronize_session=False)
        self.db.query(AppSettings).delete(synchronize_session=False)
        self.db.add(self._build_fixed_internal_material_category())
        self._reset_sequences()
        self.db.commit()

        for member_id in member_ids:
            delete_member_photo(member_id)
        for product_id in product_ids:
            delete_product_image(product_id)
        if APP_SETTINGS_DIR.exists():
            for path in APP_SETTINGS_DIR.iterdir():
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    path.unlink(missing_ok=True)

        return {
            "deleted_users": deleted_users,
            "deleted_members": len(member_ids),
            "deleted_products": len(product_ids),
        }
