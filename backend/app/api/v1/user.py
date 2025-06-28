from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from ...api.deps import get_current_user, get_db
from ...models.db import User, Application
from ...models.schemas import ResumeResponse, Dictionaries
from ...services.hh.service import HHService
from datetime import datetime, timedelta

router = APIRouter(prefix="/api", tags=["user"])
hh_service = HHService()

@router.get("/user-info")
async def get_user_info(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user info with credits and applications count for last 24h"""
    
    # Получаем количество откликов за последние 24 часа
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    
    applications_24h = db.query(Application).filter(
        Application.user_id == user.id,
        Application.created_at >= twenty_four_hours_ago
    ).count()
    
    return {
        "user_id": str(user.id),
        "hh_user_id": user.hh_user_id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "credits": user.credits,
        "applications_24h": applications_24h,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
@router.get("/resumes", response_model=List[ResumeResponse])
async def get_resumes(user: User = Depends(get_current_user)):
    """Get all user's resumes"""
    return await hh_service.get_user_resumes(user.hh_user_id)

@router.get("/dictionaries", response_model=Dictionaries)
async def get_dictionaries():
    """Get HH dictionaries for filters"""
    return await hh_service.get_dictionaries()

@router.get("/areas")
async def get_areas():
    """Get areas (cities) for filters"""
    return await hh_service.get_areas()