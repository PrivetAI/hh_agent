import os
import re
import logging
import random
import time
from typing import Dict, Any, Optional
import google.generativeai as genai
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        logger.info("Initializing AI Service...")
        
        # ===== КОНФИГУРАЦИЯ ПРОВАЙДЕРА =====
        # Установите 'openai' или 'gemini'
        self.ai_provider = 'openai'  # <-- ПЕРЕКЛЮЧЕНИЕ МЕЖДУ МОДЕЛЯМИ
        
        # Инициализация провайдеров
        if self.ai_provider == 'openai':
            self._init_openai()
        elif self.ai_provider == 'gemini':
            self._init_gemini()
        else:
            raise ValueError(f"Unknown AI provider: {self.ai_provider}")
        
        logger.info(f"Using AI provider: {self.ai_provider}")
        
        # Промпты (общие для всех провайдеров)
        # self.prompts = ["one.md", "two.md", "three.md", "four.md", "five.md", "six.md", "seven.md"]
        self.prompts = ["gemini.md"]
        
        # Путь к папке с промптами 
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
        
        # Кэш для промптов
        self._prompts_cache = {}
        
        self._validate_and_cache_prompts()
        logger.info("AI Service initialization completed successfully")
    
    def _init_openai(self):
       """Initialize OpenAI - сохраняем только ключ, клиент создаём на каждый запрос"""
       api_key = os.getenv("OPENAI_API_KEY")
       if not api_key:
           logger.error("OPENAI_API_KEY environment variable is not set")
           raise ValueError("OPENAI_API_KEY environment variable is required")

       logger.info("OpenAI API key found, length: %d characters", len(api_key))
       # НЕ создаём постоянный AsyncOpenAI клиент здесь — будем создавать и закрывать его на каждый запрос
       self.openai_api_key = api_key
       self.client = None
       self.models = ["gpt-5"]  #o3 добавляет хуеты 
    def _init_gemini(self):
        """Инициализация Google Gemini"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("GOOGLE_API_KEY environment variable is not set")
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        logger.info("Google API key found, length: %d characters", len(api_key))
        genai.configure(api_key=api_key)
        self.models = ["gemini-2.5-pro"]   # не менять

    
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
    
    async def _generate_with_openai(self, system_prompt: str, user_prompt: str, model: str) -> str:
        """Минимальная, надёжная версия для GPT-5 (Responses API).
        Создаёт AsyncOpenAI в `async with` на время одного запроса, чтобы избежать зависаний.
        """
        import time
        from openai import AsyncOpenAI

        logger.info("OpenAI request start")
        logger.debug("model=%s", model)
        logger.debug("system_prompt_len=%d user_prompt_len=%d", len(system_prompt or ""), len(user_prompt or ""))

        start_ts = time.time()
        # Объединяем промпты
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        try:
            # используем ключ, сохранённый при инициализации
            api_key = getattr(self, "openai_api_key", None)
            if not api_key:
                logger.error("OpenAI API key missing on service instance")
                raise RuntimeError("OpenAI API key not configured")

            # Создаём и используем клиент внутри контекста — гарантированное закрытие/cleanup
            async with AsyncOpenAI(api_key=api_key) as client:
                logger.info("Using temporary AsyncOpenAI client for this request")
                # вызов Responses API — минимально и согласно доке для gpt-5
                resp = await client.responses.create(
                    model=model,
                    input=[
                        {
                            "role": "user",
                            "content": full_prompt,
                        },
                    ],
                    
                    reasoning={"effort": "medium"},
                    # при желании: max_output_tokens=15000
                )

            elapsed = time.time() - start_ts
            logger.info("OpenAI call finished in %.2fs", elapsed)

            # извлечение текста — очень простое (output_text или часть output)
            text = ""
            if getattr(resp, "output_text", None):
                text = resp.output_text.strip()
            else:
                out = getattr(resp, "output", None)
                if out:
                    parts = []
                    for item in out:
                        content = item.get("content") if isinstance(item, dict) else getattr(item, "content", None)
                        if isinstance(content, list):
                            for c in content:
                                if isinstance(c, dict) and c.get("type") == "output_text" and c.get("text"):
                                    parts.append(c["text"])
                                elif isinstance(c, str):
                                    parts.append(c)
                        elif isinstance(content, str):
                            parts.append(content)
                    if parts:
                        text = "\n".join(p for p in parts if p).strip()

            logger.info("Response id=%s", getattr(resp, "id", None))
            logger.info("Response length=%d", len(text or ""))
            logger.debug("Response preview: %s", (text or "")[:400])

            return (text or "").strip()

        except Exception as e:
            logger.exception("OpenAI request error: %s", e)
            # пробрасываем ошибку наверх — ваш generate_cover_letter это обработает
            raise

    async def _generate_with_gemini(self, system_prompt: str, user_prompt: str, model: str) -> str:
        """Генерация через Google Gemini API с обработкой safety filters"""
    
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        
        # Create safety settings using proper objects
        safety_settings = [
        {
            "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
            "threshold": HarmBlockThreshold.BLOCK_NONE,
        },
        {
            "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            "threshold": HarmBlockThreshold.BLOCK_NONE,
        },
        {
            "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            "threshold": HarmBlockThreshold.BLOCK_NONE,
        },
        {
            "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            "threshold": HarmBlockThreshold.BLOCK_NONE,
        },
    ]
        
        gemini_model = genai.GenerativeModel(
            model_name=model,
            generation_config={
                "temperature": 1.1,
                "top_p": 0.7,
                "max_output_tokens": 10000,
            },
            safety_settings=safety_settings
        )

        # Объединяем промпты для Gemini
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Генерируем ответ
        response = gemini_model.generate_content(full_prompt)

        # Проверяем наличие текста в ответе
        if not response.parts or not response.text:
            # Проверяем finish_reason
            if response.candidates and response.candidates[0].finish_reason:
                finish_reason = response.candidates[0].finish_reason
                logger.warning(f"Gemini response blocked with finish_reason: {finish_reason}")

            raise Exception("Empty response from Gemini")

        letter = response.text.strip()

        # Логируем использование (если доступно)
        if hasattr(response, 'usage_metadata'):
            logger.info(f"Gemini token usage - prompt: {response.usage_metadata.prompt_token_count}, "
                      f"completion: {response.usage_metadata.candidates_token_count}, "
                      f"total: {response.usage_metadata.total_token_count}")

        return letter

    async def generate_cover_letter(self, resume: dict, vacancy: dict, user_id: str) -> Dict[str, Any]:
        """Генерация сопроводительного письма"""
        logger.info(f"Starting cover letter generation for user: {user_id}")
        logger.info(f"Using AI provider: {self.ai_provider}")
        start_time = time.time()
        
        # Выбираем модель и промпт
        selected_model = random.choice(self.models)
        selected_prompt = random.choice(self.prompts)
        logger.info(f"Selected model: {selected_model}, prompt: {selected_prompt}")
        
        # Сохраняем ФИО для fallback (если нужно)
        first_name = resume.get('first_name', '')
        last_name = resume.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        
        try:
            # Подготавливаем тексты напрямую из оригинального резюме
            resume_text = self._prepare_resume_text(resume)
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
            
            # ИЗМЕНЕНО: Убрали инструкцию про автоматическое добавление подписи
            user_prompt = f"""
    ##Резюме кандидата:
    {resume_text}
    ##Имя кандидата {full_name}
       
    ##Текст вакансии:
    {vacancy_text}"""
            
            # Генерируем письмо в зависимости от провайдера
            logger.info(f"Sending request to {self.ai_provider}")
            
            if self.ai_provider == 'openai':
                letter = await self._generate_with_openai(system_prompt, user_prompt, selected_model)
            elif self.ai_provider == 'gemini':
                letter = await self._generate_with_gemini(system_prompt, user_prompt, selected_model)
            else:
                raise ValueError(f"Unknown AI provider: {self.ai_provider}")
            
            logger.info(f"Generated letter length: {len(letter)} characters")
            
            # УДАЛЕНО: Больше не добавляем подпись вручную
            # if full_name:
            #     letter = self._add_signature(letter, full_name)
            
            total_duration = time.time() - start_time
            logger.info(f"Cover letter generation completed in {total_duration:.2f} seconds")
            
            return {
                "content": letter,
                "prompt_filename": selected_prompt,
                "ai_model": selected_model,
                "ai_provider": self.ai_provider
            }
            
        except Exception as e:
            logger.error(f"Error during cover letter generation: {e}", exc_info=True)
            
            # Возвращаем fallback письмо с информацией о модели и промпте
            fallback_result = self._get_fallback_letter(vacancy, full_name)
            fallback_result["prompt_filename"] = selected_prompt
            fallback_result["ai_model"] = selected_model
            fallback_result["ai_provider"] = self.ai_provider
            return fallback_result
    
    def _get_fallback_letter(self, vacancy: dict, full_name: str) -> Dict[str, Any]:
        """Генерация запасного письма при ошибке"""
        logger.warning("Generating fallback letter")
        
        vacancy_name = vacancy.get('name', 'вашу вакансию')
        company_name = vacancy.get('employer', {}).get('name', 'вашей компании')
        
        # Письмо уже содержит подпись
        fallback_letter = f"""Здравствуйте!
    
Меня заинтересовала вакансия "{vacancy_name}" в {company_name}.

Мой профессиональный опыт и навыки соответствуют требованиям данной позиции. Готов применить свои знания для достижения целей компании.

Буду рад обсудить возможности сотрудничества.

С уважением,
{full_name or 'Кандидат'}"""
        
        logger.info("Fallback letter generated")
        return {"content": fallback_letter}