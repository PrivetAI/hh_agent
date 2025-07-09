from sqlalchemy.orm import Session
from sqlalchemy import update
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
import logging

from ..models.db import Payment, LetterGeneration
from ..models.schemas import PaymentCreate

logger = logging.getLogger(__name__)

class PaymentCRUD:
    # Credit packages with Decimal for precision
    PACKAGES = {
        "50": {"credits": 50, "amount": Decimal("149.00")},
        "100": {"credits": 100, "amount": Decimal("249.00")},
        "200": {"credits": 200, "amount": Decimal("399.00")}
    }
    
    @staticmethod
    def create(db: Session, user_id: UUID, package: str) -> Payment:
        """Create a new payment record"""
        package_info = PaymentCRUD.PACKAGES.get(package)
        if not package_info:
            raise ValueError(f"Invalid package: {package}")
        
        try:
            payment = Payment(
                user_id=user_id,
                amount=package_info["amount"],
                credits=package_info["credits"],
                status="created"  # Start with 'created' status
            )
            db.add(payment)
            db.commit()
            db.refresh(payment) 
            
            logger.info(f"Payment created: {payment.id} for user {user_id}")
            return payment
            
        except Exception as e:
            logger.error(f"Failed to create payment: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_by_id(db: Session, payment_id: str) -> Optional[Payment]:
        """Get payment by ID"""
        try:
            return db.query(Payment).filter(Payment.id == UUID(payment_id)).first()
        except ValueError:
            logger.error(f"Invalid payment ID format: {payment_id}")
            return None
    
    @staticmethod
    def update_status(
        db: Session, 
        payment_id: UUID, 
        status: str, 
        payment_ext_id: Optional[str] = None
    ) -> Optional[Payment]:
        """Update payment status"""
        try:
            values = {"status": status}
            if payment_ext_id:
                values["payment_ext_id"] = payment_ext_id
                
            db.execute(
                update(Payment)
                .where(Payment.id == payment_id)
                .values(**values)
            )
            db.commit()
            
            logger.info(f"Payment {payment_id} status updated to {status}")
            return PaymentCRUD.get_by_id(db, str(payment_id))
            
        except Exception as e:
            logger.error(f"Failed to update payment status: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_user_payments(db: Session, user_id: UUID, limit: int = 50) -> List[Payment]:
        """Get user's payment history"""
        try:
            return db.query(Payment).filter(
                Payment.user_id == user_id
            ).order_by(Payment.created_at.desc()).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Failed to get user payments: {e}")
            return []

class LetterGenerationCRUD:
    @staticmethod
    def save_letter_generation(
        db: Session, 
        user_id: UUID, 
        vacancy_id: str, 
        vacancy_title: str,
        resume_id: str, 
        letter_content: str,
        prompt_filename: str,
        ai_model: str
    ) -> LetterGeneration:
        """Save generated letter to history"""
        try:
            generation = LetterGeneration(
                user_id=user_id,
                vacancy_id=vacancy_id,
                vacancy_title=vacancy_title,
                resume_id=resume_id,
                letter_content=letter_content,
                prompt_filename=prompt_filename,
                ai_model=ai_model
            )
            db.add(generation)
            db.commit()
            db.refresh(generation)
            
            logger.info(f"Letter generation saved for user {user_id}")
            return generation
            
        except Exception as e:
            logger.error(f"Failed to save letter generation: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_user_history(db: Session, user_id: UUID, limit: int = 50) -> List[LetterGeneration]:
        """Get user's letter generation history"""
        try:
            return db.query(LetterGeneration).filter(
                LetterGeneration.user_id == user_id
            ).order_by(LetterGeneration.created_at.desc()).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Failed to get user history: {e}")
            return []