from .auth import router as auth_router
from .user import router as user_router
from .member import router as member_router
from .product import router as product_router
from .category import router as category_router
from .transaction import router as transaction_router
from .deckel import router as deckel_router
from .voucher import admin_router as voucher_admin_router, kasse_router as voucher_kasse_router
from .app_settings import router as app_settings_router
from .data_maintenance import router as data_maintenance_router
from .import_export import router as import_export_router
from .audit_log import router as audit_log_router

__all__ = [
    "auth_router",
    "user_router",
    "member_router",
    "product_router",
    "category_router",
    "transaction_router",
    "deckel_router",
    "voucher_admin_router",
    "voucher_kasse_router",
    "app_settings_router",
    "data_maintenance_router",
    "import_export_router",
    "audit_log_router",
]
