# SlipScribe Tech Stack

## Frontend
- **Framework**: React 18+
- **Build Tool**: Vite
- **Language**: TypeScript
- **UI Library**: TailwindCSS + shadcn/ui
- **State Management**: Zustand (lightweight, modern)
- **API Client**: TanStack Query (React Query) + Axios
- **Forms**: React Hook Form + Zod validation
- **Routing**: React Router v6
- **Image Handling**: react-dropzone + image compression

## Backend
- **Framework**: FastAPI (Python 3.11+)
- **API Spec**: OpenAPI 3.1 (contract-first)
- **Auth**: JWT tokens (PyJWT)
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Task Queue**: Celery + Redis
- **ASGI Server**: Uvicorn

## OCR & Document Processing
- **Library**: Docling (IBM's document understanding)
- **Preprocessing**: Pillow + OpenCV (auto-crop, deskew, enhance)
- **Layout Analysis**: Docling built-in

## AI/LLM Layer
- **Provider Adapter**: Custom abstraction over multiple providers
- **Supported Providers**:
  - OpenAI (GPT-4o, GPT-4o-mini)
  - Groq (Llama 3, Mixtral)
  - Mistral AI
  - Anthropic Claude (optional)
- **Structured Output**: JSON Schema validation with strict mode
- **Embeddings**: OpenAI text-embedding-3-small or Sentence Transformers

## Databases
- **Primary DB**: PostgreSQL 15+
  - Extensions: uuid-ossp, pg_trgm (fuzzy text search)
- **Vector DB**: Milvus 2.3+
  - Collections: receipt_chunks, line_item_vectors
- **Cache**: Redis 7+
  - Session storage
  - Job queue backend
  - Rate limiting

## Storage
- **Object Storage**: S3-compatible (AWS S3 / MinIO for local dev)
- **File Types**: JPEG, PNG, HEIC, PDF
- **Image Processing**: Thumbnail generation, format conversion

## Development Tools
- **Container Runtime**: Docker + Docker Compose
- **Linting**: 
  - Frontend: ESLint + Prettier
  - Backend: Ruff + Black
- **Type Checking**: 
  - Frontend: TypeScript strict mode
  - Backend: mypy
- **Testing**:
  - Frontend: Vitest + React Testing Library
  - Backend: pytest + pytest-asyncio
- **API Testing**: Bruno or Postman

## Infrastructure (Production)
- **Hosting**: TBD (AWS / GCP / Fly.io)
- **CDN**: CloudFront / Cloudflare
- **Monitoring**: Sentry (errors) + Grafana (metrics)
- **Logging**: Structured JSON logs (datadog / cloudwatch)
- **CI/CD**: GitHub Actions

## Security
- **Secrets Management**: Environment variables + vault (prod)
- **HTTPS**: Required in production
- **CORS**: Configured for web app origin
- **Rate Limiting**: Redis-based per-user limits
- **File Validation**: MIME type + size checks

## Development Environment
- **Python**: 3.11+ (pyenv recommended)
- **Node**: 20+ (nvm recommended)
- **Package Managers**: 
  - Python: Poetry or pip-tools
  - Node: pnpm (faster than npm)
- **Local Services**: Docker Compose for Postgres, Milvus, Redis

## API Contract
- **Specification**: OpenAPI 3.1 (`openapi.yaml`)
- **Code Generation**: 
  - Frontend: openapi-typescript-codegen
  - Backend: Native FastAPI OpenAPI support

## LLM Provider Adapter Interface
```python
class LLMProvider(Protocol):
    def extract_structured(
        self, 
        text: str, 
        schema: dict, 
        temperature: float = 0.1
    ) -> dict:
        """Extract structured JSON from text according to schema."""
        ...
    
    def embed_text(self, text: str) -> list[float]:
        """Generate embedding vector for text."""
        ...
```

## Extraction Pipeline Architecture
1. **Upload** → S3 storage + job queue
2. **Preprocessing** → Image enhancement
3. **OCR** → Docling extraction (text + layout)
4. **Base Parsing** → Rule-based field extraction
5. **LLM Structuring** → Strict JSON schema output
6. **Validation** → Reconciliation + confidence scoring
7. **Persistence** → Postgres + Milvus embeddings
8. **Notification** → Frontend poll/websocket update

## Recommended Local Setup
```bash
# Backend
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn main:app --reload

# Worker
poetry run celery -A worker worker --loglevel=info

# Frontend
cd frontend
pnpm install
pnpm dev

# Infrastructure
docker-compose up -d  # postgres, milvus, redis
```

## Environment Variables (Sample)
```bash
# Backend
DATABASE_URL=postgresql://user:pass@localhost:5432/slipscribe
REDIS_URL=redis://localhost:6379/0
MILVUS_HOST=localhost
MILVUS_PORT=19530
S3_BUCKET=slipscribe-receipts
S3_REGION=us-east-1

# LLM Providers (use one or multiple)
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
MISTRAL_API_KEY=...

# Default provider
DEFAULT_LLM_PROVIDER=groq

# Frontend
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Performance Targets (MVP)
- Receipt upload → OCR complete: < 10s (p95)
- Line item extraction: < 5s additional (p95)
- Dashboard load: < 500ms
- Search query: < 200ms
- API response time: < 100ms (non-processing endpoints)
