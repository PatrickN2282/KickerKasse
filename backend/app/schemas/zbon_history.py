from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ZBonHistoryResponse(BaseModel):
    """Z-Bon History entry response"""
    id: int
    sequence_number: int
    business_date: datetime
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    gross_revenue_cash: float
    gross_revenue_balance: float
    recharge_total: float
    storno_total: float
    cash_opening_balance: float
    cash_calculated: Optional[float] = None
    cash_counted: Optional[float] = None
    cash_difference: Optional[float] = None
    cash_withdrawals: float
    cash_deposits: float
    transaction_count_sales: int
    transaction_count_recharge: int
    transaction_count_storno: int
    receipt_number_min: Optional[int] = None
    receipt_number_max: Optional[int] = None

    class Config:
        from_attributes = True


class ZBonHistoryListResponse(BaseModel):
    """List of Z-Bon history entries"""
    histories: list[ZBonHistoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
