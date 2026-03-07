# Spiritual Therapy AI — Backend

FastAPI backend for the Islamic Mental Health / Spiritual Therapy application.

## 🏗️ Architecture

```
app/
├── core/          # Config, dependencies, security, cache
├── db/            # SQLAlchemy engine, session
├── models/        # SQLAlchemy ORM models
├── schemas/       # Pydantic request/response schemas
├── api/v1/        # REST API endpoints
├── services/      # Business logic (MasterBrain, PrescriptionEngine, SearchRouter)
├── repositories/  # Data access layer (future)
└── utils/         # Utilities (logging, vector helpers)
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Start Infrastructure (Docker)
```bash
# From project root:
docker-compose up -d
```

### 4. Apply Migrations
```bash
cd backend
alembic upgrade head
```

### 5. Run the Server
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/health` | Detailed health (Redis, Brain status) |
| `POST` | `/api/v1/chat/send` | Main chat endpoint (conversational therapy) |
| `POST` | `/api/v1/auth/register` | User registration (placeholder) |
| `POST` | `/api/v1/auth/login` | User login (placeholder) |
| `POST` | `/api/v1/search/query` | Test search endpoint |
| `POST` | `/api/v1/plans/create` | Create 7-day spiritual plan |
| `GET` | `/api/v1/plans/{plan_id}` | Get plan with tasks |

## 🔄 Conversational Flow

```
IDLE → GATHERING (3+ turn, manevi üslup) → PROPOSING (user onayı) → READY → GENERATED
```

| Phase | Açıklama |
|-------|----------|
| `IDLE` | Karşılama, selamlama |
| `GATHERING` | Empati + manevi sohbet, en az 3 turn |
| `PROPOSING` | AI yolculuk özeti sunar, kullanıcı kabul eder |
| `READY` | Prescription + 7 günlük plan birlikte oluşur |
| `GENERATED` | Plan oluştu, kullanıcı erişebilir |
| `ONGOING` | Post-plan sohbet |

## 🔧 Scripts

Pipeline scripts are organized under `scripts/`:
- `data_preparation/` — Enrichment & embedding generation
- `database/` — Table creation & data seeding
- `testing/` — Search tests, cache tests, inspectors
- `utils/` — Missing data analysis, batch polling

## 🔒 Security Smoke Test (Live)

Run no-mock auth/authz checks against the running backend + Postgres + Redis stack:

```bash
# From project root
docker compose exec -T backend sh -lc "PYTHONPATH=. python tests/live_authz_smoke.py"
```

What it verifies:
- Access token TTL is around 24 hours
- Register/Login responses include refresh tokens
- CORS allows configured local origin and rejects disallowed origin
- Unauthenticated `GET /api/v1/prescriptions/` returns `401`
- Cross-user access to prescriptions/plans is blocked (`404`)
- Owner access to own prescription/plan succeeds (`200`)
- Refresh token rotation works, is device-bound, and old refresh token cannot be reused
- `GET /api/v1/auth/sessions` returns active sessions and marks current device
- Logout revokes token immediately (`/auth/me` returns `401` after logout)
- Refresh token is revoked on logout (`/auth/refresh` returns `401`)
- `POST /api/v1/auth/logout-all` revokes all sessions and blocks both access + refresh
