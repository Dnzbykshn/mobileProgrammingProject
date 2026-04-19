# QuranApp

Bu repo artık tek bir kanonik local stack üzerinden çalışır:

- `backend/` → **App Service**
- `resource-service/` → **Resource Service**
- `mobile-app/` → Expo Router tabanlı istemci

## Sorumluluklar

### App Service
Sahip olduğu alanlar:
- auth
- users / profiles
- conversations
- memories
- pathways
- prayer times / locations
- mobile-facing API

Sahip olmadığı alanlar:
- source content storage
- semantic search
- keyword taxonomy
- Neo4j graph

### Resource Service
Sahip olduğu alanlar:
- `knowledge_units`
- content embeddings
- keyword normalization / taxonomy
- Neo4j graph projection
- source retrieval APIs
- graph context

## Servis akışı

```text
mobile-app
   -> backend/ (App Service)
        -> resource-service/ (Resource Service)
```

Mobil istemci yalnızca App Service'e konuşur.
App Service gerektiğinde Resource Service'e HTTP üzerinden içerik isteği gönderir.

## Hızlı başlangıç

```bash
cp .env.example .env
./scripts/bootstrap_stack.sh
./scripts/smoke_test_stack.sh
```

Varsayılan local portlar:
- app-service: `18000`
- resource-service: `18100`
- app-db: `15432`
- resource-db: `15433`
- neo4j http: `17475`
- neo4j bolt: `17688`

Mobil uygulama geliştirme sırasında varsayılan olarak:
- `http://127.0.0.1:18000/api/v1`
adresine gider.

## Repo yapısı

- `backend/`: app-service
- `resource-service/`: resource mikroservisi
- `mobile-app/`: mobil uygulama
- `docs/`: mimari ve kurulum notları
- `scripts/`: bootstrap, smoke test ve bakım scriptleri

## Dokümantasyon

- `backend/README.md`
- `resource-service/README.md`
- `docs/architecture-v2.md`
- `docs/service-boundaries.md`
- `docs/clean-stack.md`
- `docs/database/kurulum.md`
