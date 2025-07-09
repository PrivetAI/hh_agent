from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
import hashlib
import logging
from decimal import Decimal

from ...api.deps import get_current_user, get_db
from ...crud.payment import PaymentCRUD
from ...crud.user import UserCRUD
from ...models.db import User
from ...models.schemas import PaymentCreate
from ...core.config import settings
from ...services.payment.robokassa import RobokassaPaymentService

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payment", tags=["payment"])
payment_service = RobokassaPaymentService()

@router.post("/create")
async def create_payment(
    payment_data: PaymentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create payment for credits package"""
    try:
        # Validate package exists
        package_info = PaymentCRUD.PACKAGES.get(payment_data.package)
        if not package_info:
            raise HTTPException(status_code=400, detail="Invalid package")
        
        # Create payment record
        payment = PaymentCRUD.create(db, user.id, payment_data.package)
        
        # Create payment URL for Robokassa
        payment_url = payment_service.create_payment_link(
            payment_id=payment.id,
            amount=float(package_info["amount"]),
            description=f"Покупка {package_info['credits']} токенов",
            user_email=user.email  # Pass user email for better UX
        )
        
        # Update payment status to pending
        PaymentCRUD.update_status(db, payment.id, "pending")
        
        logger.info(f"Payment created: {payment.id} for user {user.id}")
        
        return {
            "payment_id": str(payment.id),
            "payment_url": payment_url,
            "amount": float(package_info["amount"]),
            "credits": package_info["credits"]
        }
        
    except Exception as e:
        logger.error(f"Payment creation failed: {str(e)}")
        # Mark payment as failed if it was created
        if 'payment' in locals():
            PaymentCRUD.update_status(db, payment.id, "failed")
        raise HTTPException(status_code=500, detail="Payment creation failed")

@router.get("/result")
async def payment_result(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle payment result from Robokassa (Server-to-Server notification)"""
    try:
        # Get parameters from query string
        params = dict(request.query_params)
        
        logger.info(f"Payment result received: {params}")
        
        # Verify payment result signature
        if not payment_service.verify_payment_result(params):
            logger.error("Invalid signature in payment result")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Get payment by InvId
        payment_id = params.get("InvId")
        if not payment_id:
            logger.error("No InvId in payment result")
            raise HTTPException(status_code=400, detail="No InvId in result")
        
        payment = PaymentCRUD.get_by_id(db, payment_id)
        if not payment:
            logger.error(f"Payment not found: {payment_id}")
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Check if payment is already processed (prevent double processing)
        if payment.status == "success":
            logger.info(f"Payment already processed: {payment_id}")
            return f"OK{payment_id}"
        
        # Update payment status and add credits atomically
        with db.begin():
            PaymentCRUD.update_status(db, payment.id, "success")
            UserCRUD.add_credits(db, payment.user_id, payment.credits)
        
        logger.info(f"Payment processed successfully: {payment_id}")
        
        # Return success response for Robokassa
        return f"OK{payment_id}"
        
    except Exception as e:
        logger.error(f"Payment result error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/success")
async def payment_success(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle success redirect from Robokassa (User redirect)"""
    try:
        # Get parameters from query string
        params = dict(request.query_params)
        
        logger.info(f"Payment success redirect: {params}")
        
        # Verify success signature
        if not payment_service.verify_success_url(params):
            logger.error("Invalid signature in success URL")
            return {"redirect": f"{settings.FRONTEND_URL}/?payment=error"}
        
        # Get payment info for better UX
        payment_id = params.get("InvId")
        if payment_id:
            payment = PaymentCRUD.get_by_id(db, payment_id)
            if payment:
                logger.info(f"Payment success for user {payment.user_id}")
        
        # Redirect to frontend with success
        return {"redirect": f"{settings.FRONTEND_URL}/?payment=success"}
        
    except Exception as e:
        logger.error(f"Payment success error: {e}")
        return {"redirect": f"{settings.FRONTEND_URL}/?payment=error"}

@router.get("/fail")
async def payment_fail(request: Request):
    """Handle fail redirect from Robokassa"""
    params = dict(request.query_params)
    logger.info(f"Payment failed: {params}")
    
    # Optionally update payment status to failed
    payment_id = params.get("InvId")
    if payment_id:
        try:
            db = next(get_db())
            PaymentCRUD.update_status(db, payment_id, "failed")
        except Exception as e:
            logger.error(f"Failed to update payment status: {e}")
    
    return {"redirect": f"{settings.FRONTEND_URL}/?payment=fail"}

@router.get("/packages")
async def get_packages():
    """Get available credit packages"""
    packages = []
    for package_id, info in PaymentCRUD.PACKAGES.items():
        packages.append({
            "id": package_id,
            "credits": info["credits"],
            "amount": float(info["amount"]),
            "currency": "RUB",
            "popular": package_id == "200"  # Make 200 credits popular
        })
    return packages

@router.get("/history")
async def payment_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's payment history"""
    payments = PaymentCRUD.get_user_payments(db, user.id)
    
    # Format payments for frontend
    formatted_payments = []
    for payment in payments:
        formatted_payments.append({
            "id": str(payment.id),
            "amount": float(payment.amount),
            "credits": payment.credits,
            "status": payment.status,
            "created_at": payment.created_at.isoformat(),
            "updated_at": payment.updated_at.isoformat() if payment.updated_at else None
        })
    
    return formatted_payments

@router.get("/status/{payment_id}")
async def get_payment_status(
    payment_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payment status (for frontend polling)"""
    payment = PaymentCRUD.get_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Check if payment belongs to current user
    if payment.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": str(payment.id),
        "status": payment.status,
        "amount": float(payment.amount),
        "credits": payment.credits,
        "created_at": payment.created_at.isoformat()
    }
