from fastapi import APIRouter, HTTPException, Depends, Request, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.core import get_db
from app.schemas import (
    VoucherCreateGift,
    VoucherCreatePrepaid,
    VoucherValidateRequest,
    VoucherRedeemRequest,
    VoucherValidationResponse,
    VoucherResponse,
    VoucherListResponse,
    VoucherRedeemResponse,
)
from app.services import VoucherService
from app.repositories import VoucherRepository
from app.models import Transaction, TransactionType, PaymentMethod

logger = logging.getLogger(__name__)

# Two routers: one for admin, one for kasse
admin_router = APIRouter(prefix="/api/admin/vouchers", tags=["Admin - Vouchers"])
kasse_router = APIRouter(prefix="/api/transactions/voucher", tags=["Kasse - Voucher"])


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
    user_id = get_user_id(request)
    
    try:
        service = VoucherService(db)
        voucher = service.create_gift_voucher(
            value_cents=voucher_data.value_cents,
            reason=voucher_data.reason,
            created_by_user_id=user_id,
        )
        logger.info(
            f"[ADMIN] Created GIFT voucher {voucher.voucher_number} "
            f"(value: {voucher.value_cents} cents) by user {user_id}"
        )
        return voucher
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
    user_id = get_user_id(request)
    
    try:
        service = VoucherService(db)
        voucher = service.create_prepaid_voucher(
            value_cents=voucher_data.value_cents,
            created_by_user_id=user_id,
        )
        logger.info(
            f"[ADMIN] Created PREPAID voucher {voucher.voucher_number} "
            f"(value: {voucher.value_cents} cents) by user {user_id}"
        )
        return voucher
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
            all_vouchers = repo.get_all()
            total = len(all_vouchers)
            vouchers = all_vouchers[(page - 1) * page_size : page * page_size]
        
        total_pages = (total + page_size - 1) // page_size
        
        return VoucherListResponse(
            vouchers=[VoucherResponse.from_orm(v) for v in vouchers],
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
        validation_result = service.validate_voucher(request_data.voucher_number)
        
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
        
        if voucher.status == "REDEEMED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Voucher {request_data.voucher_number} has already been redeemed",
            )
        
        # Perform redemption based on voucher type
        if voucher.voucher_type == "GIFT":
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
        elif voucher.voucher_type == "PREPAID":
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
