"""
Receipt service - handles receipt operations and queuing
"""
import hashlib
from uuid import uuid4, UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import UploadFile
import os

from app.models import Receipt, ReceiptImage, ProcessingJob, User
from app.services.storage_service import StorageService
from app.core.config import settings
from app.tasks.ocr_task import process_receipt


class DuplicateReceiptError(Exception):
    """Raised when an identical file has already been uploaded."""
    def __init__(self, existing_receipt_id: UUID):
        self.existing_receipt_id = existing_receipt_id
        super().__init__(f"Duplicate receipt: {existing_receipt_id}")


class ReceiptService:
    """Service for receipt operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.storage = StorageService()
    
    async def upload_receipt(
        self,
        file: UploadFile,
        user_id: UUID
    ) -> Receipt:
        """
        Upload receipt file and queue for processing
        
        Args:
            file: Uploaded file
            user_id: User ID
        
        Returns:
            Receipt object with status=pending
        """
        # Validate file type
        if file.content_type not in settings.ALLOWED_MIME_TYPES:
            raise ValueError(f"Unsupported file type: {file.content_type}")
        
        # Validate file size (max 10MB)
        if file.size and file.size > 10 * 1024 * 1024:
            raise ValueError("File size exceeds 10MB limit")
        
        # Create receipt record
        receipt_id = uuid4()
        receipt = Receipt(
            id=receipt_id,
            user_id=user_id,
            status="pending",
            currency="USD",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        try:
            # Upload file to storage
            file_content = await file.read()

            # Duplicate detection: SHA-256 of file bytes
            file_hash = hashlib.sha256(file_content).hexdigest()
            existing_image = (
                self.db.query(ReceiptImage)
                .join(Receipt, ReceiptImage.receipt_id == Receipt.id)
                .filter(
                    ReceiptImage.file_hash == file_hash,
                    Receipt.user_id == user_id
                )
                .first()
            )
            if existing_image:
                raise DuplicateReceiptError(existing_image.receipt_id)

            storage_path, thumbnail_path = await self.storage.upload_receipt_image(
                file_content=file_content,
                filename=file.filename or "receipt.pdf",
                user_id=str(user_id),
                content_type=file.content_type
            )
            
            # Create receipt image record
            receipt_image = ReceiptImage(
                id=uuid4(),
                receipt_id=receipt_id,
                storage_path=storage_path,
                thumbnail_path=thumbnail_path,
                page_index=0,
                mime_type=file.content_type,
                file_size_bytes=file.size,
                file_hash=file_hash,
                created_at=datetime.utcnow()
            )
            
            # Queue OCR processing job
            processing_job = ProcessingJob(
                id=uuid4(),
                receipt_id=receipt_id,
                job_type="ocr_extraction",
                status="queued",
                attempt=0,
                max_attempts=3,
                created_at=datetime.utcnow()
            )
            
            # Save to database
            self.db.add(receipt)
            self.db.add(receipt_image)
            self.db.add(processing_job)
            self.db.commit()
            self.db.refresh(receipt)

            # Dispatch OCR task
            process_receipt.delay(str(receipt_id), str(processing_job.id))

            return receipt

        except DuplicateReceiptError:
            raise
        except Exception as e:
            self.db.rollback()
            # Cleanup: delete uploaded file
            try:
                await self.storage.delete_receipt_images([storage_path])
            except:
                pass
            raise e
    
    def get_receipts(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> tuple[List[Receipt], int]:
        """
        Get receipts for user with pagination
        
        Args:
            user_id: User ID
            limit: Number of results
            offset: Result offset
            status_filter: Filter by status (pending, processing, completed, failed)
        
        Returns:
            Tuple of (receipts list, total count)
        """
        query = self.db.query(Receipt).filter(Receipt.user_id == user_id)
        
        if status_filter:
            query = query.filter(Receipt.status == status_filter)
        
        total = query.count()
        receipts = query.order_by(Receipt.created_at.desc()).limit(limit).offset(offset).all()
        
        return receipts, total
    
    def get_receipt(self, receipt_id: UUID, user_id: UUID) -> Optional[Receipt]:
        """
        Get receipt details
        
        Args:
            receipt_id: Receipt ID
            user_id: User ID (for authorization check)
        
        Returns:
            Receipt object or None
        """
        receipt = self.db.query(Receipt).filter(
            Receipt.id == receipt_id,
            Receipt.user_id == user_id
        ).first()
        
        return receipt
    
    def update_receipt_status(
        self,
        receipt_id: UUID,
        status: str,
        **kwargs
    ) -> Receipt:
        """
        Update receipt status and optional fields
        
        Args:
            receipt_id: Receipt ID
            status: New status (pending, processing, completed, failed)
            **kwargs: Additional fields (merchant_name, total, confidence, etc.)
        
        Returns:
            Updated receipt
        """
        receipt = self.db.query(Receipt).filter(Receipt.id == receipt_id).first()
        if not receipt:
            return None
        
        receipt.status = status
        receipt.updated_at = datetime.utcnow()
        
        # Update optional fields
        for key, value in kwargs.items():
            if hasattr(receipt, key) and value is not None:
                setattr(receipt, key, value)
        
        self.db.commit()
        self.db.refresh(receipt)
        
        return receipt
    
    async def get_receipt(self, receipt_id: str, user_id: str):
        """Get receipt by ID"""
        # TODO: Implement receipt retrieval
        pass
    
    async def update_receipt(self, receipt_id: str, user_id: str, update_data: dict):
        """Update receipt fields"""
        # TODO: Implement receipt update
        pass
