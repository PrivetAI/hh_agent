from datetime import datetime
import asyncio
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from sqlalchemy.orm import Session
import logging
from .client import HHClient
from ..redis_service import RedisService
from ..ai_service import AIService
from ...core.config import settings
from ...core.database import get_db
from ...crud.vacancy import VacancyCRUD
from ...crud.application import ApplicationCRUD

logger = logging.getLogger(__name__)

RESUME_LIST_CACHE_TTL = 300  # seconds


def _resume_list_cache_key(hh_user_id: str) -> str:
    return f"resumes:api:{hh_user_id}"


def _resume_item_cache_key(hh_user_id: str, resume_id: str) -> str:
    return f"resumes:api:{hh_user_id}:{resume_id}"


class HHService:
    def __init__(self):
        self.hh_client = HHClient()
        self.redis_service = RedisService()
        self.ai_service = AIService()
        self.cover_letter_batch_size = max(1, int(settings.HH_BATCH_SIZE))
        self.cover_letter_batch_delay = max(0.0, float(settings.HH_BATCH_DELAY))
        self.cover_letter_semaphore = asyncio.Semaphore(self.cover_letter_batch_size)
        self.cover_letter_waiters = 0
        self.cover_letter_active = 0

    async def _get_token(self, hh_user_id: str) -> str:
        """Get user token with error handling"""
        token = await self.redis_service.get_user_token(hh_user_id)
        if not token:
            raise HTTPException(401, "Token expired")
        return token

    async def get_user_resumes(self, hh_user_id: str) -> List[Dict[str, Any]]:
        """Get all user's resumes from API (without RTF)"""
        cache_key = _resume_list_cache_key(hh_user_id)
        cached = await self.redis_service.get_json(cache_key)
        if cached is not None:
            return cached

        token = await self._get_token(hh_user_id)
        resumes = await self.hh_client.get_resumes(token) or []

        await self.redis_service.set_json(
            cache_key,
            resumes,
            RESUME_LIST_CACHE_TTL,
        )

        if resumes:
            tasks = []
            for resume in resumes:
                resume_id = resume.get("id")
                if not resume_id:
                    continue
                tasks.append(
                    self.redis_service.set_json(
                        _resume_item_cache_key(hh_user_id, resume_id),
                        resume,
                        RESUME_LIST_CACHE_TTL,
                    )
                )
            if tasks:
                await asyncio.gather(*tasks)

        return resumes

    async def get_user_resume(
        self, hh_user_id: str, resume_id: str = None
    ) -> Optional[Dict[str, Any]]:
        """Get specific resume or first resume"""
        if resume_id:
            resume_cache_key = _resume_item_cache_key(hh_user_id, resume_id)
            cached_resume = await self.redis_service.get_json(resume_cache_key)
            if cached_resume is not None:
                return cached_resume

        resumes = await self.get_user_resumes(hh_user_id)
        if not resumes:
            return None

        if resume_id:
            resume = next((r for r in resumes if r.get("id") == resume_id), None)
            if resume:
                await self.redis_service.set_json(
                    resume_cache_key,
                    resume,
                    RESUME_LIST_CACHE_TTL,
                )
            return resume

        resume = resumes[0]
        first_resume_id = resume.get("id")
        if first_resume_id:
            await self.redis_service.set_json(
                _resume_item_cache_key(hh_user_id, first_resume_id),
                resume,
                RESUME_LIST_CACHE_TTL,
            )
        return resume

    async def search_vacancies(
        self, hh_user_id: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search vacancies without loading full descriptions"""
        token = await self._get_token(hh_user_id)
        result = await self.hh_client.search_vacancies(token, params)
        return result




    async def _load_and_save_vacancy(
        self, token: str, vacancy_id: str, db: Session
    ) -> Dict[str, Any]:
        """Load vacancy from HH API and save to DB"""
        try:
            full_vacancy = await self.hh_client.get_vacancy(token, vacancy_id)

            if full_vacancy.get("description"):
                full_vacancy["description"] = self.ai_service._extract_text(
                    full_vacancy.get("description", "")
                )

            VacancyCRUD.create_or_update(db, full_vacancy)
            return full_vacancy

        except Exception as e:
            logger.error(f"Error loading vacancy {vacancy_id}: {e}")
            raise e

    async def get_vacancy_details(
        self, hh_user_id: str, vacancy_id: str
    ) -> Dict[str, Any]:
        """Get full vacancy details with DB caching"""
        db_gen = get_db()
        db = next(db_gen)

        try:
            db_vacancy = VacancyCRUD.get_by_id(db, vacancy_id)

            if (
                db_vacancy
                and (datetime.utcnow() - db_vacancy.updated_at).total_seconds() < 43200
            ):
                return db_vacancy.full_data

            token = await self._get_token(hh_user_id)
            vacancy = await self.hh_client.get_vacancy(token, vacancy_id)

            if vacancy.get("description"):
                vacancy["description"] = self.ai_service._extract_text(
                    vacancy.get("description", "")
                )

            VacancyCRUD.create_or_update(db, vacancy)
            return vacancy

        finally:
            db_gen.close()


    async def generate_cover_letter(
        self, hh_user_id: str, vacancy_id: str, resume_id: str, user_id: str = None
    ) -> Dict[str, Any]:
        """Generate cover letter with proper isolation"""

        # Get resume and vacancy data (these are fast operations)
        resume = await self.get_user_resume(hh_user_id, resume_id)
        if not resume:
            raise HTTPException(404, "Resume not found")

        vacancy = await self.get_vacancy_details(hh_user_id, vacancy_id)

        slot_acquired = False
        try:
            await self._acquire_cover_letter_slot()
            slot_acquired = True
            result = await self.ai_service.generate_cover_letter(resume, vacancy, user_id)
            return result

        except asyncio.CancelledError:
            logger.error("Cover letter generation was cancelled")
            raise HTTPException(500, "Generation was cancelled")
        except Exception as e:
            logger.error(f"Error in cover letter generation: {e}")
            raise
        finally:
            if slot_acquired:
                await self._release_cover_letter_slot()

    async def _acquire_cover_letter_slot(self) -> None:
        """Reserve a slot in the cover letter generation batch."""
        self.cover_letter_waiters += 1
        try:
            await self.cover_letter_semaphore.acquire()
        finally:
            if self.cover_letter_waiters > 0:
                self.cover_letter_waiters -= 1
            else:
                self.cover_letter_waiters = 0

        self.cover_letter_active += 1

    async def _release_cover_letter_slot(self) -> None:
        """Release a previously acquired cover letter generation slot."""
        try:
            if self.cover_letter_batch_delay > 0 and self.cover_letter_waiters > 0:
                await asyncio.sleep(self.cover_letter_batch_delay)
        finally:
            if self.cover_letter_active > 0:
                self.cover_letter_active -= 1
            self.cover_letter_semaphore.release()

    def estimate_cover_letter_timeout(self, include_current: bool = False) -> float:
        """Estimate total time budget needed for cover letter generation."""
        per_request = float(self.ai_service.generation_timeout) + self.cover_letter_batch_delay
        if per_request <= 0:
            per_request = max(float(self.ai_service.generation_timeout), 60.0)

        tasks_ahead = self.cover_letter_active + self.cover_letter_waiters
        if include_current:
            tasks_ahead += 1

        batches_before = tasks_ahead // self.cover_letter_batch_size
        return max(per_request, (batches_before + 1) * per_request)

    async def get_dictionaries(self) -> Dict[str, Any]:
       """Get HH dictionaries with caching"""
       cached = await self.redis_service.get_json("dictionaries")
       if cached:
           return cached
       data = await self.hh_client.get_dictionaries()
       result = {
           "experience": data.get("experience", []),
           "employment": data.get("employment", []),
           "schedule": data.get("schedule", []),
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

    async def get_saved_searches(self, hh_user_id: str) -> Dict[str, Any]:
        """Get user's saved searches with caching"""
        cache_key = f"saved_searches:{hh_user_id}"
        cached = await self.redis_service.get_json(cache_key)
        if cached:
            return cached

        token = await self._get_token(hh_user_id)
        saved_searches = await self.hh_client.get_saved_searches(token)

        await self.redis_service.set_json(cache_key, saved_searches, 60)
        return saved_searches
    
    
    async def search_vacancies_with_descriptions(
        self, hh_user_id: str, params: Dict[str, Any], user_id: str, filter_applied: bool = True
    ) -> Dict[str, Any]:
        """Search vacancies and load full descriptions with DB caching and applied check"""
        token = await self._get_token(hh_user_id)

        result = await self.hh_client.search_vacancies(token, params)

        if "items" in result and result["items"]:
            db_gen = get_db()
            db = next(db_gen)

            try:
                vacancy_ids = [v["id"] for v in result["items"]]
                VacancyCRUD.update_last_searched(db, vacancy_ids)

                # Получаем список вакансий, на которые пользователь уже откликнулся
                applied_vacancies = ApplicationCRUD.get_user_applied_vacancies(db, user_id, vacancy_ids)
                applied_set = set(applied_vacancies)

                # Фильтруем вакансии, на которые уже откликнулись
                if filter_applied:
                    filtered_items = [v for v in result["items"] if v["id"] not in applied_set]
                    # Обновляем результаты
                    result["items"] = filtered_items
                    result["found"] = len(filtered_items)
                    vacancy_ids = [v["id"] for v in filtered_items]

                stale_ids = VacancyCRUD.get_stale_vacancies(db, vacancy_ids, hours=12)

                fresh_vacancies = {}
                for vacancy_id in vacancy_ids:
                    if vacancy_id not in stale_ids:
                        db_vacancy = VacancyCRUD.get_by_id(db, vacancy_id)
                        if db_vacancy:
                            fresh_vacancies[vacancy_id] = db_vacancy.full_data

                if stale_ids:
                    batch_size = settings.HH_BATCH_SIZE

                    for i in range(0, len(stale_ids), batch_size):
                        batch = stale_ids[i : i + batch_size]

                        if i > 0:
                            await asyncio.sleep(settings.HH_BATCH_DELAY)

                        batch_tasks = []
                        for vacancy_id in batch:
                            batch_tasks.append(
                                self._load_and_save_vacancy(token, vacancy_id, db)
                            )

                        batch_results = await asyncio.gather(
                            *batch_tasks, return_exceptions=True
                        )

                        for vacancy_id, result_item in zip(batch, batch_results):
                            if isinstance(result_item, Exception):
                                logger.error(
                                    f"Error loading vacancy {vacancy_id}: {result_item}"
                                )
                                basic_info = next(
                                    (
                                        v
                                        for v in result["items"]
                                        if v["id"] == vacancy_id
                                    ),
                                    None,
                                )
                                if basic_info:
                                    fresh_vacancies[vacancy_id] = basic_info
                            else:
                                fresh_vacancies[vacancy_id] = result_item

                final_items = []
                for vacancy in result["items"]:
                    vacancy_data = fresh_vacancies.get(vacancy["id"], vacancy)
                    
                    # Добавляем флаг applied (всегда false после фильтрации)
                    vacancy_data["applied"] = vacancy["id"] in applied_set
                    
                    final_items.append(vacancy_data)

                result["items"] = final_items

            finally:
                db.close()

        return result

    async def search_vacancies_by_url(
        self, hh_user_id: str, search_url: str, user_id: str, filter_applied: bool = True
    ) -> Dict[str, Any]:
        """Search vacancies by saved search URL"""
        token = await self._get_token(hh_user_id)
        
        # Use the URL directly with HH API
        result = await self.hh_client.search_vacancies_by_url(token, search_url)
        
        if "items" in result and result["items"]:
            db_gen = get_db()
            db = next(db_gen)

            try:
                vacancy_ids = [v["id"] for v in result["items"]]
                VacancyCRUD.update_last_searched(db, vacancy_ids)

                # Get list of vacancies user has already applied to
                applied_vacancies = ApplicationCRUD.get_user_applied_vacancies(db, user_id, vacancy_ids)
                applied_set = set(applied_vacancies)

                # Filter out applied vacancies
                if filter_applied:
                    filtered_items = [v for v in result["items"] if v["id"] not in applied_set]
                    result["items"] = filtered_items
                    result["found"] = len(filtered_items)
                    vacancy_ids = [v["id"] for v in filtered_items]

                # Continue with loading descriptions...
                stale_ids = VacancyCRUD.get_stale_vacancies(db, vacancy_ids, hours=12)

                fresh_vacancies = {}
                for vacancy_id in vacancy_ids:
                    if vacancy_id not in stale_ids:
                        db_vacancy = VacancyCRUD.get_by_id(db, vacancy_id)
                        if db_vacancy:
                            fresh_vacancies[vacancy_id] = db_vacancy.full_data

                if stale_ids:
                    batch_size = settings.HH_BATCH_SIZE

                    for i in range(0, len(stale_ids), batch_size):
                        batch = stale_ids[i : i + batch_size]

                        if i > 0:
                            await asyncio.sleep(settings.HH_BATCH_DELAY)

                        batch_tasks = []
                        for vacancy_id in batch:
                            batch_tasks.append(
                                self._load_and_save_vacancy(token, vacancy_id, db)
                            )

                        batch_results = await asyncio.gather(
                            *batch_tasks, return_exceptions=True
                        )

                        for vacancy_id, result_item in zip(batch, batch_results):
                            if isinstance(result_item, Exception):
                                logger.error(
                                    f"Error loading vacancy {vacancy_id}: {result_item}"
                                )
                                basic_info = next(
                                    (
                                        v
                                        for v in result["items"]
                                        if v["id"] == vacancy_id
                                    ),
                                    None,
                                )
                                if basic_info:
                                    fresh_vacancies[vacancy_id] = basic_info
                            else:
                                fresh_vacancies[vacancy_id] = result_item

                final_items = []
                for vacancy in result["items"]:
                    vacancy_data = fresh_vacancies.get(vacancy["id"], vacancy)
                    vacancy_data["applied"] = vacancy["id"] in applied_set
                    final_items.append(vacancy_data)

                result["items"] = final_items

            finally:
                db.close()

        return result
