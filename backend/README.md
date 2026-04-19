# App Service Backend

FastAPI app-service for QuranApp.

## Owns

- authentication and tokens
- users, profiles, memories
- conversations and orchestration
- pathways and pathway definitions
- prayer time and location APIs
- mobile-facing API surface

## Does not own

- Quran / hadith / book content storage
- semantic source retrieval
- keyword taxonomy and graph context
- Neo4j and content embeddings

Those capabilities live in the sibling `resource-service/` project and are
consumed only through `app/integrations/resource_service/`.

## Simplified backend layout

```text
app/
├── api/v1/                        # HTTP endpoints exposed to mobile
├── orchestration/                 # Conversation flow / LangGraph-ready state machine
├── domain/pathways/               # Shared pathway blueprint + instantiation logic
├── integrations/resource_service/ # Only runtime boundary to the resource service
├── repositories/                  # App database access only
├── services/                      # Application services and post-processing
├── models/                        # SQLAlchemy models owned by the app service
├── schemas/                       # Pydantic request/response schemas
├── db/                            # Database engine and session
└── core/                          # Config, security, cache, exceptions
```

## Local development

Run the canonical Docker stack from repo root:

```bash
./scripts/bootstrap_stack.sh
```

If you want to run the app-service directly on your host instead of inside Docker:

```bash
cd backend
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

That local process is configured to talk to:
- app DB on `localhost:15432`
- resource service on `http://localhost:18100/api/v1`

## Public API surface

Canonical endpoints:
- `/api/v1/chat/send`
- `/api/v1/pathways/*`
- `/api/v1/content/*` (proxy facade to resource-service)
- `/api/v1/memories/*`
- `/api/v1/prayer-times/*`
- `/api/v1/locations/*`
