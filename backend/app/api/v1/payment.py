from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any
import logging
import traceback
import time

from ...api.deps import get_current_user, get_db
from ...crud.payment import PaymentCRUD
from ...crud.user import UserCRUD
from ...models.db import User
from ...models.schemas import PaymentCreate
from ...core.config import settings
from ...services.payment.robokassa import RobokassaService
from ...services.payment.receipt_generator import ReceiptGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payment", tags=["payment"])
payment_service = RobokassaService()
receipt_generator = ReceiptGenerator()
@router.post("/create")
async def create_payment(
    payment_data: PaymentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create payment for credits package"""
    start_time = time.time()
    logger.info(f"=== PAYMENT CREATE START === User: {user.id}, Package: {payment_data.package}")

    try:
        logger.info("Checking database connection...")
        db.execute(text("SELECT 1"))
        logger.info("Database connection OK")

        logger.info("Creating payment record...")
        payment = PaymentCRUD.create(db, user.id, payment_data.package)
        logger.info(f"Payment record created with ID: {payment.id}")

        logger.info(f"Getting package info for: {payment_data.package}")
        package_info = PaymentCRUD.PACKAGES.get(payment_data.package)
        if not package_info:
            logger.error(f"Invalid package requested: {payment_data.package}")
            raise HTTPException(status_code=400, detail="Invalid package")
        logger.info(f"Package info retrieved: {package_info}")

        logger.info("Creating payment URL...")
        logger.info(f"ROBOKASSA_TEST_MODE: {settings.ROBOKASSA_TEST_MODE}")
        
        try:
            # Генерация чека для продакшн режима
            receipt_data = None
            if not settings.ROBOKASSA_TEST_MODE:
                receipt_data = receipt_generator.generate_receipt(
                    credits=package_info["credits"],
                    amount=float(package_info["amount"]),
                    user_email=user.email
                )
                logger.info(f"Receipt data generated for production mode with email: {user.email}")
            
            # ВАЖНО: Всегда используем русское описание
            description = f"Покупка токенов для генерации сопроводительных писем"
            
            payment_url = payment_service.create_payment_link(
                payment_id=payment.id,
                amount=float(package_info["amount"]),
                description=description,  # Русское описание
                user_email=None if settings.ROBOKASSA_TEST_MODE else user.email,
                receipt_data=receipt_data
            )
            logger.info(f"Payment URL created successfully")

            logger.info("Updating payment status to pending...")
            PaymentCRUD.update_status(db, payment.id, "pending")
            logger.info(f"Payment {payment.id} status updated to pending")

            response_data = {
                "payment_id": payment.id,
                "payment_url": payment_url,
                "amount": float(package_info["amount"]),
                "credits": package_info["credits"]
            }

            elapsed_time = time.time() - start_time
            logger.info(f"=== PAYMENT CREATE SUCCESS === ID: {payment.id}, Time: {elapsed_time:.2f}s")

            return response_data

        except Exception as e:
            logger.error(f"Failed to create payment URL for payment {payment.id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            try:
                PaymentCRUD.update_status(db, payment.id, "failed")
                logger.info(f"Payment {payment.id} marked as failed")
            except Exception as update_error:
                logger.error(f"Failed to update payment status: {update_error}")

            raise HTTPException(status_code=500, detail=f"Payment creation failed: {str(e)}")

    except HTTPException:
        elapsed_time = time.time() - start_time
        logger.error(f"=== PAYMENT CREATE HTTP ERROR === Time: {elapsed_time:.2f}s")
        raise
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"=== PAYMENT CREATE UNEXPECTED ERROR === {e}, Time: {elapsed_time:.2f}s")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    
@router.get("/result")
async def payment_result(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle payment result from Robokassa"""
    logger.info("=== PAYMENT RESULT START ===")

    try:
        params = dict(request.query_params)
        logger.info(f"Payment result parameters received: {list(params.keys())}")
        
        for key, value in params.items():
            if key.lower() != 'signaturevalue':
                logger.info(f"Parameter {key}: {value}")

        logger.info("Verifying payment result signature...")
        if not payment_service.verify_payment_result(params):
            logger.error("Invalid signature in payment result")
            raise HTTPException(status_code=400, detail="Invalid signature")
        logger.info("Payment result signature verified successfully")

        inv_id = params.get("InvId")
        if not inv_id:
            logger.error("No InvId in payment result")
            raise HTTPException(status_code=400, detail="No InvId in result")
        try:
            payment_id = int(inv_id)
        except ValueError:
            logger.error(f"Invalid InvId format: {inv_id}")
            raise HTTPException(status_code=400, detail="Invalid InvId format")
        logger.info(f"Processing payment result for payment ID: {payment_id}")

        payment = PaymentCRUD.get_by_id(db, payment_id)
        if not payment:
            logger.error(f"Payment not found: {payment_id}")
            raise HTTPException(status_code=404, detail="Payment not found")
        logger.info(f"Payment found: {payment_id}, current status: {payment.status}")

        if payment.status == "success":
            logger.info(f"Payment {payment_id} already processed successfully")
            return f"OK{payment_id}"

        logger.info(f"Updating payment {payment_id} status to success...")
        PaymentCRUD.update_status(db, payment_id, "success")
        logger.info(f"Payment {payment_id} status updated to success")
        
        logger.info(f"Adding {payment.credits} credits to user {payment.user_id}...")
        UserCRUD.add_credits(db, payment.user_id, payment.credits)
        logger.info(f"Successfully added {payment.credits} credits to user {payment.user_id}")

        logger.info(f"=== PAYMENT RESULT SUCCESS === Payment ID: {payment_id}")
        return f"OK{payment_id}"

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"=== PAYMENT RESULT ERROR === {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/success")
async def payment_success(request: Request):
    """Handle success redirect from Robokassa"""
    logger.info("=== PAYMENT SUCCESS REDIRECT ===")
    params = dict(request.query_params)
    logger.info(f"Payment success parameters: {list(params.keys())}")
    
    try:
        if payment_service.verify_success_url(params):
            logger.info("Success URL signature verified")
        else:
            logger.warning("Success URL signature verification failed")
    except Exception as e:
        logger.warning(f"Error verifying success URL signature: {e}")
    
    return {"redirect": f"{settings.FRONTEND_URL}/?payment=success"}


@router.get("/fail")
async def payment_fail(request: Request):
    """Handle fail redirect from Robokassa"""
    logger.info("=== PAYMENT FAIL REDIRECT ===")
    params = dict(request.query_params)
    logger.info(f"Payment fail parameters: {list(params.keys())}")
    return {"redirect": f"{settings.FRONTEND_URL}/?payment=fail"}


@router.get("/packages")
async def get_packages():
    """Get available credit packages"""
    logger.info("=== GET PACKAGES REQUEST ===")
    packages = [
        {"id": "50", "credits": 50, "amount": 149, "currency": "RUB", "popular": False},
        {"id": "100", "credits": 100, "amount": 249, "currency": "RUB", "popular": False},
        {"id": "200", "credits": 200, "amount": 399, "currency": "RUB", "popular": True},
    ]
    logger.info(f"Returning {len(packages)} available packages")
    return packages


@router.get("/history")
async def payment_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's payment history"""
    logger.info(f"=== PAYMENT HISTORY REQUEST === User: {user.id}")
    try:
        payments = PaymentCRUD.get_user_payments(db, user.id)
        logger.info(f"Retrieved {len(payments)} payments for user {user.id}")
        return payments
    except Exception as e:
        logger.error(f"Error retrieving payment history for user {user.id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payment history")