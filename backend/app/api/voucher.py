from app.core.booking_route import BookingRoute
from fastapi import APIRouter, HTTPException, Depends, Request, status, Query
from sqlalchemy.orm import Session
import logging
from datetime import datetime
import csv
import io
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import joinedload
from pydantic import BaseModel, Field

from app.core import get_db
from app.core.auth import require_authenticated_user, require_roles, resolve_confirmation_user
from app.schemas import (
    VoucherBatchCreateResponse,
    VoucherCreateGift,
    VoucherCreatePrepaid,
    VoucherValidateRequest,
    VoucherRedeemRequest,
    VoucherValidationResponse,
    VoucherResponse,
    VoucherListResponse,
    VoucherRedeemResponse,
    VoucherUpdateRequest,
)
from app.services import MaterialAccountService, VoucherService
from app.repositories import VoucherRepository
from app.models import Voucher, VoucherStatus, VoucherType, UserRole

logger = logging.getLogger(__name__)

# Two routers: one for admin, one for kasse
admin_router = APIRouter(route_class=BookingRoute, prefix="/api/admin/vouchers", tags=["Admin - Vouchers"])
kasse_router = APIRouter(route_class=BookingRoute, prefix="/api/transactions/voucher", tags=["Kasse - Voucher"])


class ClubAccountTopUpRequest(BaseModel):
    amount_cents: int = Field(..., ge=1)
    auth_username: str | None = Field(default=None, min_length=1, max_length=50)
    auth_password: str = Field(..., min_length=1)


def get_user_id(request: Request, db: Session) -> int:
    return require_authenticated_user(request, db).id


def require_voucher_confirmation(
    db: Session,
    current_user,
    *,
    auth_password: str,
    auth_username: str | None = None,
) -> None:
    """Validate the confirmation step without changing log attribution."""
    resolve_confirmation_user(
        db,
        current_user,
        auth_password,
        username=auth_username,
        allow_top_admin_override=False,
    )


# ============================================================================
# ADMIN ROUTES - /api/admin/vouchers
# ============================================================================


@admin_router.post(
    "/gift",
    response_model=VoucherResponse,
    status_code=status.HTTP_201_CREATED,
)
@admin_router.post(
    "/gift/",
    response_model=VoucherResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_gift_voucher(
    voucher_data: VoucherCreateGift,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a gift voucher (no payment, loss recording on redemption)"""
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    require_voucher_confirmation(
        db,
        current_user,
        auth_password=voucher_data.auth_password,
        auth_username=voucher_data.auth_username,
    )
    
    try:
        service = VoucherService(db)
        voucher = service.create_gift_voucher(
            value_cents=voucher_data.value_cents,
            reason=voucher_data.reason,
            created_by_user_id=current_user.id,
        )
        logger.debug(f"[DEBUG] Voucher object after create: id={voucher.id}, voucher_code={voucher.voucher_code}")
        
        response = VoucherResponse.from_orm(voucher)
        
        logger.debug(f"[DEBUG] Response object: voucher_code={response.voucher_code}")
        logger.info(
            f"[ADMIN] Created GIFT voucher {voucher.voucher_code} "
            f"(value: {voucher.value_cents} cents) by user {current_user.id}"
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"[ADMIN] Error creating GIFT voucher: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating voucher: {str(e)}",
        )


@admin_router.post(
    "/prepaid",
    response_model=VoucherBatchCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
@admin_router.post(
    "/prepaid/",
    response_model=VoucherBatchCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_prepaid_voucher(
    voucher_data: VoucherCreatePrepaid,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create one or more prepaid vouchers (sold later in the register)."""
    current_user = require_roles(request, db, UserRole.ADMIN)
    require_voucher_confirmation(
        db,
        current_user,
        auth_password=voucher_data.auth_password,
        auth_username=voucher_data.auth_username,
    )
    
    try:
        service = VoucherService(db)
        vouchers, product = service.create_prepaid_vouchers(
            value_cents=voucher_data.value_cents,
            created_by_user_id=current_user.id,
            quantity=voucher_data.quantity,
        )
        logger.info(
            f"[ADMIN] Created {len(vouchers)} PREPAID vouchers "
            f"(value: {voucher_data.value_cents} cents) by user {current_user.id}"
        )
        return VoucherBatchCreateResponse(
            vouchers=[VoucherResponse.from_orm(voucher) for voucher in vouchers],
            quantity=len(vouchers),
            product_name=product.name,
            next_available_voucher_number=service.get_next_unissued_prepaid_voucher_number(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"[ADMIN] Error creating PREPAID voucher: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating voucher: {str(e)}",
        )


@admin_router.get("/", response_model=VoucherListResponse)
@admin_router.get("", response_model=VoucherListResponse)
async def list_vouchers(
    request: Request,
    db: Session = Depends(get_db),
    status_filter: str = Query(None, description="CREATED or REDEEMED"),
    type_filter: str = Query(None, description="GIFT or PREPAID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List vouchers with optional filtering"""
    user_id = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER).id
    
    try:
        repo = VoucherRepository(db)
        
        # Build filter query
        if status_filter and type_filter:
            vouchers, total = repo.get_all_by_type_and_status(
                voucher_type=type_filter,
                status=status_filter,
                skip=(page - 1) * page_size,
                limit=page_size,
            )
        elif status_filter:
            vouchers, total = repo.get_all_by_status(
                status=status_filter,
                skip=(page - 1) * page_size,
                limit=page_size,
            )
        elif type_filter:
            vouchers, total = repo.get_all_by_type(
                voucher_type=type_filter,
                skip=(page - 1) * page_size,
                limit=page_size,
            )
        else:
            # Get all
            vouchers, total = repo.get_all(
                limit=page_size,
                offset=(page - 1) * page_size,
            )
        
        total_pages = (total + page_size - 1) // page_size
        
        # Convert ORM objects to responses with error handling
        responses = []
        for v in vouchers:
            try:
                response = VoucherResponse.from_orm(v)
                responses.append(response)
            except Exception as e:
                logger.warning(f"[ADMIN] Error converting voucher {v.id}: {str(e)}")
                # Still add the response with error logging
                response = VoucherResponse.from_orm(v)
                responses.append(response)
        
        logger.info(f"[ADMIN] Listed {len(responses)} vouchers for user {user_id}")
        
        return VoucherListResponse(
            vouchers=responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        logger.error(f"[ADMIN] Error listing vouchers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing vouchers: {str(e)}",
        )


def _spreadsheet_safe(value) -> str:
    text = "" if value is None else str(value)
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


@admin_router.get("/export.csv")
async def export_vouchers_csv(
    request: Request,
    db: Session = Depends(get_db),
    status_filter: str = Query(None),
    type_filter: str = Query(None),
):
    """Export the complete current filter, independent of table pagination."""
    require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    query = db.query(Voucher).options(
        joinedload(Voucher.created_by_user),
        joinedload(Voucher.sold_by_user),
        joinedload(Voucher.redeemed_by_user),
        joinedload(Voucher.sold_in_transaction),
        joinedload(Voucher.redeemed_in_transaction),
    )
    if status_filter:
        try:
            query = query.filter(Voucher.status == VoucherStatus(status_filter))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Ungültiger Gutscheinstatus") from exc
    if type_filter:
        try:
            query = query.filter(Voucher.voucher_type == VoucherType(type_filter))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Ungültiger Gutscheintyp") from exc
    vouchers = query.order_by(Voucher.voucher_number.desc()).all()

    output = io.StringIO(newline="")
    output.write("\ufeff")
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_ALL, lineterminator="\r\n")
    writer.writerow([
        "Nummer", "Typ", "Anfangswert (Cent)", "Restwert (Cent)", "Status", "Grund",
        "Beschreibung", "Erstellt von", "Erstellt am", "Verkauft von", "Verkauft am",
        "Verkaufsbeleg", "Eingelöst von", "Eingelöst am", "Eingelöster Betrag (Cent)",
        "Einlösungsbeleg",
    ])
    for voucher in vouchers:
        writer.writerow([
            _spreadsheet_safe(voucher.voucher_code or voucher.voucher_number),
            voucher.voucher_type.value,
            voucher.original_value_cents or voucher.value_cents,
            voucher.remaining_value_cents,
            voucher.status.value,
            _spreadsheet_safe(voucher.reason.value if voucher.reason else ""),
            _spreadsheet_safe(voucher.description),
            _spreadsheet_safe(voucher.created_by_user.username if voucher.created_by_user else voucher.created_by_user_id),
            voucher.created_at.isoformat(sep=" ") if voucher.created_at else "",
            _spreadsheet_safe(voucher.sold_by_user.username if voucher.sold_by_user else voucher.sold_by_user_id),
            voucher.sold_at.isoformat(sep=" ") if voucher.sold_at else "",
            voucher.sold_in_transaction.receipt_number if voucher.sold_in_transaction else "",
            _spreadsheet_safe(voucher.redeemed_by_user.username if voucher.redeemed_by_user else voucher.redeemed_by_user_id),
            voucher.redeemed_at.isoformat(sep=" ") if voucher.redeemed_at else "",
            voucher.redeemed_amount_cents if voucher.redeemed_amount_cents is not None else "",
            voucher.redeemed_in_transaction.receipt_number if voucher.redeemed_in_transaction else "",
        ])
    filename = f"Gutscheine-{datetime.now().date().isoformat()}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Export-Count": str(len(vouchers)),
        },
    )



@admin_router.get("/club-account")
@admin_router.get("/club-account/")
async def get_club_account(
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.ADMIN)
    return VoucherService(db).get_club_account_summary()


@admin_router.get("/material-account")
@admin_router.get("/material-account/")
async def get_material_account(
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.ADMIN)
    return MaterialAccountService(db).get_account_summary()


@admin_router.get("/material-transactions")
@admin_router.get("/material-transactions/")
async def get_material_transactions(
    request: Request,
    search: str | None = None,
    entry_type: str | None = Query(None, pattern="^(SALE|STORNO)$"),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    summary = MaterialAccountService(db).get_account_summary(
        search=search,
        entry_type=entry_type,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    # Preserve material value, quantity, note and receipt; omit payment details
    # of the surrounding sale from the operational material list.
    for entry in summary["entries"]:
        transaction = entry.get("transaction")
        if transaction:
            entry["transaction"] = {"member_name": transaction.get("member_name")}
    return summary


@admin_router.post("/club-account/topup")
@admin_router.post("/club-account/topup/")
async def top_up_club_account(
    payload: ClubAccountTopUpRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = require_roles(request, db, UserRole.ADMIN)
    require_voucher_confirmation(
        db,
        current_user,
        auth_password=payload.auth_password,
        auth_username=payload.auth_username,
    )
    return VoucherService(db).top_up_club_account(payload.amount_cents, current_user.id)


@admin_router.get("/{voucher_id}", response_model=VoucherResponse)
@admin_router.get("/{voucher_id}/", response_model=VoucherResponse)
async def get_voucher_detail(
    voucher_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get voucher details by ID"""
    user_id = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER).id
    
    try:
        repo = VoucherRepository(db)
        voucher = repo.get_by_id(voucher_id)
        
        if not voucher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Voucher {voucher_id} not found",
            )
        
        return VoucherResponse.from_orm(voucher)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ADMIN] Error getting voucher {voucher_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting voucher: {str(e)}",
        )



@admin_router.put("/{voucher_id}", response_model=VoucherResponse)
@admin_router.put("/{voucher_id}/", response_model=VoucherResponse)
async def update_voucher(
    voucher_id: int,
    voucher_data: VoucherUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Update editable voucher fields before redemption."""
    current_user = require_roles(request, db, UserRole.ADMIN)
    require_voucher_confirmation(
        db,
        current_user,
        auth_password=voucher_data.auth_password,
        auth_username=voucher_data.auth_username,
    )

    try:
        service = VoucherService(db)
        voucher = service.update_voucher(
            voucher_id=voucher_id,
            value_cents=voucher_data.value_cents,
            reason=voucher_data.reason,
            description=voucher_data.description,
            performed_by_user_id=current_user.id,
        )
        logger.info(f"[ADMIN] Updated voucher {voucher_id} by user {current_user.id}")
        return VoucherResponse.from_orm(voucher)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"[ADMIN] Error updating voucher {voucher_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating voucher: {str(e)}",
        )


@admin_router.get("/by-number/{voucher_number}", response_model=VoucherResponse)
@admin_router.get("/by-number/{voucher_number}/", response_model=VoucherResponse)
async def get_voucher_by_number(
    voucher_number: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get voucher details by voucher number (e.g., V-001)"""
    user_id = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER).id
    
    try:
        repo = VoucherRepository(db)
        voucher = repo.get_by_number(voucher_number)
        
        if not voucher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Voucher {voucher_number} not found",
            )
        
        return VoucherResponse.from_orm(voucher)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[ADMIN] Error getting voucher {voucher_number}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting voucher: {str(e)}",
        )



# ============================================================================
# KASSE ROUTES - /api/transactions/voucher
# ============================================================================


@kasse_router.post(
    "/validate",
    response_model=VoucherValidationResponse,
)
@kasse_router.post(
    "/validate/",
    response_model=VoucherValidationResponse,
)
async def validate_voucher(
    request_data: VoucherValidateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Validate a voucher before redemption (displays info + validity)"""
    user_id = get_user_id(request, db)
    
    try:
        service = VoucherService(db)
        validation_result = service.validate_voucher(
            request_data.voucher_number,
            cart_total_cents=request_data.cart_total_cents,
        )
        
        logger.info(
            f"[KASSE] Validated voucher {request_data.voucher_number} "
            f"by user {user_id}: valid={validation_result['valid']}"
        )
        
        return VoucherValidationResponse(
            valid=validation_result["valid"],
            voucher_number=validation_result["voucher_number"],
            voucher_type=validation_result["voucher_type"],
            value_cents=validation_result["value_cents"],
            status=validation_result["status"],
            message=validation_result["message"],
            reason=validation_result.get("reason"),
            applicable_amount_cents=validation_result.get("applicable_amount_cents", 0),
            remaining_value_cents=validation_result.get("remaining_value_cents", 0),
            covers_cart_total=validation_result.get("covers_cart_total", False),
        )
    except Exception as e:
        logger.error(
            f"[KASSE] Error validating voucher {request_data.voucher_number}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating voucher: {str(e)}",
        )


@kasse_router.post(
    "/redeem",
    response_model=VoucherRedeemResponse,
    status_code=status.HTTP_201_CREATED,
)
@kasse_router.post(
    "/redeem/",
    response_model=VoucherRedeemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def redeem_voucher(
    request_data: VoucherRedeemRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Redeem a voucher
    
    - GIFT voucher: Creates a negative transaction (loss recording), value becomes 0 in balance
    - PREPAID voucher: Creates a null-amount transaction (0 cents), but logs payment method for audit
    """
    user_id = get_user_id(request, db)
    
    try:
        service = VoucherService(db)
        repo = VoucherRepository(db)
        
        # First validate
        voucher = repo.get_by_number(request_data.voucher_number)
        if not voucher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Voucher {request_data.voucher_number} not found",
            )
        
        if voucher.status == VoucherStatus.REDEEMED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Voucher {request_data.voucher_number} has already been redeemed",
            )

        # Perform redemption based on voucher type
        if voucher.voucher_type == VoucherType.GIFT:
            transaction = service.redeem_gift_voucher(
                voucher_number=request_data.voucher_number,
                redeemed_by=user_id,
                member_id=request_data.member_id,
            )
            logger.info(
                f"[KASSE] Redeemed GIFT voucher {request_data.voucher_number} "
                f"(value: {voucher.value_cents} cents) by user {user_id}, "
                f"transaction_id={transaction.id}"
            )
        elif voucher.voucher_type == VoucherType.PREPAID:
            transaction = service.redeem_prepaid_voucher(
                voucher_number=request_data.voucher_number,
                redeemed_by=user_id,
                member_id=request_data.member_id,
            )
            logger.info(
                f"[KASSE] Redeemed PREPAID voucher {request_data.voucher_number} "
                f"(value: {voucher.value_cents} cents) by user {user_id}, "
                f"transaction_id={transaction.id}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown voucher type: {voucher.voucher_type}",
            )
        
        return VoucherRedeemResponse(
            success=True,
            voucher_number=request_data.voucher_number,
            voucher_type=voucher.voucher_type,
            value_cents=voucher.value_cents,
            transaction_id=transaction.id,
            message=f"Voucher {request_data.voucher_number} successfully redeemed",
            applied_amount_cents=voucher.redeemed_amount_cents or voucher.value_cents,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[KASSE] Error redeeming voucher {request_data.voucher_number}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error redeeming voucher: {str(e)}",
        )
