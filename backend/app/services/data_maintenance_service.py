from sqlalchemy.orm import Session

from app.constants import (
    INTERNAL_MATERIAL_CATEGORY_DESCRIPTION,
    INTERNAL_MATERIAL_CATEGORY_NAME,
)
from app.models import (
    BalanceLog,
    CashBalance,
    CashEntry,
    Category,
    ClubAccountEntry,
    Deckel,
    DeckelItem,
    MaterialAccountEntry,
    Member,
    Product,
    Transaction,
    TransactionItem,
    User,
    Voucher,
    ZBonHistory,
    product_category,
)
from app.services.file_service import delete_member_photo, delete_product_image


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
            display_order=999,
        )

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
        self.db.query(Member).delete(synchronize_session=False)
        self.db.query(Product).delete(synchronize_session=False)
        self.db.query(Category).delete(synchronize_session=False)
        self.db.add(self._build_fixed_internal_material_category())
        self.db.commit()

        for member_id in member_ids:
            delete_member_photo(member_id)
        for product_id in product_ids:
            delete_product_image(product_id)

        return {
            "deleted_users": deleted_users,
            "deleted_members": len(member_ids),
            "deleted_products": len(product_ids),
        }
