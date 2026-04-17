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
    gross_revenue_voucher: float = 0.0
    total_revenue: float = 0.0
    recharge_total: float
    storno_total: float
    voucher_created_total: float = 0.0
    voucher_redeemed_total: float = 0.0
    voucher_open_total: float = 0.0
    cash_opening_balance: float
    cash_calculated: Optional[float] = None
    cash_counted: Optional[float] = None
    cash_difference: Optional[float] = None
    cash_withdrawals: float
    cash_deposits: float
    transaction_count_sales: int
    transaction_count_recharge: int
    transaction_count_storno: int
    transaction_count_total: int = 0
    voucher_created_count: int = 0
    voucher_redeemed_count: int = 0
    voucher_open_count: int = 0
    receipt_number_min: Optional[int] = None
    receipt_number_max: Optional[int] = None
    report_type: str = "zbon"
    created_by_name: Optional[str] = None
    skimmed_by_name: Optional[str] = None
    cash_counted_by_name: Optional[str] = None
    cash_count_details: Optional[str] = None
    report_data: Optional[str] = None
    report_content: Optional[str] = None

    class Config:
        from_attributes = True


class ZBonHistoryListResponse(BaseModel):
    """List of Z-Bon history entries"""
    histories: list[ZBonHistoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
