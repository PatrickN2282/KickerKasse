from sqlalchemy.orm import Session
from app.models import ProductStockCorrectionLog
from app.repositories import ProductRepository
from app.services.actor_resolution_service import resolve_actor_username


class ProductService:
    """Product management service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProductRepository(db)

    def _audit(self, action: str, product, user_username: str | None, old_value: dict | None = None, new_value: dict | None = None):
        """Write an audit log entry for a product action."""
        try:
            from app.services.audit_log_service import AuditLogService
            AuditLogService(self.db).log(
                entity_type="product",
                action=action,
                user_username=user_username,
                entity_id=product.id,
                entity_name=product.name,
                old_value=old_value,
                new_value=new_value,
            )
        except Exception:
            pass
    
    def create_product(
        self, name: str, price_cents: int, description: str = None,
        member_price_cents: int = None, is_discountable: bool = True,
        stock_quantity: int = 0,
        minimum_stock_quantity: int = 0,
        notify_on_low_stock: bool = False,
        is_unlimited_stock: bool = False,
        warengruppe: str = None,
        is_variable_price: bool = False,
        performed_by_username: str | None = None,
    ):
        """Create a new product"""
        product = self.repo.create(
            name, price_cents, description, member_price_cents,
            is_discountable, stock_quantity, minimum_stock_quantity, notify_on_low_stock, is_unlimited_stock, warengruppe,
            is_variable_price,
        )
        self._audit(
            "CREATED",
            product,
            performed_by_username,
            new_value={"name": name, "price_cents": price_cents, "warengruppe": warengruppe},
        )
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def get_product(self, product_id: int):
        """Get product by ID"""
        return self.repo.get_by_id(product_id)
    
    def get_all_products(self, only_active: bool = True):
        """Get all products"""
        return self.repo.get_all(only_active)
    
    def update_product(self, product_id: int, performed_by_username: str | None = None, **kwargs):
        """Update product"""
        existing = self.repo.get_by_id(product_id)
        if not existing:
            return None
        old_snapshot = {"name": existing.name, "price_cents": existing.price_cents, "warengruppe": existing.warengruppe}
        product = self.repo.update(product_id, **kwargs)
        if product:
            self._audit("UPDATED", product, performed_by_username, old_value=old_snapshot, new_value=kwargs)
            self.db.commit()
            self.db.refresh(product)
        return product
    
    def check_stock(self, product_id: int, quantity: int) -> bool:
        """Check if product has sufficient stock"""
        product = self.repo.get_by_id(product_id)
        return bool(product and (product.is_unlimited_stock or product.stock_quantity >= quantity))
    
    def adjust_stock(self, product_id: int, quantity: int, executed_by_username: str | None = None):
        """Adjust product stock (positive or negative)"""
        product = self.repo.get_by_id(product_id)
        if not product:
            return None
        
        if quantity > 0:
            old_stock_quantity = product.stock_quantity
            product = self.repo.add_stock(product_id, quantity)
            if not product:
                return None
            if not product.is_unlimited_stock:
                self._audit(
                    "RESTOCKED",
                    product,
                    executed_by_username,
                    old_value={"stock_quantity": old_stock_quantity},
                    new_value={
                        "stock_quantity": product.stock_quantity,
                        "change_quantity": quantity,
                    },
                )
            self.db.commit()
            self.db.refresh(product)
            return product
        else:
            if not self.repo.deduct_stock(product_id, abs(quantity)):
                return None
            return self.repo.get_by_id(product_id)

    def correct_stock(
        self,
        product_id: int,
        new_stock_quantity: int,
        executed_by_username: str | None = None,
        executed_by_user_id: int | None = None,
        reason: str | None = None,
    ):
        """Set product stock without cash flow and create a separate correction audit log."""
        product = self.repo.get_by_id(product_id)
        if not product:
            return None

        actor_username = resolve_actor_username(
            self.db,
            executed_by_username=executed_by_username,
            executed_by_user_id=executed_by_user_id,
        )
        old_stock_quantity = product.stock_quantity
        product.stock_quantity = new_stock_quantity
        correction_reason = (reason or "").strip() or "KORREKTURBUCHUNG"

        log = ProductStockCorrectionLog(
            product_id=product.id,
            product_name=product.name,
            old_stock_quantity=old_stock_quantity,
            new_stock_quantity=new_stock_quantity,
            change_quantity=new_stock_quantity - old_stock_quantity,
            executed_by_username=actor_username or "Unbekannt",
            reason=correction_reason,
        )
        self.db.add(log)
        self._audit(
            "STOCK_CORRECTION",
            product,
            actor_username,
            old_value={"stock_quantity": old_stock_quantity},
            new_value={
                "stock_quantity": new_stock_quantity,
                "change_quantity": new_stock_quantity - old_stock_quantity,
                "reason": correction_reason,
            },
        )
        self.db.commit()
        self.db.refresh(product)
        self.db.refresh(log)
        return product

    def get_stock_correction_logs(self):
        """Get all product stock correction logs."""
        return (
            self.db.query(ProductStockCorrectionLog)
            .order_by(ProductStockCorrectionLog.created_at.desc(), ProductStockCorrectionLog.id.desc())
            .all()
        )
    
    def delete_product(self, product_id: int, performed_by_username: str | None = None):
        """Delete product (soft delete)"""
        product = self.repo.get_by_id(product_id)
        if not product:
            return False
        product_snapshot = {"name": product.name, "price_cents": product.price_cents}
        result = self.repo.delete(product_id)
        if result:
            self._audit(
                "DELETED",
                product,
                performed_by_username,
                old_value=product_snapshot,
            )
            self.db.commit()
        return result
