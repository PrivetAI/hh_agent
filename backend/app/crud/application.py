from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from ..models.db import Application

class ApplicationCRUD:
    @staticmethod
    def create(
        db: Session, 
        user_id: UUID, 
        vacancy_id: str, 
        resume_id: str, 
        message: str,
        prompt_filename: Optional[str] = None,  # Новый параметр
        ai_model: Optional[str] = None  # Новый параметр
    ) -> Application:
        """Create new application with AI generation info"""
        application = Application(
            user_id=user_id,
            vacancy_id=vacancy_id,
            resume_id=resume_id,
            message=message,
            prompt_filename=prompt_filename,  # Сохраняем информацию о промпте
            ai_model=ai_model  # Сохраняем информацию о модели
        )
        db.add(application)
        db.commit()
        db.refresh(application)
        return application
    
    @staticmethod
    def get_user_application(db: Session, user_id: UUID, 
                            limit: int = 50) -> List[Application]:
        """Get all user's application"""
        return db.query(Application).filter(
            Application.user_id == user_id
        ).order_by(Application.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_vacancy_application(db: Session, vacancy_id: str) -> List[Application]:
        """Get all application for a vacancy"""
        return db.query(Application).filter(
            Application.vacancy_id == vacancy_id
        ).order_by(Application.created_at.desc()).all()
    
    @staticmethod
    def user_applied_to_vacancy(db: Session, user_id: UUID, 
                               vacancy_id: str) -> bool:
        """Check if user already applied to vacancy"""
        return db.query(Application).filter(
            Application.user_id == user_id,
            Application.vacancy_id == vacancy_id
        ).first() is not None