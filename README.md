# LeaveHRAlone (PolicyPilot AI)

> **Enterprise AI-Powered HR Policy & Benefits Assistant**

[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](WORKFLOW.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](backend/)
[![Next.js 14+](https://img.shields.io/badge/Next.js-14+-black.svg)](frontend/)

**LeaveHRAlone** (PolicyPilot AI) is an enterprise AI assistant designed to give employees instant, accurate, source-grounded answers about company policies, leave rules, insurance benefits, remote work guidelines, and region-specific HR handbooks. 

By employing **Retrieval-Augmented Generation (RAG)** over approved HR documentation, LeaveHRAlone eliminates repetitive HR workloads while guaranteeing strict traceability, metadata-based region filtering, and zero tolerance for policy hallucinations.

---

## 📌 Executive Summary & Problem Statement

HR teams spend up to **40% of their time** answering repetitive employee questions already covered in internal handbooks:
- *"How many annual leaves do I get in India?"*
- *"Can I carry forward unused sick leave?"*
- *"Does our insurance policy cover dependents?"*
- *"What is the maternity leave entitlement for remote workers?"*

Traditional document searches force employees to navigate static PDFs, leading to slow response times, outdated policy usage, and employee frustration.

**LeaveHRAlone solves this by providing:**
1. **Instant Natural Language Answers**: Converts complex HR policies into plain-language responses.
2. **Strict Document Grounding**: Every answer is backed by verifiable document citations (file name, section, page, version).
3. **Region & Role Isolation**: Ensures employees only see policies applicable to their location, employment type, and role.
4. **Seamless HR Escalation**: Unanswered or low-confidence queries automatically trigger HR tickets with context.

---

## 🚀 Key Features

### 🏢 Employee Self-Service Interface
- **Natural Language Querying**: Multi-turn conversational interface for policy exploration.
- **Source Verification & Citations**: Direct links to document title, section header, page number, and policy version.
- **Context-Aware Follow-ups**: Maintains conversation history (e.g., asking *"Can I carry them forward?"* after discussing annual leaves).
- **Confidence Scoring & Safety**: Clear indication of answer confidence (High/Medium/Low) with refusal handling when policy info is absent.
- **HR Escalation Button**: One-click ticket creation for queries requiring human intervention.

### 🛠️ HR Administrator Portal
- **Document Management**: Upload PDF, DOCX, and TXT HR documents with rich metadata tagging (region, category, effective date, employee type).
- **Policy Version Control**: Manage policy lifecycles (v1.0 → v2.0) and deactivate outdated documents to prevent retrieval of expired rules.
- **Analytics & Insights**: Monitor question volume, top-searched topics, unanswerable queries, and employee feedback to identify documentation gaps.
- **Ticket Dashboard**: Manage and resolve escalated employee questions directly within the HR portal.

---

## 🏗️ System Architecture & RAG Pipeline

```text
┌────────────────────────┐      ┌────────────────────────┐
│   Employee Front-End   │      │   HR Admin Portal      │
│   (Next.js / React)    │      │  (Document Management) │
└───────────┬────────────┘      └───────────┬────────────┘
            │                               │
            ▼                               ▼
┌────────────────────────────────────────────────────────┐
│                  FastAPI Backend Gateway               │
│         (Auth, Metadata Filtering, Query Router)        │
└───────────┬───────────────────────────────┬────────────┘
            │                               │
            ▼                               ▼
┌────────────────────────┐      ┌────────────────────────┐
│ Qdrant Vector Database │      │  PostgreSQL Database   │
│  (Semantic Search &    │      │ (Users, Docs, Metadata,│
│  Chunk Metadata)       │      │  Tickets & Feedback)   │
└───────────┬────────────┘      └────────────────────────┘
            │
            ▼
┌────────────────────────┐
│  LLM Answer Generator  │
│  (Grounded Prompting)  │
└────────────────────────┘
```

### Document Processing Workflow
1. **Upload & Validation**: File type, size, and metadata validation (Region, Category, Effective Date).
2. **Text Extraction & Cleaning**: Format-agnostic text extraction from PDF/DOCX files.
3. **Semantic Chunking**: Context-preserving sentence and section splitting with metadata retention.
4. **Vector Embedding**: Dense vector generation stored in **Qdrant** alongside chunk metadata.

### Retrieval & Generation Workflow
1. **Metadata Filtering**: Filter vectors by `region`, `employee_type`, and `status = 'active'`.
2. **Semantic Search & Re-ranking**: Retrieve Top-$K$ relevant chunks and re-rank based on context relevancy.
3. **Grounded Generation**: LLM generates answers strictly constrained by retrieved context.
4. **Citation Extraction**: Formats precise source tags for frontend rendering.

---

## 💻 Technology Stack

| Domain | Technology | Purpose |
| --- | --- | --- |
| **Frontend** | React, Next.js 14, TypeScript, Tailwind CSS | Responsive, accessible UI for employees & HR admins |
| **Backend API** | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy | High-performance RESTful API endpoints |
| **Vector Database**| Qdrant | Fast vector indexing, hybrid search, metadata filtering |
| **Relational DB** | PostgreSQL | User management, document metadata, audit logs, tickets |
| **AI / RAG** | LangChain / LlamaIndex, OpenAI / Custom LLM | Contextual embedding & grounded answer generation |

---

## 📂 Repository Layout

```text
Team2_SW2627_LeaveHRAlone/
├── PRD.md                    # Product Requirements Document
├── README.md                 # Project Documentation & Architecture
├── WORKFLOW.md               # Team GitHub Strategy & Commit Conventions
├── contribution.md           # Duty roster & contribution log
├── docs/                     # Architecture & Data Dictionary docs
│   └── DATA_DICTIONARY.md    # Metadata schema reference
├── frontend/                 # Next.js Application
│   ├── src/
│   │   ├── app/              # App router pages & API routes
│   │   ├── components/       # UI components (Chat, Upload, Analytics)
│   │   └── lib/              # Frontend utilities
│   └── package.json
└── backend/                  # FastAPI Application
    ├── app/
    │   ├── api/              # HTTP Route handlers
    │   ├── core/             # Configuration & security
    │   ├── db/               # Database models & schemas
    │   └── rag/              # Ingestion, Chunking, Retrieval & LLM logic
    └── requirements.txt
```

---

## ⚙️ Quick Start & Local Setup

### Prerequisites
- **Python** 3.11 or higher
- **Node.js** 20 or higher
- **Docker** (Optional, for running Qdrant & PostgreSQL locally)

### 1. Clone Repository & Setup Environment

```bash
git clone https://github.com/kalviumcommunity/Team2_SW2627_LeaveHRAlone.git
cd Team2_SW2627_LeaveHRAlone
```

### 2. Backend Setup (FastAPI)

```bash
cd backend
python -m venv .venv

# On Windows (PowerShell / Git Bash)
source .venv/Scripts/activate  # or .venv\Scripts\Activate.ps1

# On macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Health Check: `http://localhost:8000/health`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

### 3. Frontend Setup (Next.js)

```bash
cd ../frontend
cp .env.example .env.local
npm install
npm run dev
```
- Web Application: `http://localhost:3000`

---

## 📊 Evaluation & Quality Benchmarks

To ensure zero policy hallucinations and reliable source citations, PolicyPilot AI is measured against strict benchmark metrics:

| Metric | Target MVP | Description |
| --- | --- | --- |
| **Citation Accuracy** | $\ge 90\%$ | Percentage of answers with 100% accurate page/section citations |
| **Grounded Answer Rate** | $\ge 90\%$ | Answers strictly backed by retrieved policy context |
| **Retrieval Recall@5** | $\ge 85\%$ | Target policy chunk presence within top-5 retrieved results |
| **Hallucination Rate** | $< 10\%$ | Zero tolerance for invented numbers, leave days, or eligibility rules |
| **Latency** | $< 8\text{ sec}$ | End-to-end RAG answer generation time |

---

## 🤝 Team Workflow & Guidelines

We follow strict team development practices defined in our [WORKFLOW.md](WORKFLOW.md):
- **Branch Naming**: `feature/[description]`, `fix/[description]`, `docs/[description]`
- **Commit Messages**: Conventional Commit standard (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`)
- **Code Reviews**: Every PR requires issue linkage, clear testing logs, and at least 1 approval before merge.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
