"""
Insights endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter()


@router.get("/overspend")
async def get_overspend_insights(
    db: Session = Depends(get_db)
):
    """Get overspend alerts"""
    # TODO: Implement insights
    return {
        "alerts": []
    }
