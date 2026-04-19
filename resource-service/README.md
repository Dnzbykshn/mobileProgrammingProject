# Resource Service

Independent content and retrieval service.

## Owns

- Quran / hadith / book-style source content
- content embeddings
- keyword normalization and taxonomy
- graph context and Neo4j projection
- semantic search and supporting passage retrieval

## Public responsibility

This service exposes source retrieval capabilities to the app service. It does
not know anything about users, conversations, pathways, or mobile UX.

Runtime endpoints are protected with the internal `X-Service-Token` header so
only trusted upstream services can call them.

## Canonical local stack

From repo root:

```bash
./scripts/bootstrap_stack.sh
```

That stack exposes the resource service on:
- `http://localhost:18100`
- PostgreSQL on `localhost:15433`
- Neo4j Bolt on `localhost:17688`

## Run only the resource service on host

```bash
cd resource-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8100
```

`resource-service/.env.example` is already aligned to the canonical Docker DB and Neo4j ports.

## Bootstrap data

Run the scripts in `resource-service/scripts/` after provisioning the resource
PostgreSQL and Neo4j instances.
