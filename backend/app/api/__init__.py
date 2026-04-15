from .auth import router as auth_router
from .user import router as user_router
from .member import router as member_router
from .product import router as product_router
from .category import router as category_router
from .transaction import router as transaction_router
from .voucher import admin_router as voucher_admin_router, kasse_router as voucher_kasse_router

__all__ = [
    "auth_router",
    "user_router",
    "member_router",
    "product_router",
    "category_router",
    "transaction_router",
    "voucher_admin_router",
    "voucher_kasse_router",
]
