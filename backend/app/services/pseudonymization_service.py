import re
import json
from typing import Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
from uuid import UUID
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

class PseudonymizationService:
    """Сервис для псевдонимизации персональных данных перед отправкой в AI"""
    
    def __init__(self):
        # Паттерны для поиска персональных данных
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'(?:\+7|8)[\s\-\(]?\d{3}[\s\-\)]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}'),
            'social': re.compile(r'(?:https?://)?(?:www\.)?(?:vk\.com|facebook\.com|instagram\.com|linkedin\.com|github\.com|t\.me)/[\w\-\.]+'),
            'date_birth': re.compile(r'\b\d{1,2}[\.\-/]\d{1,2}[\.\-/]\d{4}\b'),
            'age': re.compile(r'\b\d{1,2}\s*(?:лет|года|год)\b', re.IGNORECASE)
        }
        
        # Список распространенных имен и фамилий для детекции
        self.common_names = self._load_common_names()
        
    def _load_common_names(self) -> set:
        """Загрузка списка распространенных имен и фамилий"""
        # В реальности загружать из файла или БД
        return {
            'александр', 'алексей', 'анастасия', 'андрей', 'анна', 'антон',
            'артем', 'виктор', 'виктория', 'владимир', 'дарья', 'денис',
            'дмитрий', 'евгений', 'екатерина', 'елена', 'иван', 'игорь',
            'ирина', 'максим', 'мария', 'михаил', 'наталья', 'никита',
            'николай', 'ольга', 'павел', 'петр', 'роман', 'сергей',
            'татьяна', 'юлия', 'юрий'
        }
    
    def create_mapping_session(self, db: Session, user_id: UUID) -> UUID:
        """Создание новой сессии маппинга"""
        result = db.execute(
            text("""
                INSERT INTO pseudonymization.mapping_sessions (user_id)
                VALUES (:user_id)
                RETURNING id
            """),
            {"user_id": str(user_id)}
        )
        session_id = result.scalar()
        db.commit()
        return session_id
    
    def save_mapping(self, db: Session, session_id: UUID, original: str, 
                     pseudonym: str, data_type: str):
        """Сохранение маппинга в БД"""
        db.execute(
            text("""
                INSERT INTO pseudonymization.mappings 
                (session_id, original_value, pseudonym, data_type)
                VALUES (:session_id, :original, :pseudonym, :data_type)
            """),
            {
                "session_id": str(session_id),
                "original": original,
                "pseudonym": pseudonym,
                "data_type": data_type
            }
        )
        db.commit()
    
    def pseudonymize_resume(self, db: Session, user_id: UUID, 
                           resume_data: Dict[str, Any]) -> Tuple[Dict[str, Any], UUID]:
        """Псевдонимизация резюме с сохранением маппинга"""
        session_id = self.create_mapping_session(db, user_id)
        
        # Создаем копию для изменения
        pseudo_resume = json.loads(json.dumps(resume_data))
        # Счетчики для уникальных псевдонимов
        counters = {
            'name': 0, 'email': 0, 'phone': 0, 'company': 0,
            'education': 0, 'address': 0, 'social': 0
        }
        
        logger.info(pseudo_resume)

        # Обработка структурированных данных из API
        if 'first_name' in pseudo_resume:
            counters['name'] += 1
            pseudonym = f"[ИМЯ_{counters['name']}]"
            self.save_mapping(db, session_id, pseudo_resume['first_name'], 
                            pseudonym, 'first_name')
            pseudo_resume['first_name'] = pseudonym
        
        if 'last_name' in pseudo_resume:
            counters['name'] += 1
            pseudonym = f"[ФАМИЛИЯ_{counters['name']}]"
            self.save_mapping(db, session_id, pseudo_resume['last_name'], 
                            pseudonym, 'last_name')
            pseudo_resume['last_name'] = pseudonym
        
        if 'middle_name' in pseudo_resume:
            counters['name'] += 1
            pseudonym = f"[ОТЧЕСТВО_{counters['name']}]"
            self.save_mapping(db, session_id, pseudo_resume['middle_name'], 
                            pseudonym, 'middle_name')
            pseudo_resume['middle_name'] = pseudonym
        
        # Обработка контактов
        if 'contact' in pseudo_resume:
            contact = pseudo_resume['contact']
            
            for email in contact.get('email', []):
                counters['email'] += 1
                pseudonym = f"[EMAIL_{counters['email']}]"
                self.save_mapping(db, session_id, email['value'], 
                                pseudonym, 'email')
                email['value'] = pseudonym
            
            for phone in contact.get('phone', []):
                counters['phone'] += 1
                pseudonym = f"[ТЕЛЕФОН_{counters['phone']}]"
                self.save_mapping(db, session_id, phone['formatted'], 
                                pseudonym, 'phone')
                phone['formatted'] = pseudonym
                phone['value'] = pseudonym
        
        # Обработка опыта работы
        if 'experience' in pseudo_resume:
            for exp in pseudo_resume['experience']:
                if 'company' in exp:
                    counters['company'] += 1
                    pseudonym = f"[КОМПАНИЯ_{counters['company']}]"
                    self.save_mapping(db, session_id, exp['company'], 
                                    pseudonym, 'company')
                    exp['company'] = pseudonym
                
                # Обработка периодов работы
                if 'start' in exp:
                    exp['start'] = self._pseudonymize_date(exp['start'])
                if 'end' in exp:
                    exp['end'] = self._pseudonymize_date(exp['end'])
        
        # Обработка образования  
        if 'education' in pseudo_resume:
            for edu in pseudo_resume.get('education', {}).get('primary', []):
                if 'name' in edu:
                    counters['education'] += 1
                    pseudonym = f"[ВУЗ_{counters['education']}]"
                    self.save_mapping(db, session_id, edu['name'], 
                                    pseudonym, 'education')
                    edu['name'] = pseudonym
                
                if 'year' in edu:
                    edu['year'] = self._pseudonymize_year(edu['year'])
        
        # Обработка даты рождения и возраста
        if 'birth_date' in pseudo_resume:
            birth_date = pseudo_resume['birth_date']
            age_range = self._calculate_age_range(birth_date)
            self.save_mapping(db, session_id, birth_date, 
                            age_range, 'birth_date')
            pseudo_resume['birth_date'] = None
            pseudo_resume['age'] = age_range
        
        # Обработка полного текста резюме (RTF fallback)
        if 'full_text' in pseudo_resume:
            pseudo_resume['full_text'] = self._pseudonymize_text(
                db, session_id, pseudo_resume['full_text'], counters
            )
        
        return pseudo_resume, session_id
    
    def _pseudonymize_text(self, db: Session, session_id: UUID, 
                          text: str, counters: Dict[str, int]) -> str:
        """Псевдонимизация произвольного текста"""
        # Замена email
        for match in self.patterns['email'].finditer(text):
            counters['email'] += 1
            pseudonym = f"[EMAIL_{counters['email']}]"
            self.save_mapping(db, session_id, match.group(), pseudonym, 'email')
            text = text.replace(match.group(), pseudonym)
        
        # Замена телефонов
        for match in self.patterns['phone'].finditer(text):
            counters['phone'] += 1
            pseudonym = f"[ТЕЛЕФОН_{counters['phone']}]"
            self.save_mapping(db, session_id, match.group(), pseudonym, 'phone')
            text = text.replace(match.group(), pseudonym)
        
        # Замена соцсетей
        for match in self.patterns['social'].finditer(text):
            counters['social'] += 1
            pseudonym = f"[ССЫЛКА_{counters['social']}]"
            self.save_mapping(db, session_id, match.group(), pseudonym, 'social')
            text = text.replace(match.group(), pseudonym)
        
        # Замена дат рождения
        for match in self.patterns['date_birth'].finditer(text):
            age_range = self._calculate_age_range_from_date_str(match.group())
            self.save_mapping(db, session_id, match.group(), age_range, 'birth_date')
            text = text.replace(match.group(), age_range)
        
        # Замена возраста
        for match in self.patterns['age'].finditer(text):
            age_range = self._age_to_range(match.group())
            self.save_mapping(db, session_id, match.group(), age_range, 'age')
            text = text.replace(match.group(), age_range)
        
        # Поиск и замена имен
        words = text.split()
        for i, word in enumerate(words):
            clean_word = word.lower().strip('.,!?;:')
            if clean_word in self.common_names:
                counters['name'] += 1
                pseudonym = f"[ИМЯ_{counters['name']}]"
                self.save_mapping(db, session_id, word, pseudonym, 'name')
                words[i] = word.replace(clean_word, pseudonym)
        
        return ' '.join(words)
    
    def _pseudonymize_date(self, date_str: str) -> str:
        """Псевдонимизация даты, оставляя только год"""
        try:
            if '-' in date_str:
                year = date_str.split('-')[0]
                return f"[{year}]"
            return "[ДАТА]"
        except:
            return "[ДАТА]"
    
    def _pseudonymize_year(self, year: int) -> str:
        """Псевдонимизация года"""
        return f"[{year}]"
    
    def _calculate_age_range(self, birth_date: str) -> str:
        """Вычисление возрастного диапазона из даты рождения"""
        try:
            birth_year = int(birth_date.split('-')[0])
            current_year = datetime.now().year
            age = current_year - birth_year
            
            if age < 20:
                return "[до 20 лет]"
            elif age < 30:
                return "[20-30 лет]"
            elif age < 40:
                return "[30-40 лет]"
            elif age < 50:
                return "[40-50 лет]"
            else:
                return "[50+ лет]"
        except:
            return "[возраст не указан]"
    
    def _calculate_age_range_from_date_str(self, date_str: str) -> str:
        """Вычисление возрастного диапазона из строки даты"""
        try:
            # Парсим различные форматы дат
            for fmt in ['%d.%m.%Y', '%d-%m-%Y', '%d/%m/%Y']:
                try:
                    birth_date = datetime.strptime(date_str, fmt)
                    age = (datetime.now() - birth_date).days // 365
                    return self._age_to_range(f"{age} лет")
                except:
                    continue
            return "[возраст не указан]"
        except:
            return "[возраст не указан]"
    
    def _age_to_range(self, age_str: str) -> str:
        """Преобразование возраста в диапазон"""
        try:
            age = int(re.search(r'\d+', age_str).group())
            if age < 20:
                return "[до 20 лет]"
            elif age < 30:
                return "[20-30 лет]"
            elif age < 40:
                return "[30-40 лет]"
            elif age < 50:
                return "[40-50 лет]"
            else:
                return "[50+ лет]"
        except:
            return "[возраст не указан]"
    
    def restore_text(self, db: Session, session_id: UUID, text: str) -> str:
        """Восстановление оригинального текста из псевдонимов"""
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
            restored_text = restored_text.replace(row.pseudonym, row.original_value)
        
        return restored_text
    
    def cleanup_old_sessions(self, db: Session):
        """Удаление устаревших сессий маппинга"""
        db.execute(
            text("""
                DELETE FROM pseudonymization.mapping_sessions
                WHERE expires_at < NOW()
            """)
        )
        db.commit()
        logger.info("Old pseudonymization sessions cleaned up")