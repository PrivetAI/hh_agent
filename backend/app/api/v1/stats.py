from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from ...core.database import get_db
from ...models.db import LetterGeneration

router = APIRouter(prefix="/api/stats", tags=["stats"])

@router.get("/cover-letters")
async def get_cover_letter_stats(db: Session = Depends(get_db)):
    """Get cover letter generation statistics"""
    
    # Общее количество за все время
    total_count = db.query(func.count(LetterGeneration.id)).scalar() or 0
    
    # Количество за последние 24 часа
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    last_24h_count = db.query(func.count(LetterGeneration.id)).filter(
        LetterGeneration.created_at >= twenty_four_hours_ago
    ).scalar() or 0
    
    return {
        "total_generated": total_count,
        "last_24h_generated": last_24h_count,
        "timestamp": datetime.utcnow().isoformat()
    }