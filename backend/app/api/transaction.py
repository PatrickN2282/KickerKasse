from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from datetime import date, datetime
from sqlalchemy import func, desc
from pydantic import BaseModel
from typing import Optional
import logging

from app.core import get_db
from app.schemas import TransactionCreate, TransactionResponse, TransactionStornoCreate, ZBonResponse
from app.services import TransactionService, ProductService, ZBonService, EmailService
from app.services.zbon_html_exporter import ZBonHTMLExporter
from app.repositories import MemberRepository, ProductRepository
from app.models import PaymentMethod, Transaction, ZBonHistory

from app.services import SchedulerService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


# Request models
class CashCountRequest(BaseModel):
    coins: Optional[dict] = None  # {"0.01": 5, "0.02": 3, ...}
    notes: Optional[dict] = None  # {"5": 2, "10": 1, ...}


class ZBonGenerateRequest(BaseModel):
    date: Optional[str] = None  # YYYY-MM-DD, defaults to today
    cash_count: Optional[CashCountRequest] = None
    report_type: str = "full-zbon"  # "full-zbon", "short-zbon", or "daily-report"


class ZBonEmailRequest(BaseModel):
    date: Optional[str] = None  # YYYY-MM-DD, defaults to today
    recipient: Optional[str] = None  # defaults to EMAIL_RECIPIENT_ZBON
    report_type: str = "full-zbon"  # "full-zbon", "short-zbon", or "daily-report"
    include_cash_count: bool = False


@router.get("/next-receipt-number")
@router.get("/next-receipt-number/")
async def get_next_receipt_number(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get the next receipt number"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
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
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    print(f"[API] Creating sale transaction for user {user_id}: payment_method={transaction_data.payment_method}, member_id={transaction_data.member_id}, items={len(transaction_data.items)}")
    
    # Validate items exist and have stock
    product_repo = ProductRepository(db)
    for item in transaction_data.items:
        product = product_repo.get_by_id(item.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found",
            )
        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unzureichender Bestand für Produkt {product.name}",
            )
    
    # Check member balance if paying with balance
    if transaction_data.payment_method == "BALANCE":
        if not transaction_data.member_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Member ID required for balance payment",
            )
        
        member_repo = MemberRepository(db)
        member = member_repo.get_by_id(transaction_data.member_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found",
            )
        
        # Calculate total amount
        total_amount = 0
        for item in transaction_data.items:
            total_amount += item.unit_price_cents * item.quantity
        
        if member.balance_cents < total_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient member balance",
            )
    
    service = TransactionService(db)
    
    # Calculate total amount
    total_amount = sum(item.unit_price_cents * item.quantity for item in transaction_data.items)
    
    # Create transaction
    items_data = [item.dict() for item in transaction_data.items]
    transaction = service.create_sale_transaction(
        user_id=user_id,
        total_amount_cents=total_amount,
        payment_method=transaction_data.payment_method,
        member_id=transaction_data.member_id,
        items=items_data,
    )
    
    # Process payment
    member_repo = MemberRepository(db)
    service.process_sale_payment(transaction, member_repo)
    
    # Deduct stock for each item
    for item in transaction.items:
        product_repo.deduct_stock(item.product_id, item.quantity)
    
    # Final commit to ensure everything is persisted
    db.commit()
    db.refresh(transaction)
    
    print(f"[API] Sale transaction created successfully: id={transaction.id}, receipt_number={transaction.receipt_number}, amount={total_amount}")
    
    return transaction


@router.post("/storno", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
@router.post("/storno/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_storno(
    storno_data: TransactionStornoCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a storno (reversal) transaction"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    service = TransactionService(db)
    
    try:
        storno = service.create_storno_transaction(
            storno_data.transaction_id,
            user_id,
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
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
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
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
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
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
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


@router.get("/revenue-stats")
@router.get("/revenue-stats/")
async def get_revenue_stats(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get revenue statistics"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
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
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
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
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
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
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
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
            detail=f"Error generating Z-Bon: {str(e)}",
        )


@router.post("/zbon/send-email")
@router.post("/zbon/send-email/")
async def send_zbon_email(
    email_req: ZBonEmailRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Send Z-Bon via email"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    try:
        from app.core.config import settings
        
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
        
        recipient = email_req.recipient or settings.EMAIL_RECIPIENT_ZBON
        
        # Generate Z-Bon first
        zbon_service = ZBonService(db)
        zbon_result = zbon_service.generate_zbon(
            target_date=target_date,
            include_cash_count=None,
            report_type=email_req.report_type,
        )
        
        # Send email
        success = EmailService.send_zbon_email(
            recipient=recipient,
            zbon_content=zbon_result["content"],
            date=target_date.isoformat(),
        )
        
        if not success:
            raise Exception("Email sending failed")
        
        return {
            "status": "success",
            "message": f"Z-Bon sent to {recipient}",
            "date": target_date.isoformat(),
            "type": email_req.report_type,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending Z-Bon via email: {str(e)}",
        )


@router.get("/zbon/html")
@router.get("/zbon/html/")
async def get_zbon_html(
    report_date: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Get Z-Bon as HTML for preview"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    try:
        from app.services.zbon_html_exporter import ZBonHTMLExporter
        
        target_date = None
        if report_date:
            target_date = datetime.strptime(report_date, "%Y-%m-%d").date()
        else:
            target_date = date.today()
        
        # Generate Z-Bon data
        zbon_service = ZBonService(db)
        transactions = db.query(Transaction).filter(
            func.date(Transaction.created_at) == target_date
        ).all()
        
        stats = zbon_service._calculate_stats(transactions)
        meta = zbon_service._collect_meta(target_date, transactions)
        product_breakdown = zbon_service._aggregate_by_product(transactions)
        category_breakdown = zbon_service._aggregate_by_category(transactions)
        customer_breakdown = zbon_service._aggregate_by_customer(transactions)
        customer_group_breakdown = zbon_service._aggregate_by_customer_group(transactions)
        storno_details = zbon_service._get_storno_details(transactions)
        
        # Get last Z-Bon number
        last_zbon = db.query(ZBonHistory).filter(
            ZBonHistory.business_date < target_date
        ).order_by(desc(ZBonHistory.sequence_number)).first()
        seq_number = (last_zbon.sequence_number + 1) if last_zbon else 1
        
        # Render HTML
        from sqlalchemy import func
        from app.models import Transaction, ZBonHistory
        
        html = ZBonHTMLExporter.render_html(
            seq_number=seq_number,
            business_date=meta['business_date'],
            created_at=meta['report_generated_at'],
            period_start=meta['first_tx_time'],
            period_end=meta['last_tx_time'],
            receipt_min=meta['receipt_min'],
            receipt_max=meta['receipt_max'],
            cash_sales_count=stats['cash_sales_count'],
            cash_sales_net=stats['cash_sales_total'],
            cash_sales_tax=0.0,
            cash_sales_gross=stats['cash_sales_total'],
            balance_sales_count=stats['balance_sales_count'],
            balance_sales_net=stats['balance_sales_total'],
            balance_sales_tax=0.0,
            balance_sales_gross=stats['balance_sales_total'],
            recharge_count=stats['recharge_count'],
            recharge_total=stats['recharge_total'],
            total_items_count=stats['cash_sales_count'] + stats['balance_sales_count'],
            total_net=stats['cash_sales_total'] + stats['balance_sales_total'],
            total_tax=0.0,
            total_gross=stats['cash_sales_total'] + stats['balance_sales_total'] + stats['recharge_total'],
            cash_revenue=stats['cash_sales_total'] + stats['recharge_total'],
            guthaben_net=stats['balance_sales_total'],
            guthaben_gross=stats['balance_sales_total'],
            total_revenue=stats['gross_revenue_cash'] + stats['gross_revenue_balance'],
            categories_breakdown=category_breakdown,
            customer_groups=customer_group_breakdown,
            customers=customer_breakdown,
            stornos=storno_details,
        )
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating Z-Bon HTML: {str(e)}",
        )


@router.get("/zbon/pdf")
@router.get("/zbon/pdf/")
async def get_zbon_pdf(
    report_date: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Download Z-Bon as PDF"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    try:
        from app.services.zbon_html_exporter import ZBonHTMLExporter
        from fastapi.responses import FileResponse
        from sqlalchemy import func
        from app.models import Transaction, ZBonHistory
        
        target_date = None
        if report_date:
            target_date = datetime.strptime(report_date, "%Y-%m-%d").date()
        else:
            target_date = date.today()
        
        # Generate Z-Bon data (same as HTML endpoint)
        zbon_service = ZBonService(db)
        transactions = db.query(Transaction).filter(
            func.date(Transaction.created_at) == target_date
        ).all()
        
        stats = zbon_service._calculate_stats(transactions)
        meta = zbon_service._collect_meta(target_date, transactions)
        product_breakdown = zbon_service._aggregate_by_product(transactions)
        category_breakdown = zbon_service._aggregate_by_category(transactions)
        customer_breakdown = zbon_service._aggregate_by_customer(transactions)
        customer_group_breakdown = zbon_service._aggregate_by_customer_group(transactions)
        storno_details = zbon_service._get_storno_details(transactions)
        
        # Get last Z-Bon number
        last_zbon = db.query(ZBonHistory).filter(
            ZBonHistory.business_date < target_date
        ).order_by(desc(ZBonHistory.sequence_number)).first()
        seq_number = (last_zbon.sequence_number + 1) if last_zbon else 1
        
        # Render HTML
        html = ZBonHTMLExporter.render_html(
            seq_number=seq_number,
            business_date=meta['business_date'],
            created_at=meta['report_generated_at'],
            period_start=meta['first_tx_time'],
            period_end=meta['last_tx_time'],
            receipt_min=meta['receipt_min'],
            receipt_max=meta['receipt_max'],
            cash_sales_count=stats['cash_sales_count'],
            cash_sales_net=stats['cash_sales_total'],
            cash_sales_tax=0.0,
            cash_sales_gross=stats['cash_sales_total'],
            balance_sales_count=stats['balance_sales_count'],
            balance_sales_net=stats['balance_sales_total'],
            balance_sales_tax=0.0,
            balance_sales_gross=stats['balance_sales_total'],
            recharge_count=stats['recharge_count'],
            recharge_total=stats['recharge_total'],
            total_items_count=stats['cash_sales_count'] + stats['balance_sales_count'],
            total_net=stats['cash_sales_total'] + stats['balance_sales_total'],
            total_tax=0.0,
            total_gross=stats['cash_sales_total'] + stats['balance_sales_total'] + stats['recharge_total'],
            cash_revenue=stats['cash_sales_total'] + stats['recharge_total'],
            guthaben_net=stats['balance_sales_total'],
            guthaben_gross=stats['balance_sales_total'],
            total_revenue=stats['gross_revenue_cash'] + stats['gross_revenue_balance'],
            categories_breakdown=category_breakdown,
            customer_groups=customer_group_breakdown,
            customers=customer_breakdown,
            stornos=storno_details,
        )
        
        # Export to PDF (with graceful fallback if WeasyPrint unavailable)
        try:
            pdf_bytes = ZBonHTMLExporter.export_pdf(html)
            
            filename = f"Z-Bon_{seq_number}_{target_date.strftime('%Y-%m-%d')}.pdf"
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
                You can still view the Z-Bon in HTML format above and print it from your browser using Ctrl+P.
            </div>
            {html}
            """
            return HTMLResponse(content=html_with_note)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating Z-Bon PDF: {str(e)}",
        )


@router.get("/scheduler/status")
@router.get("/scheduler/status/")
async def get_scheduler_status(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get current scheduler status (admin only)"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # Check if user is admin
    from app.repositories import UserRepository
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    status = SchedulerService.get_scheduler_status()
    return status


# ============================================================
# CASH MANAGEMENT ENDPOINTS
# ============================================================

class CashWithdrawalRequest(BaseModel):
    amount_cents: int  # Amount in cents
    reason: str  # Reason for withdrawal (e.g., "Abschöpfung Benny u.Carsten")


class CashDepositRequest(BaseModel):
    amount_cents: int  # Amount in cents
    reason: str  # Reason for deposit


@router.post("/cash/withdrawal")
@router.post("/cash/withdrawal/")
async def record_cash_withdrawal(
    withdrawal_req: CashWithdrawalRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Record a cash withdrawal (Entnahme)"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
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
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
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
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
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
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
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
