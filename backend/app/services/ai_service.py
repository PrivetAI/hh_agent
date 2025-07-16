import os
import re
import logging
import random
import time
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        logger.info("Initializing AI Service...")
        
        # Проверяем API ключ
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable is not set")
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        logger.info("OpenAI API key found, length: %d characters", len(api_key))
        
        # Инициализируем клиент OpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Инициализируем сервис псевдонимизации
        from .pseudonymization_service import PseudonymizationService
        self.pseudonymizer = PseudonymizationService()
        
        # Доступные модели и промпты
        self.models = ["gpt-4o-mini", "gpt-4.1-mini"]
        self.prompts = ["first.md", "second.md", "third.md"]
        
        # Путь к папке с промптами
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
        
        # Кэш для промптов
        self._prompts_cache = {}
        
        self._validate_and_cache_prompts()
        logger.info("AI Service initialization completed successfully")
    
    def _validate_and_cache_prompts(self):
        """Валидация и кэширование промптов"""
        logger.info("Validating and caching prompt files...")
        
        for prompt_file in self.prompts:
            prompt_path = os.path.join(self.prompts_dir, prompt_file)
            if os.path.exists(prompt_path):
                try:
                    with open(prompt_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        self._prompts_cache[prompt_file] = content
                        logger.info(f"Cached prompt {prompt_file} (size: {len(content)} bytes)")
                except Exception as e:
                    logger.error(f"Failed to cache prompt {prompt_file}: {e}")
            else:
                logger.warning(f"Prompt file {prompt_file} not found at {prompt_path}")
    
    def _get_prompt(self, filename: str) -> str:
        """Получить промпт из кэша или файла"""
        if filename in self._prompts_cache:
            return self._prompts_cache[filename]
        
        # Если не в кэше, загружаем
        prompt_path = os.path.join(self.prompts_dir, filename)
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                self._prompts_cache[filename] = content
                return content
        except Exception as e:
            logger.error(f"Error loading prompt file {filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Prompt file {filename} not found")
    
    def _extract_text(self, html_text: str) -> str:
        """Извлечение текста из HTML"""
        if not html_text:
            return ""
        
        # Удаляем скрипты и стили
        text = re.sub(r'<(script|style).*?>.*?</\1>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
        # Удаляем HTML теги
        text = re.sub(r'<.*?>', ' ', text)
        # Заменяем HTML entities
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&quot;', '"', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        # Нормализуем пробелы
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _prepare_resume_text(self, resume: dict) -> str:
        """Подготовка текста резюме для AI"""
        if not resume:
            return ""
        
        parts = []
        
        # О себе (skills)
        if resume.get('skills'):
            parts.append(f"О себе: {resume['skills']}")
        
        # Общий опыт
        if resume.get('total_experience', {}).get('months'):
            months = resume['total_experience']['months']
            parts.append(f"Общий опыт работы: {months} месяцев")
        
        # Опыт работы
        if resume.get('experience'):
            parts.append("\nОпыт работы:")
            for exp in resume['experience']:
                exp_parts = []
                
                if exp.get('company'):
                    exp_parts.append(f"Компания: {exp['company']}")
                if exp.get('position'):
                    exp_parts.append(f"Должность: {exp['position']}")
                if exp.get('start'):
                    period = f"с {exp['start']}"
                    if exp.get('end'):
                        period += f" по {exp['end']}"
                    exp_parts.append(period)
                if exp.get('description'):
                    exp_parts.append(f"Описание: {exp['description']}")
                
                if exp_parts:
                    parts.append("- " + ", ".join(exp_parts))
        
        # Образование
        if resume.get('education', {}).get('primary'):
            parts.append("\nОбразование:")
            for edu in resume['education']['primary']:
                edu_parts = []
                
                if edu.get('name'):
                    edu_parts.append(edu['name'])
                if edu.get('organization'):
                    edu_parts.append(edu['organization'])
                if edu.get('year'):
                    edu_parts.append(f"Год окончания: {edu['year']}")
                
                if edu_parts:
                    parts.append("- " + ", ".join(edu_parts))
        
        # Языки
        if resume.get('language'):
            lang_list = []
            for lang in resume['language']:
                if lang.get('name') and lang.get('level', {}).get('name'):
                    lang_list.append(f"{lang['name']} - {lang['level']['name']}")
            
            if lang_list:
                parts.append(f"\nЯзыки: {', '.join(lang_list)}")
        
        return '\n'.join(parts)
    
    def _prepare_vacancy_text(self, vacancy: dict) -> str:
        """Подготовка текста вакансии"""
        if not vacancy or not vacancy.get('description'):
            return ""
        
        # Если описание уже очищено от HTML, возвращаем как есть
        description = vacancy['description']
        if '<' in description and '>' in description:
            return self._extract_text(description)
        
        return description
    
    async def generate_cover_letter(self, resume: dict, vacancy: dict, user_id: str) -> Dict[str, Any]:
        """Генерация сопроводительного письма с псевдонимизацией"""
        logger.info(f"Starting cover letter generation for user: {user_id}")
        start_time = time.time()
        
        # Выбираем модель и промпт
        selected_model = random.choice(self.models)
        selected_prompt = random.choice(self.prompts)
        logger.info(f"Selected model: {selected_model}, prompt: {selected_prompt}")
        
        # Сохраняем ФИО для подписи
        first_name = resume.get('first_name', '')
        last_name = resume.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        
        # Получаем сессию БД
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Псевдонимизируем резюме
            logger.info("Starting resume pseudonymization")
            pseudo_resume, session_id = self.pseudonymizer.pseudonymize_resume(
                db, user_id, resume
            )
            
            # Подготавливаем тексты
            resume_text = self._prepare_resume_text(pseudo_resume)
            vacancy_text = self._prepare_vacancy_text(vacancy)
            
            if not resume_text:
                logger.error("Empty resume text after preparation")
                return self._get_fallback_letter(vacancy, full_name)
            
            if not vacancy_text:
                logger.error("Empty vacancy text after preparation")
                return self._get_fallback_letter(vacancy, full_name)
            
            logger.info(f"Text lengths - Resume: {len(resume_text)}, Vacancy: {len(vacancy_text)}")
            
            # Получаем промпт из кэша
            system_prompt = self._get_prompt(selected_prompt)
            system_prompt += "\n\nВАЖНО: В резюме используются псевдонимы для названий компаний и учебных заведений. Используй эти псевдонимы в письме как есть. НЕ используй имя кандидата в письме - оно будет добавлено автоматически."
            
            user_prompt = f"""Резюме кандидата:
{resume_text}

Текст вакансии:
{vacancy_text}

ВАЖНО: Не используй имя кандидата и подпись в письме. Подпись будет добавлена автоматически."""
            
            # Генерируем письмо
            logger.info("Sending request to OpenAI")
            response = await self.client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=1.1,
                max_tokens=500,
                top_p=0.7
            )
            
            letter = response.choices[0].message.content.strip()
            logger.info(f"Generated letter length: {len(letter)} characters")
            
            # Логируем токены
            if hasattr(response, 'usage') and response.usage:
                logger.info(f"Token usage - prompt: {response.usage.prompt_tokens}, "
                          f"completion: {response.usage.completion_tokens}, "
                          f"total: {response.usage.total_tokens}")
            
            # Восстанавливаем оригинальные названия
            logger.info("Restoring original company/education names")
            original_letter = self.pseudonymizer.restore_text(db, session_id, letter)
            
            # Добавляем подпись
            if full_name:
                original_letter = self._add_signature(original_letter, full_name)
            
            # Очищаем кэш псевдонимизации для этой сессии
            self.pseudonymizer.clear_cache(session_id)
            
            total_duration = time.time() - start_time
            logger.info(f"Cover letter generation completed in {total_duration:.2f} seconds")
            
            return {
                "content": original_letter,
                "prompt_filename": selected_prompt,
                "ai_model": selected_model
            }
            
        except Exception as e:
            logger.error(f"Error during cover letter generation: {e}", exc_info=True)
            
            # Возвращаем fallback письмо с информацией о модели и промпте
            fallback_result = self._get_fallback_letter(vacancy, full_name)
            fallback_result["prompt_filename"] = selected_prompt
            fallback_result["ai_model"] = selected_model
            return fallback_result
            
        finally:
            try:
                db.close()
            except Exception as e:
                logger.error(f"Error closing database session: {e}")
    
    def _add_signature(self, letter: str, full_name: str) -> str:
        """Добавление подписи к письму"""
        if not full_name:
            return letter
        
        # Убираем лишние пробелы в конце
        letter = letter.rstrip()
        
        # Проверяем, не заканчивается ли письмо уже на имя
        if letter.endswith(full_name):
            return letter
        
        # Добавляем подпись
        if not letter.endswith(','):
            letter += "\n\nС уважением,"
        
        letter += f"\n{full_name}"
        
        logger.info(f"Added signature with name: {full_name}")
        return letter
    
    def _get_fallback_letter(self, vacancy: dict, full_name: str) -> Dict[str, Any]:
        """Генерация запасного письма при ошибке"""
        logger.warning("Generating fallback letter")
        
        vacancy_name = vacancy.get('name', 'вашу вакансию')
        company_name = vacancy.get('employer', {}).get('name', 'вашей компании')
        
        fallback_letter = f"""Здравствуйте!

Меня заинтересовала вакансия "{vacancy_name}" в {company_name}.

Мой профессиональный опыт и навыки соответствуют требованиям данной позиции. Готов применить свои знания для достижения целей компании.

Буду рад обсудить возможности сотрудничества.

С уважением,
{full_name or 'Кандидат'}"""
        
        logger.info("Fallback letter generated")
        return {"content": fallback_letter}