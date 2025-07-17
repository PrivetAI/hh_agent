import logging
from typing import Dict, Tuple, Any, List
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class PseudonymizationService:
    """Сервис для псевдонимизации компаний и учебных заведений"""
    
    def __init__(self):
        # Кэш для хранения маппингов в памяти
        self._mappings_cache = {}
    
    def pseudonymize_resume(self, db: Session, user_id: str, 
                           resume_data: Dict[str, Any]) -> Tuple[Dict[str, Any], UUID]:
        """Псевдонимизация резюме - только компании и учебные заведения"""
        session_id = uuid4()
        pseudo_resume = resume_data.copy()
        
        company_counter = 0
        education_counter = 0
        mappings = []
        
        # Обработка опыта работы
        if 'experience' in pseudo_resume and pseudo_resume['experience']:
            for exp in pseudo_resume['experience']:
                if exp.get('company'):
                    company_counter += 1
                    pseudonym = f"[КОМПАНИЯ_{company_counter}]"
                    
                    mappings.append({
                        'original': exp['company'],
                        'pseudonym': pseudonym,
                        'type': 'company'
                    })
                    
                    exp['company'] = pseudonym
        
        # Обработка образования
        if 'education' in pseudo_resume and pseudo_resume['education']:
            primary_education = pseudo_resume['education'].get('primary', [])
            for edu in primary_education:
                if edu.get('name'):
                    education_counter += 1
                    pseudonym = f"[УЧЕБНОЕ_ЗАВЕДЕНИЕ_{education_counter}]"
                    
                    mappings.append({
                        'original': edu['name'],
                        'pseudonym': pseudonym,
                        'type': 'education'
                    })
                    
                    edu['name'] = pseudonym
        
        # Сохраняем маппинги в кэш
        self._mappings_cache[str(session_id)] = mappings
        
        # Сохраняем в БД только если есть маппинги
        if mappings:
            try:
                # Import here to avoid circular imports
                from ..crud.application import ApplicationCRUD
                
                ApplicationCRUD.save_pseudonymization_mappings(
                    db=db,
                    session_id=session_id,
                    user_id=UUID(user_id),
                    mappings=mappings
                )
                logger.info(f"Saved {len(mappings)} mappings to DB via ORM")
                
            except Exception as e:
                logger.error(f"Failed to save mappings to DB: {e}")
                # Продолжаем работу, используя кэш
        
        logger.info(f"Pseudonymized {company_counter} companies and {education_counter} education institutions")
        
        return pseudo_resume, session_id
    
    def restore_text(self, db: Session, session_id: UUID, pseudonymized_text: str) -> str:
        """Восстановление оригинального текста из псевдонимов"""
        session_id_str = str(session_id)
        
        # Сначала пробуем кэш
        if session_id_str in self._mappings_cache:
            mappings = self._mappings_cache[session_id_str]
            restored = pseudonymized_text
            
            for mapping in mappings:
                if mapping['pseudonym'] in restored:
                    restored = restored.replace(
                        mapping['pseudonym'], 
                        mapping['original']
                    )
            
            logger.info(f"Restored text from cache for session {session_id_str}")
            return restored
        
        # Если нет в кэше, загружаем из БД
        try:
            # Import here to avoid circular imports
            from ..crud.application import ApplicationCRUD
            
            mappings = ApplicationCRUD.get_pseudonymization_mappings(
                db=db,
                session_id=session_id
            )
            
            restored = pseudonymized_text
            mappings_count = 0
            
            for mapping in mappings:
                if mapping['pseudonym'] in restored:
                    restored = restored.replace(
                        mapping['pseudonym'], 
                        mapping['original']
                    )
                    mappings_count += 1
            
            logger.info(f"Restored {mappings_count} mappings from DB for session {session_id_str}")
            return restored
            
        except Exception as e:
            logger.error(f"Failed to restore text from DB: {e}", exc_info=True)
            # Возвращаем оригинальный текст если не можем восстановить
            return pseudonymized_text
    
    def clear_cache(self, session_id: UUID = None):
        """Очистка кэша маппингов"""
        if session_id:
            session_id_str = str(session_id)
            if session_id_str in self._mappings_cache:
                del self._mappings_cache[session_id_str]
                logger.info(f"Cleared cache for session {session_id_str}")
        else:
            self._mappings_cache.clear()
            logger.info("Cleared all mappings cache")
    
    def cleanup_expired_mappings(self, db: Session) -> int:
        """Очистка устаревших маппингов"""
        try:
            # Import here to avoid circular imports
            from ..crud.application import ApplicationCRUD
            
            deleted_count = ApplicationCRUD.cleanup_expired_mappings(db)
            logger.info(f"Cleaned up {deleted_count} expired mapping sessions")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired mappings: {e}", exc_info=True)
            return 0