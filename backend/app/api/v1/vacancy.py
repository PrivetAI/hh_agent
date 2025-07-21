from fastapi import APIRouter, Depends, Query, HTTPException, status
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
    ApplicationCreate
)

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
    remote: Optional[bool] = Query(None),
    excluded_text: Optional[str] = Query(None),
    page: int = Query(0),
    per_page: int = Query(20, ge=20, le=100),
    period: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    resume_id: Optional[str] = Query(None),
    for_resume: Optional[bool] = Query(None),
    saved_search_id: Optional[str] = Query(None),
    saved_search_url: Optional[str] = Query(None),
    no_magic: Optional[bool] = Query(None),
    filter_applied: Optional[bool] = Query(True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get vacancies list with full descriptions - unified endpoint"""
    
    # If saved_search_url is provided, use it directly
    if saved_search_url:
        result = await hh_service.search_vacancies_by_url(
            user.hh_user_id, saved_search_url, str(user.id), filter_applied
        )
        return result
    
    params = {"page": page, "per_page": per_page}

    if text:
        params["text"] = text
    if area:
        params["area"] = area
    if salary is not None:
        params["salary"] = salary
    if only_with_salary:
        params["only_with_salary"] = "true"
    if experience:
        params["experience"] = experience
    if employment:
        params["employment"] = employment
    if schedule:
        params["schedule"] = schedule
    if remote is True:
        params["remote"] = True
    if excluded_text:
        params["excluded_text"] = excluded_text
    if period is not None:
        params["period"] = period
    if date_from:
        params["date_from"] = date_from
    if saved_search_id:
        params["saved_search_id"] = saved_search_id
        params["per_page"] = 100
    if no_magic is not None:
        params["no_magic"] = "true" if no_magic else "false"

    if for_resume and resume_id:
        result = await hh_service.search_vacancies_by_resume(
            user.hh_user_id, resume_id, params
        )
    else:
        result = await hh_service.search_vacancies_with_descriptions(
            user.hh_user_id, params, str(user.id), filter_applied
        )
    
    return result


@router.get("/vacancy/{vacancy_id}")
async def get_vacancy_details(vacancy_id: str, user: User = Depends(get_current_user)):
    """Get full vacancy details"""
    return await hh_service.get_vacancy_details(user.hh_user_id, vacancy_id)


@router.post("/vacancy/{vacancy_id}/generate-letter", response_model=CoverLetter)
async def generate_letter(
    vacancy_id: str,
    resume_id: Optional[str] = None,
    user: User = Depends(check_user_credits),
    db: Session = Depends(get_db)
):
    """Generate cover letter for vacancy (costs 1 credit)"""
    logger.info(f"Generating letter for vacancy {vacancy_id}, user {user.hh_user_id}")
    
    try:
        # Get vacancy details first
        vacancy = await hh_service.get_vacancy_details(user.hh_user_id, vacancy_id)
        vacancy_title = vacancy.get("name", "Неизвестная вакансия")
        
        # Generate letter with user_id for pseudonymization
        result = await hh_service.generate_cover_letter(
            user.hh_user_id, 
            vacancy_id, 
            resume_id,
            str(user.id)  # Передаем user_id для псевдонимизации
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
    user: User = Depends(get_current_user),
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
    vacancy_title = "Неизвестная вакансия"

    try:
        # Получаем информацию о вакансии для истории
        try:
            vacancy = await hh_service.get_vacancy_details(user.hh_user_id, vacancy_id)
            vacancy_title = vacancy.get("name", "Неизвестная вакансия")
        except:
            logger.warning(f"Could not get vacancy details for {vacancy_id}")
        
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
            prompt_filename=application_data.prompt_filename,
            ai_model=application_data.ai_model
        )
        
        # Сохраняем в историю отправленных писем (только после успешной отправки)
        if application_data.prompt_filename and application_data.ai_model:
            LetterGenerationCRUD.save_letter_generation(
                db=db,
                user_id=user.id,
                vacancy_id=vacancy_id,
                vacancy_title=vacancy_title,
                resume_id=application_data.resume_id,
                letter_content=application_data.message,
                prompt_filename=application_data.prompt_filename,
                ai_model=application_data.ai_model
            )
        
        logger.info(f"Application sent successfully for user {user.id} to vacancy {vacancy_id}")
        
        return {"status": "success", "message": "Отклик успешно отправлен"}
        
    except HTTPException as http_exc:
        # При ошибке НЕ сохраняем в историю писем, только в applications
        error_message = f"HTTP Error: {http_exc.detail}"
        logger.error(f"HTTP error applying to vacancy: {error_message}")
        
        # Сохраняем в БД applications с информацией об ошибке
        ApplicationCRUD.create(
            db,
            user_id=user.id,
            vacancy_id=vacancy_id,
            resume_id=application_data.resume_id,
            message=error_message,
            prompt_filename=application_data.prompt_filename,
            ai_model=application_data.ai_model
        )
        
        raise http_exc
    except Exception as e:
        # При ошибке НЕ сохраняем в историю писем
        error_message = f"General Error: {str(e)}"
        logger.error(f"Error applying to vacancy: {error_message}")
        
        # Сохраняем в БД applications с информацией об ошибке
        ApplicationCRUD.create(
            db,
            user_id=user.id,
            vacancy_id=vacancy_id,
            resume_id=application_data.resume_id,
            message=error_message,
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
    """Get user's sent letters history"""
    history = LetterGenerationCRUD.get_user_history(db, user.id)
    return history