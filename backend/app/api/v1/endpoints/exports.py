"""
Export endpoints
"""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter()


@router.get("/csv")
async def export_csv(
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db)
):
    """Export receipts to CSV"""
    # TODO: Implement CSV export
    csv_content = "merchant,date,total\n"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=receipts.csv"
        }
    )
