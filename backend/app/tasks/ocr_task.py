"""
Celery task: OCR extraction pipeline for receipts.

Flow:
  1. Fetch image/PDF from MinIO
  2. Extract text:
       - Images (jpg/png/heic) → pytesseract (fast, no ML models, no tensor issues)
       - Native-text PDFs      → Docling with OCR disabled (text already embedded)
  3. Call LLM to parse structured fields
  4. Persist results and mark receipt as completed/failed
"""
import io
import logging
import os
import re
import tempfile
from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models import Receipt, ReceiptImage, ReceiptLineItem, ProcessingJob
from app.services.storage_service import StorageService
from app.services.extraction_service import ExtractionService

logger = logging.getLogger(__name__)


def _safe_decimal(value) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None


def _ocr_image(file_bytes: bytes) -> str:
    """
    OCR a receipt image with pytesseract.
    Requires: brew install tesseract  (macOS)
              apt install tesseract-ocr  (Linux)
    """
    import pytesseract
    from PIL import Image, ImageOps, ImageFilter

    img = Image.open(io.BytesIO(file_bytes)).convert("L")  # grayscale

    # Scale up small images for better OCR accuracy
    w, h = img.size
    if max(w, h) < 2000:
        scale = 2000 / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # Stretch histogram then sharpen — works across varied photo conditions
    img = ImageOps.autocontrast(img, cutoff=2)
    img = img.filter(ImageFilter.SHARPEN)

    # psm 6 = uniform block of text; reads top-to-bottom in natural order
    return pytesseract.image_to_string(img, config="--psm 6 --oem 3")


def _extract_pdf_text(file_bytes: bytes) -> str:
    """
    Extract text from a native (text-based) PDF using Docling, OCR disabled.
    Works for e-receipts and online invoices where text is already embedded.
    """
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions

    opts = PdfPipelineOptions()
    opts.do_ocr = False
    opts.do_table_structure = False

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
        )
        result = converter.convert(tmp_path)
        return result.document.export_to_markdown()
    finally:
        os.unlink(tmp_path)


def _fallback_date(ocr_text: str) -> str | None:
    """
    Try to find a date in OCR text when the LLM couldn't extract one.
    Handles MM/DD/YYYY, MM/DD/YY, YYYY-MM-DD patterns, and common OCR
    character misreads (O→0, I/l→1, S→5, TV→11, etc.).
    Returns ISO "YYYY-MM-DD" string or None.
    """
    def _fix_ocr_digits(s: str) -> str:
        """Replace common OCR letter-for-digit misreads."""
        return (s
            .replace('O', '0').replace('o', '0')
            .replace('I', '1').replace('l', '1')
            .replace('S', '5')
            .replace('B', '8')
            .replace('T', '1').replace('V', '1')  # TV → 11 (common for "11")
        )

    # Work on a normalised copy of the OCR text
    normalized = _fix_ocr_digits(ocr_text)

    patterns = [
        # ISO: 2023-06-18
        (r'\b(\d{4})-(\d{2})-(\d{2})\b', lambda m: f"{m[0]}-{m[1]}-{m[2]}"),
        # US: 06/18/2023 or 06/18/23
        (r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})\b', lambda m: (
            f"20{m[2]}-{int(m[0]):02d}-{int(m[1]):02d}"
            if len(m[2]) == 2
            else f"{m[2]}-{int(m[0]):02d}-{int(m[1]):02d}"
        )),
    ]
    for pattern, formatter in patterns:
        match = re.search(pattern, normalized)
        if match:
            try:
                groups = match.groups()
                candidate = formatter(groups)
                # Basic sanity: year between 2000-2030, month 1-12, day 1-31
                parts = candidate.split("-")
                if (2000 <= int(parts[0]) <= 2030
                        and 1 <= int(parts[1]) <= 12
                        and 1 <= int(parts[2]) <= 31):
                    return candidate
            except Exception:
                continue
    return None


def _ocr(file_bytes: bytes, mime: str) -> str:
    if "pdf" in mime:
        return _extract_pdf_text(file_bytes)
    return _ocr_image(file_bytes)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_receipt(self, receipt_id: str, job_id: str):
    """
    Orchestrate OCR + LLM extraction for a single receipt.

    Args:
        receipt_id: UUID string of the Receipt row
        job_id:     UUID string of the ProcessingJob row
    """
    db = SessionLocal()
    try:
        receipt = db.query(Receipt).filter(Receipt.id == UUID(receipt_id)).first()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == UUID(job_id)).first()

        if not receipt or not job:
            logger.error("Receipt %s or job %s not found", receipt_id, job_id)
            return

        # Mark as running
        job.status = "running"
        job.started_at = datetime.utcnow()
        job.attempt = (job.attempt or 0) + 1
        receipt.status = "processing"
        receipt.updated_at = datetime.utcnow()
        db.commit()

        # ── Step 1: fetch file from MinIO ────────────────────────────────────
        image = (
            db.query(ReceiptImage)
            .filter(ReceiptImage.receipt_id == UUID(receipt_id))
            .order_by(ReceiptImage.page_index)
            .first()
        )
        if not image:
            raise ValueError("No image record found for receipt")

        storage = StorageService()
        s3_obj = storage.s3_client.get_object(
            Bucket=storage.bucket, Key=image.storage_path
        )
        file_bytes = s3_obj["Body"].read()

        # ── Step 2: extract text ─────────────────────────────────────────────
        mime = (image.mime_type or "image/jpeg").lower()
        ocr_text = _ocr(file_bytes, mime)

        logger.info("Extracted %d chars from receipt %s", len(ocr_text), receipt_id)

        # ── Step 3: structured extraction ────────────────────────────────────
        extractor = ExtractionService()
        fields = extractor.extract_receipt_fields(ocr_text)

        # ── Step 4: persist ───────────────────────────────────────────────────
        receipt.ocr_text = ocr_text
        receipt.merchant_name = fields.get("merchant_name")
        purchase_date = fields.get("purchase_date") or _fallback_date(ocr_text)
        receipt.purchase_date = purchase_date
        receipt.subtotal = _safe_decimal(fields.get("subtotal"))
        receipt.tax = _safe_decimal(fields.get("tax"))
        receipt.total = _safe_decimal(fields.get("total"))
        receipt.currency = fields.get("currency") or "USD"
        receipt.confidence = fields.get("confidence")
        receipt.status = "completed"
        receipt.updated_at = datetime.utcnow()

        # Clear old line items before inserting new ones (re-run case)
        db.query(ReceiptLineItem).filter(
            ReceiptLineItem.receipt_id == UUID(receipt_id)
        ).delete(synchronize_session=False)

        for item in fields.get("line_items") or []:
            line_total = _safe_decimal(item.get("line_total"))
            if line_total is None:
                continue
            db.add(
                ReceiptLineItem(
                    receipt_id=UUID(receipt_id),
                    name=item.get("name") or "Unknown",
                    quantity=_safe_decimal(item.get("quantity")) or Decimal("1"),
                    unit_price=_safe_decimal(item.get("unit_price")),
                    line_total=line_total,
                    raw_text=item.get("raw_text"),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

        logger.info("Receipt %s processed successfully", receipt_id)

    except Exception as exc:
        db.rollback()
        logger.error("Error processing receipt %s: %s", receipt_id, exc, exc_info=True)

        try:
            receipt = db.query(Receipt).filter(Receipt.id == UUID(receipt_id)).first()
            job = db.query(ProcessingJob).filter(ProcessingJob.id == UUID(job_id)).first()
            if receipt:
                receipt.status = "failed"
                receipt.updated_at = datetime.utcnow()
            if job:
                job.status = "failed"
                job.error_message = str(exc)[:1000]
                job.completed_at = datetime.utcnow()
            db.commit()
        except Exception:
            pass

        raise self.retry(exc=exc)
    finally:
        db.close()

