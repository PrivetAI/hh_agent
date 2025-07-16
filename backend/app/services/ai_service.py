import os
import re
import logging
import random
import time
from typing import Dict, Any
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
        
        try:
            self.client = AsyncOpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize OpenAI client: %s", e)
            raise
        
        # Инициализируем сервис псевдонимизации
        try:
            from .pseudonymization_service import PseudonymizationService
            self.pseudonymizer = PseudonymizationService()
            logger.info("Pseudonymization service initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize pseudonymization service: %s", e)
            raise
        
        # Доступные модели и промпты
        self.models = ["gpt-4o-mini", "gpt-4.1-mini"]
        self.prompts = ["first.md", "second.md", "third.md"]
        
        # Получаем путь к папке с промптами
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.prompts_dir = os.path.join(current_dir, "prompts")
        
        self._validate_prompt_files()
        logger.info("AI Service initialization completed successfully")
    
    def _validate_prompt_files(self):
        """Validate that all prompt files exist"""
        logger.info("Validating prompt files...")
        
        for prompt_file in self.prompts:
            prompt_path = os.path.join(self.prompts_dir, prompt_file)
            if os.path.exists(prompt_path):
                file_size = os.path.getsize(prompt_path)
                logger.info("Prompt file %s exists (size: %d bytes)", prompt_file, file_size)
            else:
                logger.warning("Prompt file %s not found at %s", prompt_file, prompt_path)
    
    def _load_prompt(self, filename: str) -> str:
        """Load prompt from markdown file"""
        logger.info("Loading prompt from file: %s", filename)
        
        try:
            prompt_path = os.path.join(self.prompts_dir, filename)
            with open(prompt_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                logger.info("Prompt loaded successfully, length: %d characters", len(content))
                return content
                
        except FileNotFoundError:
            logger.error("Prompt file not found: %s", prompt_path)
            raise HTTPException(status_code=500, detail=f"Prompt file {filename} not found")
        except Exception as e:
            logger.error("Error loading prompt file %s: %s", filename, e)
            raise HTTPException(status_code=500, detail=f"Error loading prompt file {filename}")
    
    def _extract_text(self, html_text: str) -> str:
        """Extract clean text from HTML"""
        if not html_text:
            return ""
        
        try:
            # Удаляем скрипты и стили
            text = re.sub(r'<(script|style).*?>.*?</\1>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
            # Удаляем HTML теги
            text = re.sub(r'<.*?>', ' ', text)
            # Заменяем HTML entities
            text = re.sub(r'&nbsp;', ' ', text)
            text = re.sub(r'&quot;', '"', text)
            text = re.sub(r'&amp;', '&', text)
            # Нормализуем пробелы
            text = ' '.join(text.split())
            return text.strip()
            
        except Exception as e:
            logger.error("Error extracting text from HTML: %s", e)
            return html_text
    
    def _prepare_resume_text(self, resume: dict) -> str:
        """Prepare resume text for AI analysis"""
        logger.info("Preparing resume text for AI analysis")
        
        if not resume:
            logger.warning("Empty resume provided")
            return ""
        
        parts = []
        
        try:
            # Информация о себе (skills)
            if resume.get('skills'):
                parts.append(f"\nО себе: {resume['skills']}")
            
            # Общий опыт
            if resume.get('total_experience'):
                months = resume['total_experience'].get('months', 0)
                parts.append(f"Общий опыт работы: {months} месяцев")
            
            # Опыт работы
            if resume.get('experience'):
                parts.append("\n Опыт работы:")
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
                        else:
                            period += " по настоящее время"
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
            
            
            result = '\n'.join(parts)
            logger.info("Resume text prepared successfully, total length: %d characters", len(result))
            return result
            
        except Exception as e:
            logger.error("Error preparing resume text: %s", e, exc_info=True)
            return ""
    
    def _prepare_vacancy_text(self, vacancy: dict) -> str:
        """Prepare vacancy text for AI analysis"""
        logger.info("Preparing vacancy text for AI analysis")
        
        if not vacancy:
            logger.warning("Empty vacancy provided")
            return ""
        
        try:
            # Получаем полный текст вакансии
            full_text = vacancy.get('description', '')
            if not full_text:
                logger.warning("No description found in vacancy")
                return ""
            
            # Очищаем HTML  
            clean_text = self._extract_text(full_text)
            logger.info("Vacancy text prepared successfully, length: %d characters", len(clean_text))
            
            return clean_text
            
        except Exception as e:
            logger.error("Error preparing vacancy text: %s", e, exc_info=True)
            return ""
    
    def _log_final_resume(self, resume_text: str, user_id: str):
        """Log final resume text that will be sent to AI"""
        logger.info("Final resume text for user %s:", user_id)
        logger.info("=" * 50)
        logger.info(resume_text)
        logger.info("=" * 50)
    
    async def generate_cover_letter(self, resume: dict, vacancy: dict, user_id: str) -> Dict[str, Any]:
        """Generate personalized cover letter with pseudonymization"""
        logger.info("Starting cover letter generation for user: %s", user_id)
        start_time = time.time()
        
        try:
            # Случайный выбор модели и промпта
            selected_model = random.choice(self.models)
            selected_prompt = random.choice(self.prompts)
            logger.info("Selected model: %s, prompt: %s", selected_model, selected_prompt)
            
            # Сохраняем ФИО для подписи
            first_name = resume.get('first_name', '')
            last_name = resume.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            
            # Получаем сессию БД для псевдонимизации
            db_gen = get_db()
            db = next(db_gen)
            
            try:
                # Псевдонимизируем резюме
                logger.info("Starting resume pseudonymization")
                pseudo_resume, session_id = self.pseudonymizer.pseudonymize_resume(
                    db, user_id, resume
                )
                logger.info("Resume pseudonymization completed, session_id: %s", session_id)
                
                # Подготавливаем тексты
                resume_text = self._prepare_resume_text(pseudo_resume)
                vacancy_text = self._prepare_vacancy_text(vacancy)
                
                # Логируем итоговое резюме
                self._log_final_resume(resume_text, user_id)
                
                logger.info("Text lengths - Resume: %d, Vacancy: %d", len(resume_text), len(vacancy_text))
                logger.info(" Vacancy: %d",vacancy_text)
                
                # Загружаем промпт
                system_prompt = self._load_prompt(selected_prompt)
                system_prompt += "\n\nВАЖНО: В резюме используются псевдонимы для названий компаний и учебных заведений. Используй эти псевдонимы в письме как есть. НЕ используй имя кандидата в письме - оно будет добавлено автоматически."
                
                user_prompt = f"""
Резюме кандидата:
{resume_text}

Текст вакансии:
{vacancy_text}

ВАЖНО: Не используй имя кандидата и подпись в письме. Подпись будет добавлена автоматически.
"""
                
                # Отправляем запрос к OpenAI
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
                
                # Получаем сгенерированное письмо
                letter = response.choices[0].message.content.strip()
                logger.info("Generated letter length: %d characters", len(letter))
                
                # Логируем использование токенов
                if hasattr(response, 'usage') and response.usage:
                    logger.info("Token usage - prompt: %d, completion: %d, total: %d",
                              response.usage.prompt_tokens,
                              response.usage.completion_tokens,
                              response.usage.total_tokens)
                
                # Восстанавливаем оригинальные названия
                logger.info("Restoring original company/education names")
                original_letter = self.pseudonymizer.restore_text(db, session_id, letter)
                
                # Добавляем подпись
                if full_name and not original_letter.endswith(full_name):
                    original_letter = original_letter.rstrip()
                    if not original_letter.endswith(','):
                        original_letter += "\n\nС уважением,"
                    original_letter += f"\n{full_name}"
                    logger.info("Added signature with name: %s", full_name)
                
                total_duration = time.time() - start_time
                logger.info("Cover letter generation completed in %.2f seconds", total_duration)
                
                return {
                    "content": original_letter,
                    "prompt_filename": selected_prompt,
                    "ai_model": selected_model
                }
                
            except Exception as e:
                logger.error("Error during cover letter generation: %s", e, exc_info=True)
                fallback_result = self._get_fallback_letter(vacancy, full_name)
                fallback_result["prompt_filename"] = selected_prompt
                fallback_result["ai_model"] = selected_model
                return fallback_result
                
            finally:
                try:
                    db.close()
                except Exception as e:
                    logger.error("Error closing database session: %s", e)
                    
        except Exception as e:
            logger.error("Critical error in cover letter generation: %s", e, exc_info=True)
            return self._get_fallback_letter(vacancy, "")

    def _get_fallback_letter(self, vacancy: dict, full_name: str) -> Dict[str, Any]:
        """Return fallback cover letter on error"""
        logger.warning("Generating fallback letter")
        
        try:
            # Получаем базовую информацию из вакансии
            vacancy_name = "интересную позицию"
            company_name = "вашей компании"
            
            if vacancy:
                # Пытаемся извлечь название вакансии из описания
                description = vacancy.get('description', '')
                if description:
                    clean_desc = self._extract_text(description)
                    # Простое извлечение названия компании и вакансии из текста
                    lines = clean_desc.split('\n')[:5]  # Берем первые 5 строк
                    for line in lines:
                        if any(word in line.lower() for word in ['вакансия', 'позиция', 'должность']):
                            vacancy_name = line.strip()
                            break
            
            fallback_letter = f"""Здравствуйте!

Меня заинтересовала {vacancy_name} в {company_name}.

Мой профессиональный опыт и навыки соответствуют требованиям данной позиции. Готов применить свои знания для достижения целей компании.

Буду рад обсудить возможности сотрудничества.

С уважением,
{full_name or 'Кандидат'}"""
            
            logger.info("Fallback letter generated")
            return {"content": fallback_letter}
            
        except Exception as e:
            logger.error("Error generating fallback letter: %s", e, exc_info=True)
            return {
                "content": "Произошла ошибка при генерации письма. Пожалуйста, попробуйте еще раз."
            }