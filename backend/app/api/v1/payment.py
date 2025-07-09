from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
import hashlib

from ...api.deps import get_current_user, get_db
from ...crud.payment import PaymentCRUD
from ...crud.user import UserCRUD
from ...models.db import User
from ...models.schemas import PaymentCreate
from ...core.config import settings
from ...services.payment.robokassa import RobokassaPaymentService

router = APIRouter(prefix="/api/payment", tags=["payment"])
payment_service = RobokassaPaymentService()

@router.post("/create")
async def create_payment(
    payment_data: PaymentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create payment for credits package"""
    # Create payment record
    payment = PaymentCRUD.create(db, user.id, payment_data.package)
    
    # Get package info
    package_info = PaymentCRUD.PACKAGES.get(payment_data.package)
    if not package_info:
        raise HTTPException(status_code=400, detail="Invalid package")
    
    # Create payment URL for Robokassa
    try:
        payment_url = payment_service.create_payment_link(
            payment_id=payment.id,  # Теперь это int
            amount=float(package_info["amount"]),
            description=f"Покупка {package_info['credits']} токенов",
            user_email=user.email,
            receipt_data=PaymentCRUD.get_receipt_data(payment_data.package)
        )
        
        # Update payment status to pending
        PaymentCRUD.update_status(db, payment.id, "pending")
        
        return {
            "payment_id": payment.id,  # Убрали str() преобразование
            "payment_url": payment_url,
            "amount": float(package_info["amount"]),
            "credits": package_info["credits"]
        }
        
    except Exception as e:
        # Mark payment as failed
        PaymentCRUD.update_status(db, payment.id, "failed")
        raise HTTPException(status_code=500, detail=f"Payment creation failed: {str(e)}")

@router.get("/result")
async def payment_result(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle payment result from Robokassa"""
    try:
        # Get parameters from query string
        params = dict(request.query_params)
        
        # Verify payment result
        if not payment_service.verify_payment_result(params):
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Get payment by InvId
        payment_id = params.get("InvId")
        if not payment_id:
            raise HTTPException(status_code=400, detail="No InvId in result")
        
        # Преобразуем в int
        try:
            payment_id = int(payment_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid InvId format")
        
        payment = PaymentCRUD.get_by_id(db, payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Update payment status
        PaymentCRUD.update_status(db, payment.id, "success")
        
        # Add credits to user
        UserCRUD.add_credits(db, payment.user_id, payment.credits)
        
        # Return success response for Robokassa
        return f"OK{payment_id}"
        
    except Exception as e:
        print(f"Payment result error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/success")
async def payment_success(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle success redirect from Robokassa"""
    try:
        # Get parameters from query string
        params = dict(request.query_params)
        
        # Verify success signature
        if not payment_service.verify_success_url(params):
            # Redirect to frontend with error
            return {"redirect": f"{settings.FRONTEND_URL}/?payment=error"}
        
        # Redirect to frontend with success
        return {"redirect": f"{settings.FRONTEND_URL}/?payment=success"}
        
    except Exception as e:
        print(f"Payment success error: {e}")
        return {"redirect": f"{settings.FRONTEND_URL}/?payment=error"}

@router.get("/fail")
async def payment_fail(request: Request):
    """Handle fail redirect from Robokassa"""
    # Redirect to frontend with error
    return {"redirect": f"{settings.FRONTEND_URL}/?payment=fail"}

@router.get("/packages")
async def get_packages():
    """Get available credit packages"""
    return [
        {
            "id": "50",
            "credits": 50,
            "amount": 149,
            "currency": "RUB",
            "popular": False
        },
        {
            "id": "100",
            "credits": 100,
            "amount": 249,
            "currency": "RUB",
            "popular": False
        },
        {
            "id": "200",
            "credits": 200,
            "amount": 399,
            "currency": "RUB",
            "popular": True
        }
    ]

@router.get("/history")
async def payment_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's payment history"""
    payments = PaymentCRUD.get_user_payments(db, user.id)
    return payments