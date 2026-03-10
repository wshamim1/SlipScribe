"""
Dashboard endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter()


@router.get("/monthly")
async def get_monthly_dashboard(
    month: str | None = None,
    db: Session = Depends(get_db)
):
    """Get monthly spending dashboard"""
    # TODO: Implement dashboard
    return {
        "month": month or "2026-03",
        "total_spent": 0,
        "receipt_count": 0,
        "by_category": [],
        "by_merchant": [],
        "daily_trend": []
    }
