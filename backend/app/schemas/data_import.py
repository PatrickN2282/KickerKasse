from datetime import datetime
from pydantic import Field

from .category import CategoryCreate
from .member import MemberCreate
from .product import ProductCreate
from .validation import MAX_INT, NonNegativeInt


class ProductImport(ProductCreate):
    is_active: bool = True
    tax_rate: float = Field(default=0, ge=0, le=100, allow_inf_nan=False)


class MemberImport(MemberCreate):
    archived_at: datetime | None = None
    balance_cents: NonNegativeInt = 0
    member_number: int | None = Field(default=None, gt=0, le=MAX_INT)


IMPORT_SCHEMAS = {"categories": CategoryCreate, "products": ProductImport, "members": MemberImport}
