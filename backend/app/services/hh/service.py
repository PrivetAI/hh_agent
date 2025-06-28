from datetime import datetime  # Добавить в начало файла
import asyncio
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .client import HHClient
from ..redis_service import RedisService
from ..ai_service import AIService
from ...core.config import settings
from ...core.database import get_db
from ...crud.vacancy import VacancyCRUD

class HHService:
    def __init__(self):
        self.hh_client = HHClient()
        self.redis_service = RedisService()
        self.ai_service = AIService()

    async def _get_token(self, hh_user_id: str) -> str:
        """Get user token with error handling"""
        token = await self.redis_service.get_user_token(hh_user_id)
        if not token:
            raise HTTPException(401, "Token expired")
        return token

    async def get_user_resumes(self, hh_user_id: str) -> List[Dict[str, Any]]:
        """Get all user's resumes with full text"""
        cached = await self.redis_service.get_json(f"resumes:full:{hh_user_id}")
        if cached:
            return cached

        token = await self._get_token(hh_user_id)
        resumes = await self.hh_client.get_resumes(token)

        # Cache for 1 minute
        await self.redis_service.set_json(f"resumes:full:{hh_user_id}", resumes, 60)
        return resumes

    async def get_user_resume(self, hh_user_id: str, resume_id: str = None) -> Optional[Dict[str, Any]]:
        """Get specific resume or first resume"""
        resumes = await self.get_user_resumes(hh_user_id)
        if not resumes:
            return None

        if resume_id:
            return next((r for r in resumes if r.get("id") == resume_id), None)
        return resumes[0]

    async def search_vacancies(self, hh_user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search vacancies without loading full descriptions"""
        token = await self._get_token(hh_user_id)
        result = await self.hh_client.search_vacancies(token, params)
        
        # Normalize response
        if "items" in result:
            for vacancy in result["items"]:
                self._normalize_vacancy(vacancy)
        
        return result

    def _normalize_vacancy(self, vacancy: Dict[str, Any]) -> None:
        """Normalize vacancy data"""
        if "employer" not in vacancy:
            vacancy["employer"] = {"name": "Не указано"}
        if "area" not in vacancy:
            vacancy["area"] = {"name": "Не указано"}
        if "salary" not in vacancy:
            vacancy["salary"] = None

    async def search_vacancies_with_descriptions(self, hh_user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search vacancies and load full descriptions with DB caching"""
        token = await self._get_token(hh_user_id)
        result = await self.hh_client.search_vacancies(token, params)

        if "items" in result and result["items"]:
            # Получаем database session
            db_gen = get_db()
            db = next(db_gen)

            try:
                # Собираем ID всех вакансий из результатов
                vacancy_ids = [v["id"] for v in result["items"]]

                # Обновляем last_searched_at для всех найденных вакансий
                VacancyCRUD.update_last_searched(db, vacancy_ids)

                # Определяем какие вакансии нужно обновить (старше 12ч или отсутствуют)
                stale_ids = VacancyCRUD.get_stale_vacancies(db, vacancy_ids, hours=12)

                # Загружаем из БД актуальные вакансии
                fresh_vacancies = {}
                for vacancy_id in vacancy_ids:
                    if vacancy_id not in stale_ids:
                        db_vacancy = VacancyCRUD.get_by_id(db, vacancy_id)
                        if db_vacancy:
                            fresh_vacancies[vacancy_id] = db_vacancy.full_data

                # Загружаем устаревшие вакансии с HH API
                if stale_ids:
                    batch_size = settings.HH_BATCH_SIZE

                    for i in range(0, len(stale_ids), batch_size):
                        batch = stale_ids[i:i + batch_size]

                        # Add delay between batches (except for first batch)
                        if i > 0:
                            await asyncio.sleep(settings.HH_BATCH_DELAY)

                        # Process batch
                        batch_tasks = []
                        for vacancy_id in batch:
                            batch_tasks.append(self._load_and_save_vacancy(token, vacancy_id, db))

                        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                        for vacancy_id, result_item in zip(batch, batch_results):
                            if isinstance(result_item, Exception):
                                print(f"Error loading vacancy {vacancy_id}: {result_item}")
                                # Используем базовую информацию из поиска
                                basic_info = next((v for v in result["items"] if v["id"] == vacancy_id), None)
                                if basic_info:
                                    fresh_vacancies[vacancy_id] = self._get_basic_vacancy_info(basic_info)
                            else:
                                fresh_vacancies[vacancy_id] = result_item

                # Формируем финальный результат с правильным порядком
                final_items = []
                for vacancy in result["items"]:
                    if vacancy["id"] in fresh_vacancies:
                        final_items.append(fresh_vacancies[vacancy["id"]])
                    else:
                        # Fallback для вакансий, которые не удалось загрузить
                        final_items.append(self._get_basic_vacancy_info(vacancy))

                result["items"] = final_items

            finally:
                # Закрываем сессию
                db.close()

        return result
    async def _load_and_save_vacancy(self, token: str, vacancy_id: str, db: Session) -> Dict[str, Any]:
        """Load vacancy from HH API and save to DB"""
        try:
            # Get full vacancy data
            full_vacancy = await self.hh_client.get_vacancy(token, vacancy_id)
            
            # Extract description as plain text
            if full_vacancy.get("description"):
                full_vacancy["description"] = self.ai_service._extract_text(
                    full_vacancy.get("description", "")
                )
            
            # Save to DB
            VacancyCRUD.create_or_update(db, full_vacancy)
            
            # Extract essential fields for response
            return self._extract_vacancy_details(full_vacancy)
            
        except Exception as e:
            print(f"Error loading vacancy {vacancy_id}: {e}")
            raise e

    def _extract_vacancy_details(self, full_vacancy: Dict[str, Any]) -> Dict[str, Any]:
        """Extract essential fields from full vacancy"""
        return {
            "id": full_vacancy["id"],
            "name": full_vacancy.get("name", ""),
            "salary": full_vacancy.get("salary"),
            "employer": full_vacancy.get("employer", {"name": "Не указано"}),
            "area": full_vacancy.get("area", {"name": "Не указано"}),
            "published_at": full_vacancy.get("published_at"),
            "schedule": full_vacancy.get("schedule"),
            "employment": full_vacancy.get("employment"),
            "description": full_vacancy.get("description", ""),
            "snippet": full_vacancy.get("snippet"),
            "experience": full_vacancy.get("experience"),
            "key_skills": full_vacancy.get("key_skills", []),
            "professional_roles": full_vacancy.get("professional_roles", []),
            "accept_handicapped": full_vacancy.get("accept_handicapped"),
            "accept_kids": full_vacancy.get("accept_kids"),
            "branded_description": full_vacancy.get("branded_description"),
            "vacancy_constructor_template": full_vacancy.get("vacancy_constructor_template"),
            "working_days": full_vacancy.get("working_days"),
            "working_time_intervals": full_vacancy.get("working_time_intervals"),
            "working_time_modes": full_vacancy.get("working_time_modes")
        }

    def _get_basic_vacancy_info(self, vacancy: Dict[str, Any]) -> Dict[str, Any]:
        """Return basic vacancy info on error"""
        return {
            "id": vacancy["id"],
            "name": vacancy.get("name", ""),
            "salary": vacancy.get("salary"),
            "employer": vacancy.get("employer", {"name": "Не указано"}),
            "area": vacancy.get("area", {"name": "Не указано"}),
            "published_at": vacancy.get("published_at"),
            "snippet": vacancy.get("snippet"),
            "description": "Не удалось загрузить описание"
        }

    async def get_vacancy_details(self, hh_user_id: str, vacancy_id: str) -> Dict[str, Any]:
        """Get full vacancy details with DB caching"""
        # Сначала проверяем БД
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            db_vacancy = VacancyCRUD.get_by_id(db, vacancy_id)
            
            # Если вакансия свежая (обновлена менее 12ч назад), возвращаем из БД
            if db_vacancy and (datetime.utcnow() - db_vacancy.updated_at).total_seconds() < 43200:
                return db_vacancy.full_data
            
            # Иначе загружаем с HH API
            token = await self._get_token(hh_user_id)
            vacancy = await self.hh_client.get_vacancy(token, vacancy_id)
            
            # Extract plain text from HTML description
            if vacancy.get("description"):
                vacancy["description"] = self.ai_service._extract_text(vacancy.get("description", ""))
            
            # Сохраняем в БД
            VacancyCRUD.create_or_update(db, vacancy)
            
            return self._extract_vacancy_details(vacancy)
            
        finally:
            db_gen.close()

    async def analyze_vacancy_match(self, hh_user_id: str, vacancy_id: str, resume_id: str) -> Dict[str, Any]:
        """Analyze match between resume and vacancy"""
        cache_key = f"analysis:{hh_user_id}:{vacancy_id}:{resume_id}"
        cached = await self.redis_service.get_json(cache_key)
        if cached:
            return cached
        
        token = await self._get_token(hh_user_id)
        resume = await self.get_user_resume(hh_user_id, resume_id)
        
        # Получаем вакансию из БД или с API
        vacancy = await self.get_vacancy_details(hh_user_id, vacancy_id)
        
        score = await self.ai_service.analyze_match(resume, vacancy)
        await self.redis_service.set_json(cache_key, score, 86400)
        return score

    async def generate_cover_letter(self, hh_user_id: str, vacancy_id: str, resume_id: str) -> Dict[str, Any]:
        """Generate cover letter for vacancy"""
        token = await self._get_token(hh_user_id)
        resume = await self.get_user_resume(hh_user_id, resume_id)
        
        # Получаем вакансию из БД или с API
        vacancy = await self.get_vacancy_details(hh_user_id, vacancy_id)
        
        return await self.ai_service.generate_cover_letter(resume, vacancy)

    async def get_dictionaries(self) -> Dict[str, Any]:
        """Get HH dictionaries with caching"""
        cached = await self.redis_service.get_json("dictionaries")
        if cached:
            return cached
        
        data = await self.hh_client.get_dictionaries()
        result = {
            "experience": data.get("experience", []),
            "employment": data.get("employment", []),
            "schedule": data.get("schedule", [])
        }
        
        await self.redis_service.set_json("dictionaries", result, 604800)
        return result

    async def get_areas(self) -> Dict[str, Any]:
        """Get areas with caching"""
        cached = await self.redis_service.get_json("areas")
        if cached:
            return cached
        
        data = await self.hh_client.get_areas()
        await self.redis_service.set_json("areas", data, 604800)
        return data
