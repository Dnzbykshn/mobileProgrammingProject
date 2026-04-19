# QuranApp (Final Project)

QuranApp is an AI-powered mobile application designed to offer users a personalized experience through chat-based conversational therapy, learning pathways, and prayer times enriched with Islamic context.

This final project is backed by a robust, scalable microservices architecture that leverages the power of semantic search and a persistent Graph Database (Neo4j).

---

## 🏗️ System Architecture & Request Flow

The project adopts a canonical "local stack" architecture built around three core components:

```text
📱 mobile-app (Mobile Client)
   └── 🌐 backend/ (App Service)
        └── 🧠 resource-service/ (Resource Service)
```

1. **Mobile Client** strictly communicates only with the **App Service**. 
2. The **App Service** makes HTTP requests to the **Resource Service** when dealing with operations outside its domain—such as retrieving AI components, semantic context, and knowledge base nodes.

### Microservice Boundaries & Responsibilities

| Service Name | Core Responsibilities (Owns) | Out of Scope (Does Not Own) |
| :--- | :--- | :--- |
| **App Service** | - Authentication & Authorization<br>- Users & Profiles<br>- Chat / Conversations<br>- Memories<br>- Active Learning Pathways<br>- Prayer Times & Locations<br>- Serves as the mobile-facing API Gateway | - Source Content Storage<br>- Semantic Search<br>- Keyword Taxonomy<br>- Neo4j Graph Operations |
| **Resource Serv.** | - `knowledge_units` Management<br>- Content Embeddings (Vectors)<br>- Keyword Normalization & Taxonomy<br>- Neo4j Graph Projections<br>- AI Source Retrieval APIs<br>- Graph Context Provision | - User operations<br>- Auth states |

---

## 🛠️ Technology Stack & Requirements

The system seamlessly orchestrates both Node.js (Frontend) and Python (Backend) ecosystems together.

### Environment Prerequisites
- **Operating System:** Linux / macOS / Windows (WSL2 recommended)
- **Docker & Docker Compose** (For spinning up databases and isolated containers)
- **Node.js** (v18.x or higher) and `npm` / `yarn`
- **Python** (3.10+, for local scripts and virtual environments)
- **Git**

### 📱 Mobile Application (`mobile-app`)
- **Framework:** React Native (`0.81.5`) & Expo (`54.0.0`)
- **Routing/Navigation:** Expo Router (`~6.0.23`)
- **UI & Design:** Custom Mosqui Design System, Lucide React Native (Icons), `@expo-google-fonts/` suite (Inter, Amiri, Fraunces).
- **Local/Async Storage:** `@react-native-async-storage/async-storage` and `expo-secure-store`
- **Animations:** `react-native-reanimated`

### 🌐 App Service (`backend/`)
- **Framework:** FastAPI (`0.115.0`) & Uvicorn (`0.32.0`)
- **Database ORM & Driver:** PostgreSQL Async (`asyncpg`, `sqlalchemy[asyncio]`), `pgvector`, Alembic (`1.14.0` for migrations)
- **Validation & Schema:** Pydantic (`2.10.3`) & Pydantic Settings
- **Security & Auth:** `python-jose`, `passlib[bcrypt]`
- **AI Integration:** `google-genai`, `langgraph`
- **Client & Logging:** `httpx`, `structlog`

### 🧠 Resource Service (`resource-service/`)
- **Framework:** FastAPI (`0.115.0`) & Uvicorn
- **Relational DB:** PostgreSQL Async & pgvector
- **Graph Database:** Neo4j Python Driver (`neo4j==6.1.0`)
- **AI Validation:** `google-genai`

---

## 🚀 Quick Start

The project is structured to boot up the entire local development environment effortlessly using Docker.

### 1. Configure Environment Variables
Copy the example environment configuration to establish your local secrets:
```bash
cp .env.example .env
```
*(If required, make sure to insert your specific LLM/Gemini API keys directly into `.env`)*

### 2. Bootstrap the Backend Stack
Run the following bash scripts to provision your databases (App / Resource / Neo4j) and ensure the entire Python backend stack is successfully verified:
```bash
# Bootstraps the local DB schemas and Python microservices using Docker
./scripts/bootstrap_stack.sh

# Run post-build checks to ensure all HTTP services are healthy and responsive
./scripts/smoke_test_stack.sh
```

### 3. Launch the Mobile Application (Expo)
Once the backend is confirmed running, navigate to the mobile app directory and start the Expo dev server:
```bash
cd mobile-app
npm install  # (or yarn install)
npm start
```
During local mobile application development, the default HTTP request route points to **`http://127.0.0.1:18000/api/v1`** (App Service).

---

## 🔌 Local Ports & Container Mappings

Upon executing `docker-compose`, the application serves on the following local mappings:

| Component | Local Port (Host) | Description |
| :--- | :--- | :--- |
| **App Service** | `18000` | The main API entrypoint the mobile client talks to |
| **Resource Service** | `18100` | Internal knowledge-base retrieval access |
| **PostgreSQL (App)** | `15432` | Storage for Users/App State schemas |
| **PostgreSQL (Resource)** | `15433` | Storage for vectors and content embeddings |
| **Neo4j (HTTP)** | `17475` | Graph Database web UI / Browser interface |
| **Neo4j (Bolt)** | `17688` | Application integration channel protocol |

---

## 📁 Repository Structure

- `backend/` : Contains the code for the **App Service** (fastapi servers, alembic DB migrations, tests).
- `resource-service/` : Contains the code for the **Resource/Knowledge** microservice.
- `mobile-app/` : Holds the frontend client, built entirely using **React Native/Expo**.
- `docs/` : Features comprehensive tech-design documentation, architectural schemas, and reference material.
- `scripts/` : Shell scripts meant to automate initial setup (`bootstrap`), testing (`smoke_test`), and daily dev-ops.

---

## 📚 Documentation References

For an in-depth technical analysis, step-by-step setups, or database architectural reviews, refer to the following:

1. **System Architecture**
   - [`docs/architecture-v2.md`](docs/architecture-v2.md) (Detailed v2 architecture overview)
   - [`docs/service-boundaries.md`](docs/service-boundaries.md) (Service responsibilities and domains)
   - [`docs/clean-stack.md`](docs/clean-stack.md) (Local clean stack guidelines)
2. **Setup & Configurations**
   - [`docs/database/kurulum.md`](docs/database/kurulum.md) (Database-specific installation guides)
3. **Core Readmes**
   - [`backend/README.md`](backend/README.md)
   - [`resource-service/README.md`](resource-service/README.md)
