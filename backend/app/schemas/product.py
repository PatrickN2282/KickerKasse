from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from typing import Optional, List


from .validation import NormalizedModel, UpdateModel, Name, Description, NonNegativeInt


class ProductBase(NormalizedModel):
    name: Name
    description: Description = None
    warengruppe: Optional[str] = Field(default=None, max_length=120)
    price_cents: NonNegativeInt
    member_price_cents: Optional[NonNegativeInt] = None
    is_discountable: bool = True
    stock_quantity: NonNegativeInt = 0
    minimum_stock_quantity: NonNegativeInt = 0
    notify_on_low_stock: bool = False
    is_unlimited_stock: bool = False
    is_variable_price: bool = False
    is_visible_in_kasse: bool = True
    requires_guest_list: bool = False
    opens_small_parts_drawer: bool = False


class ProductCreate(ProductBase):
    pass


class ProductUpdate(UpdateModel):
    non_nullable_fields = {"name", "price_cents", "is_discountable", "minimum_stock_quantity", "notify_on_low_stock", "is_unlimited_stock", "is_variable_price", "is_visible_in_kasse", "requires_guest_list", "opens_small_parts_drawer", "is_active"}

    @model_validator(mode="before")
    @classmethod
    def reject_stock_changes(cls, data):
        if isinstance(data, dict) and "stock_quantity" in data:
            raise ValueError("Bestand bitte über Einlagerung oder Bestandskorrektur ändern")
        return data

    name: Optional[Name] = None
    description: Description = None
    warengruppe: Optional[str] = Field(default=None, max_length=120)
    price_cents: Optional[NonNegativeInt] = None
    member_price_cents: Optional[NonNegativeInt] = None
    is_discountable: Optional[bool] = None
    minimum_stock_quantity: Optional[NonNegativeInt] = None
    notify_on_low_stock: Optional[bool] = None
    is_unlimited_stock: Optional[bool] = None
    is_variable_price: Optional[bool] = None
    is_visible_in_kasse: Optional[bool] = None
    requires_guest_list: Optional[bool] = None
    opens_small_parts_drawer: Optional[bool] = None
    is_active: Optional[bool] = None


class ProductStockCorrectionRequest(BaseModel):
    new_stock_quantity: NonNegativeInt
    reason: Optional[str] = Field(default=None, max_length=255)
    open_small_parts_drawer: bool = False


class CategoryInfo(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ProductResponse(ProductBase):
    id: int
    is_active: bool
    image_path: Optional[str] = None  # Path to product image file
    categories: List[CategoryInfo] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductMutationResponse(ProductResponse):
    drawer_targets: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ProductStockCorrectionLogResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    old_stock_quantity: int
    new_stock_quantity: int
    change_quantity: int
    executed_by_username: str
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True
