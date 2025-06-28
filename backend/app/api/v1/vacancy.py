from fastapi import APIRouter, Depends, Query, HTTPException, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from ...api.deps import get_current_user, check_user_credits, get_db
from ...crud.user import UserCRUD
from ...crud.payment import LetterGenerationCRUD
from ...crud.application import ApplicationCRUD

from ...models.db import User
from ...services.hh.service import HHService
from ...services.redis_service import RedisService
import logging
from ...models.schemas import (
    CoverLetter,
)
from ...models.schemas import ApplicationCreate  # Добавить импорт

router = APIRouter(prefix="/api", tags=["vacancy"])
hh_service = HHService()
redis_service = RedisService()
logger = logging.getLogger(__name__)


class ApplyRequest(BaseModel):
    message: str
    resume_id: Optional[str] = None


@router.get("/vacancies")
async def get_vacancies(
    text: Optional[str] = Query(None),
    area: Optional[str] = Query(None),
    salary: Optional[int] = Query(None),
    only_with_salary: Optional[bool] = Query(False),
    experience: Optional[str] = Query(None),
    employment: Optional[str] = Query(None),
    schedule: Optional[str] = Query(None),
    page: int = Query(0),
    per_page: int = Query(20, ge=20, le=100),
    user: User = Depends(get_current_user),
):
    """Get vacancies list with full descriptions"""
    params = {"page": page, "per_page": per_page}

    if text:
        params["text"] = text
    if area:
        params["area"] = area
    if salary:
        params["salary"] = salary
    if only_with_salary:
        params["only_with_salary"] = "true"
    if experience:
        params["experience"] = experience
    if employment:
        params["employment"] = employment
    if schedule:
        params["schedule"] = schedule

    result = await hh_service.search_vacancies_with_descriptions(
        user.hh_user_id, params
    )
    return result


@router.get("/vacancy/{vacancy_id}")
async def get_vacancy_details(vacancy_id: str, user: User = Depends(get_current_user)):
    """Get full vacancy details"""
    return await hh_service.get_vacancy_details(user.hh_user_id, vacancy_id)


@router.post("/vacancy/{vacancy_id}/analyze")
async def analyze_vacancy(
    vacancy_id: str,
    resume_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
):
    """Analyze vacancy match (free)"""
    return await hh_service.analyze_vacancy_match(
        user.hh_user_id, vacancy_id, resume_id
    )



# Метод generate_letter СО списанием кредитов:

@router.post("/vacancy/{vacancy_id}/generate-letter", response_model=CoverLetter)
async def generate_letter(
    vacancy_id: str,
    resume_id: Optional[str] = None,
    user: User = Depends(check_user_credits),  # Проверяем наличие кредитов
    db: Session = Depends(get_db)
):
    """Generate cover letter for vacancy (costs 1 credit)"""
    logger.info(f"Generating letter for vacancy {vacancy_id}, user {user.hh_user_id}")
    
    try:
        # Get vacancy details first
        vacancy = await hh_service.get_vacancy_details(user.hh_user_id, vacancy_id)
        vacancy_title = vacancy.get("name", "Неизвестная вакансия")
        
        # Generate letter (возвращает content, prompt_filename и ai_model)
        result = await hh_service.generate_cover_letter(
            user.hh_user_id, 
            vacancy_id, 
            resume_id
        )
        
        # Списываем кредит за генерацию
        success = UserCRUD.decrement_credits(db, user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Failed to deduct credits"
            )
        
        logger.info(f"Successfully generated letter and deducted 1 credit from user {user.id}")
        
        # Возвращаем полную информацию клиенту
        return CoverLetter(
            content=result["content"],
            prompt_filename=result["prompt_filename"],
            ai_model=result["ai_model"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating letter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/vacancy/{vacancy_id}/apply")
async def apply_to_vacancy(
    vacancy_id: str,
    application_data: ApplicationCreate,
    user: User = Depends(get_current_user),  # Изменено обратно на get_current_user
    db: Session = Depends(get_db)
):
    """Apply to vacancy with cover letter (FREE, credits already charged on generation)"""
    logger.info(f"Applying to vacancy {vacancy_id}, user {user.hh_user_id}")
    
    # Проверяем, не откликался ли уже
    if ApplicationCRUD.user_applied_to_vacancy(db, user.id, vacancy_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже откликались на эту вакансию"
        )
    
    error_message = None
    
    try:
        # Получаем токен
        token = await hh_service.redis_service.get_user_token(user.hh_user_id)
        if not token:
            raise HTTPException(401, "Token expired")
        
        # Отправляем отклик на HH
        await hh_service.hh_client.apply_to_vacancy(
            token, 
            vacancy_id, 
            resume_id=application_data.resume_id, 
            message=application_data.message
        )
        
        # Сохраняем в БД после успешной отправки на HH
        ApplicationCRUD.create(
            db,
            user_id=user.id,
            vacancy_id=vacancy_id,
            resume_id=application_data.resume_id,
            message=application_data.message,
            prompt_filename=application_data.prompt_filename,  # Сохраняем какой промпт использовался
            ai_model=application_data.ai_model  # Сохраняем какая модель использовалась
        )
        
        logger.info(f"Application sent successfully for user {user.id} to vacancy {vacancy_id}")
        
        return {"status": "success", "message": "Отклик успешно отправлен"}
        
    except HTTPException as http_exc:
        # Сохраняем информацию об ошибке
        error_message = f"HTTP Error: {http_exc.detail}"
        logger.error(f"HTTP error applying to vacancy: {error_message}")
        
        # Сохраняем в БД с информацией об ошибке
        ApplicationCRUD.create(
            db,
            user_id=user.id,
            vacancy_id=vacancy_id,
            resume_id=application_data.resume_id,
            message=error_message, # Сохраняем ошибку
            prompt_filename=application_data.prompt_filename,
            ai_model=application_data.ai_model
        )
        
        raise http_exc
    except Exception as e:
        # Сохраняем информацию об ошибке
        error_message = f"General Error: {str(e)}"
        logger.error(f"Error applying to vacancy: {error_message}")
        
        # Сохраняем в БД с информацией об ошибке
        ApplicationCRUD.create(
            db,
            user_id=user.id,
            vacancy_id=vacancy_id,
            resume_id=application_data.resume_id,
            error=error_message,  # Сохраняем ошибку
            prompt_filename=application_data.prompt_filename,
            ai_model=application_data.ai_model
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при отправке отклика: {str(e)}"
        )
    
@router.get("/history")
async def get_history(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get user's letter generation history"""
    history = LetterGenerationCRUD.get_user_history(db, user.id)
    return history
