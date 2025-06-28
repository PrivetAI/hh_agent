from sqlalchemy.orm import Session
from sqlalchemy import update, and_
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from ..models.db import Vacancy

class VacancyCRUD:
    @staticmethod
    def get_by_id(db: Session, vacancy_id: str) -> Optional[Vacancy]:
        """Get vacancy by ID"""
        return db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
    
    @staticmethod
    def create_or_update(db: Session, vacancy_data: Dict[str, Any]) -> Vacancy:
        """Create new vacancy or update existing"""
        vacancy_id = vacancy_data["id"]
        existing = VacancyCRUD.get_by_id(db, vacancy_id)
        
        # Подготовка данных для сохранения
        db_data = {
            "id": vacancy_id,
            "name": vacancy_data.get("name", ""),
            "employer_name": vacancy_data.get("employer", {}).get("name"),
            "area_name": vacancy_data.get("area", {}).get("name"),
            "description": vacancy_data.get("description", ""),
            "experience": vacancy_data.get("experience", {}).get("name"),
            "employment": vacancy_data.get("employment", {}).get("name"),
            "schedule": vacancy_data.get("schedule", {}).get("name"),
            "key_skills": [s.get("name") for s in vacancy_data.get("key_skills", [])],
            "full_data": vacancy_data
        }
        
        # Обработка зарплаты
        if vacancy_data.get("salary"):
            salary = vacancy_data["salary"]
            db_data["salary_from"] = salary.get("from")
            db_data["salary_to"] = salary.get("to")
            db_data["salary_currency"] = salary.get("currency")
        
        if existing:
            # Обновляем существующую
            for key, value in db_data.items():
                setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            existing.last_searched_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Создаем новую
            vacancy = Vacancy(**db_data)
            db.add(vacancy)
            db.commit()
            db.refresh(vacancy)
            return vacancy
    
    @staticmethod
    def update_last_searched(db: Session, vacancy_ids: List[str]) -> None:
        """Update last_searched_at for multiple vacancies"""
        if vacancy_ids:
            db.execute(
                update(Vacancy)
                .where(Vacancy.id.in_(vacancy_ids))
                .values(last_searched_at=datetime.utcnow())
            )
            db.commit()
    
    @staticmethod
    def get_stale_vacancies(db: Session, vacancy_ids: List[str], hours: int = 12) -> List[str]:
        """Get IDs of vacancies that need update (older than X hours or not in DB)"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Находим существующие вакансии
        existing = db.query(Vacancy.id, Vacancy.updated_at).filter(
            Vacancy.id.in_(vacancy_ids)
        ).all()
        
        existing_dict = {v.id: v.updated_at for v in existing}
        stale_ids = []
        
        for vacancy_id in vacancy_ids:
            if vacancy_id not in existing_dict:
                # Вакансии нет в БД - нужно загрузить
                stale_ids.append(vacancy_id)
            elif existing_dict[vacancy_id] < cutoff_time:
                # Вакансия устарела - нужно обновить
                stale_ids.append(vacancy_id)
        
        return stale_ids
    
    @staticmethod
    def clean_old_vacancies(db: Session, days: int = 7) -> int:
        """Delete vacancies not searched for X days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Находим старые вакансии без откликов
        old_vacancies = db.query(Vacancy).filter(
            and_(
                Vacancy.last_searched_at < cutoff_date,
                ~Vacancy.applications.any()  # Не имеют откликов
            )
        ).all()
        
        count = len(old_vacancies)
        
        for vacancy in old_vacancies:
            db.delete(vacancy)
        
        db.commit()
        return count