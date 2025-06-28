import os
import re
import json
import logging
import random  # Добавить импорт
from typing import Dict, Any, Tuple  # Обновить импорт
from openai import AsyncOpenAI
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Доступные модели
        self.models = ["gpt-4o-mini", "gpt-4.1-mini"]
        
        # Доступные промпты
        self.prompts = ["first.md", "second.md", "third.md"]
        
        # Get path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.prompts_dir = os.path.join(current_dir, "prompts")
        
        logger.info(f"AI Service initialized with models: {self.models}")
        logger.info(f"Available prompts: {self.prompts}")
        logger.info(f"Prompts directory: {self.prompts_dir}")
        logger.info(f"Prompts directory exists: {os.path.exists(self.prompts_dir)}")
        
        # List files in prompts directory
        if os.path.exists(self.prompts_dir):
            files = os.listdir(self.prompts_dir)
            logger.info(f"Files in prompts directory: {files}")
        else:
            logger.error(f"Prompts directory does not exist: {self.prompts_dir}")
    
    def _load_prompt(self, filename: str) -> str:
        """Load prompt from markdown file"""
        try:
            prompt_path = os.path.join(self.prompts_dir, filename)
            logger.info(f"Loading prompt from: {prompt_path}")
            with open(prompt_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                logger.info(f"Prompt loaded successfully, length: {len(content)} chars")
                return content
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {prompt_path}")
            raise HTTPException(status_code=500, detail=f"Prompt file {filename} not found")
        except Exception as e:
            logger.error(f"Error loading prompt {filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Error loading prompt: {e}")
    
    def _extract_text(self, html_text: str) -> str:
        """Extract clean text from HTML"""
        if not html_text:
            return ""
        
        text = re.sub(r'<(script|style).*?>.*?</\1>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<.*?>', ' ', text)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&quot;', '"', text)
        text = re.sub(r'&amp;', '&', text)
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _prepare_resume_text(self, resume: dict) -> str:
        """Prepare resume text for AI analysis"""
        parts = []
        
        # Basic info
        full_name = f"{resume.get('first_name', '')} {resume.get('last_name', '')}".strip()
        if full_name:
            parts.append(f"Кандидат: {full_name}")
        
        if resume.get('title'):
            parts.append(f"Желаемая должность: {resume['title']}")
        
        # Use full_text if available, otherwise fallback to basic fields
        if resume.get('full_text'):
            parts.append(f"\nПолный текст резюме:\n{resume['full_text']}")
       
        return '\n'.join(parts)
    
    def _prepare_vacancy_text(self, vacancy: dict) -> str:
        """Prepare vacancy text for AI analysis"""
        parts = []
        
        # Basic info
        parts.append(f"Вакансия: {vacancy.get('name', 'Не указано')}")
        parts.append(f"Компания: {vacancy.get('employer', {}).get('name', 'Не указано')}")
        
        # Location
        if vacancy.get('area', {}).get('name'):
            parts.append(f"Местоположение: {vacancy['area']['name']}")
        
        # Salary
        if vacancy.get('salary'):
            salary = vacancy['salary']
            salary_parts = []
            if salary.get('from'):
                salary_parts.append(f"от {salary['from']:,}")
            if salary.get('to'):
                salary_parts.append(f"до {salary['to']:,}")
            if salary_parts:
                currency = salary.get('currency', 'RUR')
                parts.append(f"Зарплата: {' '.join(salary_parts)} {currency}")
        
        # Experience
        experience = vacancy.get('experience', {}).get('name', '')
        if experience:
            parts.append(f"Требуемый опыт: {experience}")
        
        # Employment type
        if vacancy.get('employment', {}).get('name'):
            parts.append(f"Тип занятости: {vacancy['employment']['name']}")
        
        # Schedule
        if vacancy.get('schedule', {}).get('name'):
            parts.append(f"График работы: {vacancy['schedule']['name']}")
        
        # Key skills
        if vacancy.get('key_skills'):
            skills = [s.get('name', '') for s in vacancy['key_skills'] if s.get('name')]
            if skills:
                parts.append(f"\nТребуемые навыки: {', '.join(skills)}")
        
        # Professional roles
        if vacancy.get('professional_roles'):
            roles = [r.get('name', '') for r in vacancy['professional_roles'] if r.get('name')]
            if roles:
                parts.append(f"\nПрофессиональные роли: {', '.join(roles)}")
        
        # Description
        description = self._extract_text(vacancy.get('description', ''))
        if description:
            desc_preview = description[:800] + "..." if len(description) > 800 else description
            parts.append(f"\nОписание:\n{desc_preview}")
        
        # Snippet
        if vacancy.get('snippet', {}).get('responsibility'):
            snippet_resp = self._extract_text(vacancy['snippet']['responsibility'])
            if snippet_resp and snippet_resp not in description:
                parts.append(f"\nОбязанности: {snippet_resp}")
        
        if vacancy.get('snippet', {}).get('requirement'):
            snippet_req = self._extract_text(vacancy['snippet']['requirement'])
            if snippet_req and snippet_req not in description:
                parts.append(f"\nТребования: {snippet_req}")
        
        return '\n'.join(parts)
    
    async def generate_cover_letter(self, resume: dict, vacancy: dict) -> Dict[str, Any]:
        """Generate personalized cover letter with random model and prompt selection"""
        # Случайный выбор модели и промпта
        selected_model = random.choice(self.models)
        selected_prompt = random.choice(self.prompts)
        
        logger.info(f"Selected model: {selected_model}, prompt: {selected_prompt}")
        
        # Get candidate info early for error handling
        first_name = resume.get('first_name', '')
        last_name = resume.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        
        try:
            # Load selected prompt from file
            system_prompt = self._load_prompt(selected_prompt)
            logger.info(f"System prompt loaded from {selected_prompt}: {system_prompt[:100]}...")
            
            resume_text = self._prepare_resume_text(resume)
            vacancy_text = self._prepare_vacancy_text(vacancy)
            
            user_prompt = f"""
Резюме кандидата:
{resume_text}

Текст вакансии:
{vacancy_text}
"""
            
            logger.info(f"Sending request to OpenAI model: {selected_model}")
            logger.debug(f"User prompt preview: {user_prompt[:200]}...")
            
            response = await self.client.chat.completions.create(
                model=selected_model,
                messages=[
                    {
                        "role": "system", 
                        "content": system_prompt
                    },
                    {"role": "user", "content": user_prompt}
                ],
                temperature=1.1,  
                max_tokens=500,
                top_p=0.7
            )
            
            letter = response.choices[0].message.content.strip()
            
            logger.info(f"Cover letter generated successfully with model {selected_model}. Words: {len(letter.split())}")
            logger.debug(f"Generated letter preview: {letter[:200]}...")
            
            return {
                "content": letter,
                "prompt_filename": selected_prompt,
                "ai_model": selected_model
            }
            
        except Exception as e:
            logger.error(f"Cover letter generation error: {type(e).__name__}: {e}")
            logger.error(f"Full error details:", exc_info=True)
            # В случае ошибки также возвращаем информацию о выбранных модели и промпте
            fallback_result = self._get_fallback_letter(vacancy, full_name)
            fallback_result["prompt_filename"] = selected_prompt
            fallback_result["ai_model"] = selected_model
            return fallback_result

    def _get_fallback_letter(self, vacancy: dict, full_name: str) -> Dict[str, Any]:
        """Return fallback cover letter on error"""
        logger.warning(f"Using fallback letter for candidate: {full_name}")
        
        fallback_letter = f"""Здравствуйте!

Меня очень заинтересовала вакансия {vacancy.get('name', 'в вашей компании')} в {vacancy.get('employer', {}).get('name', 'вашей компании')}. 

Мой профессиональный опыт и навыки хорошо соответствуют требованиям данной позиции. Готов(а) применить свои знания и компетенции для достижения целей компании и решения поставленных задач.

Буду рад(а) обсудить возможности сотрудничества в удобное для вас время.

С уважением,
{full_name or 'Кандидат'}"""
        
        logger.info(f"Fallback letter generated, length: {len(fallback_letter)} chars")
        
        return {
            "content": fallback_letter,
        }