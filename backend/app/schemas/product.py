from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = None
    price_cents: int = Field(..., ge=0)
    member_price_cents: Optional[int] = Field(None, ge=0)
    is_discountable: bool = True
    stock_quantity: int = Field(default=0, ge=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_cents: Optional[int] = None
    member_price_cents: Optional[int] = None
    is_discountable: Optional[bool] = None
    stock_quantity: Optional[int] = None
    is_active: Optional[bool] = None


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

    class Config:
        from_attributes = True
