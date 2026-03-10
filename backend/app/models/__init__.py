"""
Database models for SlipScribe
"""
from sqlalchemy import Column, String, Integer, DateTime, Float, Boolean, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    receipts = relationship("Receipt", back_populates="user", cascade="all, delete-orphan")


class Receipt(Base):
    """Receipt model"""
    __tablename__ = "receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    merchant_name = Column(String(255), nullable=True, index=True)
    purchase_date = Column(String(10), nullable=True, index=True)  # YYYY-MM-DD format
    subtotal = Column(Numeric(12, 2), nullable=True)
    tax = Column(Numeric(12, 2), nullable=True)
    total = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="USD")
    status = Column(String(50), default="pending", nullable=False, index=True)
    # Status: pending, processing, completed, failed, manual_review
    confidence = Column(Float, nullable=True)  # 0.0-1.0
    ocr_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="receipts")
    images = relationship("ReceiptImage", back_populates="receipt", cascade="all, delete-orphan")
    line_items = relationship("ReceiptLineItem", back_populates="receipt", cascade="all, delete-orphan")


class ReceiptImage(Base):
    """Receipt image model"""
    __tablename__ = "receipt_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id = Column(UUID(as_uuid=True), ForeignKey("receipts.id"), nullable=False, index=True)
    storage_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500), nullable=True)
    page_index = Column(Integer, default=0)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(50), nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hex digest
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    receipt = relationship("Receipt", back_populates="images")


class ReceiptLineItem(Base):
    """Receipt line item model"""
    __tablename__ = "receipt_line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id = Column(UUID(as_uuid=True), ForeignKey("receipts.id"), nullable=False, index=True)
    name = Column(String(500), nullable=False, index=True)
    quantity = Column(Numeric(10, 3), default=1.0)
    unit_price = Column(Numeric(12, 2), nullable=True)
    line_total = Column(Numeric(12, 2), nullable=False)
    discount_flag = Column(Boolean, default=False)
    raw_text = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)  # 0.0-1.0
    category = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    receipt = relationship("Receipt", back_populates="line_items")


class ProcessingJob(Base):
    """Processing job model"""
    __tablename__ = "processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id = Column(UUID(as_uuid=True), ForeignKey("receipts.id"), nullable=False, index=True)
    job_type = Column(String(50), nullable=False)
    # Job types: ocr_extraction, llm_structuring, validation
    status = Column(String(50), default="queued", nullable=False, index=True)
    # Status: queued, running, completed, failed, retrying
    attempt = Column(Integer, default=1)
    max_attempts = Column(Integer, default=3)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    receipt = relationship("Receipt")
