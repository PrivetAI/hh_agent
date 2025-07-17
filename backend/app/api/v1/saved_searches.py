from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from ...api.deps import get_current_user, get_db
from ...models.db import User
from ...services.hh.service import HHService
import logging

router = APIRouter(prefix="/api", tags=["saved_searches"])
hh_service = HHService()
logger = logging.getLogger(__name__)


@router.get("/saved-searches")
async def get_saved_searches(
    user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get user's saved searches from HH"""
    logger.info(f"Getting saved searches for user {user.hh_user_id}")
    
    try:
        saved_searches = await hh_service.get_saved_searches(user.hh_user_id)
        return saved_searches
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting saved searches: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get saved searches"
        )
@router.get("/saved-searches/{saved_search_id}/vacancies")
async def get_vacancies_by_saved_search(
    saved_search_id: str,
    page: int = Query(0, ge=0),
    per_page: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get vacancies by saved search ID"""
    hh_service = HHService()
    
    try:
        result = await hh_service.search_vacancies_by_saved_search(
            hh_user_id=current_user.hh_user_id,
            saved_search_id=saved_search_id,
            page=page,
            per_page=per_page
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error searching vacancies: {str(e)}")