"""
Receipt endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID, uuid4
from datetime import datetime, date

from app.db.session import get_db
from app.schemas.receipt import ReceiptResponse, ReceiptDetailResponse, ReceiptUpdate
from app.services.receipt_service import ReceiptService, DuplicateReceiptError
from app.models import Receipt, ReceiptImage, ReceiptLineItem, ProcessingJob
from app.tasks.ocr_task import process_receipt as process_receipt_task

router = APIRouter()

# Mock user ID for now (will be replaced with JWT auth)
MOCK_USER_ID = "a1000000-0000-0000-0000-000000000001"


@router.post("/upload", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a receipt image or PDF
    Queues OCR and extraction job
    """
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    try:
        service = ReceiptService(db)
        receipt = await service.upload_receipt(file, UUID(MOCK_USER_ID))
        return receipt
    except DuplicateReceiptError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "This file has already been uploaded.", "existing_receipt_id": str(e.existing_receipt_id)}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload receipt: {str(e)}"
        )


@router.get("", response_model=dict)
async def list_receipts(
    limit: int = 50,
    offset: int = 0,
    status_filter: str | None = None,
    db: Session = Depends(get_db)
):
    """List user receipts with pagination and filters"""
    try:
        service = ReceiptService(db)
        receipts, total = service.get_receipts(
            user_id=UUID(MOCK_USER_ID),
            limit=limit,
            offset=offset,
            status_filter=status_filter
        )

        return {
            "receipts": [ReceiptResponse.model_validate(r) for r in receipts],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/stats", response_model=dict)
async def get_stats(db: Session = Depends(get_db)):
    """Return dashboard statistics for the current user."""
    user_id = UUID(MOCK_USER_ID)
    this_month_prefix = date.today().strftime("%Y-%m")

    base = db.query(Receipt).filter(
        Receipt.user_id == user_id,
        Receipt.status == "completed",
        Receipt.total.isnot(None),
    )

    # All-time totals
    all_time = base.with_entities(
        func.sum(Receipt.total).label("total_spent"),
        func.count(Receipt.id).label("receipt_count"),
    ).one()

    # This-month totals — purchase_date is a VARCHAR "YYYY-MM-DD"
    this_month = base.filter(
        func.substring(Receipt.purchase_date, 1, 7) == this_month_prefix,
    ).with_entities(
        func.sum(Receipt.total).label("total_spent"),
        func.count(Receipt.id).label("receipt_count"),
    ).one()

    # Monthly breakdown — group by "YYYY-MM" prefix, last 12 months
    ym = func.substring(Receipt.purchase_date, 1, 7).label("ym")
    monthly_rows = (
        base.filter(Receipt.purchase_date.isnot(None))
        .with_entities(
            ym,
            func.sum(Receipt.total).label("total"),
            func.count(Receipt.id).label("count"),
        )
        .group_by(func.substring(Receipt.purchase_date, 1, 7))
        .order_by(func.substring(Receipt.purchase_date, 1, 7))
        .limit(12)
        .all()
    )

    # Top merchants — by total spend
    merchant_rows = (
        base.filter(Receipt.merchant_name.isnot(None))
        .with_entities(
            Receipt.merchant_name,
            func.sum(Receipt.total).label("total"),
            func.count(Receipt.id).label("count"),
        )
        .group_by(Receipt.merchant_name)
        .order_by(func.sum(Receipt.total).desc())
        .limit(5)
        .all()
    )

    return {
        "all_time": {
            "total_spent": float(all_time.total_spent or 0),
            "receipt_count": all_time.receipt_count or 0,
        },
        "this_month": {
            "total_spent": float(this_month.total_spent or 0),
            "receipt_count": this_month.receipt_count or 0,
        },
        "monthly": [
            {"label": r.ym, "total": float(r.total), "count": r.count}
            for r in monthly_rows
        ],
        "top_merchants": [
            {"name": r.merchant_name, "total": float(r.total), "count": r.count}
            for r in merchant_rows
        ],
    }


@router.get("/{receipt_id}", response_model=ReceiptDetailResponse)
async def get_receipt(
    receipt_id: str,
    db: Session = Depends(get_db)
):
    """Get receipt details including line items"""
    try:
        service = ReceiptService(db)
        receipt = service.get_receipt(UUID(receipt_id), UUID(MOCK_USER_ID))
        
        if not receipt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receipt not found"
            )
        
        # Get images
        images = db.query(ReceiptImage).filter(
            ReceiptImage.receipt_id == UUID(receipt_id)
        ).all()
        
        # Get line items
        line_items = db.query(ReceiptLineItem).filter(
            ReceiptLineItem.receipt_id == UUID(receipt_id)
        ).all()
        
        # Build response
        return {
            "id": receipt.id,
            "user_id": receipt.user_id,
            "merchant_name": receipt.merchant_name,
            "purchase_date": receipt.purchase_date,
            "subtotal": receipt.subtotal,
            "tax": receipt.tax,
            "total": receipt.total,
            "currency": receipt.currency,
            "status": receipt.status,
            "confidence": receipt.confidence,
            "created_at": receipt.created_at,
            "updated_at": receipt.updated_at,
            "images": [
                {
                    "id": img.id,
                    "url": img.storage_path,  # TODO: generate signed URL
                    "thumbnail_url": img.thumbnail_path,
                    "page_index": img.page_index or 0,
                    "width": img.width or 0,
                    "height": img.height or 0
                }
                for img in images
            ],
            "line_items": line_items,
            "validation_warnings": []
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/{receipt_id}", response_model=ReceiptResponse)
async def update_receipt(
    receipt_id: str,
    update: ReceiptUpdate,
    db: Session = Depends(get_db)
):
    """Update receipt fields"""
    # TODO: Implement receipt update
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Receipt not found"
    )


@router.post("/{receipt_id}/reprocess", status_code=status.HTTP_202_ACCEPTED)
async def reprocess_receipt(
    receipt_id: str,
    db: Session = Depends(get_db)
):
    """Reprocess a receipt (re-run OCR and extraction)"""
    receipt = db.query(Receipt).filter(
        Receipt.id == UUID(receipt_id),
        Receipt.user_id == UUID(MOCK_USER_ID)
    ).first()

    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")

    job = ProcessingJob(
        id=uuid4(),
        receipt_id=receipt.id,
        job_type="ocr_extraction",
        status="queued",
        attempt=0,
        max_attempts=3,
        created_at=datetime.utcnow(),
    )
    receipt.status = "pending"
    receipt.updated_at = datetime.utcnow()
    db.add(job)
    db.commit()

    process_receipt_task.delay(str(receipt.id), str(job.id))

    return {"job_id": str(job.id), "status": "queued"}


@router.delete("/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_receipts(
    receipt_status: str = "failed",
    db: Session = Depends(get_db)
):
    """Delete all receipts with a given status (default: failed). Also removes files from storage."""
    from app.services.storage_service import StorageService

    receipts = db.query(Receipt).filter(
        Receipt.user_id == UUID(MOCK_USER_ID),
        Receipt.status == receipt_status
    ).all()

    if not receipts:
        return {"deleted": 0}

    storage = StorageService()
    storage_paths = []
    receipt_ids = [r.id for r in receipts]

    # Delete processing jobs first (no cascade on FK)
    db.query(ProcessingJob).filter(ProcessingJob.receipt_id.in_(receipt_ids)).delete(synchronize_session=False)

    for r in receipts:
        images = db.query(ReceiptImage).filter(ReceiptImage.receipt_id == r.id).all()
        storage_paths.extend(img.storage_path for img in images)
        db.delete(r)

    db.commit()

    if storage_paths:
        try:
            storage.delete_receipt_images(storage_paths)
        except Exception:
            pass  # DB already cleaned up; storage failure is non-fatal

    return {"deleted": len(receipts)}


@router.delete("/{receipt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_receipt(
    receipt_id: str,
    db: Session = Depends(get_db)
):
    """Delete a single receipt and its files from storage."""
    from app.services.storage_service import StorageService

    receipt = db.query(Receipt).filter(
        Receipt.id == UUID(receipt_id),
        Receipt.user_id == UUID(MOCK_USER_ID)
    ).first()

    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")

    images = db.query(ReceiptImage).filter(ReceiptImage.receipt_id == receipt.id).all()
    storage_paths = [img.storage_path for img in images]

    # Delete processing jobs first (no cascade on FK)
    db.query(ProcessingJob).filter(ProcessingJob.receipt_id == receipt.id).delete()

    db.delete(receipt)
    db.commit()

    if storage_paths:
        try:
            StorageService().delete_receipt_images(storage_paths)
        except Exception:
            pass
