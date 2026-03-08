# SlipScribe

SlipScribe is a mobile-first receipt & bill vault that turns photos into structured data. Snap a receipt, and SlipScribe extracts the merchant, totals, taxes, and **line items** so you can search what you bought, track spending by category/merchant, and export clean reports when you need them.

## What it does (MVP)
- Capture receipts/bills with the phone camera (single or multi-photo receipts)
- Auto-enhance images (crop, deskew, contrast) for better readability
- OCR + parsing to extract:
  - Merchant name, purchase date, subtotal/tax/total
  - **Line items** (name, qty, unit price, line total)
- Review & edit extracted fields with a fast correction UI
- Receipt vault with full-text search (e.g., search for “battery”, “milk”, “Home Depot”)
- Export data (CSV) for reimbursements, budgeting, or tax time

## Why SlipScribe
Receipts are easy to lose and hard to use. SlipScribe makes them searchable and actionable—without manual typing.

## Privacy-first by design
- Receipts belong to you
- Local storage supported from day one (with optional cloud sync later)
- Clear controls for export and deletion

## Roadmap (later)
- Auto-match receipts to transactions (CSV/Plaid)
- Spending insights + anomaly alerts
- Warranty/return reminders
- Household sharing (shared vault)
- Tags & smart categorization

## Tech notes
SlipScribe uses an OCR + structuring pipeline to convert receipt text into a strict JSON schema, with confidence scoring and reconciliation checks (totals vs. line item sums).

---
**Status:** early development
