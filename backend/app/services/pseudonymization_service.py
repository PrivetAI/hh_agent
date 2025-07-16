import logging
from typing import Dict, Tuple, Any
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

class PseudonymizationService:
    """Упрощенный сервис для псевдонимизации только компаний и учебных заведений"""
    
    def pseudonymize_resume(self, db: Session, user_id: UUID, 
                           resume_data: Dict[str, Any]) -> Tuple[Dict[str, Any], UUID]:
        """Псевдонимизация резюме - только компании и учебные заведения"""
        session_id = uuid4()
        
        # Создаем копию резюме для псевдонимизации
        pseudo_resume = resume_data.copy()
        
        # Счетчики для уникальных псевдонимов
        company_counter = 0
        education_counter = 0
        
        # Сохраняем маппинги в памяти (можно сохранить в БД при необходимости)
        mappings = []
        
        # Обработка опыта работы - только названия компаний
        if 'experience' in pseudo_resume:
            for exp in pseudo_resume['experience']:
                if 'company' in exp and exp['company']:
                    company_counter += 1
                    pseudonym = f"[КОМПАНИЯ_{company_counter}]"
                    
                    mappings.append({
                        'original': exp['company'],
                        'pseudonym': pseudonym,
                        'type': 'company'
                    })
                    
                    exp['company'] = pseudonym
        
        # Обработка образования - только названия учебных заведений
        if 'education' in pseudo_resume:
            primary_education = pseudo_resume.get('education', {}).get('primary', [])
            for edu in primary_education:
                if 'name' in edu and edu['name']:
                    education_counter += 1
                    pseudonym = f"[УЧЕБНОЕ_ЗАВЕДЕНИЕ_{education_counter}]"
                    
                    mappings.append({
                        'original': edu['name'],
                        'pseudonym': pseudonym,
                        'type': 'education'
                    })
                    
                    edu['name'] = pseudonym
        
        # Сохраняем маппинги в БД если нужно
        if mappings:
            self._save_mappings_to_db(db, session_id, user_id, mappings)
        
        logger.info(f"Pseudonymized {company_counter} companies and {education_counter} education institutions")
        
        return pseudo_resume, session_id
    
    def _save_mappings_to_db(self, db: Session, session_id: UUID, 
                            user_id: UUID, mappings: list):
        """Опциональное сохранение маппингов в БД"""
        try:
            # Создаем сессию
            db.execute(
                text("""
                    INSERT INTO pseudonymization.mapping_sessions (id, user_id)
                    VALUES (:session_id, :user_id)
                """),
                {"session_id": str(session_id), "user_id": str(user_id)}
            )
            
            # Сохраняем маппинги
            for mapping in mappings:
                db.execute(
                    text("""
                        INSERT INTO pseudonymization.mappings 
                        (session_id, original_value, pseudonym, data_type)
                        VALUES (:session_id, :original, :pseudonym, :data_type)
                    """),
                    {
                        "session_id": str(session_id),
                        "original": mapping['original'],
                        "pseudonym": mapping['pseudonym'],
                        "data_type": mapping['type']
                    }
                )
            
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save mappings: {e}")
            db.rollback()
    
    def restore_text(self, db: Session, session_id: UUID, text: str) -> str:
        """Восстановление оригинального текста из псевдонимов"""
        try:
            result = db.execute(
                text("""
                    SELECT pseudonym, original_value 
                    FROM pseudonymization.mappings
                    WHERE session_id = :session_id
                """),
                {"session_id": str(session_id)}
            )
            
            restored_text = text
            for row in result:
                if row.pseudonym in restored_text:
                    restored_text = restored_text.replace(row.pseudonym, row.original_value)
            
            return restored_text
        except Exception as e:
            logger.error(f"Failed to restore text: {e}")
            return text