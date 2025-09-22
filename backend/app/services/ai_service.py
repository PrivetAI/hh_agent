# app/services/ai_service.py
import os
import re
import logging
import random
import time
import asyncio
from typing import Dict, Any, Optional
from fastapi import HTTPException
from concurrent.futures import ThreadPoolExecutor
import asyncio
import random

from ..core.config import settings

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        logger.info("Initializing AI Service...")
        
        # Provider configuration
        self.ai_provider = 'openai'
        self.generation_timeout = 120  # Total timeout for generation
        
        # Initialize providers
        if self.ai_provider == 'openai':
            from .ai_providers.openai_provider import OpenAIProvider
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("OPENAI_API_KEY environment variable is not set")
                raise ValueError("OPENAI_API_KEY environment variable is required")
            self.provider = OpenAIProvider(api_key)
        elif self.ai_provider == 'gemini':
            from .ai_providers.gemini_provider import GeminiProvider
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logger.error("GOOGLE_API_KEY environment variable is not set")
                raise ValueError("GOOGLE_API_KEY environment variable is required")
            self.provider = GeminiProvider(api_key)
        else:
            raise ValueError(f"Unknown AI provider: {self.ai_provider}")
        
        logger.info(f"Using AI provider: {self.ai_provider}")
        
        # Prompts
        self.prompts = ["new_gpt.md"]
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
        self._prompts_cache = {}
        
        # Thread pool for CPU-bound tasks
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        self._validate_and_cache_prompts()
        logger.info("AI Service initialization completed successfully")

        # Batch processing semaphore to control concurrent AI generations
        self.ai_semaphore = asyncio.Semaphore(settings.HH_AI_BATCH_SIZE)
        logger.info(f"AI batch size set to {settings.HH_AI_BATCH_SIZE}")

        # Batch counter for delay logic
        self.batch_counter = 0
    
    def _validate_and_cache_prompts(self):
        """Validation and caching of prompts"""
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
        """Get prompt from cache or file"""
        if filename in self._prompts_cache:
            return self._prompts_cache[filename]
        
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
        """Extract text from HTML - CPU-bound operation"""
        if not html_text:
            return ""
        
        # Remove scripts and styles
        text = re.sub(r'<(script|style).*?>.*?</\1>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        text = re.sub(r'<.*?>', ' ', text)
        # Replace HTML entities
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&quot;', '"', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        # Normalize spaces
        text = ' '.join(text.split())
        
        return text.strip()
    
    async def _extract_text_async(self, html_text: str) -> str:
        """Run CPU-bound text extraction in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._extract_text, html_text)
    
    def _prepare_resume_text(self, resume: dict) -> str:
        """Prepare resume text for AI"""
        if not resume:
            return ""
        
        parts = []
        
        # About section
        if resume.get('skills'):
            parts.append(f"О себе: {resume['skills']}")
        
        # Work experience
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
        
        # Education
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
        
        # Languages
        if resume.get('language'):
            lang_list = []
            for lang in resume['language']:
                if lang.get('name') and lang.get('level', {}).get('name'):
                    lang_list.append(f"{lang['name']} - {lang['level']['name']}")
            
            if lang_list:
                parts.append(f"\nЯзыки: {', '.join(lang_list)}")
        
        return '\n'.join(parts)
    
    async def _prepare_vacancy_text(self, vacancy: dict) -> str:
        """Prepare vacancy text with async HTML extraction"""
        if not vacancy or not vacancy.get('description'):
            return ""
        
        description = vacancy['description']
        if '<' in description and '>' in description:
            # Use async text extraction for CPU-bound operation
            return await self._extract_text_async(description)
        
        return description
    
    async def generate_cover_letter(self, resume: dict, vacancy: dict, user_id: str) -> Dict[str, Any]:
        """Generate cover letter with timeout protection and fallback"""
        logger.info(f"Starting cover letter generation for user: {user_id}")
        logger.info(f"Using AI provider: {self.ai_provider}")
        start_time = time.time()
        
        # Select prompt
        selected_prompt = random.choice(self.prompts)
        logger.info(f"Selected prompt: {selected_prompt}")
        
        # Save name for fallback
        first_name = resume.get('first_name', '')
        last_name = resume.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        
        try:
            # Prepare texts asynchronously
            resume_text = self._prepare_resume_text(resume)
            vacancy_text = await self._prepare_vacancy_text(vacancy)
            vacancy_title = vacancy.get('name', '')
            
            if not resume_text:
                logger.error("Empty resume text after preparation")
                return self._get_fallback_letter(vacancy, full_name, selected_prompt)
            
            if not vacancy_text:
                logger.error("Empty vacancy text after preparation")
                return self._get_fallback_letter(vacancy, full_name, selected_prompt)
            logger.info(f"Text lengths - Resume: {len(resume_text)}, Vacancy: {len(vacancy_text)}")
            
            # Get prompt from cache
            system_prompt = self._get_prompt(selected_prompt)
            
            # Form user prompt
            user_prompt = f"""
##Резюме кандидата:
{resume_text}
##Позиция
{vacancy_title}
##Текст вакансии:
{vacancy_text}"""
            
            # Batch processing to reduce CPU load during high concurrent requests
            active_count = settings.HH_AI_BATCH_SIZE - self.ai_semaphore._value
            logger.info(f"AI Batch control: active={active_count}, max={settings.HH_AI_BATCH_SIZE}, waiting for semaphore...")

            # Small random delay to prevent thundering herd
            await asyncio.sleep(random.uniform(0, 1))

            async with self.ai_semaphore:
                self.batch_counter += 1
                logger.info(f"Acquired AI semaphore, generating letter (batch #{self.batch_counter})...")

                try:
                    letter = await asyncio.wait_for(
                        self.provider.generate(system_prompt, user_prompt),
                        timeout=self.generation_timeout
                    )
                except asyncio.TimeoutError:
                    logger.error(f"AI generation timed out after {self.generation_timeout} seconds")
                    return self._get_fallback_letter(vacancy, full_name, selected_prompt)
            
            signed_letter = f"""{letter}

С уважением,
{full_name}"""
            logger.info(f"Generated letter length: {len(signed_letter)} characters")
            
            total_duration = time.time() - start_time
            logger.info(f"Cover letter generation completed in {total_duration:.2f} seconds")
            
            return {
                "content": signed_letter,
                "prompt_filename": selected_prompt,
                "ai_model": 'secret1',
                "ai_provider": self.ai_provider,
                "is_fallback": False
            }
            
        except Exception as e:
            logger.error(f"Error during cover letter generation: {e}", exc_info=True)
            # Return fallback on any error
            return self._get_fallback_letter(vacancy, full_name, selected_prompt)
    
    def _get_fallback_letter(self, vacancy: dict, full_name: str, 
                            prompt_filename: str) -> Dict[str, Any]:
        """Generate fallback letter on error"""
        logger.warning("Generating fallback letter")
        
        vacancy_name = vacancy.get('name', 'вашу вакансию')
        company_name = vacancy.get('employer', {}).get('name', 'вашей компании')
        
        fallback_letter = f"""Здравствуйте!

Меня заинтересовала вакансия "{vacancy_name}" в {company_name}.

Мой профессиональный опыт и навыки соответствуют требованиям данной позиции. Готов применить свои знания для достижения целей компании.

Буду рад обсудить возможности сотрудничества.

С уважением,
{full_name}"""
        
        logger.info("Fallback letter generated")
        
        return {
            "content": fallback_letter,
            "prompt_filename": prompt_filename,
            "ai_model": 'fallback',
            "ai_provider": self.ai_provider,
            "is_fallback": True
        }
    
    def __del__(self):
        """Cleanup thread pool on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
