"""
Receipt schemas (Pydantic models)
"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID


class ReceiptBase(BaseModel):
    """Base receipt schema"""
    merchant_name: Optional[str] = None
    purchase_date: Optional[date] = None
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    total: Optional[Decimal] = None
    currency: str = "USD"


class ReceiptCreate(ReceiptBase):
    """Schema for creating receipt"""
    pass


class ReceiptUpdate(BaseModel):
    """Schema for updating receipt"""
    merchant_name: Optional[str] = None
    purchase_date: Optional[date] = None
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    total: Optional[Decimal] = None
    currency: Optional[str] = None


class ReceiptResponse(ReceiptBase):
    """Receipt response schema"""
    id: UUID
    user_id: UUID
    status: str
    confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ReceiptImage(BaseModel):
    """Receipt image schema"""
    id: UUID
    url: str
    thumbnail_url: str
    page_index: int
    width: int
    height: int


class LineItem(BaseModel):
    """Line item schema"""
    id: UUID
    receipt_id: UUID
    name: str
    quantity: Decimal = Decimal("1.0")
    unit_price: Optional[Decimal] = None
    line_total: Decimal
    discount_flag: bool = False
    raw_text: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ReceiptDetailResponse(ReceiptResponse):
    """Detailed receipt response with images and line items"""
    images: List[ReceiptImage] = []
    line_items: List[LineItem] = []
    validation_warnings: List[str] = []
