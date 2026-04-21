from fastapi import APIRouter, HTTPException, Depends, Request, status, Query
from sqlalchemy.orm import Session
import logging
from pydantic import BaseModel, Field

from app.core import get_db
from app.core.auth import require_roles, resolve_confirmation_user
from app.schemas import (
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
from app.services import VoucherService
from app.repositories import VoucherRepository
from app.models import VoucherStatus, VoucherType, UserRole

logger = logging.getLogger(__name__)

# Two routers: one for admin, one for kasse
admin_router = APIRouter(prefix="/api/admin/vouchers", tags=["Admin - Vouchers"])
kasse_router = APIRouter(prefix="/api/transactions/voucher", tags=["Kasse - Voucher"])


class ClubAccountTopUpRequest(BaseModel):
    amount_cents: int = Field(..., ge=1)
    auth_username: str | None = Field(default=None, min_length=1, max_length=50)
    auth_password: str = Field(..., min_length=1)


def get_user_id(request: Request) -> int:
    """Extract and validate user_id from session"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user_id


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
    user_id = current_user.id
    resolve_confirmation_user(
        db,
        current_user,
        voucher_data.auth_password,
        username=voucher_data.auth_username,
        allow_top_admin_override=True,
    )
    
    try:
        service = VoucherService(db)
        voucher = service.create_gift_voucher(
            value_cents=voucher_data.value_cents,
            reason=voucher_data.reason,
            created_by_user_id=user_id,
        )
        logger.debug(f"[DEBUG] Voucher object after create: id={voucher.id}, voucher_code={voucher.voucher_code}")
        
        response = VoucherResponse.from_orm(voucher)
        
        logger.debug(f"[DEBUG] Response object: voucher_code={response.voucher_code}")
        logger.info(
            f"[ADMIN] Created GIFT voucher {voucher.voucher_code} "
            f"(value: {voucher.value_cents} cents) by user {user_id}"
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
    response_model=VoucherResponse,
    status_code=status.HTTP_201_CREATED,
)
@admin_router.post(
    "/prepaid/",
    response_model=VoucherResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_prepaid_voucher(
    voucher_data: VoucherCreatePrepaid,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a prepaid voucher (purchased now, redeemed later)"""
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    user_id = current_user.id
    resolve_confirmation_user(
        db,
        current_user,
        voucher_data.auth_password,
        username=voucher_data.auth_username,
        allow_top_admin_override=True,
    )
    
    try:
        service = VoucherService(db)
        voucher = service.create_prepaid_voucher(
            value_cents=voucher_data.value_cents,
            created_by_user_id=user_id,
        )
        logger.debug(f"[DEBUG] Voucher object after create: id={voucher.id}, voucher_code={voucher.voucher_code}")
        
        response = VoucherResponse.from_orm(voucher)
        
        logger.debug(f"[DEBUG] Response object: voucher_code={response.voucher_code}")
        logger.info(
            f"[ADMIN] Created PREPAID voucher {voucher.voucher_code} "
            f"(value: {voucher.value_cents} cents) by user {user_id}"
        )
        return response
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
    user_id = get_user_id(request)
    
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


@admin_router.get("/club-account")
@admin_router.get("/club-account/")
async def get_club_account(
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.ADMIN)
    return VoucherService(db).get_club_account_summary()


@admin_router.post("/club-account/topup")
@admin_router.post("/club-account/topup/")
async def top_up_club_account(
    payload: ClubAccountTopUpRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = require_roles(request, db, UserRole.ADMIN)
    resolve_confirmation_user(
        db,
        current_user,
        payload.auth_password,
        username=payload.auth_username,
        allow_top_admin_override=True,
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
    user_id = get_user_id(request)
    
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
    user_id = get_user_id(request)

    try:
        service = VoucherService(db)
        voucher = service.update_voucher(
            voucher_id=voucher_id,
            value_cents=voucher_data.value_cents,
            reason=voucher_data.reason,
            description=voucher_data.description,
        )
        logger.info(f"[ADMIN] Updated voucher {voucher_id} by user {user_id}")
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
    user_id = get_user_id(request)
    
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
    user_id = get_user_id(request)
    
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
    user_id = get_user_id(request)
    
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
