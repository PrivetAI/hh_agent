from sqlalchemy.orm import Session
from sqlalchemy import and_
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