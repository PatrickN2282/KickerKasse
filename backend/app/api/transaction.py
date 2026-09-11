from app.core.booking_route import BookingRoute
from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import HTMLResponse, FileResponse, Response
from sqlalchemy.orm import Session
from datetime import date, datetime
from sqlalchemy import func, desc
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional
import logging

from app.core import get_db
from app.core.auth import require_authenticated_user, require_password_confirmation, require_roles
from app.schemas import (
    TransactionCreate,
    TransactionResponse,
    TransactionStornoCreate,
    ZBonResponse,
    ZBonHistoryResponse,
    ZBonHistoryListResponse,
)
from app.services import (
    DeckelService,
    EmailService,
    MaterialAccountService,
    SchedulerService,
    TransactionService,
    VoucherService,
    ZBonService,
)
from app.services.app_settings_service import AppSettingsService
from app.services.zbon_html_exporter import ZBonHTMLExporter
from app.services.transaction_export_service import TransactionExportService
from app.services.sale_pricing_service import resolve_sale_unit_price_cents
from app.repositories import MemberRepository, ProductRepository, UserRepository
from app.models import GuestListEntry, Member, Voucher, CashEntryType, PaymentMethod, Transaction, ZBonHistory, UserRole
from app.utils.drawer import SMALL_PARTS_DRAWER, drawer_targets_for_sale

logger = logging.getLogger(__name__)
router = APIRouter(route_class=BookingRoute, prefix="/api/transactions", tags=["Transactions"])


# Request models
class CashCountRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coins: Optional[dict] = None
    notes: Optional[dict] = None

    @model_validator(mode="after")
    def validate_count(self):
        from app.utils.cash_count import cash_count_cents
        cash_count_cents(self.model_dump())
        return self


class ZBonGenerateRequest(BaseModel):
    date: Optional[str] = None  # YYYY-MM-DD, defaults to today
    cash_count: Optional[CashCountRequest] = None
    report_type: str = "full-zbon"  # "full-zbon", "short-zbon", or "daily-report"


class ZBonEmailRequest(BaseModel):
    date: Optional[str] = None  # YYYY-MM-DD, defaults to today
    recipient: Optional[str] = None  # defaults to persisted recipient setting
    report_type: str = "full-zbon"  # "full-zbon", "short-zbon", or "daily-report"
    include_cash_count: bool = False


class ZBonPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    created_by_id: Optional[str] = Field(default=None, pattern=r"^(user|member)-[1-9][0-9]*$")
    cash_counted_by_member_id: Optional[int] = Field(default=None, gt=0)
    cash_count: Optional[CashCountRequest] = None
    cash_count_total: Optional[float] = None
    pending_withdrawals: list["PendingWithdrawalRequest"] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_total(self):
        from app.utils.cash_count import cash_count_cents
        cash_count_cents(self.cash_count.model_dump() if self.cash_count else None, self.cash_count_total)
        return self


class ZBonCreateRequest(ZBonPreviewRequest):
    created_by_id: str = Field(pattern=r"^(user|member)-[1-9][0-9]*$")
    cash_counted_by_member_id: int = Field(gt=0)
    cash_count_total: float = Field(ge=0, allow_inf_nan=False)
    difference_reason: Optional[str] = Field(default=None, max_length=1000)
    auth_password: str


def resolve_zbon_actors(db, data):
    from app.services.user_service import UserService
    creator = None
    if data.created_by_id:
        creator = next((u["username"] for u in UserService(db).get_finance_options()
                        if u["id"] == data.created_by_id), None)
        if not creator:
            raise HTTPException(400, "Ersteller nicht gefunden oder ohne Finanzberechtigung.")
    verifier = None
    if data.cash_counted_by_member_id:
        member = db.get(Member, data.cash_counted_by_member_id)
        if member is None or member.archived_at is not None:
            raise HTTPException(400, "Prüfendes Mitglied nicht gefunden oder archiviert.")
        verifier = member.name
    return creator, verifier


class ZBonPreviewEmailRequest(BaseModel):
    html_zbon: str
    recipient: Optional[str] = None
    report_date: Optional[str] = None  # YYYY-MM-DD
    seq_number: Optional[int] = None


class PendingWithdrawalRequest(BaseModel):
    amount_cents: int = Field(..., gt=0)
    reason: str = Field(..., min_length=1)


def _require_finance_access(request: Request, db: Session):
    return require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)


def _get_combined_voucher_type(vouchers: list[tuple]) -> str | None:
    if not vouchers:
        return None

    voucher_types = [voucher.voucher_type.value for voucher, _ in vouchers]
    first_type = voucher_types[0]
    return first_type if all(voucher_type == first_type for voucher_type in voucher_types) else "MIXED"


@router.get("/operations/{operation_key}")
async def get_booking_operation(operation_key: str, request: Request, db: Session = Depends(get_db)):
    from app.models import BookingOperation
    import json
    user = require_authenticated_user(request, db)
    operation = db.query(BookingOperation).filter_by(operation_key=operation_key, user_id=user.id).first()
    if operation is None:
        raise HTTPException(404, "Vorgang noch nicht bestätigt. Erneut mit derselben Kennung versuchen.")
    return {"status": "completed", "response": json.loads(operation.response_json),
            "response_status": operation.response_status}


@router.get("/next-receipt-number")
@router.get("/next-receipt-number/")
async def get_next_receipt_number(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get the next receipt number"""
    cashier = require_authenticated_user(request, db)
    user_id = cashier.id
    
    service = TransactionService(db)
    next_number = service.get_next_receipt_number()
    return {"receipt_number": next_number}


@router.post("/sale", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
@router.post("/sale/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    transaction_data: TransactionCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a sale transaction"""
    current_user = require_authenticated_user(request, db)
    user_id = current_user.id
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    print(f"[API] Creating sale transaction for user {user_id}: payment_method={transaction_data.payment_method}, member_id={transaction_data.member_id}, items={len(transaction_data.items)}")
    
    # The authenticated server-side user is authoritative, never request.user_id.
    performed_by_username = current_user.username

    try:
        # Validate items exist and have stock
        product_repo = ProductRepository(db)
        member = None
        if transaction_data.member_id:
            member = MemberRepository(db).get_by_id_for_update(transaction_data.member_id)
            if not member:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        requested_quantities = {}
        for item in transaction_data.items:
            requested_quantities[item.product_id] = requested_quantities.get(item.product_id, 0) + item.quantity
        product_names: dict[int, str] = {}
        products_for_drawer = []
        for product_id in sorted({item.product_id for item in transaction_data.items}):
            product_repo.get_by_id_for_update(product_id)
        reserved_quantities = DeckelService(db).get_reserved_quantities()
        sold_prepaid_quantities_by_value: dict[int, int] = {}
        voucher_service = VoucherService(db)
        for item in transaction_data.items:
            product = product_repo.get_by_id_for_update(item.product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product {item.product_id} not found",
                )
            if not product.is_active:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product {product.name} is inactive")
            try:
                item.unit_price_cents = resolve_sale_unit_price_cents(
                    product,
                    item.unit_price_cents,
                    is_internal_material=item.is_internal_material,
                    member=member,
                )
            except ValueError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
            product_names[product.id] = product.name
            products_for_drawer.append(product)
            if not product.is_unlimited_stock:
                available_quantity = max(product.stock_quantity - reserved_quantities.get(product.id, 0), 0)
                if available_quantity < requested_quantities[item.product_id]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unzureichender Bestand für Produkt {product.name}",
                    )
            if product.requires_guest_list:
                if item.is_internal_material or len(item.guests) != item.quantity:
                    raise HTTPException(status_code=400, detail=f"Für {product.name} muss je Einheit genau ein Gast erfasst werden; interne Gastbuchungen sind nicht möglich.")
            elif item.guests:
                raise HTTPException(status_code=400, detail="Gäste dürfen nur einem Gastartikel zugeordnet werden")
            for guest in item.guests:
                if guest.member_id is not None and MemberRepository(db).get_by_id(guest.member_id) is None:
                    raise HTTPException(status_code=400, detail="Das zugeordnete Mitglied existiert nicht")
            prepaid_value_cents = voucher_service.get_prepaid_value_from_product(product)
            if prepaid_value_cents is not None and product.requires_guest_list:
                raise HTTPException(status_code=400, detail="Verzehrkarten und Gastartikel dürfen nicht kombiniert werden")
            if prepaid_value_cents is not None:
                sold_prepaid_quantities_by_value[prepaid_value_cents] = (
                    sold_prepaid_quantities_by_value.get(prepaid_value_cents, 0) + item.quantity
                )

        if sold_prepaid_quantities_by_value:
            try:
                voucher_service.ensure_prepaid_stock(sold_prepaid_quantities_by_value)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc
        
        total_amount = sum(item.unit_price_cents * item.quantity for item in transaction_data.items)
        vouchers = []
        voucher_applied_cents = 0
        voucher_candidates = []
        for redemption in transaction_data.voucher_redemptions:
            candidate = voucher_service.repository.get_by_number(redemption.voucher_number)
            if not candidate:
                raise HTTPException(status_code=400, detail="Gutschein nicht gefunden")
            voucher_candidates.append(candidate.id)
        if len(set(voucher_candidates)) != len(voucher_candidates):
            raise HTTPException(status_code=400, detail="Derselbe Gutschein darf nur einmal im Bon vorkommen")
        for voucher_id in sorted(voucher_candidates):
            db.query(Voucher).filter_by(id=voucher_id).populate_existing().with_for_update().first()
        for voucher_redemption in transaction_data.voucher_redemptions:
            try:
                voucher = voucher_service.get_redeemable_voucher(voucher_redemption.voucher_number)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                )

            remaining_cart_value = max(total_amount - voucher_applied_cents, 0)
            available_voucher_cents = (
                voucher.remaining_value_cents
                if voucher.remaining_value_cents is not None
                else voucher.value_cents
            )
            applied_amount = min(available_voucher_cents, remaining_cart_value)

            if applied_amount <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Voucher kann bei leerem Warenkorb nicht eingelöst werden",
                )

            vouchers.append((voucher, applied_amount))
            voucher_applied_cents += applied_amount

        payable_after_vouchers_cents = max(total_amount - voucher_applied_cents, 0)
        balance_applied_cents = 0
        member_balance_changed = bool(
            member is not None
            and transaction_data.expected_member_balance_cents is not None
            and transaction_data.expected_member_balance_cents != member.balance_cents
        )

        # Check member balance if paying with balance
        if transaction_data.payment_method == "BALANCE" or transaction_data.balance_discount_cents > 0:
            if not transaction_data.member_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Member ID required for balance payment",
                )
            
            requested_balance_cents = (
                payable_after_vouchers_cents
                if transaction_data.payment_method == "BALANCE"
                else transaction_data.balance_discount_cents
            )
            balance_applied_cents = min(requested_balance_cents, member.balance_cents, payable_after_vouchers_cents)

            if (
                transaction_data.payment_method == "BALANCE"
                and balance_applied_cents < payable_after_vouchers_cents
                and not member_balance_changed
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient member balance",
                )

        payable_amount_cents = max(payable_after_vouchers_cents - balance_applied_cents, 0)
        if (
            transaction_data.payment_method == "BALANCE"
            and payable_amount_cents != 0
            and not member_balance_changed
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Balance payment must cover the full remaining amount",
            )

        amount_changed = (
            transaction_data.expected_total_amount_cents is not None
            and transaction_data.expected_total_amount_cents != payable_amount_cents
        )
        balance_changed = (
            member_balance_changed
            and (transaction_data.payment_method == "BALANCE" or transaction_data.balance_discount_cents > 0)
        )
        if amount_changed or balance_changed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "SALE_CONFIRMATION_CHANGED",
                    "message": "Preis oder Guthaben hat sich geändert. Bitte die aktualisierten Beträge erneut bestätigen.",
                    "expected_total_amount_cents": transaction_data.expected_total_amount_cents,
                    "actual_total_amount_cents": payable_amount_cents,
                    "actual_member_balance_cents": member.balance_cents if member is not None else None,
                    "items": [
                        {
                            "product_id": item.product_id,
                            "unit_price_cents": item.unit_price_cents,
                        }
                        for item in transaction_data.items
                    ],
                },
            )

        try:
            change_given_cents = TransactionService.validate_cash_payment(
                transaction_data.payment_method,
                payable_amount_cents,
                transaction_data.tip_cents,
                transaction_data.cash_received_cents,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        service = TransactionService(db)
        
        # Collect member name snapshot
        member_name_snapshot = None
        if transaction_data.member_id:
            member_repo_for_snapshot = MemberRepository(db)
            m = member_repo_for_snapshot.get_by_id(transaction_data.member_id)
            if m:
                member_name_snapshot = m.name

        # Create transaction with snapshot fields
        items_data = [
            {**item.dict(), "product_name": product_names.get(item.product_id)}
            for item in transaction_data.items
        ]
        transaction = service.create_sale_transaction(
            user_id=user_id,
            total_amount_cents=payable_amount_cents,
            payment_method=transaction_data.payment_method,
            member_id=transaction_data.member_id,
            member_name=member_name_snapshot,
            performed_by_username=performed_by_username,
            items=items_data,
            voucher_code=", ".join(voucher.voucher_code for voucher, _ in vouchers) if vouchers else None,
            voucher_type=_get_combined_voucher_type(vouchers),
            voucher_applied_cents=voucher_applied_cents,
            balance_applied_cents=balance_applied_cents,
            tip_cents=transaction_data.tip_cents,
            cash_received_cents=transaction_data.cash_received_cents,
            change_given_cents=change_given_cents,
            commit=False,
        )
        
        # Process payment
        member_repo = MemberRepository(db)
        service.process_sale_payment(transaction, member_repo, commit=False)
        
        # Deduct once per product, including multiple guest/variable-price lines.
        for product_id, quantity in requested_quantities.items():
            if not product_repo.deduct_stock(product_id, quantity, commit=False):
                raise HTTPException(status_code=409, detail="Stock changed during checkout")

        MaterialAccountService(db).record_sale_transaction(transaction)

        for voucher, applied_amount in vouchers:
            voucher_service.repository.apply_redemption(
                voucher.id,
                user_id,
                transaction.id,
                applied_amount_cents=applied_amount,
                commit=False,
            )

        issued_prepaid_vouchers = []
        next_unissued_prepaid_voucher_number = None
        try:
            issued_prepaid_vouchers, next_unissued_prepaid = voucher_service.issue_prepaid_vouchers_for_sale(
                transaction,
                sold_prepaid_quantities_by_value,
                user_id,
            )
            next_unissued_prepaid_voucher_number = voucher_service.format_voucher_identifier(next_unissued_prepaid)
        except ValueError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        for payload_item, saved_item in zip(transaction_data.items, transaction.items):
            for guest in payload_item.guests:
                db.add(GuestListEntry(product_id=saved_item.product_id, transaction_id=transaction.id,
                    transaction_item_id=saved_item.id, member_id=guest.member_id,
                    guest_first_name=guest.guest_first_name, guest_last_name=guest.guest_last_name,
                    guest_name=f"{guest.guest_first_name} {guest.guest_last_name or ''}".strip()))

        # Final commit to ensure everything is persisted
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(transaction)

        drawer_targets = drawer_targets_for_sale(
            products_for_drawer,
            transaction.payment_method,
            payable_amount_cents,
            transaction.tip_cents,
            transaction.cash_received_cents,
            transaction.change_given_cents,
        )
        
        print(
            f"[API] Sale transaction created successfully: "
            f"id={transaction.id}, receipt_number={transaction.receipt_number}, "
            f"gross={total_amount}, payable={payable_amount_cents}, voucher={voucher_applied_cents}, balance={balance_applied_cents}"
        )
        
        return {
            "id": transaction.id,
            "receipt_number": transaction.receipt_number,
            "type": transaction.type.value,
            "payment_method": transaction.payment_method.value,
            "total_amount_cents": transaction.total_amount_cents,
            "user_id": transaction.user_id,
            "member_id": transaction.member_id,
            "voucher_code": transaction.voucher_code,
            "voucher_type": transaction.voucher_type,
            "voucher_redemptions": transaction.voucher_redemptions,
            "voucher_applied_cents": transaction.voucher_applied_cents or 0,
            "balance_applied_cents": transaction.balance_applied_cents or 0,
            "tip_cents": transaction.tip_cents or 0,
            "cash_received_cents": transaction.cash_received_cents,
            "change_given_cents": transaction.change_given_cents,
            "open_small_parts_drawer": SMALL_PARTS_DRAWER in drawer_targets,
            "drawer_targets": drawer_targets,
            "items": transaction.items,
            "issued_prepaid_voucher_numbers": [
                code
                for voucher in issued_prepaid_vouchers
                for code in [voucher_service.format_voucher_identifier(voucher)]
                if code
            ],
            "next_unissued_prepaid_voucher_number": next_unissued_prepaid_voucher_number,
            "created_at": transaction.created_at,
            "updated_at": transaction.updated_at,
        }
    except Exception:
        db.rollback()
        raise


@router.post("/storno", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
@router.post("/storno/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_storno(
    storno_data: TransactionStornoCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a storno (reversal) transaction"""
    current_user = require_authenticated_user(request, db)
    user_id = current_user.id
    
    service = TransactionService(db)

    # Load cashier username for snapshot
    performed_by_username_storno = None
    performed_by_username_storno = current_user.username
    
    try:
        storno = service.create_storno_transaction(
            storno_data.transaction_id,
            user_id,
            performed_by_username=performed_by_username_storno,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    # Process storno payment
    member_repo = MemberRepository(db)
    service.process_storno_payment(storno, member_repo)
    
    # Add back stock for each item
    product_repo = ProductRepository(db)
    for item in storno.reference_transaction.items:
        product_repo.add_stock(item.product_id, item.quantity)

    MaterialAccountService(db).record_storno_transaction(storno)

    original = storno.reference_transaction
    drawer_targets = drawer_targets_for_sale(
        (item.product for item in original.items),
        original.payment_method,
        original.total_amount_cents,
        original.tip_cents,
        original.cash_received_cents,
        original.change_given_cents,
    )
    storno.drawer_targets = drawer_targets
    storno.open_small_parts_drawer = SMALL_PARTS_DRAWER in drawer_targets
    
    return storno


@router.get("/daily-summary")
@router.get("/daily-summary/")
async def get_daily_summary(
    date_param: str,  # format: YYYY-MM-DD
    request: Request,
    password: str = None,
    db: Session = Depends(get_db),
):
    """Get daily summary (Z-Bon) - requires password"""
    _require_finance_access(request, db)
    
    # Password check (should be passed as query or body)
    # For now, just check if user is authenticated
    # In production, add additional password protection
    
    try:
        summary_date = datetime.strptime(date_param, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD",
        )
    
    service = TransactionService(db)
    summary = service.get_daily_summary(summary_date)
    
    return ZBonResponse(
        total_cash_cents=summary["total_cash_cents"],
        total_balance_cents=summary["total_balance_cents"],
        transaction_count=summary["transaction_count"],
        created_at=datetime.now(),
    )


@router.get("/daily-stats")
@router.get("/daily-stats/")
async def get_daily_stats(
    date: str,  # format: YYYY-MM-DD
    request: Request,
    db: Session = Depends(get_db),
):
    """Get daily statistics with transaction list"""
    require_roles(request, db, UserRole.ADMIN)
    
    try:
        summary_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD",
        )
    
    service = TransactionService(db)
    stats = service.get_daily_stats(summary_date)
    
    return stats


@router.get("/filtered")
@router.get("/filtered/")
async def get_filtered_transactions(
    start_date: str,
    end_date: str,
    request: Request,
    payment_method: str = None,
    db: Session = Depends(get_db),
):
    """Get filtered transactions"""
    require_roles(request, db, UserRole.ADMIN)
    
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD",
        )
    
    service = TransactionService(db)
    result = service.get_filtered_transactions(start, end, payment_method)
    
    return result


def _parse_transaction_export_filters(start_date: str, end_date: str) -> tuple[date, date]:
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD",
        ) from exc

    if end < start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Das Bis-Datum darf nicht vor dem Von-Datum liegen",
        )
    return start, end


def _build_transaction_export(
    db: Session,
    start_date: str,
    end_date: str,
    payment_method: str | None,
) -> tuple[date, date, dict, str]:
    start, end = _parse_transaction_export_filters(start_date, end_date)
    allowed_payment_methods = {None, "", "CASH", "BALANCE", "VOUCHER_GIFT", "VOUCHER_PREPAID", "WITHDRAWAL"}
    if payment_method not in allowed_payment_methods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültige Zahlungsart",
        )

    result = TransactionService(db).get_filtered_transactions(start, end, payment_method or None)
    html = TransactionExportService.render_html(
        transactions=result["transactions"],
        total_amount_cents=result["total_amount"],
        start_date=start,
        end_date=end,
        payment_method=payment_method or None,
        business_info=AppSettingsService(db).get_business_info(),
    )
    return start, end, result, html


@router.get("/export/preview", response_class=HTMLResponse)
@router.get("/export/preview/", response_class=HTMLResponse)
async def preview_transaction_export(
    start_date: str,
    end_date: str,
    request: Request,
    payment_method: str | None = None,
    db: Session = Depends(get_db),
):
    """Render the selected transaction history as a printable HTML preview."""
    require_roles(request, db, UserRole.ADMIN)
    _, _, _, html = _build_transaction_export(db, start_date, end_date, payment_method)
    return HTMLResponse(content=html)


@router.get("/export/csv")
@router.get("/export/csv/")
async def download_transaction_csv(
    start_date: str,
    end_date: str,
    request: Request,
    payment_method: str | None = None,
    db: Session = Depends(get_db),
):
    """Download the selected transaction history as an Excel-friendly CSV file."""
    require_roles(request, db, UserRole.ADMIN)
    start, end, result, _ = _build_transaction_export(db, start_date, end_date, payment_method)
    filename = TransactionExportService.filename(start, end, "csv")
    return Response(
        content=TransactionExportService.render_csv(result["transactions"]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/pdf")
@router.get("/export/pdf/")
async def download_transaction_pdf(
    start_date: str,
    end_date: str,
    request: Request,
    payment_method: str | None = None,
    db: Session = Depends(get_db),
):
    """Download the selected transaction history as PDF."""
    require_roles(request, db, UserRole.ADMIN)
    start, end, result, html = _build_transaction_export(db, start_date, end_date, payment_method)
    pdf = TransactionExportService.render_pdf(
        html,
        result["transactions"],
        result["total_amount"],
        start,
        end,
    )
    filename = TransactionExportService.filename(start, end, "pdf")
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/revenue-stats")
@router.get("/revenue-stats/")
async def get_revenue_stats(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get revenue statistics"""
    require_roles(request, db, UserRole.ADMIN)
    
    try:
        service = TransactionService(db)
        stats = service.get_revenue_stats()
        print(f"[API] Revenue stats loaded: {stats}")
        return stats
    except Exception as e:
        print(f"[API] Error loading revenue stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading revenue stats: {str(e)}",
        )


@router.get("/{transaction_id}", response_model=TransactionResponse)
@router.get("/{transaction_id}/", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get transaction by ID"""
    require_roles(request, db, UserRole.ADMIN)
    
    service = TransactionService(db)
    transaction = service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    
    return transaction


@router.get("/", response_model=list[TransactionResponse])
@router.get("", response_model=list[TransactionResponse])
async def get_transactions(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get all transactions"""
    require_roles(request, db, UserRole.ADMIN)
    
    service = TransactionService(db)
    return service.get_all_transactions(skip, limit)


# ============================================================
# Z-BON ENDPOINTS
# ============================================================

@router.post("/zbon/generate")
@router.post("/zbon/generate/")
async def generate_zbon(
    zbon_req: ZBonGenerateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Generate Z-Bon or daily report"""
    _require_finance_access(request, db)
    
    try:
        target_date = None
        if zbon_req.date:
            target_date = datetime.strptime(zbon_req.date, "%Y-%m-%d").date()
        else:
            target_date = date.today()
        
        # Convert cash count to dict if provided
        cash_count = None
        if zbon_req.cash_count:
            cash_count = {
                "coins": zbon_req.cash_count.coins or {},
                "notes": zbon_req.cash_count.notes or {},
            }
        
        service = ZBonService(db)
        result = service.generate_zbon(
            target_date=target_date,
            include_cash_count=cash_count,
            report_type=zbon_req.report_type,
        )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating Kassenbericht: {str(e)}",
        )


@router.post("/zbon/preview")
@router.post("/zbon/preview/")
async def preview_current_zbon(
    zbon_req: ZBonPreviewRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Preview the current Z-Bon period since the last generated Z-Bon."""
    _require_finance_access(request, db)
    creator_name, verifier_name = resolve_zbon_actors(db, zbon_req)

    cash_count = None
    if zbon_req.cash_count:
        cash_count = {
            "coins": zbon_req.cash_count.coins or {},
            "notes": zbon_req.cash_count.notes or {},
        }

    pending_withdrawals = [
        {
            "amount_cents": withdrawal.amount_cents,
            "reason": withdrawal.reason,
        }
        for withdrawal in zbon_req.pending_withdrawals
        if withdrawal.amount_cents > 0
    ]

    service = ZBonService(db)
    return service.build_current_zbon_preview(
        created_by_name=creator_name,
        skimmed_by_name=None,
        cash_counted_by_name=verifier_name,
        include_cash_count=cash_count,
        cash_count_total=zbon_req.cash_count_total,
        pending_withdrawals=pending_withdrawals,
    )


@router.post("/zbon/preview/send-email")
@router.post("/zbon/preview/send-email/")
async def send_zbon_preview_email(
    email_req: ZBonPreviewEmailRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Send the currently rendered Z-Bon preview HTML via email without creating a Z-Bon."""
    _require_finance_access(request, db)

    if not EmailService.is_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is not enabled",
        )

    html_zbon = (email_req.html_zbon or "").strip()
    if not html_zbon:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kein Vorschau-HTML übergeben",
        )

    recipient = email_req.recipient or AppSettingsService(db).get_email_settings().get("email_recipient_zbon")
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kein Empfänger für den Kassenbericht konfiguriert",
        )

    target_date = date.today()
    if email_req.report_date:
        try:
            target_date = datetime.strptime(email_req.report_date, "%Y-%m-%d").date()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ungültiges Datumsformat. Verwende YYYY-MM-DD",
            ) from exc

    success = EmailService.send_zbon_html_email(
        recipient=recipient,
        html_zbon=html_zbon,
        date=target_date.isoformat(),
        seq_number=email_req.seq_number,
        include_pdf=None,
        informational_only=True,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Versand der Vorschau per E-Mail",
        )

    return {
        "status": "success",
        "message": f"Vorschau per E-Mail an {recipient} gesendet",
        "recipient": recipient,
        "report_date": target_date.isoformat(),
    }


@router.post("/zbon/create")
@router.post("/zbon/create/")
async def create_zbon(
    zbon_req: ZBonCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create and archive a new immutable Z-Bon."""
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    require_password_confirmation(current_user, zbon_req.auth_password, db)
    creator_name, verifier_name = resolve_zbon_actors(db, zbon_req)
    from app.core.financial_booking import lock_financial_period
    lock_financial_period(db)

    cash_count = None
    if zbon_req.cash_count:
        cash_count = {
            "coins": zbon_req.cash_count.coins or {},
            "notes": zbon_req.cash_count.notes or {},
        }

    pending_withdrawals = [
        {
            "amount_cents": withdrawal.amount_cents,
            "reason": withdrawal.reason,
        }
        for withdrawal in zbon_req.pending_withdrawals
        if withdrawal.amount_cents > 0
    ]

    if pending_withdrawals:
        from app.repositories import CashEntryRepository

        period_end = datetime.now()
        cash_repo = CashEntryRepository(db)
        for withdrawal in pending_withdrawals:
            cash_repo.create(
                entry_type=CashEntryType.WITHDRAWAL,
                amount_cents=withdrawal["amount_cents"],
                reason=withdrawal["reason"],
                user_id=current_user.id,
                created_at=period_end,
                commit=False,
            )

    service = ZBonService(db)
    payload = service.create_zbon(
        created_by_name=creator_name,
        skimmed_by_name=None,
        cash_counted_by_name=verifier_name,
        include_cash_count=cash_count,
        cash_count_total=zbon_req.cash_count_total,
        difference_reason=zbon_req.difference_reason,
        pending_withdrawals=None,
    )

    def notify_zbon_created():
        email_settings = AppSettingsService(db).get_email_settings()
        recipient = (email_settings.get("email_recipient_zbon") or "").strip()
        if (
            email_settings.get("email_enabled")
            and email_settings.get("send_zbon_on_create_enabled")
            and recipient
        ):
            sent = EmailService.send_zbon_html_email(
                recipient=recipient,
                html_zbon=payload.get("report_content") or "",
                date=payload.get("business_date") or date.today().isoformat(),
                seq_number=payload.get("sequence_number"),
                informational_only=False,
            )
            if not sent:
                logger.warning("Auto-send after Z-Bon creation failed for sequence=%s", payload.get("sequence_number"))
    if hasattr(request.state, "after_booking_commit"):
        request.state.after_booking_commit.append(notify_zbon_created)
    else:
        notify_zbon_created()

    payload["drawer_targets"] = ["main"] if pending_withdrawals else []
    return payload


@router.post("/zbon/send-email")
@router.post("/zbon/send-email/")
async def send_zbon_email(
    email_req: ZBonEmailRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Send daily update via the unified full HTML report."""
    _require_finance_access(request, db)
    
    try:
        if not EmailService.is_enabled():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service is not enabled",
            )
        
        target_date = None
        if email_req.date:
            target_date = datetime.strptime(email_req.date, "%Y-%m-%d").date()
        else:
            target_date = date.today()
        
        recipient = email_req.recipient or AppSettingsService(db).get_email_settings().get("email_recipient_zbon")
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kein Empfänger für den Kassenbericht konfiguriert",
            )
        
        zbon_service = ZBonService(db)
        zbon_result = zbon_service.generate_daily_html_update(target_date)

        success = EmailService.send_zbon_html_email(
            recipient=recipient,
            html_zbon=zbon_result["html"],
            date=zbon_result["business_date"],
            seq_number=zbon_result.get("sequence_number"),
            informational_only=True,
        )
        
        if not success:
            raise Exception("Email sending failed")
        
        return {
            "status": "success",
            "message": f"Tagesupdate gesendet an {recipient}",
            "date": target_date.isoformat(),
            "type": "full-html",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending Kassenbericht via email: {str(e)}",
        )


@router.get("/zbon/html")
@router.get("/zbon/html/")
async def get_zbon_html(
    report_date: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Get Z-Bon as HTML for preview"""
    _require_finance_access(request, db)
    
    try:
        from app.services.zbon_html_exporter import ZBonHTMLExporter

        payload = ZBonService(db).build_current_zbon_preview()
        return HTMLResponse(content=payload["report_content"])
        
        target_date = None
        if report_date:
            target_date = datetime.strptime(report_date, "%Y-%m-%d").date()
        else:
            target_date = date.today()
        
        logger.info(f"Generating Z-Bon HTML for date: {target_date}")
        
        # Generate Z-Bon data
        zbon_service = ZBonService(db)
        transactions = db.query(Transaction).filter(
            func.date(Transaction.created_at) == target_date
        ).all()
        
        logger.info(f"Found {len(transactions)} transactions for {target_date}")
        
        stats = zbon_service._calculate_stats(transactions)
        meta = zbon_service._collect_meta(target_date, transactions)
        product_breakdown = zbon_service._aggregate_by_product(transactions)
        product_group_breakdown = zbon_service._aggregate_by_warengruppe(transactions)
        category_breakdown = zbon_service._aggregate_by_category(transactions)
        customer_breakdown = zbon_service._aggregate_by_customer(transactions)
        customer_group_breakdown = zbon_service._aggregate_by_customer_group(transactions)
        storno_details = zbon_service._get_storno_details(transactions)
        material_account_sales_count = zbon_service._count_internal_material_sales(transactions)
        
        # Get last Z-Bon number
        last_zbon = db.query(ZBonHistory).filter(
            ZBonHistory.business_date < target_date
        ).order_by(desc(ZBonHistory.sequence_number)).first()
        seq_number = (last_zbon.sequence_number + 1) if last_zbon else 1
        
        # Convert receipt min/max to integers or 0
        receipt_min = meta.get('receipt_min', 0)
        receipt_max = meta.get('receipt_max', 0)
        
        if isinstance(receipt_min, str) and receipt_min != "-":
            receipt_min = int(receipt_min)
        else:
            receipt_min = 0
            
        if isinstance(receipt_max, str) and receipt_max != "-":
            receipt_max = int(receipt_max)
        else:
            receipt_max = 0
        
        logger.info(f"Z-Bon stats: cash={stats.get('cash_sales_total', 0)}, balance={stats.get('balance_sales_total', 0)}")
        business_info = zbon_service.get_business_info()

        # Render HTML
        html = ZBonHTMLExporter.render_html(
            seq_number=seq_number,
            business_date=meta['business_date'],
            created_at=meta['report_generated_at'],
            period_start=meta['first_tx_time'],
            period_end=meta['last_tx_time'],
            receipt_min=receipt_min,
            receipt_max=receipt_max,
            cash_sales_count=stats.get('cash_sales_count', 0),
            cash_sales_net=stats.get('cash_sales_total', 0),
            cash_sales_tax=0.0,
            cash_sales_gross=stats.get('cash_sales_total', 0),
            balance_sales_count=stats.get('balance_sales_count', 0),
            balance_sales_net=stats.get('balance_sales_total', 0),
            balance_sales_tax=0.0,
            balance_sales_gross=stats.get('balance_sales_total', 0),
            recharge_count=stats.get('recharge_count', 0),
            recharge_total=stats.get('recharge_total', 0),
            total_items_count=stats.get('cash_sales_count', 0) + stats.get('balance_sales_count', 0),
            total_net=stats.get('cash_sales_total', 0) + stats.get('balance_sales_total', 0),
            total_tax=0.0,
            total_gross=stats.get('cash_sales_total', 0) + stats.get('balance_sales_total', 0) + stats.get('recharge_total', 0),
            cash_revenue=stats.get('cash_sales_total', 0) + stats.get('recharge_total', 0),
            guthaben_net=stats.get('balance_sales_total', 0),
            guthaben_gross=stats.get('balance_sales_total', 0),
            total_revenue=stats.get('gross_revenue_cash', 0) + stats.get('gross_revenue_balance', 0),
            product_groups_breakdown=product_group_breakdown or {},
            categories_breakdown=category_breakdown or {},
            customer_groups=customer_group_breakdown or {},
            customers=customer_breakdown or {},
            stornos=storno_details or [],
            material_account_sales_count=material_account_sales_count,
            business_info=business_info,
        )
        
        logger.info(f"Z-Bon HTML generated successfully ({len(html)} bytes)")
        return HTMLResponse(content=html)
        
    except Exception as e:
        logger.error(f"Error generating Z-Bon HTML: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating Kassenbericht HTML: {str(e)}",
        )


@router.get("/zbon/pdf")
@router.get("/zbon/pdf/")
async def get_zbon_pdf(
    report_date: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Download Z-Bon as PDF"""
    _require_finance_access(request, db)
    
    try:
        from app.services.zbon_html_exporter import ZBonHTMLExporter

        payload = ZBonService(db).build_current_zbon_preview()
        html = payload["report_content"]
        try:
            pdf_file = ZBonHTMLExporter.export_pdf(html)
            filename = f"Kassenbericht_{payload['sequence_number']}_{payload['business_date']}.pdf"
            return Response(
                content=pdf_file.getvalue(),
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        except RuntimeError as pdf_error:
            logger.warning("PDF export unavailable: %s", pdf_error)
            return HTMLResponse(content=html)
        
        target_date = None
        if report_date:
            target_date = datetime.strptime(report_date, "%Y-%m-%d").date()
        else:
            target_date = date.today()
        
        logger.info(f"Generating Z-Bon PDF for date: {target_date}")
        
        # Generate Z-Bon data (same as HTML endpoint)
        zbon_service = ZBonService(db)
        transactions = db.query(Transaction).filter(
            func.date(Transaction.created_at) == target_date
        ).all()
        
        logger.info(f"Found {len(transactions)} transactions for {target_date}")
        
        stats = zbon_service._calculate_stats(transactions)
        meta = zbon_service._collect_meta(target_date, transactions)
        product_breakdown = zbon_service._aggregate_by_product(transactions)
        product_group_breakdown = zbon_service._aggregate_by_warengruppe(transactions)
        category_breakdown = zbon_service._aggregate_by_category(transactions)
        customer_breakdown = zbon_service._aggregate_by_customer(transactions)
        customer_group_breakdown = zbon_service._aggregate_by_customer_group(transactions)
        storno_details = zbon_service._get_storno_details(transactions)
        material_account_sales_count = zbon_service._count_internal_material_sales(transactions)
        
        # Get last Z-Bon number
        last_zbon = db.query(ZBonHistory).filter(
            ZBonHistory.business_date < target_date
        ).order_by(desc(ZBonHistory.sequence_number)).first()
        seq_number = (last_zbon.sequence_number + 1) if last_zbon else 1
        
        # Convert receipt min/max to integers or 0
        receipt_min = meta.get('receipt_min', 0)
        receipt_max = meta.get('receipt_max', 0)
        
        if isinstance(receipt_min, str) and receipt_min != "-":
            receipt_min = int(receipt_min)
        else:
            receipt_min = 0
            
        if isinstance(receipt_max, str) and receipt_max != "-":
            receipt_max = int(receipt_max)
        else:
            receipt_max = 0
        
        logger.info(f"Z-Bon stats: cash={stats.get('cash_sales_total', 0)}, balance={stats.get('balance_sales_total', 0)}")
        business_info = zbon_service.get_business_info()

        # Render HTML
        html = ZBonHTMLExporter.render_html(
            seq_number=seq_number,
            business_date=meta['business_date'],
            created_at=meta['report_generated_at'],
            period_start=meta['first_tx_time'],
            period_end=meta['last_tx_time'],
            receipt_min=receipt_min,
            receipt_max=receipt_max,
            cash_sales_count=stats.get('cash_sales_count', 0),
            cash_sales_net=stats.get('cash_sales_total', 0),
            cash_sales_tax=0.0,
            cash_sales_gross=stats.get('cash_sales_total', 0),
            balance_sales_count=stats.get('balance_sales_count', 0),
            balance_sales_net=stats.get('balance_sales_total', 0),
            balance_sales_tax=0.0,
            balance_sales_gross=stats.get('balance_sales_total', 0),
            recharge_count=stats.get('recharge_count', 0),
            recharge_total=stats.get('recharge_total', 0),
            total_items_count=stats.get('cash_sales_count', 0) + stats.get('balance_sales_count', 0),
            total_net=stats.get('cash_sales_total', 0) + stats.get('balance_sales_total', 0),
            total_tax=0.0,
            total_gross=stats.get('cash_sales_total', 0) + stats.get('balance_sales_total', 0) + stats.get('recharge_total', 0),
            cash_revenue=stats.get('cash_sales_total', 0) + stats.get('recharge_total', 0),
            guthaben_net=stats.get('balance_sales_total', 0),
            guthaben_gross=stats.get('balance_sales_total', 0),
            total_revenue=stats.get('gross_revenue_cash', 0) + stats.get('gross_revenue_balance', 0),
            product_groups_breakdown=product_group_breakdown or {},
            categories_breakdown=category_breakdown or {},
            customer_groups=customer_group_breakdown or {},
            customers=customer_breakdown or {},
            stornos=storno_details or [],
            material_account_sales_count=material_account_sales_count,
            business_info=business_info,
        )
        
        logger.info(f"Z-Bon HTML generated successfully ({len(html)} bytes) for PDF export")
        
        # Export to PDF (with graceful fallback if WeasyPrint unavailable)
        try:
            pdf_bytes = ZBonHTMLExporter.export_pdf(html)
            
            filename = f"Kassenbericht_{seq_number}_{target_date.strftime('%Y-%m-%d')}.pdf"
            logger.info(f"Returning PDF file: {filename}")
            return FileResponse(
                pdf_bytes,
                media_type="application/pdf",
                filename=filename,
            )
        except RuntimeError as pdf_error:
            # WeasyPrint not available - return HTML with note
            logger.warning(f"PDF export unavailable: {str(pdf_error)}")
            
            # Return HTML with download header as fallback
            html_with_note = f"""
            <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 10px 0; border-radius: 4px;">
                <strong>⚠️ PDF export not available</strong><br>
                PDF export is optional and requires additional system libraries. 
                You can still view the Kassenbericht in HTML format above and print it from your browser using Ctrl+P.
            </div>
            {html}
            """
            return HTMLResponse(content=html_with_note)
        
    except Exception as e:
        logger.error(f"Error generating Z-Bon PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating Kassenbericht PDF: {str(e)}",
        )


@router.post("/zbon/email")
async def send_zbon_email(
    recipient: str,
    report_date: Optional[str] = None,
    include_pdf: bool = False,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """
    Send Z-Bon via email with professional HTML formatting
    
    Args:
        recipient: Email address to send to
        report_date: Optional date (YYYY-MM-DD), defaults to today
        include_pdf: Optional - attach PDF if WeasyPrint available
        request: HTTP request (for auth)
        db: Database session
    
    Returns:
        JSON response with status
    """
    _require_finance_access(request, db)
    
    try:
        target_date = None
        if report_date:
            target_date = datetime.strptime(report_date, "%Y-%m-%d").date()
        else:
            target_date = date.today()
        
        zbon_service = ZBonService(db)
        update_payload = zbon_service.generate_daily_html_update(target_date)
        html = update_payload["html"]
        seq_number = update_payload.get("sequence_number")
        
        # Optional: Generate PDF if requested
        pdf_bytes = None
        if include_pdf:
            try:
                pdf_file = ZBonHTMLExporter.export_pdf(html)
                pdf_bytes = pdf_file.getvalue()
            except RuntimeError:
                # PDF export not available, send without it
                logger.info("PDF export not available, sending HTML only")
        
        # Send email with HTML Z-Bon
        email_service = EmailService()
        success = email_service.send_zbon_html_email(
            recipient=recipient,
            html_zbon=html,
            date=update_payload["business_date"],
            seq_number=seq_number,
            include_pdf=pdf_bytes,
            informational_only=True,
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Kassenbericht sent to {recipient}",
                "date": target_date.strftime("%Y-%m-%d"),
                "seq_number": seq_number,
                "pdf_attached": include_pdf and pdf_bytes is not None,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email",
            )
        
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(ve)}",
        )
    except Exception as e:
        logger.error(f"Error sending Z-Bon email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending Kassenbericht email: {str(e)}",
        )
@router.get("/scheduler/status")
@router.get("/scheduler/status/")
async def get_scheduler_status(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get current scheduler status (admin only)"""
    require_roles(request, db, UserRole.ADMIN)

    return SchedulerService.get_scheduler_status()


# ============================================================
# CASH MANAGEMENT ENDPOINTS
# ============================================================

class CashWithdrawalRequest(BaseModel):
    amount_cents: int = Field(..., gt=0)  # Amount in cents
    reason: str  # Reason for withdrawal (e.g., "Abschöpfung Benny u.Carsten")


class CashDepositRequest(BaseModel):
    amount_cents: int = Field(..., gt=0)  # Amount in cents
    reason: str  # Reason for deposit


@router.post("/cash/withdrawal")
@router.post("/cash/withdrawal/")
async def record_cash_withdrawal(
    withdrawal_req: CashWithdrawalRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Record a cash withdrawal (Entnahme)"""
    current_user = require_roles(request, db, UserRole.ADMIN)
    user_id = current_user.id
    
    try:
        from app.repositories import CashEntryRepository
        from app.models import CashEntryType
        
        cash_repo = CashEntryRepository(db)
        entry = cash_repo.create(
            entry_type=CashEntryType.WITHDRAWAL,
            amount_cents=withdrawal_req.amount_cents,
            reason=withdrawal_req.reason,
            user_id=user_id,
        )
        
        return {
            "id": entry.id,
            "type": "WITHDRAWAL",
            "amount_cents": entry.amount_cents,
            "amount_eur": entry.amount_cents / 100,
            "reason": entry.reason,
            "created_at": entry.created_at.isoformat(),
            "drawer_targets": ["main"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording cash withdrawal: {str(e)}",
        )


@router.post("/cash/deposit")
@router.post("/cash/deposit/")
async def record_cash_deposit(
    deposit_req: CashDepositRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Record a cash deposit (Einlage)"""
    current_user = require_roles(request, db, UserRole.ADMIN)
    user_id = current_user.id
    
    try:
        from app.repositories import CashEntryRepository
        from app.models import CashEntryType
        
        cash_repo = CashEntryRepository(db)
        entry = cash_repo.create(
            entry_type=CashEntryType.DEPOSIT,
            amount_cents=deposit_req.amount_cents,
            reason=deposit_req.reason,
            user_id=user_id,
        )
        
        return {
            "id": entry.id,
            "type": "DEPOSIT",
            "amount_cents": entry.amount_cents,
            "amount_eur": entry.amount_cents / 100,
            "reason": entry.reason,
            "created_at": entry.created_at.isoformat(),
            "drawer_targets": ["main"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording cash deposit: {str(e)}",
        )


@router.get("/cash/entries")
@router.get("/cash/entries/")
async def get_cash_entries(
    target_date: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Get cash entries (withdrawals and deposits) for a date"""
    require_roles(request, db, UserRole.ADMIN)
    
    try:
        from app.repositories import CashEntryRepository
        
        target = None
        if target_date:
            target = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            target = date.today()
        
        cash_repo = CashEntryRepository(db)
        entries = cash_repo.get_by_date(target)
        
        return {
            "date": target.isoformat(),
            "entries": [
                {
                    "id": entry.id,
                    "type": entry.entry_type.value,
                    "amount_cents": entry.amount_cents,
                    "amount_eur": entry.amount_cents / 100,
                    "reason": entry.reason,
                    "user_id": entry.user_id,
                    "created_at": entry.created_at.isoformat(),
                }
                for entry in entries
            ],
            "total_withdrawals_eur": cash_repo.get_total_withdrawals(target) / 100,
            "total_deposits_eur": cash_repo.get_total_deposits(target) / 100,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching cash entries: {str(e)}",
        )


@router.get("/cash/balance")
@router.get("/cash/balance/")
async def get_cash_balance(
    target_date: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Get cash balance snapshot for a date"""
    require_roles(request, db, UserRole.ADMIN)
    
    try:
        from app.repositories import CashBalanceRepository
        
        target = None
        if target_date:
            target = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            target = date.today()
        
        balance_repo = CashBalanceRepository(db)
        balance = balance_repo.get_by_date(target)
        
        if not balance:
            return {
                "date": target.isoformat(),
                "status": "not_found",
                "message": "No cash balance recorded for this date",
            }
        
        return {
            "id": balance.id,
            "date": balance.balance_date.strftime("%d.%m.%Y"),
            "opening_balance_eur": balance.opening_balance_cents / 100,
            "closing_balance_eur": balance.closing_balance_cents / 100 if balance.closing_balance_cents else None,
            "cash_sales_eur": balance.cash_sales_cents / 100,
            "balance_recharges_eur": balance.balance_recharges_cents / 100,
            "cash_withdrawals_eur": balance.cash_withdrawals_cents / 100,
            "cash_deposits_eur": balance.cash_deposits_cents / 100,
            "created_at": balance.created_at.isoformat(),
            "updated_at": balance.updated_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching cash balance: {str(e)}",
        )


# ============================================================================
# Z-BON HISTORY ENDPOINTS
# ============================================================================


@router.get("/zbon/audit")
@router.get("/zbon/audit/")
async def get_zbon_consistency_audit(
    request: Request,
    db: Session = Depends(get_db),
):
    """Return a read-only consistency report for all archived Z-Bons."""
    _require_finance_access(request, db)
    return ZBonService(db).build_history_consistency_report()


@router.get("/zbon/history", response_model=ZBonHistoryListResponse)
@router.get("/zbon/history/", response_model=ZBonHistoryListResponse)
async def get_zbon_history(
    request: Request,
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 20,
    start_date: str = None,
    end_date: str = None,
):
    """Get Z-Bon history with optional date filtering
    
    Query parameters:
    - page: Page number (default 1)
    - page_size: Items per page (default 20, max 100)
    - start_date: Filter from date (YYYY-MM-DD)
    - end_date: Filter to date (YYYY-MM-DD)
    """
    _require_finance_access(request, db)
    
    try:
        query = db.query(ZBonHistory)
        
        # Apply date filters if provided
        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(ZBonHistory.business_date >= start)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format, use YYYY-MM-DD",
                )
        
        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d")
                # Add 1 day to include all of end_date
                end = end.replace(hour=23, minute=59, second=59)
                query = query.filter(ZBonHistory.business_date <= end)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format, use YYYY-MM-DD",
                )
        
        # Sort by sequence number descending (newest first)
        query = query.order_by(desc(ZBonHistory.sequence_number))
        
        # Count total
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        histories = query.offset(offset).limit(page_size).all()
        
        total_pages = (total + page_size - 1) // page_size
        
        logger.info(
            f"[TRANSACTION] Z-Bon history retrieved: total={total}, page={page}, "
            f"filters={{'start_date': {start_date}, 'end_date': {end_date}}}"
        )
        
        return ZBonHistoryListResponse(
            histories=[ZBonHistoryResponse.from_orm(h) for h in histories],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TRANSACTION] Error retrieving Z-Bon history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving Kassenbericht history: {str(e)}",
        )


@router.get("/zbon/history/{sequence_number}", response_model=ZBonHistoryResponse)
@router.get("/zbon/history/{sequence_number}/", response_model=ZBonHistoryResponse)
async def get_zbon_history_detail(
    sequence_number: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get Z-Bon history detail by sequence number"""
    _require_finance_access(request, db)
    
    try:
        history = db.query(ZBonHistory).filter(
            ZBonHistory.sequence_number == sequence_number
        ).first()
        
        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Kassenbericht #{sequence_number} not found",
            )
        
        return ZBonHistoryResponse.from_orm(history)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[TRANSACTION] Error retrieving Z-Bon #{sequence_number}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving Kassenbericht: {str(e)}",
        )


@router.get("/zbon/history/{sequence_number}/html")
@router.get("/zbon/history/{sequence_number}/html/")
async def get_zbon_history_html(
    sequence_number: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Return archived Z-Bon content as HTML/text."""
    _require_finance_access(request, db)

    history = db.query(ZBonHistory).filter(ZBonHistory.sequence_number == sequence_number).first()
    if not history or not history.report_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Kassenbericht #{sequence_number} not found",
        )

    return HTMLResponse(content=history.report_content)


@router.get("/zbon/history/{sequence_number}/pdf")
@router.get("/zbon/history/{sequence_number}/pdf/")
async def get_zbon_history_pdf(
    sequence_number: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Render archived Z-Bon content as PDF when PDF export is available."""
    _require_finance_access(request, db)

    history = db.query(ZBonHistory).filter(ZBonHistory.sequence_number == sequence_number).first()
    if not history or not history.report_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Kassenbericht #{sequence_number} not found",
        )

    try:
        pdf_file = ZBonHTMLExporter.export_pdf(history.report_content)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    return Response(
        content=pdf_file.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Kassenbericht-{sequence_number}.pdf"'},
    )
