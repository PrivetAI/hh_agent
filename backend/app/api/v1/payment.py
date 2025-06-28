from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any

from ...api.deps import get_current_user, get_db
from ...crud.payment import PaymentCRUD
from ...crud.user import UserCRUD
from ...models.db import User
from ...models.schemas import PaymentCreate
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
    
    # Create payment in Tinkoff
    try:
        tinkoff_response = await payment_service.create_payment(
            payment_id=payment.id,
            amount=int(package_info["amount"]),
            user_email=user.email or f"{user.hh_user_id}@hh-assistant.ru"
        )
        
        # Update payment with Tinkoff payment ID
        PaymentCRUD.update_status(
            db, 
            payment.id, 
            "pending", 
            tinkoff_response.get("PaymentId")
        )
        
        return {
            "payment_id": str(payment.id),
            "payment_url": tinkoff_response.get("PaymentURL"),
            "amount": float(package_info["amount"]),
            "credits": package_info["credits"]
        }
        
    except Exception as e:
        # Mark payment as failed
        PaymentCRUD.update_status(db, payment.id, "failed")
        raise HTTPException(status_code=500, detail=f"Payment creation failed: {str(e)}")

@router.post("/webhook")
async def payment_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle payment webhook from Tinkoff"""
    try:
        data = await request.json()
        
        # Verify webhook signature
        if not payment_service.verify_webhook(data):
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Get payment by order ID
        payment_id = data.get("OrderId")
        if not payment_id:
            raise HTTPException(status_code=400, detail="No OrderId in webhook")
        
        payment = PaymentCRUD.get_by_id(db, payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Update payment status
        status = data.get("Status")
        if status == "CONFIRMED":
            # Payment successful
            PaymentCRUD.update_status(db, payment.id, "success")
            
            # Add credits to user
            UserCRUD.add_credits(db, payment.user_id, payment.credits)
            
        elif status in ["REJECTED", "REFUNDED", "PARTIAL_REFUNDED"]:
            # Payment failed
            PaymentCRUD.update_status(db, payment.id, "failed")
        
        return {"status": "ok"}
        
    except Exception as e:
        # Log error but return 200 to avoid retries
        print(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

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

