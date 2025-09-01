from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4

from ..models.db import Application, Mapping, MappingSession
from ..models.schemas import ApplicationCreate

class ApplicationCRUD:
    @staticmethod
    def create(
        db: Session,
        user_id: UUID,
        vacancy_id: str,
        vacancy_title: Optional[str] = None,
        resume_id: Optional[str] = None,
        message: str = "",
        status: str = "pending",
        error_message: Optional[str] = None,
        prompt_filename: Optional[str] = None,
        ai_model: Optional[str] = None
    ) -> Application:
        """Create new application with status tracking"""
        application = Application(
            user_id=user_id,
            vacancy_id=vacancy_id,
            vacancy_title=vacancy_title,
            resume_id=resume_id,
            message=message,
            status=status,
            error_message=error_message,
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
        """Check if user already applied to vacancy (only successful applications)"""
        return db.query(Application).filter(
            and_(
                Application.user_id == user_id,
                Application.vacancy_id == vacancy_id,
                Application.status == "success"
            )
        ).first() is not None

    @staticmethod
    def get_user_applied_vacancies(db: Session, user_id: str, vacancy_ids: List[str]) -> List[str]:
        """Get list of vacancy IDs that user has successfully applied to"""
        applied = db.query(Application.vacancy_id).filter(
            and_(
                Application.user_id == user_id,
                Application.vacancy_id.in_(vacancy_ids),
                Application.status == "success"
            )
        ).all()
        
        return [app.vacancy_id for app in applied]

    @staticmethod
    def get_user_applications(
        db: Session, 
        user_id: UUID, 
        limit: int = 50,
        status_filter: Optional[str] = None
    ) -> List[Application]:
        """Get user applications with optional status filter"""
        query = db.query(Application).filter(Application.user_id == user_id)
        
        if status_filter:
            query = query.filter(Application.status == status_filter)
        
        return query.order_by(desc(Application.created_at)).limit(limit).all()

    @staticmethod
    def get_user_application_history(
        db: Session, 
        user_id: UUID, 
        limit: int = 50
    ) -> List[Application]:
        """Get user's successful application history for display"""
        return db.query(Application).filter(
            and_(
                Application.user_id == user_id,
                Application.status == "success"
            )
        ).order_by(desc(Application.created_at)).limit(limit).all()

    @staticmethod
    def update_application_status(
        db: Session,
        application_id: UUID,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[Application]:
        """Update application status"""
        application = db.query(Application).filter(Application.id == application_id).first()
        if application:
            application.status = status
            if error_message:
                application.error_message = error_message
            db.commit()
            db.refresh(application)
        return application

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

    @staticmethod
    def save_pseudonymization_mappings(
        db: Session, 
        session_id: UUID, 
        user_id: UUID, 
        mappings: List[dict]
    ) -> None:
        """Save pseudonymization mappings using ORM"""
        try:
            # Create mapping session
            mapping_session = MappingSession(
                id=session_id,
                user_id=user_id
            )
            db.add(mapping_session)
            
            # Add mappings
            for mapping in mappings:
                mapping_obj = Mapping(
                    session_id=session_id,
                    original_value=mapping['original'],
                    pseudonym=mapping['pseudonym'],
                    data_type=mapping['type']
                )
                db.add(mapping_obj)
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_pseudonymization_mappings(
        db: Session, 
        session_id: UUID
    ) -> List[dict]:
        """Get pseudonymization mappings for a session"""
        mappings = db.query(Mapping).filter(
            Mapping.session_id == session_id
        ).all()
        
        return [
            {
                'original': mapping.original_value,
                'pseudonym': mapping.pseudonym,
                'type': mapping.data_type
            }
            for mapping in mappings
        ]

    @staticmethod
    def cleanup_expired_mappings(db: Session) -> int:
        """Clean up expired pseudonymization mappings"""
        try:
            # Delete expired mapping sessions (cascades to mappings)
            deleted_count = db.query(MappingSession).filter(
                MappingSession.expires_at < datetime.utcnow()
            ).delete()
            
            db.commit()
            return deleted_count
            
        except Exception as e:
            db.rollback()
            raise e