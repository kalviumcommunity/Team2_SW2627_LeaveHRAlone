# LeaveHRAlone

Internal AI-powered HR assistant. Employees will eventually ask questions about leave, benefits, and other HR policies. Answers will come from the organization's own documents using RAG (retrieval-augmented generation), with citations and region-specific results.

This repository is the **initial project foundation**. RAG, authentication, vector search, and LLM integrations are not implemented yet.

## Stack

- Frontend: Next.js, TypeScript, Tailwind CSS
- Backend: Python, FastAPI
- AI / RAG: Python modules are stubbed for later work

## Repository layout

```text
.
├── frontend/                 Next.js app (UI)
├── backend/                  FastAPI app (API + future RAG)
├── .gitignore
└── README.md
```

### Frontend

| Path | Purpose |
| --- | --- |
| `frontend/src/app/` | App Router pages and layout |
| `frontend/src/components/` | UI pieces such as the chat placeholder |
| `frontend/src/lib/` | Shared frontend helpers (API URL) |
| `frontend/.env.example` | Frontend env template |

### Backend

| Path | Purpose |
| --- | --- |
| `backend/app/main.py` | FastAPI entry point, CORS |
| `backend/app/core/` | Settings loaded from environment variables |
| `backend/app/api/routes/` | HTTP endpoints (health check today) |
| `backend/app/rag/ingestion/` | Future: load HR documents |
| `backend/app/rag/processing/` | Future: clean and chunk documents |
| `backend/app/rag/embeddings/` | Future: embedding models |
| `backend/app/rag/retrieval/` | Future: vector search and region filters |
| `backend/app/rag/generation/` | Future: LLM answers |
| `backend/app/rag/citations/` | Future: source citations |
| `backend/app/rag/evaluation/` | Future: quality checks |
| `backend/data/documents/` | Local place for HR files (not committed) |
| `backend/data/processed/` | Local processed/chunked output (not committed) |
| `backend/.env.example` | Backend env template |

## Environment variables

Copy the templates. Do not commit real `.env` files or API keys.

### Backend (`backend/.env`)

| Variable | Example | Purpose |
| --- | --- | --- |
| `APP_NAME` | `LeaveHRAlone` | Service name in health responses |
| `APP_ENV` | `development` | Environment label |
| `API_HOST` | `0.0.0.0` | Bind address |
| `API_PORT` | `8000` | API port |
| `FRONTEND_ORIGIN` | `http://localhost:3000` | Allowed CORS origin |

Later (leave blank until needed): `OPENAI_API_KEY`, `EMBEDDING_MODEL`, `VECTOR_DB_URL`.

### Frontend (`frontend/.env.local`)

| Variable | Example | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL used by the browser |

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

On Windows PowerShell, use `Copy-Item` instead of `cp`.

## Run locally

Use two terminals. Python 3.11+ and Node.js 20+ are recommended.

### Backend

```bash
cd backend
python -m venv .venv

# Git Bash on Windows
source .venv/Scripts/activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: http://localhost:8000/health
- Docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000

The landing page shows a disabled chat placeholder and a simple API health indicator. It does not answer HR questions yet.

## Git for the team

If this folder is already a git repository:

```bash
git add .
git status
git commit -m "Add initial Next.js frontend and FastAPI backend foundation."
```

If you are starting git from scratch:

```bash
git init
git add .
git commit -m "Add initial Next.js frontend and FastAPI backend foundation."
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

Suggested first commit message:

```text
Add initial Next.js frontend and FastAPI backend foundation.
```

Keep secrets out of git. Real HR documents belong in `backend/data/documents/` locally and are ignored.
