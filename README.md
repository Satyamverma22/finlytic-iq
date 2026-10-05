# Finlytic IQ

> AI-powered personal finance intelligence platform for financial health analysis, credit planning, government scheme discovery, fraud detection, and conversational financial guidance.

Finlytic IQ is a full-stack AI financial intelligence platform designed to help users understand their financial situation, explore credit scenarios, discover relevant financial schemes, identify potential fraud, and interact with a unified AI copilot.

The platform combines traditional financial calculations with AI, retrieval-augmented generation (RAG), vector search, fraud intelligence, consent management, and backend observability.

---

## Key Features

### Financial Health

* Manage personal financial profiles
* Track income and expenses
* Manage loan information
* Calculate financial health indicators
* Analyse overall financial position

### Credit Scenario Simulator

* Create credit and loan scenarios
* Compare multiple scenarios
* Analyse financial decision outcomes
* Support what-if financial planning

### Scheme Intelligence

* Match users with potentially relevant financial schemes
* Use structured scheme information and vector search
* Generate explanations for scheme recommendations
* Store scheme document chunks for retrieval
* Support personalised recommendations with consent

> **Development notice:** The current scheme dataset contains synthetic/demo data. Before production deployment, it must be replaced or verified using authoritative official government scheme information and official source links.

### Fraud Intelligence

* Analyse suspicious messages and text
* Detect potential fraud signals
* Categorise scam and fraud patterns
* Generate risk scores and explanations
* Store previous fraud scans
* Apply rate limiting to fraud analysis

### AI Financial Copilot

* Conversational financial assistance
* Connect financial context with supported platform capabilities
* Provide contextual financial guidance
* Apply authentication and consent requirements
* Rate-limit AI chat requests

### Consent & Privacy

Finlytic IQ uses explicit consent for sensitive financial features.

Supported consent purposes include:

* `financial_analysis`
* `fraud_analysis`
* `personalised_recommendations`

Sensitive operations are protected using authentication and consent dependencies.

### Observability

The backend includes basic observability for:

* Request IDs
* HTTP method and path
* Response status
* Request latency
* LLM model name
* LLM latency
* LLM call status

Sensitive values such as passwords, access tokens, OTPs, and other secret-like values are filtered from logs.

---

## Architecture

```text
                         +----------------------+
                         |     Next.js Web UI   |
                         | React + TypeScript   |
                         | Tailwind + shadcn/ui |
                         +----------+-----------+
                                    |
                                    | HTTP API
                                    v
                         +----------------------+
                         |      FastAPI API     |
                         |       Backend        |
                         +----------+-----------+
                                    |
             +----------------------+----------------------+
             |                      |                      |
             v                      v                      v
      +-------------+        +-------------+        +-------------+
      | PostgreSQL  |        |    Redis    |        |   Gemini    |
      | + pgvector  |        |             |        |     LLM     |
      +-------------+        +-------------+        +-------------+
             |
             v
      +---------------------+
      | Scheme / RAG Data   |
      | Vector Search       |
      +---------------------+
```

---

## Tech Stack

### Frontend

* Next.js 16
* React 19
* TypeScript
* Tailwind CSS
* shadcn/ui
* Lucide React
* React Hook Form
* Zod
* Sonner

### Backend

* Python
* FastAPI
* SQLAlchemy
* PostgreSQL
* pgvector
* Redis
* Pydantic
* JWT authentication

### AI

* Google Gemini
* Gemini `gemini-3.6-flash`
* Retrieval-Augmented Generation (RAG)
* Vector embeddings
* pgvector-based vector search

### Infrastructure

* Docker
* Docker Compose
* GitHub Actions
* PostgreSQL + pgvector
* Redis

---

## Project Structure

```text
financial-compass/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   ├── auth/
│   │   ├── consent/
│   │   ├── copilot/
│   │   ├── credit/
│   │   ├── financial/
│   │   ├── fraud/
│   │   ├── schemes/
│   │   ├── transactions/
│   │   ├── users/
│   │   └── ...
│   │
│   ├── tests/
│   ├── evaluation/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── public/
│   ├── Dockerfile
│   ├── package.json
│   └── ...
│
├── data/
├── docker/
├── docs/
├── ml/
│
├── .env.example
├── docker-compose.yml
├── test.csv
├── test_categorization.csv
├── test_duplicates.csv
└── README.md
```

---

## Local Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd financial-compass
```

### 2. Create the Environment File

The environment template is located at the project root.

```bash
cp .env.example .env
```

For Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Then configure the required values inside `.env`.

> Never commit `.env` to Git.

---

## Environment Variables

The root `.env.example` contains configuration for:

```env
# Database
DATABASE_URL=

# Redis
REDIS_URL=

# Auth
JWT_SECRET=
JWT_ALGORITHM=
ACCESS_TOKEN_EXPIRE_MINUTES=

# AI
LLM_PROVIDER=
LLM_API_KEY=
EMBEDDING_PROVIDER=
OCR_PROVIDER=

# Storage
STORAGE_ENDPOINT=
STORAGE_BUCKET=
```

For Gemini:

```env
LLM_PROVIDER=gemini
LLM_API_KEY=<your-gemini-api-key>
```

Do not expose API keys in source code, screenshots, commits, or documentation.

---

## Running with Docker

Finlytic IQ provides a Docker Compose setup for the main services.

### Start the Application

```bash
docker compose up --build
```

The main services are:

| Service               | Container     |   Port |
| --------------------- | ------------- | -----: |
| PostgreSQL + pgvector | `fc-postgres` | `5432` |
| Redis                 | `fc-redis`    | `6379` |
| FastAPI Backend       | `fc-backend`  | `8000` |
| Next.js Frontend      | `fc-frontend` | `3000` |

Frontend:

```text
http://localhost:3000
```

Backend:

```text
http://localhost:8000
```

Health endpoint:

```text
http://localhost:8000/health
```

Expected health response:

```json
{
  "api": "ok",
  "database": "ok",
  "redis": "ok"
}
```

---

## Scheme Data Setup

The scheme module contains seed data and embedding utilities.

Relevant files:

```text
backend/app/schemes/
├── seed_runner.py
├── seed_data.py
├── embed_chunks_runner.py
├── embedding_pipeline.py
├── vector_search.py
└── ...
```

After the application is running, seed the development scheme data:

```bash
docker exec -it fc-backend python -m app.schemes.seed_runner
```

Then generate embeddings for pending document chunks:

```bash
docker exec -it fc-backend python -m app.schemes.embed_chunks_runner
```

### Production Data Warning

The current scheme data is synthetic/demo data intended for development and evaluation.

Before production:

1. Replace synthetic scheme data.
2. Verify scheme eligibility criteria.
3. Verify scheme names and descriptions.
4. Use official government sources.
5. Store authoritative source links.
6. Re-run the embedding pipeline with the verified documents.

Finlytic IQ should not present synthetic scheme information as official government information.

---

## API

The backend exposes REST APIs through FastAPI.

Base URL:

```text
http://localhost:8000
```

### Authentication

Base route:

```text
/api/auth
```

| Method | Endpoint             | Purpose          |
| ------ | -------------------- | ---------------- |
| POST   | `/api/auth/register` | Register user    |
| POST   | `/api/auth/login`    | Login            |
| GET    | `/api/auth/me`       | Get current user |
| DELETE | `/api/auth/me`       | Delete account   |

### Consent

Base route:

```text
/api/consents
```

| Method | Endpoint                            | Purpose        |
| ------ | ----------------------------------- | -------------- |
| GET    | `/api/consents`                     | List consents  |
| POST   | `/api/consents`                     | Create consent |
| PATCH  | `/api/consents/{consent_id}/revoke` | Revoke consent |

### Financial Profile & Loans

Base route:

```text
/api/financial
```

| Method | Endpoint                                    | Purpose                   |
| ------ | ------------------------------------------- | ------------------------- |
| PUT    | `/api/financial/profile`                    | Update financial profile  |
| GET    | `/api/financial/profile`                    | Get financial profile     |
| POST   | `/api/financial/loans`                      | Add loan                  |
| GET    | `/api/financial/loans`                      | List loans                |
| PATCH  | `/api/financial/loans/{loan_id}/deactivate` | Deactivate loan           |
| GET    | `/api/financial/health`                     | Financial health analysis |

### Transactions

Base route:

```text
/api/transactions
```

| Method | Endpoint                   | Purpose                 |
| ------ | -------------------------- | ----------------------- |
| POST   | `/api/transactions/upload` | Upload transaction data |
| GET    | `/api/transactions`        | Retrieve transactions   |

### Credit Scenarios

Base route:

```text
/api/credit-scenarios
```

| Method | Endpoint                        | Purpose           |
| ------ | ------------------------------- | ----------------- |
| POST   | `/api/credit-scenarios`         | Create scenario   |
| GET    | `/api/credit-scenarios`         | List scenarios    |
| POST   | `/api/credit-scenarios/compare` | Compare scenarios |

### Scheme Intelligence

Base route:

```text
/api/schemes
```

| Method | Endpoint             | Purpose                |
| ------ | -------------------- | ---------------------- |
| POST   | `/api/schemes/match` | Match relevant schemes |
| GET    | `/api/schemes`       | List schemes           |

Personalised scheme recommendations require the appropriate consent.

Rate limit:

```text
20 requests / minute
```

### Fraud Intelligence

Base route:

```text
/api/fraud
```

| Method | Endpoint                  | Purpose                   |
| ------ | ------------------------- | ------------------------- |
| POST   | `/api/fraud/analyse-text` | Analyse suspicious text   |
| GET    | `/api/fraud/scans`        | List previous fraud scans |

Fraud analysis requires the `fraud_analysis` consent.

Rate limit:

```text
20 requests / minute
```

### AI Copilot

Base route:

```text
/api/copilot
```

| Method | Endpoint            | Purpose                             |
| ------ | ------------------- | ----------------------------------- |
| POST   | `/api/copilot/chat` | Conversational financial assistance |

Copilot requests are authenticated and rate-limited.

Rate limit:

```text
30 requests / minute
```

---

## AI & RAG Architecture

Finlytic IQ uses AI selectively instead of sending every financial operation directly to an LLM.

A simplified flow:

```text
User Request
     |
     v
Authentication
     |
     v
Consent Check
     |
     v
Relevant Backend Service
     |
     +---------------> Structured Financial Data
     |
     +---------------> PostgreSQL
     |
     +---------------> Vector Search
     |
     +---------------> Gemini
                           |
                           v
                    Contextual Response
```

For scheme intelligence:

```text
Scheme Documents
      |
      v
Document Chunks
      |
      v
Embeddings
      |
      v
pgvector
      |
      v
Similarity Search
      |
      v
Relevant Schemes
      |
      v
Explanation / Recommendation
```

This approach helps keep retrieval grounded in available scheme information instead of relying entirely on model-generated knowledge.

---

## Security & Privacy

Finlytic IQ handles sensitive financial information, so security is part of the architecture.

Implemented protections include:

* JWT authentication
* Password-protected account operations
* Consent-based access to sensitive features
* Per-user data access
* Rate limiting
* Sensitive log filtering
* Request IDs
* No API keys committed to Git
* AI observability without storing prompts/responses in logs

### Important

`.env` must remain local.

Never commit:

```text
.env
```

Never put API keys directly into:

```text
Python source code
TypeScript source code
README.md
Git commits
screenshots
GitHub Actions logs
```

---

## Evaluation

Finlytic IQ includes evaluation scripts for important AI-powered components.

### Fraud Evaluation

Final evaluation:

```text
Precision: 1.00
Recall:    0.83
FPR:       0.00

TP: 5
FP: 0
TN: 4
FN: 1
```

### Scheme Evaluation

Final evaluation:

```text
Precision: 1.00
Recall:    1.00

TP: 6
FP: 0
FN: 0
```

Run the evaluations from the backend:

```bash
cd backend

pytest tests/ -v

python -m evaluation.run_fraud_eval

python -m evaluation.run_scheme_eval
```

---

## Testing

Run backend tests:

```bash
cd backend
pytest tests/ -v
```

The project also includes frontend build validation through CI.

Gemini calls are mocked during CI testing, so CI does not require a live Gemini API key or consume Gemini API quota.

---

## CI/CD

GitHub Actions is configured through:

```text
.github/workflows/ci.yml
```

The CI pipeline validates:

* Backend tests
* PostgreSQL/pgvector integration
* Redis integration
* Mocked AI behaviour
* Frontend build

The CI workflow runs on pushes and pull requests.

---

## Development Workflow

The project uses a feature-branch workflow.

Stable production code:

```text
main
```

Development:

```text
feature/<feature-name>
```

Example:

```bash
git checkout main
git pull origin main

git checkout -b feature/new-feature
```

After development and testing:

```bash
git add .
git commit -m "Add new feature"
git push -u origin feature/new-feature
```

After verification, merge the feature into `main`.

---

## Roadmap

Current project progression:

* [x] Core financial backend
* [x] Authentication
* [x] Consent management
* [x] Financial health
* [x] Credit scenario simulation
* [x] Scheme intelligence
* [x] RAG/vector search foundation
* [x] Fraud intelligence
* [x] AI Copilot
* [x] Fraud evaluation
* [x] Scheme evaluation
* [x] Dockerization
* [x] GitHub Actions CI
* [x] Basic observability
* [ ] UI/UX polish
* [ ] Production-ready verified government scheme dataset
* [ ] Cloud deployment
* [ ] Production monitoring
* [ ] Final production demo

---

## Deployment

Deployment is planned after the documentation and local validation phase.

Before production deployment:

* Replace synthetic scheme data with verified official data.
* Configure production PostgreSQL.
* Configure production Redis.
* Generate a strong production JWT secret.
* Configure production Gemini credentials securely.
* Configure frontend/backend production URLs.
* Enable HTTPS.
* Configure production logging and monitoring.
* Review consent and privacy behaviour.
* Review rate limits.
* Run the complete test and evaluation suite.

---

## Disclaimer

Finlytic IQ is a software project for financial intelligence and decision-support experimentation.

AI-generated information should not be treated as professional financial, legal, tax, investment, or government-authoritative advice.

Users should verify important financial information with appropriate professionals and authoritative sources.

---

## Author

**Satyam Verma**

B.Tech Computer Science & Engineering

**Finlytic IQ — AI-powered financial intelligence platform.**
