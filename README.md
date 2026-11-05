| Component | Technology | Purpose |
|---|---|---|
| **Frontend** | React 19, Next.js 16, TypeScript, Tailwind CSS | Responsive, accessible UI recreating the Buddy aesthetic |
| **Backend API** | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2 | Asynchronous RESTful API endpoints |
| **Relational Database** | PostgreSQL 16 + Alembic Migrations | Persistent user, role, document metadata, ticket, and feedback storage |
| **Vector Database** | Qdrant (Server or In-Memory local fallback) | Hybrid vector search with metadata filtering |
| **Embeddings & LLM** | Provider-Agnostic Adapter (Gemini / OpenAI / Anthropic / Mock) | Dense embedding and grounded generation without vendor lock-in |
| **Background Processing**| Celery + Redis | Asynchronous document ingestion and chunking pipeline |
| **Testing & Eval** | Pytest, AsyncIO, Custom RAG Benchmark Harness | 100% test coverage and evaluation metrics |
| **Containerization** | Docker, Docker Compose | Reproducible multi-container production deployment |

---

## ⚙️ Quick Start Guide

### Option A: 1-Command Docker Compose (Recommended)

To run the complete production stack (PostgreSQL, Qdrant, Redis, Backend, Worker, Frontend) in Docker:

```bash
# 1. Clone repository
git clone https://github.com/kalviumcommunity/Team2_SW2627_LeaveHRAlone.git
cd Team2_SW2627_LeaveHRAlone

# 2. Copy environment configuration
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# 3. Launch all containers
docker compose up --build
```

- **Frontend App**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Qdrant Dashboard**: `http://localhost:6333/dashboard`

---

### Option B: Local Step-by-Step Development Setup

#### 1. Prerequisites
- **Python** 3.11+
- **Node.js** 20+
- **Git**

#### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On macOS / Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env

# Run database migrations
alembic upgrade head

# Seed demo users and policy documents
python scripts/seed.py

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API health check: `http://localhost:8000/api/health`
- OpenAPI Documentation: `http://localhost:8000/docs`

#### 3. Frontend Setup

In a new terminal:

```bash
cd frontend

# Setup environment variables
cp .env.example .env.local

# Install dependencies
npm install

# Run Next.js development server
npm run dev
```

- Web Application: `http://localhost:3000`

---

## 🔑 Pre-Configured Demo Accounts

The database seed script (`python backend/scripts/seed.py`) pre-configures standard test accounts:

| Role | Email | Password | Region | Department |
|---|---|---|---|---|
| **Employee (India)** | `employee.india@example.com` | `password123` | India | Engineering |
| **Employee (US)** | `employee.us@example.com` | `password123` | US | Product |
| **HR Admin** | `hr.admin@example.com` | `password123` | India | Human Resources |
| **Super Admin** | `super.admin@example.com` | `password123` | Global | Executive |

---

## 📄 Real Document Ingestion & Document Lifecycle (Upload, Update, Delete)

LeaveHRAlone AI supports end-to-end enterprise document lifecycle management with zero dependency on pre-seeded data:

### 1. Uploading Real Documents
- HR Admins navigate to **HR Command Center ➔ Documents ➔ + Upload Real Policy**.
- Supported formats: **PDF** (with embedded tables and OCR fallback), **DOCX**, **TXT**, and **Markdown** (up to 25 MB).
- Set title, category, target region (`India`, `US`, `UK`, `Singapore`, `Germany`, `Australia`, or `Global`), employee type (`All`, `Full-Time`, `Contractor`, `Intern`), version, effective date, and expiration date.
- Real-time processing status indicator transitions: `QUEUED` ➔ `PROCESSING` ➔ `READY` (or `FAILED` with error details).

### 2. Updating Document Metadata (✏️ Edit)
- Click **✏️ Edit** on any document row in the HR Command Center.
- Update policy title, category, jurisdiction region, employee entitlement type, version, or effective/expiration dates.
- Changes are instantly synchronized into PostgreSQL and update metadata payload filters in Qdrant in real-time.

### 3. Deleting Documents (🗑️ Delete)
- Click **🗑️** to permanently delete a policy document.
- Performs cascading deletion:
  1. Deletes extracted chunk embeddings and points from Qdrant vector database.
  2. Deletes relational chunk records from PostgreSQL.
  3. Deletes the physical file on disk.
  4. Records an audit log event (`DOCUMENT_DELETE`).

### 4. Zero-Seed Mode (Fresh Database Deployment)
- On a completely fresh database without running `seed.py`, LeaveHRAlone AI automatically provisions the initial administrative credentials on startup:
  - **Email**: `hr.admin@example.com`
  - **Password**: `password123`
- Admins can immediately log in, upload their own company handbooks, and employees will receive answers strictly grounded in the uploaded files.
- If no documents have been uploaded yet for a given query/region, the assistant returns an explicit low-confidence refusal and prompts the employee to escalate to HR with 1 click.

---

## 📚 Seed Policy Corpus (Optional Demo Mode)

For automated test suites and demonstration, the database can also be optionally pre-seeded (`python backend/scripts/seed.py`):

1. `India_Leave_Policy_2026_v2.0.txt` (**Active**): 24 annual leaves, 12 sick leaves, 26 weeks maternity.
2. `India_Leave_Policy_2025_v1.0.txt` (**Archived / Inactive**): Older v1 rules demonstrating version prioritization.
3. `India_Benefits_and_Insurance_2026.txt` (**Active**): Group Medical Coverage (GMC), outpatient, dependent parents.
4. `US_Employee_Handbook_2026_v1.0.txt` (**Active**): PTO guidelines, 401(k) matching, FMLA rules.
5. `US_Remote_Work_Policy_Expired_2024.txt` (**Expired / Inactive**): Expired policy demonstrating date filtering.
6. `Global_Code_of_Conduct_2026.txt` (**Active Global**): Anti-harassment, ethics, reporting lines.

---
