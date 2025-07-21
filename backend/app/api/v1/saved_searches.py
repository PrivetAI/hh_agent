from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

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
    """Get user's saved searches from HH with URLs"""
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