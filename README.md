# QuranApp (Final Projesi)

QuranApp, kullanıcıların İslami içeriklerle zenginleştirilmiş, sohbet tabanlı terapi flows (conversational therapy), öğrenme yolları (pathways) ve namaz vakitleri gibi özellikleri kişiselleştirilmiş bir şekilde deneyimleyebileceği yapay zeka (AI) destekli bir mobil uygulamadır.

Bu proje projesi, ölçeklenebilir mikroservis mimarisine, anlamsal arama (semantic search) ve Graph veritabanı (Neo4j) gücüne dayanan sağlam bir backend katmanıyla desteklenmektedir.

---

## 🏗️ Sistem Mimarisi ve İstek Akışı

Proje üç ana bileşen üzerinden çalışacak şekilde tasarlanmış tek bir kanonik "local stack" yapısını benimser:

```text
📱 mobile-app (Mobil İstemci)
   └── 🌐 backend/ (App Service)
        └── 🧠 resource-service/ (Resource Service)
```

1. **Mobil istemci** yalnızca ve doğrudan **App Service** ile iletişim kurar. 
2. **App Service**, domain'ine girmeyen ve bilgi tabanı / AI işlemleri gerektiren durumlarda HTTP üzerinden **Resource Service**'e ağrı yapar.

### Mikroservis Sınırları & Sorumluluklar

| Servis Adı | Sorumluluk Alanları (Sahiptir) | Sahip Olmadığı Alanlar |
| :--- | :--- | :--- |
| **App Service** | - Authentication (Kullanıcı Girişi)<br>- Users & Profiles<br>- Sohbetler (Conversations)<br>- Hafıza Yönetimi (Memories)<br>- Aktif Öğrenme Yolları (Pathways)<br>- Namaz Vakitleri & Konum Yönetimi<br>- Mobile özel tasarlanmış API gateway işlevi | - Kaynak içerik depolama (Source Content)<br>- Anlamsal Arama (Semantic Search)<br>- Anahtar Kelime Taksonomisi<br>- Neo4j Graph İşlemleri |
| **Resource Serv.** | - `knowledge_units` Yönetimi<br>- İçerik Embedding'leri (Vektör Varlıkları)<br>- Anahtar kelime normalizasyonu & taxonomy<br>- Neo4j Graph izdüşümleri (Projection)<br>- AI Arama (Source Retrieval) API'leri<br>- Graph Context | Kullanıcı yönetimi veya auth state'leri |

---

## 🛠️ Kullanılan Teknolojiler ve Gereksinimler (Requirements)

Sistem hem Node.js (Frontend) hem de Python (Backend) ekosistemlerini bir arada çalıştırır.

### Ortam Gereksinimleri
- **İşletim Sistemi:** Linux / macOS / Windows (WSL2 önerilir)
- **Docker & Docker Compose** (Veritabanları ve servis container'ları için)
- **Node.js** (v18.x veya üzeri) ve `npm` / `yarn`
- **Python** (3.10 veya üzeri, lokal betikler için)
- **Git**

### 📱 Mobil Uygulama (mobile-app)
- **Framework:** React Native (`0.81.5`) & Expo (`54.0.0`)
- **Router/Gezinme:** Expo Router (`~6.0.23`)
- **UI & Tasarım:** Özel Mosqui Design System, Lucide React Native (İkonlar), `@expo-google-fonts/` suite (Inter, Amiri, Fraunces).
- **Yerel/Async Depolama:** `@react-native-async-storage/async-storage` ve `expo-secure-store`
- **Animasyon:** `react-native-reanimated`

### 🌐 App Service (Backend)
- **Framework:** FastAPI (`0.115.0`) & Uvicorn (`0.32.0`)
- **Veritabanı:** PostgreSQL Async (`asyncpg`, `sqlalchemy[asyncio]`), `pgvector`, Alembic (`1.14.0` migration aracı)
- **Validasyon & Şema:** Pydantic (`2.10.3`) & Pydantic Settings
- **Güvenlik & Auth:** `python-jose`, `passlib[bcrypt]`
- **AI & Dil İşleme:** `google-genai`, `langgraph`
- **İstemci & Loglama:** `httpx`, `structlog`

### 🧠 Resource Service
- **Framework:** FastAPI (`0.115.0`) & Uvicorn
- **İlişkisel Veritabanı:** PostgreSQL Async & pgvector
- **Grafik Veritabanı:** Neo4j Python Driver (`neo4j==6.1.0`)
- **AI:** `google-genai`

---

## 🚀 Hızlı Başlangıç (Quick Start)

Proje lokal geliştirme ortamında Docker üzerinden tek satırla ayağa kaldırılabilecek şekilde tasarlanmıştır.

### 1. Ortam Değişkenlerinin Hazırlanması
İlk olarak `.env.example` dosyasından bir yerel ayar dosyası oluşturun:
```bash
cp .env.example .env
```
*(Gerekiyorsa LLM / Gemini vb. API key'lerinizi `.env` içerisine tanımlayın)*

### 2. Backend Stack'inin Ayağa Kaldırılması
Aşağıdaki bash scriptleri Docker kullanarak stack'i kurar ve ayağa kalktığından emin olmak için test eder:
```bash
# Tüm sistemin veritabanlarını ve python servislerini bootstrap eder (App / Resource / Neo4j)
./scripts/bootstrap_stack.sh

# Sistemlerin sağlıklı şekilde HTTP yanıtı verdiğini doğrular
./scripts/smoke_test_stack.sh
```

### 3. Mobil Uygulamayı (Expo) Başlatma
Backend başarılı bir şekilde çalıştıktan sonra mobil tarafı ayağa kaldırmak için:
```bash
cd mobile-app
npm install  # (veya yarn install)
npm start
```
Mobil uygulama geliştirme sırasında, istekler varsayılan olarak **`http://127.0.0.1:18000/api/v1`** (App Service) adresine yönlendirilecektir.

---

## 🔌 Yerel Geliştirme Portları & Yapılandırma

`docker-compose` çalıştırıldığında sistem şu portlardan servis sunar:

| Bileşen | Yerel Port (Host) | Açıklama |
| :--- | :--- | :--- |
| **App Service** | `18000` | Mobilin istek yaptığı ana giriş noktası |
| **Resource Service** | `18100` | Backend'in dahili bilgi havuzu erişimi |
| **PostgreSQL (App)** | `15432` | Kullanıcı/App verilerinin tutulduğu DB |
| **PostgreSQL (Resource)** | `15433` | Vektörlerin & embed'lerin tutulduğu DB |
| **Neo4j (HTTP)** | `17475` | Graph veritabanı tarayıcı / HTTP arayüzü |
| **Neo4j (Bolt)** | `17688` | Uygulama entegrasyon protokol kanalı |

---

## 📁 Repo Dizini / Klasör Yapısı

- `backend/` : **App Service** kodunu barındırır (FastAPI, Alembic migrations, testler vb.).
- `resource-service/` : **Resource (Bilgi/Graph)** mikroservisinin kodunu barındırır.
- `mobile-app/` : İstemci yüzü olan **React Native/Expo** projesini içerir.
- `docs/` : Detaylı sistem mimarisi, kurulum senaryoları ve referans dokümanları barındırır.
- `scripts/` : Sistemi ayağa kaldırma (`bootstrap`), test (`smoke_test`) ve otomasyon betiklerini içerir.

---

## 📚 Dokümantasyon Referansları

Daha derin teknik analiz, kurulum aşamaları ve veritabanı şemaları için aşağıdaki kaynakları okumanız önerilir:

1. **Sistem Mimarisi**
   - [`docs/architecture-v2.md`](docs/architecture-v2.md) (Güncel v2 mimarisi)
   - [`docs/service-boundaries.md`](docs/service-boundaries.md) (Servis domain alanları)
   - [`docs/clean-stack.md`](docs/clean-stack.md) (Temiz lokal geliştirme prensipleri)
2. **Setup ve Kurulum**
   - [`docs/database/kurulum.md`](docs/database/kurulum.md) (Veritabanı spesifik kurulum adımları)
3. **Servis README Dosyaları**
   - [`backend/README.md`](backend/README.md)
   - [`resource-service/README.md`](resource-service/README.md)
