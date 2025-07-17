from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from ..models.db import Application
from ..models.schemas import ApplicationCreate

class ApplicationCRUD:
    @staticmethod
    def create(
        db: Session,
        user_id: UUID,
        vacancy_id: str,
        resume_id: Optional[str] = None,
        message: str = "",
        prompt_filename: Optional[str] = None,
        ai_model: Optional[str] = None
    ) -> Application:
        """Create new application"""
        application = Application(
            user_id=user_id,
            vacancy_id=vacancy_id,
            resume_id=resume_id,
            message=message,
            prompt_filename=prompt_filename,
            ai_model=ai_model,
            created_at=datetime.utcnow()
        )
        db.add(application)
        db.commit()
        db.refresh(application)
        return application

    @staticmethod
    def user_applied_to_vacancy(db: Session, user_id: UUID, vacancy_id: str) -> bool:
        """Check if user already applied to vacancy"""
        return db.query(Application).filter(
            and_(
                Application.user_id == user_id,
                Application.vacancy_id == vacancy_id
            )
        ).first() is not None

    @staticmethod
    def get_user_applied_vacancies(db: Session, user_id: str, vacancy_ids: List[str]) -> List[str]:
        """Get list of vacancy IDs that user has already applied to"""
        applied = db.query(Application.vacancy_id).filter(
            and_(
                Application.user_id == user_id,
                Application.vacancy_id.in_(vacancy_ids)
            )
        ).all()
        
        return [app.vacancy_id for app in applied]

    @staticmethod
    def get_user_applications(db: Session, user_id: UUID) -> List[Application]:
        """Get all user applications"""
        return db.query(Application).filter(
            Application.user_id == user_id
        ).order_by(Application.created_at.desc()).all()

    @staticmethod
    def get_by_id(db: Session, application_id: UUID) -> Optional[Application]:
        """Get application by ID"""
        return db.query(Application).filter(Application.id == application_id).first()

    @staticmethod
    def delete(db: Session, application_id: UUID) -> bool:
        """Delete application by ID"""
        application = ApplicationCRUD.get_by_id(db, application_id)
        if application:
            db.delete(application)
            db.commit()
            return True
        return False