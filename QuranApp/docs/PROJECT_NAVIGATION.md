# Proje Navigasyonu

Bu repo hızlıca yön bulmak için hazırlanmış kısa bir haritadır.

## Başlangıç Noktaları

- API sunucusu: `backend/app/main.py`
- Ana zeka akışı: `backend/app/services/master_brain.py`
- rutin motoru: `backend/app/services/prescription_engine.py`
- Arama motoru: `backend/app/services/search_router.py`
- AI servisi: `backend/app/services/ai_service.py`
- Docker servisleri: `docker-compose.yml`

## Backend Mimarisi

- API Endpoints: `backend/app/api/v1/endpoints/`
- Servisler: `backend/app/services/`
- Modeller (DB): `backend/app/models/`
- Şemalar (Pydantic): `backend/app/schemas/`
- Altyapı: `backend/app/core/` (config, security, cache, dependencies)
- Veritabanı: `backend/app/db/`

## Mobil Uygulama (React Native / Expo)

- Tablar: `mobile-app/app/(tabs)/`
- Aksiyon akışları: `mobile-app/app/action/`
- Ayarlar: `mobile-app/app/settings.tsx`
- API Servisleri: `mobile-app/services/`
- Auth Context: `mobile-app/contexts/AuthContext.tsx`

## Veri ve İşleme (Pipeline)

- Veri zenginleştirme: `scripts/01_enrichment/`
- Embedding üretimi: `scripts/02_embedding/`
- DB yükleme ve senkron: `scripts/03_database/`
- Pipeline yardımcıları: `scripts/utils/`
- Ham veri setleri: `data/`

## Ne zaman nereye bakmalı?

- API cevapları neden yanlış? → `backend/app/services/master_brain.py`
- rutin kartı içeriği? → `backend/app/services/prescription_engine.py`
- Mobil UI hatası? → `mobile-app/app/...`
- Veri eksik/yanlış? → `data/` ve `scripts/03_database/`
- Auth problemi? → `backend/app/api/v1/endpoints/auth.py`
- Plan sistemi? → `backend/app/services/plan_service.py`
