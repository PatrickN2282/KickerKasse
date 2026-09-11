from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


from .validation import NormalizedModel, UpdateModel, Name, Description, DatabaseInt


class CategoryBase(NormalizedModel):
    name: Name
    description: Description = None
    color: Optional[str] = Field(None, max_length=20)
    is_active_in_kasse: bool = True
    display_order: DatabaseInt = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(UpdateModel):
    non_nullable_fields = {"name", "is_active_in_kasse", "display_order"}

    name: Optional[Name] = None
    description: Description = None
    color: Optional[str] = Field(None, max_length=20)
    is_active_in_kasse: Optional[bool] = None
    display_order: Optional[DatabaseInt] = None


class CategoryResponse(CategoryBase):
    id: int
    is_fixed: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
