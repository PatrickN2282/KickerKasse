"""Enhanced Z-Bon Generation Service with comprehensive reporting"""
from datetime import datetime, date
import json
from jinja2 import Template
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models import (
    Transaction, TransactionType, PaymentMethod, BalanceLog,
    ZBonHistory, Member, Product, Voucher, VoucherType, VoucherStatus, CashEntry, CashEntryType
)
from app.repositories import TransactionRepository
from app.templates.zbon_template import ZBON_HTML_TEMPLATE
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ZBonService:
    """Service for generating comprehensive Z-Bon reports with full aggregations"""
    PREPAID_PRODUCT_MARKER = "VERZEHRKARTE:"
    
    def __init__(self, db: Session):
        self.db = db
        self.trans_repo = TransactionRepository(db)

    def _calculate_sale_gross_cents(self, transaction: Transaction) -> int:
        return sum(item.total_price_cents for item in transaction.items)

    @classmethod
    def _get_prepaid_product_value_cents(cls, product: Product | None) -> int | None:
        description = (getattr(product, "description", None) or "").strip()
        if not description.startswith(cls.PREPAID_PRODUCT_MARKER):
            return None
        try:
            return int(description.split(":", 1)[1])
        except (IndexError, ValueError):
            return None

    def _calculate_prepaid_item_total_cents(self, transaction: Transaction) -> int:
        return sum(
            item.total_price_cents
            for item in transaction.items
            if self._get_prepaid_product_value_cents(item.product) is not None
        )

    def _calculate_non_prepaid_sale_gross_cents(self, transaction: Transaction) -> int:
        return max(self._calculate_sale_gross_cents(transaction) - self._calculate_prepaid_item_total_cents(transaction), 0)

    @staticmethod
    def _format_member_name(member: Member | None) -> str:
        if not member:
            return "Gast"

        first_name = (member.first_name or "").strip()
        last_name = (member.last_name or "").strip()
        if first_name or last_name:
            return " ".join(part for part in [first_name, f"{last_name[:1]}." if last_name else ""] if part)

        return member.name or "Gast"

    def _get_current_period_bounds(self) -> tuple[datetime, datetime, ZBonHistory | None]:
        period_end = datetime.now()
        last_zbon = self.db.query(ZBonHistory).order_by(desc(ZBonHistory.sequence_number)).first()
        period_start = last_zbon.period_end if last_zbon else None
        return period_start, period_end, last_zbon

    def _get_transactions_for_period(self, period_start: datetime | None, period_end: datetime) -> list[Transaction]:
        query = self.db.query(Transaction).order_by(Transaction.created_at.asc())
        if period_start:
            query = query.filter(Transaction.created_at > period_start)
        query = query.filter(Transaction.created_at <= period_end)
        return query.all()

    def _get_opening_cash_balance(self, last_zbon: ZBonHistory | None) -> float:
        if not last_zbon:
            return 0.0
        if last_zbon.cash_counted is not None:
            return float(last_zbon.cash_counted)
        return float(last_zbon.cash_calculated or 0.0)

    def _get_cash_entry_summary(
        self,
        period_start: datetime | None,
        period_end: datetime,
        pending_withdrawals: list[dict] | None = None,
    ) -> dict:
        query = self.db.query(CashEntry).filter(CashEntry.created_at <= period_end)
        if period_start:
            query = query.filter(CashEntry.created_at > period_start)

        entries = query.order_by(CashEntry.created_at.asc()).all()
        pending_entries = pending_withdrawals or []
        withdrawals = [entry for entry in entries if entry.entry_type == CashEntryType.WITHDRAWAL]
        deposits = [entry for entry in entries if entry.entry_type == CashEntryType.DEPOSIT]
        pending_withdrawals_total = sum(entry.get("amount_cents", 0) for entry in pending_entries) / 100

        return {
            "entries": entries,
            "pending_withdrawals": pending_entries,
            "withdrawals_total": (sum(entry.amount_cents for entry in withdrawals) / 100) + pending_withdrawals_total,
            "deposits_total": sum(entry.amount_cents for entry in deposits) / 100,
        }

    def _get_voucher_summary(self, period_start: datetime | None, period_end: datetime) -> dict:
        created_query = self.db.query(Voucher).filter(Voucher.created_at <= period_end)
        if period_start:
            created_query = created_query.filter(Voucher.created_at > period_start)
        created_vouchers = created_query.all()

        redeemed_transactions = self.db.query(Transaction).filter(
            Transaction.type == TransactionType.SALE,
            Transaction.voucher_applied_cents > 0,
            Transaction.created_at <= period_end,
        )
        if period_start:
            redeemed_transactions = redeemed_transactions.filter(Transaction.created_at > period_start)
        redeemed_transactions = redeemed_transactions.all()

        open_vouchers = self.db.query(Voucher).filter(Voucher.remaining_value_cents > 0).all()

        return {
            "created_count": len(created_vouchers),
            "created_total": sum(v.original_value_cents or v.value_cents for v in created_vouchers) / 100,
            "redeemed_count": len(redeemed_transactions),
            "redeemed_total": sum(t.voucher_applied_cents or 0 for t in redeemed_transactions) / 100,
            "open_count": len(open_vouchers),
            "open_total": sum(v.remaining_value_cents or 0 for v in open_vouchers) / 100,
        }

    def _get_open_member_balance_total(self) -> float:
        total_balance_cents = self.db.query(func.sum(Member.balance_cents)).scalar() or 0
        return total_balance_cents / 100

    def _format_datetime_display(self, value: str | datetime | None, fallback: str = "-") -> str:
        if not value:
            return fallback

        if isinstance(value, datetime):
            dt_value = value
        else:
            dt_value = datetime.fromisoformat(value)

        return dt_value.strftime("%d.%m.%Y %H:%M")

    def build_current_zbon_preview(
        self,
        created_by_name: str | None = None,
        skimmed_by_name: str | None = None,
        cash_counted_by_name: str | None = None,
        include_cash_count: dict | None = None,
        cash_count_total: float | None = None,
        pending_withdrawals: list[dict] | None = None,
    ) -> dict:
        period_start, period_end, last_zbon = self._get_current_period_bounds()
        transactions = self._get_transactions_for_period(period_start, period_end)
        cash_summary = self._get_cash_entry_summary(period_start, period_end, pending_withdrawals)
        voucher_summary = self._get_voucher_summary(period_start, period_end)
        open_balance_total = self._get_open_member_balance_total()

        sales = [t for t in transactions if t.type == TransactionType.SALE]
        recharges = [t for t in transactions if t.type == TransactionType.RECHARGE]
        stornos = [t for t in transactions if t.type == TransactionType.STORNO]
        first_transaction_at = transactions[0].created_at if transactions else None
        effective_period_start = period_start or first_transaction_at

        gross_sales_total = sum(self._calculate_non_prepaid_sale_gross_cents(t) for t in sales) / 100
        prepaid_voucher_sales_total = sum(self._calculate_prepaid_item_total_cents(t) for t in sales) / 100
        total_revenue = gross_sales_total + prepaid_voucher_sales_total
        cash_sales_total = sum(
            t.total_amount_cents
            for t in sales if t.payment_method == PaymentMethod.CASH
        ) / 100
        cash_sales_count = len([t for t in sales if t.payment_method == PaymentMethod.CASH])
        balance_sales_total = sum(
            (t.balance_applied_cents or 0)
            + (t.total_amount_cents if t.payment_method == PaymentMethod.BALANCE else 0)
            for t in sales
        ) / 100
        balance_sales_count = len([
            t for t in sales
            if t.payment_method == PaymentMethod.BALANCE or (t.balance_applied_cents or 0) > 0
        ])
        voucher_sales_total = sum(t.voucher_applied_cents or 0 for t in sales) / 100
        voucher_sales_count = len([t for t in sales if (t.voucher_applied_cents or 0) > 0])
        recharge_total = sum(t.total_amount_cents for t in recharges) / 100
        storno_total = sum(t.total_amount_cents for t in stornos) / 100
        opening_balance = self._get_opening_cash_balance(last_zbon)
        cash_calculated = (
            opening_balance
            + cash_sales_total
            + recharge_total
            - cash_summary["withdrawals_total"]
        )

        provided_cash_count_total = cash_count_total
        resolved_cash_count_total = None
        cash_difference = None
        if include_cash_count:
            coins = include_cash_count.get("coins", {})
            notes = include_cash_count.get("notes", {})
            resolved_cash_count_total = (
                sum(float(denom) * count for denom, count in coins.items())
                + sum(float(denom) * count for denom, count in notes.items())
            )
        elif provided_cash_count_total is not None:
            resolved_cash_count_total = float(provided_cash_count_total)
        if resolved_cash_count_total is not None:
            cash_difference = resolved_cash_count_total - cash_calculated

        receipt_numbers = [t.receipt_number for t in transactions if t.receipt_number is not None]
        transaction_rows = [
            {
                "id": t.id,
                "receipt_number": t.receipt_number,
                "created_at": t.created_at.isoformat(),
                "type": t.type.value,
                "payment_method": t.payment_method.value,
                "total_amount_cents": t.total_amount_cents,
                "gross_amount_cents": self._calculate_sale_gross_cents(t) if t.type == TransactionType.SALE else t.total_amount_cents,
                "voucher_applied_cents": t.voucher_applied_cents or 0,
                "balance_applied_cents": t.balance_applied_cents or 0,
                "voucher_type": t.voucher_type,
                "member_name": self._format_member_name(t.member),
                "items": [
                    {
                        "id": item.id,
                        "quantity": item.quantity,
                        "unit_price_cents": item.unit_price_cents,
                        "total_price_cents": item.total_price_cents,
                        "product": {
                            "id": item.product.id if item.product else None,
                            "name": item.product.name if item.product else None,
                        },
                    }
                    for item in t.items
                ],
            }
            for t in transactions
        ]

        payload = {
            "sequence_number": (last_zbon.sequence_number + 1) if last_zbon else 1,
            "generated_at": period_end.isoformat(),
            "report_type": "zbon",
            "period_start": effective_period_start.isoformat() if effective_period_start else None,
            "period_end": period_end.isoformat(),
            "business_date": period_end.date().isoformat(),
            "created_by_name": created_by_name,
            "skimmed_by_name": skimmed_by_name,
            "cash_counted_by_name": cash_counted_by_name,
            "transactions": transaction_rows,
            "summary": {
                "transaction_count": len(transactions),
                "sales_count": len(sales),
                "recharge_count": len(recharges),
                "prepaid_voucher_sales_count": sum(
                    item.quantity
                    for t in sales
                    for item in t.items
                    if self._get_prepaid_product_value_cents(item.product) is not None
                ),
                "storno_count": len(stornos),
                "cash_sales_count": cash_sales_count,
                "balance_sales_count": balance_sales_count,
                "voucher_sales_count": voucher_sales_count,
                "gross_sales_total": gross_sales_total,
                "total_revenue": total_revenue,
                "cash_sales_total": cash_sales_total,
                "balance_sales_total": balance_sales_total,
                "voucher_sales_total": voucher_sales_total,
                "recharge_total": recharge_total,
                "prepaid_voucher_sales_total": prepaid_voucher_sales_total,
                "storno_total": storno_total,
                "opening_cash_balance": opening_balance,
                "cash_withdrawals_total": cash_summary["withdrawals_total"],
                "cash_deposits_total": cash_summary["deposits_total"],
                "cash_calculated": cash_calculated,
                "cash_counted": resolved_cash_count_total,
                "cash_difference": cash_difference,
                "receipt_number_min": min(receipt_numbers) if receipt_numbers else None,
                "receipt_number_max": max(receipt_numbers) if receipt_numbers else None,
                "voucher_created_count": voucher_summary["created_count"],
                "voucher_created_total": voucher_summary["created_total"],
                "voucher_redeemed_count": voucher_summary["redeemed_count"],
                "voucher_redeemed_total": voucher_summary["redeemed_total"],
                "voucher_open_count": voucher_summary["open_count"],
                "voucher_open_total": voucher_summary["open_total"],
                "balance_open_total": open_balance_total,
                "withdrawals": [
                    {
                        "created_at": entry.created_at.isoformat(),
                        "amount": entry.amount_cents / 100,
                        "reason": entry.reason,
                        "performed_by": entry.user.username if entry.user else None,
                    }
                    for entry in cash_summary["entries"]
                    if entry.entry_type == CashEntryType.WITHDRAWAL
                ] + [
                    {
                        "created_at": period_end.isoformat(),
                        "amount": entry.get("amount_cents", 0) / 100,
                        "reason": entry.get("reason"),
                        "performed_by": None,
                    }
                    for entry in cash_summary.get("pending_withdrawals", [])
                ],
            },
            "cash_count": include_cash_count,
        }

        payload["report_content"] = self._render_current_zbon_html(payload)
        return payload

    def create_zbon(
        self,
        created_by_name: str,
        skimmed_by_name: str | None = None,
        cash_counted_by_name: str | None = None,
        include_cash_count: dict | None = None,
        cash_count_total: float | None = None,
        pending_withdrawals: list[dict] | None = None,
    ) -> dict:
        payload = self.build_current_zbon_preview(
            created_by_name=created_by_name,
            skimmed_by_name=skimmed_by_name,
            cash_counted_by_name=cash_counted_by_name,
            include_cash_count=include_cash_count,
            cash_count_total=cash_count_total,
            pending_withdrawals=pending_withdrawals,
        )

        summary = payload["summary"]
        report_data = json.dumps(payload, ensure_ascii=False)
        report_content = self._render_current_zbon_html(payload)
        history = ZBonHistory(
            sequence_number=payload["sequence_number"],
            business_date=datetime.fromisoformat(payload["business_date"]),
            generated_at=datetime.fromisoformat(payload["generated_at"]),
            period_start=datetime.fromisoformat(payload["period_start"]) if payload["period_start"] else datetime.fromisoformat(payload["generated_at"]),
            period_end=datetime.fromisoformat(payload["period_end"]),
            report_type=payload["report_type"],
            gross_revenue_cash=summary["cash_sales_total"],
            gross_revenue_balance=summary["balance_sales_total"],
            gross_revenue_voucher=summary["voucher_sales_total"],
            total_revenue=summary["total_revenue"],
            recharge_total=summary["recharge_total"],
            storno_total=summary["storno_total"],
            voucher_created_total=summary["voucher_created_total"],
            voucher_redeemed_total=summary["voucher_redeemed_total"],
            voucher_open_total=summary["voucher_open_total"],
            cash_opening_balance=summary["opening_cash_balance"],
            cash_calculated=summary["cash_calculated"],
            cash_counted=summary["cash_counted"],
            cash_difference=summary["cash_difference"],
            cash_withdrawals=summary["cash_withdrawals_total"],
            cash_deposits=summary["cash_deposits_total"],
            transaction_count_sales=summary["sales_count"],
            transaction_count_recharge=summary["recharge_count"],
            transaction_count_storno=summary["storno_count"],
            transaction_count_total=summary["transaction_count"],
            voucher_created_count=summary["voucher_created_count"],
            voucher_redeemed_count=summary["voucher_redeemed_count"],
            voucher_open_count=summary["voucher_open_count"],
            receipt_number_min=summary["receipt_number_min"],
            receipt_number_max=summary["receipt_number_max"],
            created_by_name=created_by_name,
            skimmed_by_name=skimmed_by_name,
            cash_counted_by_name=cash_counted_by_name,
            cash_count_details=json.dumps(include_cash_count, ensure_ascii=False) if include_cash_count else None,
            report_data=report_data,
            report_content=report_content,
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        payload["history_id"] = history.id
        payload["report_content"] = report_content
        return payload

    def _render_current_zbon_html(self, payload: dict) -> str:
        summary = payload["summary"]
        cash_count = payload.get("cash_count") or {}
        coins = cash_count.get("coins") or {}
        notes = cash_count.get("notes") or {}
        withdrawals = summary.get("withdrawals") or []

        template = Template(ZBON_HTML_TEMPLATE)
        return template.render(
            seq_number=payload["sequence_number"],
            business_date=datetime.fromisoformat(payload["business_date"]).strftime("%d.%m.%Y"),
            created_at=self._format_datetime_display(payload["generated_at"]),
            period_start=self._format_datetime_display(payload["period_start"], "Beginn"),
            period_end=self._format_datetime_display(payload["period_end"]),
            receipt_min=summary.get("receipt_number_min") or "-",
            receipt_max=summary.get("receipt_number_max") or "-",
            transaction_count_total=summary.get("transaction_count", 0),
            created_by_name=payload.get("created_by_name") or "-",
            cash_counted_by_name=payload.get("cash_counted_by_name") or "-",
            cash_sales_count=summary.get("cash_sales_count", 0),
            cash_sales_net=f"{summary.get('cash_sales_total', 0):.2f}",
            cash_sales_tax="0.00",
            cash_sales_gross=f"{summary.get('cash_sales_total', 0):.2f}",
            balance_sales_count=summary.get("balance_sales_count", 0),
            balance_sales_net=f"{summary.get('balance_sales_total', 0):.2f}",
            balance_sales_tax="0.00",
            balance_sales_gross=f"{summary.get('balance_sales_total', 0):.2f}",
            voucher_sales_count=summary.get("voucher_sales_count", 0),
            voucher_sales_total=f"{summary.get('voucher_sales_total', 0):.2f}",
            recharge_count=summary.get("recharge_count", 0),
            recharge_total=f"{summary.get('recharge_total', 0):.2f}",
            prepaid_voucher_sales_count=summary.get("prepaid_voucher_sales_count", 0),
            prepaid_voucher_sales_total=f"{summary.get('prepaid_voucher_sales_total', 0):.2f}",
            balance_open_total=f"{summary.get('balance_open_total', 0):.2f}",
            total_items_count=summary.get("sales_count", 0),
            total_net=f"{summary.get('total_revenue', 0):.2f}",
            total_tax="0.00",
            total_gross=f"{summary.get('total_revenue', 0):.2f}",
            total_revenue=f"{summary.get('total_revenue', 0):.2f}",
            voucher_created_count=summary.get("voucher_created_count", 0),
            voucher_created_total=f"{summary.get('voucher_created_total', 0):.2f}",
            voucher_redeemed_count=summary.get("voucher_redeemed_count", 0),
            voucher_redeemed_total=f"{summary.get('voucher_redeemed_total', 0):.2f}",
            voucher_open_count=summary.get("voucher_open_count", 0),
            voucher_open_total=f"{summary.get('voucher_open_total', 0):.2f}",
            storno_count=summary.get("storno_count", 0),
            storno_total=f"{summary.get('storno_total', 0):.2f}",
            cash_opening_balance=f"{summary.get('opening_cash_balance', 0):.2f}",
            cash_revenue=f"{summary.get('cash_sales_total', 0):.2f}",
            cash_withdrawals_total=f"{summary.get('cash_withdrawals_total', 0):.2f}",
            cash_calculated=f"{summary.get('cash_calculated', 0):.2f}",
            cash_counted=f"{summary.get('cash_counted', 0):.2f}" if summary.get("cash_counted") is not None else "-",
            cash_difference=f"{summary.get('cash_difference', 0):.2f}" if summary.get("cash_difference") is not None else None,
            withdrawals=withdrawals,
            cash_count=bool(cash_count),
            coins={
                denomination: {
                    "count": count,
                    "subtotal": float(denomination) * count,
                }
                for denomination, count in coins.items()
            },
            notes={
                denomination: {
                    "count": count,
                    "subtotal": float(denomination) * count,
                }
                for denomination, count in notes.items()
            },
            coins_total=f"{sum(float(denomination) * count for denomination, count in coins.items()):.2f}",
            notes_total=f"{sum(float(denomination) * count for denomination, count in notes.items()):.2f}",
            categories_breakdown={},
            customer_groups={},
            customers={},
            stornos=[],
            report_type_label="Z-BON",
        )
    
    def generate_zbon(
        self,
        target_date: date = None,
        include_cash_count: dict = None,
        report_type: str = "full-zbon"  # "full-zbon", "short-zbon", "daily-report"
    ) -> dict:
        """
        Generate comprehensive Z-Bon or daily report
        
        Args:
            target_date: Date to generate report for (default: today)
            include_cash_count: Dict with cash count {'coins': {...}, 'notes': {...}} (optional)
            report_type: Type of report
        
        Returns:
            Dict with report data and formatted text
        """
        if not target_date:
            target_date = date.today()
        
        # Get all transactions for the day
        transactions = self.db.query(Transaction).filter(
            func.date(Transaction.created_at) == target_date
        ).all()
        
        # Calculate comprehensive statistics
        stats = self._calculate_stats(transactions)
        meta = self._collect_meta(target_date, transactions)
        
        # Additional aggregations
        product_breakdown = self._aggregate_by_product(transactions)
        category_breakdown = self._aggregate_by_category(transactions)
        customer_breakdown = self._aggregate_by_customer(transactions)
        customer_group_breakdown = self._aggregate_by_customer_group(transactions)
        tax_breakdown = self._aggregate_by_tax_rate(transactions)
        storno_details = self._get_storno_details(transactions)
        
        # Generate report content
        if report_type == "daily-report":
            content = self._generate_daily_report(
                target_date, stats, meta, include_cash_count, transactions,
                product_breakdown, category_breakdown
            )
        else:
            content = self._generate_full_zbon(
                target_date, stats, meta, include_cash_count, transactions,
                product_breakdown, category_breakdown, customer_breakdown,
                customer_group_breakdown, tax_breakdown, storno_details
            )
        
        return {
            "content": content,
            "date": target_date.isoformat(),
            "type": report_type,
            "stats": stats,
            "meta": meta,
            "has_cash_count": include_cash_count is not None,
            "breakdowns": {
                "products": product_breakdown,
                "categories": category_breakdown,
                "customers": customer_breakdown,
                "customer_groups": customer_group_breakdown,
                "tax_rates": tax_breakdown,
                "stornos": storno_details,
            }
        }
    
    def _calculate_stats(self, transactions: list) -> dict:
        """Calculate statistics from transactions"""
        cash_sales = [t for t in transactions if t.payment_method == PaymentMethod.CASH and t.type == TransactionType.SALE]
        balance_sales = [t for t in transactions if t.payment_method == PaymentMethod.BALANCE and t.type == TransactionType.SALE]
        recharges = [t for t in transactions if t.type == TransactionType.RECHARGE]
        stornos = [t for t in transactions if t.type == TransactionType.STORNO]
        gift_voucher_sales = [
            t for t in transactions
            if t.type == TransactionType.SALE and t.voucher_type == "GIFT" and (t.voucher_applied_cents or 0) > 0
        ]
        prepaid_voucher_sales = [
            t for t in transactions
            if t.type == TransactionType.SALE and t.voucher_type == "PREPAID" and (t.voucher_applied_cents or 0) > 0
        ]
        legacy_gift_redemptions = [
            t for t in transactions
            if t.type == TransactionType.VOUCHER_REDEMPTION and t.payment_method == PaymentMethod.VOUCHER_GIFT
        ]
         
        cash_total = sum(t.total_amount_cents for t in cash_sales) / 100
        balance_total = sum(t.total_amount_cents for t in balance_sales) / 100
        recharge_total = sum(t.total_amount_cents for t in recharges) / 100
        storno_total = sum(t.total_amount_cents for t in stornos) / 100
        gift_voucher_total = (
            sum(t.voucher_applied_cents or 0 for t in gift_voucher_sales)
            + abs(sum(t.total_amount_cents for t in legacy_gift_redemptions))
        ) / 100
        prepaid_voucher_total = sum(t.voucher_applied_cents or 0 for t in prepaid_voucher_sales) / 100
         
        return {
            "cash_sales_count": len(cash_sales),
            "cash_sales_total": cash_total,
            "balance_sales_count": len(balance_sales),
            "balance_sales_total": balance_total,
            "recharge_count": len(recharges),
            "recharge_total": recharge_total,
            "storno_count": len(stornos),
            "storno_total": storno_total,
            "gift_voucher_count": len(gift_voucher_sales) + len(legacy_gift_redemptions),
            "gift_voucher_total": gift_voucher_total,
            "prepaid_voucher_count": len(prepaid_voucher_sales),
            "prepaid_voucher_total": prepaid_voucher_total,
            "voucher_total": gift_voucher_total + prepaid_voucher_total,
            "total_transactions": len(transactions),
            "gross_revenue_cash": cash_total,
            "gross_revenue_balance": balance_total,
            "net_revenue": (cash_total + balance_total) - storno_total,
            "total_member_recharge": recharge_total,
        }

    def _collect_meta(self, target_date: date, transactions: list) -> dict:
        """Collect additional metadata for report transparency and audit."""
        sorted_transactions = sorted(transactions, key=lambda t: t.created_at) if transactions else []
        first_tx = sorted_transactions[0] if sorted_transactions else None
        last_tx = sorted_transactions[-1] if sorted_transactions else None

        receipt_numbers = [t.receipt_number for t in sorted_transactions if t.receipt_number is not None]
        
        # Get last Z-Bon
        last_zbon = self.db.query(ZBonHistory).filter(
            ZBonHistory.business_date < target_date
        ).order_by(desc(ZBonHistory.sequence_number)).first()

        return {
            "business_date": target_date.strftime("%d.%m.%Y"),
            "report_generated_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "report_id": f"ZB-{target_date.strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}",
            "first_tx_time": first_tx.created_at.strftime("%H:%M:%S") if first_tx else "-",
            "last_tx_time": last_tx.created_at.strftime("%H:%M:%S") if last_tx else "-",
            "receipt_min": min(receipt_numbers) if receipt_numbers else "-",
            "receipt_max": max(receipt_numbers) if receipt_numbers else "-",
            "last_zbon_number": last_zbon.sequence_number if last_zbon else None,
            "last_zbon_datetime": last_zbon.generated_at.strftime("%d.%m.%Y %H:%M:%S") if last_zbon else "-",
            "has_tse_signature": False,
        }

    def _aggregate_by_product(self, transactions: list) -> dict:
        """Aggregate sales by product"""
        aggregation = defaultdict(lambda: {"count": 0, "net_total": 0, "tax_total": 0, "gross_total": 0})
        
        for trans in transactions:
            if trans.type != TransactionType.SALE:
                continue
            
            for item in trans.items:
                product = item.product
                unit_price = item.unit_price_cents / 100
                quantity = item.quantity
                tax_rate = product.tax_rate / 100
                
                net = unit_price / (1 + tax_rate) if tax_rate > 0 else unit_price
                tax = unit_price - net
                gross = unit_price
                
                aggregation[product.name]["count"] += quantity
                aggregation[product.name]["net_total"] += net * quantity
                aggregation[product.name]["tax_total"] += tax * quantity
                aggregation[product.name]["gross_total"] += gross * quantity
                aggregation[product.name]["unit_price"] = unit_price
                aggregation[product.name]["tax_rate"] = product.tax_rate
        
        return dict(aggregation)

    def _aggregate_by_category(self, transactions: list) -> dict:
        """Aggregate sales by category"""
        aggregation = defaultdict(lambda: {"count": 0, "net_total": 0, "tax_total": 0, "gross_total": 0})
        
        for trans in transactions:
            if trans.type != TransactionType.SALE:
                continue
            
            for item in trans.items:
                product = item.product
                quantity = item.quantity
                unit_price = item.unit_price_cents / 100
                tax_rate = product.tax_rate / 100
                
                net = unit_price / (1 + tax_rate) if tax_rate > 0 else unit_price
                tax = unit_price - net
                gross = unit_price
                
                # Get primary category
                if product.categories:
                    category_name = product.categories[0].name
                else:
                    category_name = "Uncategorized"
                
                aggregation[category_name]["count"] += quantity
                aggregation[category_name]["net_total"] += net * quantity
                aggregation[category_name]["tax_total"] += tax * quantity
                aggregation[category_name]["gross_total"] += gross * quantity
        
        return dict(aggregation)

    def _aggregate_by_customer(self, transactions: list) -> dict:
        """Aggregate sales by customer (member or guest)"""
        aggregation = defaultdict(lambda: {"count": 0, "net_total": 0, "tax_total": 0, "gross_total": 0})
        
        for trans in transactions:
            if trans.type != TransactionType.SALE:
                continue
            
            customer_name = "Gast"  # Default for guests
            if trans.member:
                customer_name = trans.member.name
            
            for item in trans.items:
                quantity = item.quantity
                unit_price = item.unit_price_cents / 100
                tax_rate = item.product.tax_rate / 100
                
                net = unit_price / (1 + tax_rate) if tax_rate > 0 else unit_price
                tax = unit_price - net
                gross = unit_price
                
                aggregation[customer_name]["count"] += quantity
                aggregation[customer_name]["net_total"] += net * quantity
                aggregation[customer_name]["tax_total"] += tax * quantity
                aggregation[customer_name]["gross_total"] += gross * quantity
        
        return dict(aggregation)

    def _aggregate_by_customer_group(self, transactions: list) -> dict:
        """Aggregate sales by customer group (Guest vs Member)"""
        aggregation = {"Gast": {"count": 0, "net_total": 0, "tax_total": 0, "gross_total": 0},
                      "Mitglied": {"count": 0, "net_total": 0, "tax_total": 0, "gross_total": 0}}
        
        for trans in transactions:
            if trans.type != TransactionType.SALE:
                continue
            
            group = "Mitglied" if trans.member else "Gast"
            
            for item in trans.items:
                quantity = item.quantity
                unit_price = item.unit_price_cents / 100
                tax_rate = item.product.tax_rate / 100
                
                net = unit_price / (1 + tax_rate) if tax_rate > 0 else unit_price
                tax = unit_price - net
                gross = unit_price
                
                aggregation[group]["count"] += quantity
                aggregation[group]["net_total"] += net * quantity
                aggregation[group]["tax_total"] += tax * quantity
                aggregation[group]["gross_total"] += gross * quantity
        
        return aggregation

    def _aggregate_by_tax_rate(self, transactions: list) -> dict:
        """Aggregate sales by tax rate"""
        aggregation = defaultdict(lambda: {"count": 0, "net_total": 0, "tax_total": 0, "gross_total": 0})
        
        for trans in transactions:
            if trans.type != TransactionType.SALE:
                continue
            
            for item in trans.items:
                quantity = item.quantity
                unit_price = item.unit_price_cents / 100
                tax_rate = item.product.tax_rate
                
                net = unit_price / (1 + tax_rate/100) if tax_rate > 0 else unit_price
                tax = unit_price - net
                gross = unit_price
                
                tax_key = f"{tax_rate}%"
                aggregation[tax_key]["count"] += quantity
                aggregation[tax_key]["net_total"] += net * quantity
                aggregation[tax_key]["tax_total"] += tax * quantity
                aggregation[tax_key]["gross_total"] += gross * quantity
        
        return dict(aggregation)

    def _get_storno_details(self, transactions: list) -> list:
        """Get detailed storno information"""
        stornos = []
        
        for trans in transactions:
            if trans.type != TransactionType.STORNO:
                continue
            
            for item in trans.items:
                stornos.append({
                    "receipt_number": trans.receipt_number,
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price_cents / 100,
                    "total": item.total_price_cents / 100,
                    "timestamp": trans.created_at.isoformat(),
                })
        
        return stornos

    def _generate_full_zbon(
        self,
        target_date: date,
        stats: dict,
        meta: dict,
        cash_count: dict = None,
        transactions: list = None,
        product_breakdown: dict = None,
        category_breakdown: dict = None,
        customer_breakdown: dict = None,
        customer_group_breakdown: dict = None,
        tax_breakdown: dict = None,
        storno_details: list = None,
    ) -> str:
        """
        Generate comprehensive Z-Bon similar to German POS systems
        
        Format based on actual Z-Bon example
        """
        lines = []
        lines.append("KGB Zentrale")
        
        # Get sequence number for header
        last_zbon = self.db.query(ZBonHistory).filter(
            ZBonHistory.business_date < target_date
        ).order_by(desc(ZBonHistory.sequence_number)).first()
        
        next_seq = (last_zbon.sequence_number + 1) if last_zbon else 1
        lines.append(f"Endabrechnung {next_seq}")
        lines.append("(Z-Bon)")
        
        lines.append("Erstellt am:")
        lines.append(f"{meta['report_generated_at']}")
        lines.append("Kasse Kasse 1")
        
        if meta['last_zbon_number']:
            lines.append(f"Letzte Endabrechnung #{meta['last_zbon_number']}, {meta['last_zbon_datetime']}")
        
        lines.append(f"Zeitraum {meta['first_tx_time']} - {meta['last_tx_time']}")
        lines.append(f"Belege von #{meta['receipt_min']} bis #{meta['receipt_max']}")
        lines.append("-" * 60)
        
        # Artikelumsatz
        lines.append(" EUR")
        lines.append("Artikelumsatz")
        lines.append(f"{stats['cash_sales_count']} Verkäufe netto {stats['cash_sales_total']:>8.2f}")
        lines.append(f"0 Retouren netto {0:>8.2f}")
        lines.append(" _____________")
        
        net_total = stats['cash_sales_total']
        tax_total = sum(item.get('tax_total', 0) for item in product_breakdown.values()) if product_breakdown else 0
        
        lines.append(f"Nettoumsatz {net_total:>8.2f}")
        lines.append(f"Steuern {tax_total:>8.2f}")
        lines.append(" _____________")
        lines.append(f"Bruttoumsatz {stats['cash_sales_total']:>8.2f}")
        
        # Kundenguthabenumsatz
        lines.append("")
        lines.append("Kundenguthabenumsatz")
        lines.append(f"{stats['recharge_count']} Aufbuchungen netto {stats['recharge_total']:>8.2f}")
        lines.append(f"{stats['balance_sales_count']} Einlösungen netto {-stats['balance_sales_total']:>8.2f}")
        lines.append(" _____________")
        
        guthaben_netto = stats['recharge_total'] - stats['balance_sales_total']
        lines.append(f"Buchungen netto {guthaben_netto:>8.2f}")
        lines.append(f"Steuern {0:>8.2f}")
        lines.append(" _____________")
        lines.append(f"Buchungen brutto {guthaben_netto:>8.2f}")

        # Gutscheine
        lines.append("")
        lines.append("Gutscheineinlösungen")
        lines.append(
            f"{stats['gift_voucher_count']}x Geschenk-Gutschein {stats['gift_voucher_total']:>8.2f}"
        )
        lines.append(
            f"{stats['prepaid_voucher_count']}x Verzehrkarte {stats['prepaid_voucher_total']:>8.2f}"
        )
        lines.append(" _____________")
        lines.append(f"Gutscheinwert gesamt {stats['voucher_total']:>8.2f}")
        
        # Gesamtumsatz
        lines.append("")
        lines.append("Gesamtumsatz")
        lines.append(f"{stats['cash_sales_count']} Verkäufe netto {stats['cash_sales_total']:>8.2f}")
        lines.append(f"0 Retouren netto {0:>8.2f}")
        lines.append(f"{stats['recharge_count'] + stats['balance_sales_count']} Kundenguthabenumsatz netto {guthaben_netto:>8.2f}")
        lines.append(" _____________")
        
        gesamt_netto = stats['cash_sales_total'] + guthaben_netto
        lines.append(f"Nettoumsatz {gesamt_netto:>8.2f}")
        lines.append(f"Steuern {tax_total:>8.2f}")
        lines.append(" _____________")
        lines.append(f"Bruttoumsatz {gesamt_netto:>8.2f}")
        
        # Bargeldbestand
        lines.append("")
        lines.append("Bargeldbestand")
        lines.append(f"Kassenanfangsbestand {0:>8.2f}")
        lines.append(f"0 Einlagen {0:>8.2f}")
        lines.append(f"0 Entnahmen {0:>8.2f}")
        lines.append(f"Bruttoumsatz BAR {stats['cash_sales_total']:>8.2f}")
        lines.append(" _____________")
        
        calculated_balance = stats['cash_sales_total'] + stats['recharge_total']
        if cash_count:
            counted_total = self._format_cash_count(cash_count, lines, return_only_value=False)
            lines.append(f"Kassenbestand (gezählt) {counted_total:>8.2f}")
            lines.append(f"Zähldifferenz {counted_total - calculated_balance:>8.2f}")
        
        # Geldzählprotokoll
        if cash_count:
            lines.append("")
            lines.append("Geldzählprotokoll")
            self._format_cash_count(cash_count, lines)
        
        # Page break indicator
        lines.append("Seite 1 von 3 Kasse 1 Endabrechnung {} vom {}.p".format(
            next_seq, 
            datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        ))
        
        # Gesamtumsatz nach Zahlungsart
        lines.append("")
        lines.append("Gesamtumsatz nach Zahlungsart")
        lines.append(" Brutto")
        lines.append(f"BAR {stats['cash_sales_total']:>8.2f}")
        lines.append(f"{stats['balance_sales_count']}x Guthaben {stats['balance_sales_total']:>8.2f}")
        if stats['gift_voucher_count'] > 0:
            lines.append(f"{stats['gift_voucher_count']}x Gutschein (Geschenk) {stats['gift_voucher_total']:>8.2f}")
        if stats['prepaid_voucher_count'] > 0:
            lines.append(f"{stats['prepaid_voucher_count']}x Gutschein (Guthaben) {stats['prepaid_voucher_total']:>8.2f}")
        lines.append(" _____________")
        lines.append(
            f" {stats['cash_sales_total'] + stats['balance_sales_total'] + stats['voucher_total']:>8.2f}"
        )
        
        # Gesamtumsatz nach Steuersätzen
        lines.append("")
        lines.append("Gesamtumsatz nach Steuersätzen")
        lines.append(" Steuern Netto Brutto")
        for tax_pct, data in sorted(tax_breakdown.items()) if tax_breakdown else []:
            lines.append(f"{tax_pct} {data['tax_total']:>8.2f} {data['net_total']:>8.2f} {data['gross_total']:>8.2f}")
        lines.append(" _______________________________")
        lines.append(f" {tax_total:>8.2f} {net_total:>8.2f} {net_total + tax_total:>8.2f}")
        
        # Artikelumsatz nach Artikelgruppen
        lines.append("")
        lines.append("Artikelumsatz nach Artikelgruppen")
        lines.append(" Netto Brutto")
        if category_breakdown:
            for cat_name, data in sorted(category_breakdown.items()):
                lines.append(f"{cat_name} {data['net_total']:>8.2f} {data['gross_total']:>8.2f}")
        lines.append(" ______________________")
        lines.append(f" {net_total:>8.2f} {stats['cash_sales_total']:>8.2f}")
        
        # Artikelumsatz Detail
        lines.append("")
        lines.append("Artikelumsatz")
        lines.append(" Netto Brutto")
        if product_breakdown:
            for prod_name, data in sorted(product_breakdown.items()):
                lines.append(f"{data['count']} Stk {prod_name} {data['net_total']:>8.2f} {data['gross_total']:>8.2f}")
        lines.append(" ______________________")
        lines.append(f" {net_total:>8.2f} {stats['cash_sales_total']:>8.2f}")
        
        # Artikelumsatz nach Kundengruppen
        lines.append("")
        lines.append("Artikelumsatz nach Kundengruppen")
        lines.append(" Netto Brutto")
        if customer_group_breakdown:
            for group_name, data in customer_group_breakdown.items():
                lines.append(f"{group_name} {data['net_total']:>8.2f} {data['gross_total']:>8.2f}")
        lines.append(" ______________________")
        lines.append(f" {net_total:>8.2f} {stats['cash_sales_total']:>8.2f}")
        
        lines.append("")
        lines.append("Seite 2 von 3 Kasse 1 Endabrechnung {} vom {}.p".format(
            next_seq, 
            datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        ))
        
        # Artikelumsatz nach Kunden
        lines.append("")
        lines.append("Artikelumsatz nach Kunden")
        lines.append(" Netto Brutto")
        if customer_breakdown:
            for cust_name, data in sorted(customer_breakdown.items()):
                lines.append(f"{cust_name} {data['net_total']:>8.2f} {data['gross_total']:>8.2f}")
        lines.append(" ______________________")
        lines.append(f" {net_total:>8.2f} {stats['cash_sales_total']:>8.2f}")
        
        # Stornos
        if storno_details:
            lines.append("")
            lines.append("Stornos (S) und Retouren (R)")
            lines.append(" Netto Brutto")
            storno_total_net = 0
            for storno in storno_details:
                lines.append(f"S #{storno['receipt_number']} {storno['quantity']}Stk {storno['product_name']} {storno['unit_price']:>8.2f} {storno['unit_price']:>8.2f}")
                storno_total_net += storno['unit_price'] * storno['quantity']
            lines.append(" ______________________")
            lines.append(f" {storno_total_net:>8.2f} {storno_total_net:>8.2f}")
        
        # Einlage/Entnahme
        lines.append("")
        lines.append("Einlage/Entnahme")
        lines.append(" Netto Brutto")
        lines.append(f"Abschöpfung Benny u.carsten {-calculated_balance:>8.2f} {-calculated_balance:>8.2f}")
        lines.append(" ______________________")
        lines.append(f" {-calculated_balance:>8.2f} {-calculated_balance:>8.2f}")
        
        lines.append("-" * 60)
        lines.append("vielen Dank für deinen Besuch")
        lines.append("Seite 3 von 3 Kasse 1 Endabrechnung {} vom {}.pdf".format(
            next_seq, 
            datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        ))
        
        return "\n".join(lines)

    def _generate_daily_report(
        self,
        target_date: date,
        stats: dict,
        meta: dict,
        cash_count: dict = None,
        transactions: list = None,
        product_breakdown: dict = None,
        category_breakdown: dict = None,
    ) -> str:
        """Generate detailed daily protocol report"""
        lines = []
        lines.append("=" * 70)
        lines.append("KGB - KICKERKASSE - TAGESBERICHTSPROTOKOLL")
        lines.append("=" * 70)
        lines.append("")
        lines.append("Geschäftsadresse:")
        lines.append("Krökel Gemeinschaft Badenstedt – Hannover e.V.")
        lines.append("Davenstedter Str. 115")
        lines.append("30453 Hannover")
        lines.append("Vereinsregister: VR 203296")
        lines.append("Registergericht: Amtsgericht Hannover")
        lines.append("")
        lines.append("Kontakt: info@kgbhannover.de")
        lines.append("")
        lines.append("-" * 70)
        lines.append("")
        lines.append(f"Datum:                      {meta['business_date']}")
        lines.append(f"Berichtszeit:               {meta['report_generated_at']}")
        lines.append(f"Report-ID:                  {meta['report_id']}")
        lines.append(f"Belegnummern:               {meta['receipt_min']} - {meta['receipt_max']}")
        lines.append("")
        lines.append("-" * 70)
        lines.append("TAGESSTATISTIK")
        lines.append("-" * 70)
        lines.append("")
        
        lines.append(f"Gesamttransaktionen:        {stats['total_transactions']:>6}")
        lines.append("")
        
        lines.append("Nach Transaktionstyp:")
        lines.append(f"  Verkäufe (Bargeld):       {stats['cash_sales_count']:>6}")
        lines.append(f"  Verkäufe (Guthaben):      {stats['balance_sales_count']:>6}")
        lines.append(f"  Guthabenaufladungen:      {stats['recharge_count']:>6}")
        lines.append(f"  Stornierungen:            {stats['storno_count']:>6}")
        lines.append("")
        
        lines.append("-" * 70)
        lines.append("UMSATZAUSZUG")
        lines.append("-" * 70)
        lines.append("")
        
        lines.append(f"Bruttoumsatz (Bargeld):       {stats['cash_sales_total']:>10.2f} EUR")
        lines.append(f"Bruttoumsatz (Guthaben):      {stats['balance_sales_total']:>10.2f} EUR")
        lines.append(f"Guthabenaufladungen:          {stats['recharge_total']:>10.2f} EUR")
        
        if stats['storno_total'] > 0:
            lines.append(f"Stornierungen:                {-stats['storno_total']:>10.2f} EUR")
        
        lines.append("")
        net_value = (stats['cash_sales_total'] + stats['recharge_total'])
        lines.append(f"KASSENEINNAHME (BAR):         {net_value:>10.2f} EUR")
        lines.append("-" * 70)
        lines.append("")
        
        if cash_count:
            lines.append("KASSENZÄHLUNG & VERGLEICH")
            lines.append("-" * 70)
            lines.append("")
            
            counted_total = self._format_cash_count(cash_count, lines)
            lines.append("")
            lines.append(f"Gezählter Bestand:            {counted_total:>10.2f} EUR")
            lines.append(f"Sollbestand (Umsätze):        {net_value:>10.2f} EUR")
            diff = counted_total - net_value
            lines.append(f"Differenz:                    {diff:>10.2f} EUR")
            
            if abs(diff) < 0.01:
                lines.append("")
                lines.append("✓ Kasse stimmt überein")
            else:
                lines.append("")
                lines.append("⚠ Abweichung erkannt - bitte überprüfen")
            
            lines.append("")
        
        # Category breakdown
        if category_breakdown:
            lines.append("-" * 70)
            lines.append("UMSATZ NACH KATEGORIEN")
            lines.append("-" * 70)
            lines.append("")
            
            for cat_name, data in sorted(category_breakdown.items()):
                lines.append(f"{cat_name}: {data['gross_total']:>10.2f} EUR ({data['count']} Stk)")
        
        # Transaction details
        if transactions:
            lines.append("")
            lines.append("-" * 70)
            lines.append("TRANSAKTIONSDETAILS (erste 50)")
            lines.append("-" * 70)
            lines.append("")
            
            for trans in sorted(transactions, key=lambda t: t.created_at)[:50]:
                time = trans.created_at.strftime("%H:%M:%S")
                type_str = "SALE" if trans.type == TransactionType.SALE else "RECHARGE" if trans.type == TransactionType.RECHARGE else "STORNO"
                payment = "BAR" if trans.payment_method == PaymentMethod.CASH else "GUTHABEN"
                
                lines.append(f"{time} | Belegnr. {trans.receipt_number:>6} | {type_str:>8} | {payment:>8} | {trans.total_amount_cents/100:>8.2f} EUR")
            
            if len(transactions) > 50:
                lines.append(f"... und {len(transactions) - 50} weitere Transaktionen")
            
            lines.append("")

        lines.append("TSE-Hinweis: Dieser Bericht enthaelt keine TSE-Signaturdaten")
        lines.append("(Seriennummer, Signaturzaehler, Pruefwert) und dient als")
        lines.append("interner Tagesabschluss-/Pruefbericht.")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def _format_cash_count(self, cash_count: dict, lines: list, return_only_value: bool = True) -> float:
        """Format cash count details and return total"""
        total = 0.0
        
        if 'coins' in cash_count:
            if not return_only_value:
                lines.append("Münzen:")
            for denomination, count in sorted(cash_count['coins'].items(), key=lambda x: float(x[0]), reverse=True):
                value = float(denomination) * count
                total += value
                if not return_only_value:
                    lines.append(f"  {denomination:>6} EUR × {count:>3} St. = {value:>8.2f} EUR")
        
        if 'notes' in cash_count:
            if not return_only_value:
                lines.append("")
                lines.append("Scheine:")
            for denomination, count in sorted(cash_count['notes'].items(), key=lambda x: float(x[0]), reverse=True):
                value = float(denomination) * count
                total += value
                if not return_only_value:
                    lines.append(f"  {denomination:>6} EUR × {count:>3} St. = {value:>8.2f} EUR")
        
        return total
