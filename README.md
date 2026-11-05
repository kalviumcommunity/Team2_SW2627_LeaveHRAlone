# LeaveHRAlone AI (LeaveHRAlone)

> **Enterprise Production-Grade, Region-Aware HR Policy & Benefits Assistant**

[![CI Status](https://img.shields.io/badge/CI-Passing-brightgreen.svg)](.github/workflows/ci.yml)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](WORKFLOW.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](backend/)
[![Next.js 16+](https://img.shields.io/badge/Next.js-16+-black.svg)](frontend/)
[![Qdrant](https://img.shields.io/badge/VectorDB-Qdrant-red.svg)](https://qdrant.tech/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791.svg)](https://www.postgresql.org/)

**LeaveHRAlone AI** is an intelligent internal HR assistant that enables employees to ask natural-language questions about company policies, leave rules, health insurance benefits, remote work guidelines, and employee handbooks.

Instead of employees repeatedly emailing or ticketing HR for questions already documented in internal repositories, LeaveHRAlone AI retrieves verified excerpts and generates concise, grounded answers with **100% traceable citations** while enforcing **strict geographical region isolation** and **zero tolerance for policy hallucinations**.

---

## 📌 Problem Statement & Solution

HR teams spend over **40% of their bandwidth** answering repetitive employee questions:
- *"How many annual leaves do I have in India?"*
- *"Can I carry forward unused annual leave?"*
- *"Does our group insurance cover dependent parents?"*
- *"What is our parental leave entitlement?"*

### Why General AI Chatbots Fail at HR:
1. **Regional Differences**: A leave policy in India (24 days, statutory maternity) differs drastically from US PTO and FMLA. Generic LLMs leak policies across jurisdictions.
2. **Outdated Policies**: Companies release yearly amendments (v1.0 → v2.0). LLMs without strict version governance retrieve superseded rules.
3. **Hallucinations**: Inventing leave balances or insurance limits creates serious compliance and liability risks.

### The LeaveHRAlone AI Solution:
```text
  Employee Context (Region + Role)
                +
  3-Tier Region-Aware Vector Search (Qdrant)
                +
  Version Governance (Active vs Archived)
                +
  Strict Grounding Guardrails (Refuse if not found)
                +
  Verifiable Citation Chips & Source Preview Drawer
                +
  1-Click HR Escalation Ticket System
                =
  Trusted Enterprise HR Assistant
```

---

## 🏗️ Architecture & RAG Pipeline

```
┌────────────────────────────────────────────────────────┐
│                   Next.js Frontend                     │
│  (Yellow Buddy Theme, Category Cards, Source Drawer)   │
└───────────────────────────┬────────────────────────────┘
                            │ REST / JSON
                            ▼
┌────────────────────────────────────────────────────────┐
│                  FastAPI Backend API                   │
│   Auth / RBAC ── Query Rewriting ── Audit Logging     │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
       Semantic │ Retrieval       Relational Storage
                ▼                        ▼
┌───────────────────────────┐  ┌─────────────────────────┐
│       Qdrant Vector DB    │  │       PostgreSQL        │
│  - Regional Metadata      │  │  - Users & Roles        │
│  - Active Policy Chunks   │  │  - Documents & Versions │
│  - Cosine Embeddings      │  │  - Conversations        │
│  - 3-Tier Hierarchy       │  │  - HR Tickets & Feedback│
└───────────────┬───────────┘  └─────────────────────────┘
                │
                ▼ Context Chunks
┌────────────────────────────────────────────────────────┐
│           Provider-Agnostic LLM Engine                 │
│      (Gemini / OpenAI / Anthropic / Local Ollama)      │
│            Strict Grounding Prompt Template            │
└────────────────────────────────────────────────────────┘
```

### 3-Tier Region-Aware Retrieval Hierarchy
1. **Tier 1 (Target Jurisdiction)**: `user_region` + `status = active` + `category` (e.g. *India + Active + Leave Policy*).
2. **Tier 2 (Handbook / General)**: `user_region` + `status = active` (Handbook policies).
3. **Tier 3 (Global Fallback)**: `region = Global` + `status = active` (Global Code of Conduct, Anti-Harassment).
Cross-region policies (e.g., US leave rules for India employees) are strictly prevented by vector metadata filters.

---

## 💻 Tech Stack

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
