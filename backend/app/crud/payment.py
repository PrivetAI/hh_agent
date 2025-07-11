from sqlalchemy.orm import Session
from sqlalchemy import update
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
import logging

from ..models.db import Payment, LetterGeneration
from ..models.schemas import PaymentCreate
from ..services.payment.receipt_validator import ReceiptValidator

logger = logging.getLogger(__name__)

class PaymentCRUD:
    # Пакеты кредитов
    PACKAGES = {
        "50": {"credits": 50, "amount": Decimal("149")},
        "100": {"credits": 100, "amount": Decimal("249")},
        "200": {"credits": 200, "amount": Decimal("399")}
    }
    
    @staticmethod
    def get_receipt_data(package: str, user_email: Optional[str] = None) -> Dict[str, Any]:
        """Generate receipt data for Robokassa fiscalization according to 54-FZ"""
        package_info = PaymentCRUD.PACKAGES.get(package)
        if not package_info:
            raise ValueError(f"Invalid package: {package}")
        
        # Генерируем чек через валидатор
        receipt = ReceiptValidator.generate_receipt(
            package_name=f"Пакет {package}",
            credits=package_info["credits"],
            amount=float(package_info["amount"]),
            user_email=user_email,
            sno="usn_income"  # УСН доходы
        )
        
        # Валидируем чек
        errors = ReceiptValidator.validate_receipt(receipt)
        if errors:
            logger.error(f"Receipt validation errors: {errors}")
            # В продакшене можно кинуть исключение
            # raise ValueError(f"Invalid receipt: {', '.join(errors)}")
        else:
            logger.info(f"Receipt validated successfully for package {package}")
        
        return receipt
    
    @staticmethod
    def create(db: Session, user_id: UUID, package: str) -> Payment:
        package_info = PaymentCRUD.PACKAGES.get(package)
        if not package_info:
            raise ValueError("Invalid package")
        
        payment = Payment(
            user_id=user_id,
            amount=package_info["amount"],
            credits=package_info["credits"],
            status="pending"
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment
    
    @staticmethod
    def get_by_id(db: Session, payment_id: int) -> Optional[Payment]:  # Changed from UUID to int
        return db.query(Payment).filter(Payment.id == payment_id).first()
    
    @staticmethod
    def update_status(db: Session, payment_id: int, status: str, payment_ext_id: str = None) -> Optional[Payment]:  # Changed from UUID to int
        values = {"status": status}
        if payment_ext_id:
            values["payment_id"] = payment_ext_id
            
        db.execute(
            update(Payment)
            .where(Payment.id == payment_id)
            .values(**values)
        )
        db.commit()
        return PaymentCRUD.get_by_id(db, payment_id)
    
    @staticmethod
    def get_user_payments(db: Session, user_id: UUID) -> List[Payment]:
        return db.query(Payment).filter(
            Payment.user_id == user_id
        ).order_by(Payment.created_at.desc()).all()

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
        return generation
    
    @staticmethod
    def get_user_history(db: Session, user_id: UUID, limit: int = 50) -> List[LetterGeneration]:
        """Get user's letter generation history"""
        return db.query(LetterGeneration).filter(
            LetterGeneration.user_id == user_id
        ).order_by(LetterGeneration.created_at.desc()).limit(limit).all()