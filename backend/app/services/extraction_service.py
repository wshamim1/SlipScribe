"""
LLM extraction service — parses structured receipt fields from OCR text.
Uses Groq by default (OpenAI-compatible API), falls back to OpenAI.
"""
import json
import logging
from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
You are a receipt data extractor. Given the raw OCR text of a receipt, return a \
single valid JSON object with exactly these fields:

  merchant_name   : string or null  — the BUSINESS/STORE name, found at the very
                    top of the receipt (e.g. "Costco Wholesale", "Walmart",
                    "Starbucks"). It is NEVER a product, item, or line-item name.
  purchase_date   : string "YYYY-MM-DD" or null
  subtotal        : number or null  — amount before tax
  tax             : number or null
  total           : number or null  — the final amount paid, usually labeled
                    "TOTAL", "GRAND TOTAL", or "AMOUNT DUE" near the bottom
  currency        : 3-letter ISO code, default "USD"
  confidence      : float 0.0–1.0 reflecting extraction quality
  line_items      : array of objects, each with:
                      name       : string
                      quantity   : number (default 1)
                      unit_price : number or null
                      line_total : number

Return ONLY the JSON object — no explanation, no markdown fences.

Receipt text:
{text}
"""


class ExtractionService:
    def __init__(self):
        if settings.DEFAULT_LLM_PROVIDER == "groq" and settings.GROQ_API_KEY:
            self.client = OpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1",
            )
            self.model = "llama-3.3-70b-versatile"
        elif settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = "gpt-4o-mini"
        else:
            raise ValueError(
                "No LLM provider configured. Set GROQ_API_KEY or OPENAI_API_KEY."
            )

    def extract_receipt_fields(self, ocr_text: str) -> dict:
        """Call the LLM and return a dict of extracted receipt fields."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(text=ocr_text),
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        raw = response.choices[0].message.content
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response as JSON: %s", raw)
            return {}
