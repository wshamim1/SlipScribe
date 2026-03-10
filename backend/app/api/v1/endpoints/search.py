"""
Search endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter()


@router.get("")
async def search_receipts(
    q: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Search receipts and line items"""
    # TODO: Implement search
    return {
        "results": [],
        "total": 0
    }
