# 📖 QuranApp - Manevi rutin Sistemi

> **Yapay Zeka Destekli İslami Manevi Terapist**  
> Kullanıcının ruh halini analiz edip teşhis koyan ve kişiselleştirilmiş manevi rutin yazan bir AI sistemi.

---

## 🧭 Hızlı Navigasyon

Repo karışıksa önce buradan başlayın:

- docs/PROJECT_NAVIGATION.md
- run_app.sh
- scripts/api_server.py

## 📋 İçindekiler

1. [Proje Vizyonu](#-proje-vizyonu)
2. [Sistem Mimarisi](#-sistem-mimarisi)
3. [Teknoloji Yığını](#-teknoloji-yığını)
4. [Veri Akışı](#-veri-akışı-pipeline)
5. [Veritabanı Şeması](#-veritabanı-şeması)
6. [Backend Scriptleri](#-backend-scriptleri)
7. [API Dokümantasyonu](#-api-dokümantasyonu)
8. [Frontend (Web + Mobil)](#-frontend-web--mobil)
9. [Kurulum Rehberi](#-kurulum-rehberi)
10. [Geliştirme Araçları](#-geliştirme-araçları)

---

## 🌟 Proje Vizyonu

### Problem
Kullanıcılar dini sorular sorduğunda veya manevi sıkıntılarını paylaştığında, sadece bir ayet aramak yeterli değildir. Kişinin duygusal durumuna göre **bütüncül bir yaklaşım** gerekir.

### Çözüm
Bu sistem, bir **Manevi Terapist** gibi çalışır:

1. **Dinler:** Kullanıcının derdini anlar
2. **Teşhis Koyar:** Hangi duygusal/ruhsal ihtiyaç var?
3. **rutin Yazar:** Kişiye özel Ayet + Esma + Dua kombinasyonu sunar

### Örnek Senaryo

**Kullanıcı:** *"İçim çok daralıyor, uyuyamıyorum geceleri"*

**Sistem Analizi:**
- Duygu: Kaygı, Huzursuzluk
- İhtiyaç: Güven, Sekinet, Teslimiyet

**rutin:**
| Bileşen | İçerik |
|---------|--------|
| 💊 Zikir | **Es-Selâm** (Esenlik veren) - Günde 99 kez |
| 🤲 Dua | *"Allah'ım, bana huzur ve sükûnet ver..."* - Hz. Muhammed (s.a.v.) |
| 📖 Ayet | İnşirah Suresi 5-6: *"Muhakkak ki zorlukla beraber kolaylık vardır"* |

---

## 🏗 Sistem Mimarisi

### Üst Düzey Görünüm

```
┌────────────────────────────────────────────────────────────────────┐
│                         KULLANICI ARAYÜZÜ                          │
├──────────────────────────┬─────────────────────────────────────────┤
│     📱 Mobil Uygulama    │           🌐 Web Arayüzü                │
│    (React Native/Expo)   │          (HTML/CSS/JS)                  │
│    mobile/App.js         │         frontend/index.html             │
└──────────────────────────┴──────────────────┬──────────────────────┘
                                              │
                                    HTTP POST /chat
                                              │
                                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                         API KATMANI                                │
│                    scripts/api_server.py                           │
│                                                                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │    FastAPI   │───▶│  Redis Cache │───▶│   Response   │         │
│  │   Endpoint   │    │  (24h TTL)   │    │   Handler    │         │
│  └──────────────┘    └──────────────┘    └──────────────┘         │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                        MASTER BRAIN                                │
│                   scripts/main_assistant.py                        │
│                                                                    │
│   Gemini 2.0 Flash ile Intent Classification (Niyet Sınıflandırma) │
│                                                                    │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐              │
│   │    CHAT     │   │ PRESCRIPTION│   │  GUARDRAIL  │              │
│   │  (Sohbet)   │   │  (rutin)   │   │ (Güvenlik)  │              │
│   └──────┬──────┘   └──────┬──────┘   └─────────────┘              │
│          │                 │                                       │
│          ▼                 ▼                                       │
│   Doğrudan Yanıt    prescribe.py                                   │
└────────────────────────────┬───────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                     PRESCRIPTION ENGINE                            │
│                     scripts/prescribe.py                           │
│                                                                    │
│   AŞAMA 1: DIAGNOSE (Teşhis)                                       │
│   ├── Gemini 2.0 ile duygu analizi                                 │
│   └── Çıktı: emotional_state, root_cause, search_keywords          │
│                                                                    │
│   AŞAMA 2: RETRIEVE (Tedarik)                                      │
│   ├── retrieve_esma() → esma_ul_husna tablosundan                  │
│   ├── retrieve_dua()  → prophet_duas tablosundan                   │
│   └── retrieve_verses() → knowledge_units tablosundan              │
│       └── Hybrid Search: TEXT + VECTOR                             │
│                                                                    │
│   AŞAMA 3: SYNTHESIZE (Sentez)                                     │
│   └── rutin Kartı oluştur                                         │
└────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                        VERİTABANI                                  │
│                      PostgreSQL + pgvector                         │
│                                                                    │
│   ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐      │
│   │ knowledge_units │ │  esma_ul_husna  │ │  prophet_duas   │      │
│   │   (6236 Ayet)   │ │   (99 Esma)     │ │  (100+ Dua)     │      │
│   │  + embeddings   │ │  + embeddings   │ │  + embeddings   │      │
│   └─────────────────┘ └─────────────────┘ └─────────────────┘      │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Teknoloji Yığını

### Backend
| Teknoloji | Kullanım Amacı |
|-----------|----------------|
| **Python 3.10+** | Ana programlama dili |
| **FastAPI** | REST API framework |
| **Gemini 2.0 Flash** | LLM (Intent classification, Diagnosis) |
| **Gemini Embedding** | Metin vektörleştirme (768 boyut) |
| **PostgreSQL** | Ana veritabanı |
| **pgvector** | Vektör benzerlik araması |
| **Redis** | Sonuç önbellekleme |
| **Docker** | Servis konteynerizasyonu |

### Frontend
| Teknoloji | Kullanım Amacı |
|-----------|----------------|
| **HTML/CSS/JS** | Web arayüzü |
| **React Native** | Mobil uygulama |
| **Expo** | React Native geliştirme ortamı |
| **Axios** | HTTP client |

---

## 🔄 Veri Akışı (Pipeline)

Projenin veri işleme süreci 4 aşamadan oluşur:

### Aşama 1: Veri Toplama
```
Ham Kuran Meali (Türkçe) → quran_turkish.json
```
- 6236 ayet
- Sure adı, ayet numarası, Türkçe meal

### Aşama 2: Zenginleştirme (Enrichment)
```
scripts/01_enrichment/batch_prepare.py
scripts/01_enrichment/batch_submit.py
```

Her ayet için Gemini AI şunları üretir:
- **Anahtar Kelimeler** (5-7 adet): Arama için
- **Psiko-Spiritüel Açıklama**: Ayetin psikolojik bağlamı

**Örnek:**
```json
{
  "surah_no": 94,
  "verse_no": 5,
  "text_tr": "Muhakkak zorlukla beraber kolaylık vardır",
  "keywords": ["zorluk", "kolaylık", "umut", "sabır", "ferahlık"],
  "explanation": "Bu ayet, hayatın döngüsel doğasını vurgular. Sıkıntı anlarında bile umudun korunması gerektiğini öğretir..."
}
```

### Aşama 3: Vektörleştirme (Embedding)
```
scripts/02_embedding/generate_embeddings.py
```

Her metnin (ayet + açıklama) 768 boyutlu sayısal vektöre dönüştürülmesi:
```
"Zorlukla beraber kolaylık vardır" → [0.023, -0.156, 0.089, ...]
```

Bu vektörler **anlam benzerliği** aramayı mümkün kılar:
- "Sıkıntı çekiyorum" sorgusu
- → Vektöre dönüştür
- → En yakın vektörleri bul
- → "Zorluk/Kolaylık" ayeti çıkar

### Aşama 4: Veritabanına Yükleme
```
scripts/03_database/final_db_insert.py
scripts/03_database/create_prescription_tables.py
scripts/embed_and_insert_prescription.py
```

---

## 💾 Veritabanı Şeması

### Tablo 1: `knowledge_units` (Kuran Ayetleri)

| Kolon | Tip | Açıklama | Örnek |
|-------|-----|----------|-------|
| `id` | SERIAL | Primary Key | 1 |
| `content_text` | TEXT | Türkçe meal | "Zorlukla beraber kolaylık vardır" |
| `explanation` | TEXT | Psiko-spiritüel açıklama | "Bu ayet umut ve sabır mesajı verir..." |
| `embedding` | VECTOR(768) | Anlam vektörü | [0.023, -0.156, ...] |
| `metadata` | JSONB | Ek bilgiler | `{"surah_no": 94, "verse_no": 5, "surah_name": "İnşirah", "arabic_text": "..."}` |

**İndeksler:**
- `idx_knowledge_units_embedding` (HNSW): Vektör araması için
- GIN index on `metadata`: JSON sorguları için

---

### Tablo 2: `esma_ul_husna` (99 İsim)

| Kolon | Tip | Açıklama | Örnek |
|-------|-----|----------|-------|
| `id` | SERIAL | Primary Key | 1 |
| `name` | VARCHAR(50) | Türkçe isim | "Es-Selâm" |
| `appellation` | VARCHAR(50) | Arapça yazılış | "السلام" |
| `meaning` | TEXT | Anlam açıklaması | "Esenlik veren, huzur kaynağı" |
| `referral_note` | TEXT | Ne zaman zikredilir | "Kaygı ve huzursuzluk hallerinde..." |
| `embedding` | VECTOR(768) | Anlam vektörü | [...] |

---

### Tablo 3: `prophet_duas` (Peygamber Duaları)

| Kolon | Tip | Açıklama | Örnek |
|-------|-----|----------|-------|
| `id` | SERIAL | Primary Key | 1 |
| `source` | VARCHAR(100) | Kaynak | "Buhari, Deavat 46" |
| `turkish_text` | TEXT | Türkçe metin | "Allah'ım, bana huzur ver..." |
| `context` | TEXT | Hangi durumda okunur | "Uykusuzluk çekenler için" |
| `emotional_tags` | TEXT[] | Duygu etiketleri | ["kaygı", "uykusuzluk", "huzur"] |
| `embedding` | VECTOR(768) | Anlam vektörü | [...] |

---

## 📁 Backend Scriptleri

### Ana Motorlar

| Script | Dosya | Açıklama |
|--------|-------|----------|
| **API Server** | `scripts/api_server.py` | REST API endpoint'lerini yönetir |
| **Master Brain** | `scripts/main_assistant.py` | Intent classification yapar (CHAT/PRESCRIPTION/GUARDRAIL) |
| **Prescription Engine** | `scripts/prescribe.py` | Teşhis + rutin mantığı |
| **Search Router** | `scripts/search_router.py` | Arama stratejisini belirler |

---

### `scripts/api_server.py` - API Sunucusu

**Görev:** HTTP isteklerini alır, cache kontrol eder, Master Brain'e yönlendirir.

**Akış:**
```python
1. POST /chat → İstek al
2. Redis Cache kontrol et (SHA256 hash)
   ├── HIT: Anında döndür (5ms)
   └── MISS: Devam et
3. Master Brain'e gönder
4. Sonucu Redis'e kaydet (24 saat TTL)
5. Response döndür
```

**Kod Parçası:**
```python
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    cache_key = get_cache_key(request.message)  # SHA256 hash
    
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)  # ⚡ Anında
    
    result = brain.process(request.message)  # 🧠 İşle
    
    redis_client.setex(cache_key, 86400, result)  # 💾 Kaydet
    return result
```

---

### `scripts/main_assistant.py` - Master Brain

**Görev:** Kullanıcının niyetini anlamak ve doğru yöne yönlendirmek.

**Intent Türleri:**

| Intent | Tetikleyici | Aksiyon |
|--------|-------------|---------|
| `CHAT` | Selamlaşma, genel sohbet | Doğrudan LLM yanıtı |
| `PRESCRIPTION` | Dert, şikayet, dua/ayet isteği | rutin motorunu çalıştır |
| `GUARDRAIL` | Uygunsuz içerik | Nazik reddetme |

**Örnek Sınıflandırma:**
```
"Merhaba" → CHAT
"Çok bunaldım" → PRESCRIPTION
"Şu kişiye beddua et" → GUARDRAIL
```

---

### `scripts/prescribe.py` - rutin Motoru

**Görev:** 3 aşamalı manevi terapi süreci.

#### Aşama 1: Diagnose (Teşhis)

```python
def diagnose(self, user_input: str) -> Diagnosis:
    """Gemini ile duygu analizi"""
    prompt = f"""
    Kullanıcı: "{user_input}"
    
    Analiz et:
    1. emotional_state: Ana duygu (Kaygı, Öfke, Üzüntü...)
    2. root_cause: Psikolojik sebep
    3. spiritual_needs: Manevi ihtiyaçlar
    4. search_keywords: Arama anahtar kelimeleri
    """
    return gemini.generate(prompt)
```

#### Aşama 2: Retrieve (Tedarik)

**Hibrit Arama Stratejisi:**

```python
def retrieve_verses(self, keywords):
    # 1. METİN ARAMASI (Öncelikli)
    for keyword in keywords:
        # Normalize et (ş→s, ğ→g)
        normalized = normalize(keyword)
        # Kırp (Şifa→Sif) - Aksan problemleri için
        chopped = normalized[:-1]
        
        results = db.query("""
            SELECT * FROM knowledge_units
            WHERE content_text ILIKE %s  -- Tam kelime
               OR content_text ILIKE %s  -- Normalize
               OR content_text ILIKE %s  -- Kırpılmış
            ORDER BY content_match DESC  -- İçerikte geçen önce
            LIMIT 1
        """, [keyword, normalized, chopped])
    
    # 2. VEKTÖR ARAMASI (Fallback)
    if len(results) < 2:
        results += db.query("""
            SELECT * FROM knowledge_units
            ORDER BY embedding <=> %s::vector  -- Cosine similarity
            LIMIT 2
        """, [query_embedding])
    
    return results
```

**Neden Hibrit?**
- "Uyku ayeti ver" → TEXT aramayla doğrudan "uyku" kelimesi geçen ayet bulunur
- "Hayatın anlamı" → VECTOR aramayla anlam benzerliği ile ilgili ayetler bulunur

#### Aşama 3: Synthesize (Sentez)

```python
def synthesize_prescription(self, diagnosis, esmas, duas, verses):
    return {
        "advice": f"Bu rutin {diagnosis.emotional_state} durumunuz için hazırlandı...",
        "esmas": esmas,
        "duas": duas,
        "verses": verses,
        "zikir_count": 33  # Günlük zikir sayısı
    }
```

---

## 🔌 API Dokümantasyonu

### Endpoint: `POST /chat`

**URL:** `http://localhost:8000/chat`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "string (kullanıcı mesajı)"
}
```

**Response (CHAT Intent):**
```json
{
  "intent": "CHAT",
  "response_text": "Merhaba! Size nasıl yardımcı olabilirim?",
  "prescription": null
}
```

**Response (PRESCRIPTION Intent):**
```json
{
  "intent": "PRESCRIPTION",
  "response_text": "Bu rutin sizin manevi durumunuza özel hazırlanmıştır.",
  "prescription": {
    "advice": "Duygusal durumunuz: Kaygı...",
    "esmas": [
      {
        "name_tr": "Es-Selâm",
        "name_ar": "السلام",
        "meaning": "Esenlik veren, huzur kaynağı",
        "reason": "Kaygı ve huzursuzluk hallerinde zikredilir"
      }
    ],
    "duas": [
      {
        "source": "Buhari, Deavat 46",
        "text_tr": "Allah'ım! Nefsime takvasını ver...",
        "context": "Kalp huzuru için"
      }
    ],
    "verses": [
      {
        "verse_text_ar": "أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ",
        "verse_text_tr": "Dikkat edin! Kalpler ancak Allah'ı anmakla huzur bulur.",
        "surah_no": 13,
        "verse_no": 28,
        "verse_tr_name": "Ra'd Suresi",
        "explanation": "Bu ayet kalp huzurunun kaynağını gösterir..."
      }
    ]
  }
}
```

---

## 📱 Frontend (Web + Mobil)

### Web Arayüzü (`frontend/index.html`)

Basit bir chat arayüzü:
- Mesaj giriş alanı
- Mesaj listesi (kullanıcı/bot)
- rutin kartı görüntüleme

**Çalıştırma:**
```bash
# API sunucusunu başlat
python scripts/api_server.py

# HTML dosyasını tarayıcıda aç
start frontend/index.html
```

---

### Mobil Uygulama (`mobile/`)

React Native (Expo) ile geliştirilmiş native uygulama.

**Dosya Yapısı:**
```
mobile/
├── App.js                    # Ana ekran (Chat UI)
├── components/
│   └── PrescriptionCard.js   # rutin kartı bileşeni
└── services/
    └── api.js                # Backend bağlantısı
```

**`services/api.js` - Backend Bağlantısı:**
```javascript
import axios from 'axios';

// Fiziksel cihaz için bilgisayarın LAN IP'si
const BASE_URL = 'http://192.168.1.164:8000';

export const sendMessage = async (message) => {
  const response = await axios.post('/chat', { message });
  return response.data;
};
```

**`components/PrescriptionCard.js` - rutin Kartı:**
```javascript
const PrescriptionCard = ({ prescription }) => {
  const esma = prescription.esmas?.[0];
  const dua = prescription.duas?.[0];
  const verse = prescription.verses?.[0];

  return (
    <View style={styles.card}>
      {/* Esma Bölümü */}
      <Text style={styles.title}>ZİKİR</Text>
      <Text>{esma?.name_tr}</Text>
      
      {/* Dua Bölümü */}
      <Text style={styles.title}>DUA</Text>
      <Text>"{dua?.text_tr}"</Text>
      
      {/* Ayet Bölümü */}
      <Text style={styles.title}>AYET</Text>
      <Text>{verse?.verse_text_tr}</Text>
    </View>
  );
};
```

**Çalıştırma:**
```bash
cd mobile
npm install
npx expo start
```

> **Not:** Telefonunuza Expo Go uygulamasını indirip QR kodu taratın.

---

## 🚀 Kurulum Rehberi

### Önkoşullar

1. **Python 3.10+**
2. **Node.js 18+** (Mobil için)
3. **Docker Desktop**
4. **Gemini API Key** (Google AI Studio'dan alın)

### Adım 1: Repository'yi Klonlayın

```bash
git clone https://github.com/rtndigital/QuranApp.git
cd QuranApp
```

### Adım 2: Docker Servislerini Başlatın

```bash
docker-compose up -d
```

Bu komut şunları başlatır:
- PostgreSQL (port 5432)
- Redis (port 6379)

### Adım 3: Backend'i Başlatın

```bash
# Terminal 1:
cd backend
source venv/bin/activate     # macOS/Linux
# venv\Scripts\activate      # Windows
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

> **✅ Başarılı çıktı:**
> ```
> 🧠 Master Brain (Conversational) Initializing...
> ✅ Master Brain Ready.
> ✅ Redis connected
> INFO:     Application startup complete.
> ```

### Adım 4: Mobil Uygulamayı Başlatın

```bash
# Terminal 2:
cd mobile-app
npm install          # İlk seferde
npm start            # Expo Dev Server
```

> **📱 Test:** Expo Go uygulamasıyla QR kodu taratın.

### Adım 5: Ortam Değişkenleri

Backend `.env` dosyası (`backend/.env`):
```bash
cp backend/.env.example backend/.env
# .env içini doldurun:
# GEMINI_API_KEY=...
# DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
# REDIS_HOST, REDIS_PORT
```

### Adım 6: Veritabanını Hazırlayın (İlk Kurulum)

```bash
cd backend && source venv/bin/activate

# Tabloları oluştur
python scripts/03_database/create_prescription_tables.py

# Ayetleri yükle (eğer data varsa)
python scripts/03_database/final_db_insert.py

# Esma ve Duaları yükle
python scripts/embed_and_insert_prescription.py
```

---

## ⚡ Hızlı Başlangıç (Özet)

Her geliştirme oturumunda sadece bu 3 adım yeterli:

```bash
# 1. Docker (PostgreSQL + Redis)
docker-compose up -d

# 2. Backend (Terminal 1)
cd backend && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Mobile (Terminal 2)
cd mobile-app && npm start
```

---

## 🔧 Geliştirme Araçları

### Test Scriptleri

| Script | Açıklama | Kullanım |
|--------|----------|----------|
| `test_search.py` | Arama motorunu test et | `python scripts/test_search.py --query "uyku"` |
| `analyze_relevance.py` | Sonuç kalitesini ölç | `python scripts/analyze_relevance.py` |
| `inspect_metadata.py` | DB yapısını incele | `python scripts/inspect_metadata.py` |
| `test_api_cache.py` | Redis cache'i test et | `python scripts/test_api_cache.py` |

### Debug Komutları

```bash
# Redis içeriğini temizle
docker exec quran-redis redis-cli FLUSHALL

# PostgreSQL'e bağlan
docker exec -it quran-postgres psql -U admin -d islamic_knowledge_source

# Tüm ayetleri say
SELECT COUNT(*) FROM knowledge_units;

# Esmaları listele
SELECT name, meaning FROM esma_ul_husna LIMIT 10;
```

---

## 📊 Performans Metrikleri

| Metrik | Değer |
|--------|-------|
| Ortalama yanıt süresi (cache miss) | 2-3 saniye |
| Ortalama yanıt süresi (cache hit) | 5-10 ms |
| Vektör arama süresi | < 50 ms |
| Toplam ayet sayısı | 6236 |
| Toplam esma sayısı | 99 |
| Toplam dua sayısı | 100+ |

---

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Değişiklikleri commit edin (`git commit -m 'Yeni özellik eklendi'`)
4. Branch'i push edin (`git push origin feature/yeni-ozellik`)
5. Pull Request açın

---

## 📄 Lisans

Bu proje eğitim ve kişisel kullanım amaçlıdır.

---

## 👤 Geliştirici

**Deniz**  
*Ocak 2026*

---

## 🙏 Teşekkürler

- Google Gemini AI ekibine
- PostgreSQL ve pgvector topluluğuna
- React Native ve Expo ekibine
