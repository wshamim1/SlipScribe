# SlipScribe Project Plan

## 1) Product Goal
Build a mobile-first receipt intelligence app that lets users upload receipt images/PDFs, extract accurate line items, review/edit results, and track spending trends.

## 2) Tech Stack (Confirmed)
- Frontend: React (responsive web app first; mobile-friendly UX)
- Backend API: FastAPI (OpenAPI-first)
- OCR/Document Parsing: Docling
- Primary Database: Postgres
- Vector Database: Milvus
- LLM Providers: Pluggable adapter (OpenAI, Groq, Mistral, etc.)

## 3) MVP Scope (Best Path)
1. Receipt upload (photo/PDF)
2. OCR + extraction (merchant, date, totals, line items)
3. Review/edit screen for corrections
4. Receipt vault + search
5. Spending dashboard (monthly/category/merchant)
6. Overspend alert vs last 90-day baseline

## 4) System Architecture
### Frontend (React)
- Screen 1: Inbox (upload/capture)
- Screen 2: Receipt details (extracted fields + editable line items)
- Screen 3: Dashboard (monthly trends and category totals)
- Screen 4: Insights (overspend/anomaly cards)

### Backend (FastAPI + OpenAPI)
- Authentication + user management
- Receipt CRUD APIs
- Processing-job orchestration
- Search + dashboard + insights APIs
- CSV export API

### Extraction Worker (Python)
- Ingest file from storage
- Run Docling OCR/layout extraction
- Rule-based base field extraction
- LLM structured extraction into strict JSON
- Reconciliation and confidence scoring
- Persist normalized output to Postgres
- Generate embeddings and write to Milvus

## 5) Data Model (v1)
### Postgres tables
- `users`
- `receipts` (`id`, `user_id`, `merchant_name`, `purchase_date`, `subtotal`, `tax`, `total`, `currency`, `status`, `confidence`, `created_at`, `updated_at`)
- `receipt_images` (`id`, `receipt_id`, `storage_path`, `page_index`, `width`, `height`, `created_at`)
- `receipt_line_items` (`id`, `receipt_id`, `name`, `quantity`, `unit_price`, `line_total`, `discount_flag`, `raw_text`, `confidence`, `created_at`, `updated_at`)
- `merchant_category_rules` (`id`, `user_id`, `match_pattern`, `category`, `priority`, `created_at`)
- `processing_jobs` (`id`, `receipt_id`, `job_type`, `status`, `attempt`, `error_message`, `created_at`, `updated_at`)
- `budgets` (`id`, `user_id`, `category`, `monthly_limit`, `created_at`, `updated_at`)
- `alerts` (`id`, `user_id`, `receipt_id`, `alert_type`, `message`, `severity`, `created_at`)

### Milvus collections
- `receipt_chunks`: OCR text chunks + metadata (`receipt_id`, `user_id`, `chunk_index`)
- `line_item_vectors`: line item text + metadata (`line_item_id`, `receipt_id`, `merchant_name`, `category`)

## 6) OpenAPI v1 Endpoint Plan
- `POST /receipts/upload`
- `GET /receipts`
- `GET /receipts/{id}`
- `PATCH /receipts/{id}`
- `GET /receipts/{id}/line-items`
- `PATCH /receipts/{id}/line-items/{lineItemId}`
- `POST /receipts/{id}/reprocess`
- `GET /search`
- `GET /dashboard/monthly`
- `GET /insights/overspend`
- `GET /exports/csv`

## 7) OCR + AI Extraction Strategy
1. Docling extracts text + layout blocks
2. Rule parser identifies high-confidence fields:
   - merchant, date, subtotal, tax, total
3. LLM converts OCR/layout into strict receipt JSON schema
4. Reconciliation checks:
   - `sum(line_items)` close to `subtotal`/`total`
   - tax/discount consistency
5. Confidence scoring:
   - field-level and receipt-level
6. Low-confidence receipts flagged for user review

## 8) LLM Provider Adapter Design
Single interface:
- `extractStructuredReceipt(input, schema, provider)`

Provider implementations:
- `openaiProvider`
- `groqProvider`
- `mistralProvider`

Selection strategy:
- User/workspace default provider
- Per-request override support
- Unified retry and timeout policy

## 9) Delivery Plan (6 Sprints)
### Sprint 0: Foundations
- Monorepo setup
- OpenAPI scaffold
- Postgres and Milvus setup
- Object storage setup (S3-compatible)
- Auth skeleton

### Sprint 1: Upload + Vault
- Upload endpoint and file persistence
- Receipt list/detail APIs
- React inbox and receipt list UI
- Processing job queue skeleton

### Sprint 2: Docling Pipeline
- Worker integration with Docling
- OCR text/layout persistence
- Base field extraction via rules
- Receipt details review UI

### Sprint 3: Line Items + LLM
- Strict extraction schema
- Provider adapter with first LLM backend
- Line item editing UX
- Reconciliation and confidence warnings

### Sprint 4: Search + Milvus
- Embedding pipeline
- Milvus indexing and semantic search API
- UI search across merchant/item/text

### Sprint 5: Dashboard + Insights
- Monthly spend aggregations
- Category totals and top merchants
- Overspend alerts vs 90-day baseline
- CSV export

### Sprint 6: Hardening
- Retries, idempotency, dead-letter handling
- Security checks and rate limiting
- Observability/logging/alerts
- QA and release checklist

## 10) Success Metrics (MVP)
- OCR-to-edit completion rate
- Median extraction time per receipt
- Line-item extraction accuracy (manual QA sample)
- Weekly active users
- % receipts requiring manual correction

## 11) Risks and Mitigations
- OCR variance on low-quality images
  - Mitigation: preprocessing + manual correction UX + confidence flags
- LLM formatting instability
  - Mitigation: strict schema validation + retries + fallback parser
- Cost growth from LLM/OCR usage
  - Mitigation: confidence-gated LLM calls and caching
- Search relevance quality
  - Mitigation: hybrid keyword + vector search

## 12) Immediate Next Tasks
1. Finalize OpenAPI v1 schemas
2. Write Postgres migration scripts for v1 tables
3. Implement `POST /receipts/upload` + job enqueue
4. Build worker: Docling OCR + base parser
5. Implement receipt details review screen in React
