# Deploying LeaveHRAlone to Vercel

This guide explains how to deploy the **LeaveHRAlone** application to **Vercel** step-by-step.

---

## Architecture Overview

LeaveHRAlone is composed of two primary components:
1. **Frontend (Next.js 16)**: Built with React 19, Tailwind CSS v4, and TypeScript. Designed for zero-config global deployment on Vercel's Edge/Serverless platform.
2. **Backend (FastAPI / Python 3.13)**: Hosts the RAG vector retrieval pipeline, authentication, and policy database. Can be deployed on **Render**, **Railway**, **Fly.io**, or **AWS/GCP/DigitalOcean**.

The frontend communicates with the backend via the `NEXT_PUBLIC_API_URL` environment variable.

---

## Step 1: Deploying the Frontend to Vercel

### Method A: Deploy via Vercel Web Dashboard (Recommended)

1. Push your repository to **GitHub**, **GitLab**, or **Bitbucket**.
2. Go to [vercel.com](https://vercel.com) and log into your account.
3. Click **"Add New..."** > **"Project"**.
4. Select and import the `Team2_SW2627_LeaveHRAlone` repository.
5. In the **Configure Project** screen:
   - **Project Name**: `leave-hr-alone` (or your preferred name)
   - **Framework Preset**: `Next.js` (automatically detected)
   - **Root Directory**: Click *Edit* and select `frontend` (or leave default root, as both `vercel.json` and root `package.json` are pre-configured to build `frontend`).
   - **Build Command**: `next build --webpack` (default configured in `frontend/package.json`)
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`
6. Expand **Environment Variables** and add:
   | Key | Value | Description |
   | :--- | :--- | :--- |
   | `NEXT_PUBLIC_API_URL` | `https://your-backend-api-url.com` | The public URL of your deployed FastAPI backend (e.g. on Render/Railway) |
7. Click **"Deploy"**.
8. Within 1–2 minutes, Vercel will complete the build and assign a production URL (e.g., `https://leave-hr-alone.vercel.app`).

---

### Method B: Deploy via Vercel CLI

If you have the Vercel CLI installed:

```bash
# 1. Install Vercel CLI globally (if not already installed)
npm install -g vercel

# 2. Login to your Vercel account
vercel login

# 3. Deploy from the repository root (or inside the frontend directory)
vercel

# 4. When prompted:
# - Set up and deploy? [Y]
# - Which scope? [Select your team or account]
# - Link to existing project? [N]
# - What's your project's name? [leave-hr-alone]
# - In which directory is your code located? [./frontend] (or ./)

# 5. Deploy to production
vercel --prod
```

---

## Step 2: Configure CORS on the Backend

When your Vercel deployment completes, add your Vercel production and preview URLs to the backend configuration.

In your backend `.env` (or cloud host environment variables):
```env
FRONTEND_ORIGIN=https://leave-hr-alone.vercel.app,http://localhost:3000
```

> **Note**: The backend `main.py` is pre-configured with `allow_origin_regex=r"https://.*\.vercel\.app"`, so all Vercel preview branch deployments will automatically work without CORS rejections.

---

## Step 3: Backend Deployment Options (Quick Reference)

To give your Vercel frontend a live API:

### Option 1: Render (Easiest & Free/Affordable)
1. Sign up at [render.com](https://render.com).
2. Create a new **Web Service** connected to your repository.
3. Configure:
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set Environment Variables:
   - `LLM_PROVIDER`: `gemini` (or `openai`, `mock`)
   - `GEMINI_API_KEY`: `<your-gemini-api-key>`
   - `JWT_SECRET_KEY`: `<random-secret-key>`
   - `FRONTEND_ORIGIN`: `https://your-vercel-domain.vercel.app`

### Option 2: Railway
1. Sign up at [railway.app](https://railway.app).
2. Create a new project and connect the repo.
3. Add a PostgreSQL database and a Python service pointing to `backend`.
4. Copy the public domain URL and paste it into Vercel as `NEXT_PUBLIC_API_URL`.

---

## Pre-deployment Checklist

- [x] All references to `PolicyPilot` updated to `LeaveHRAlone`.
- [x] Comprehensive `.gitignore` ignores `.env`, virtualenvs, SQLite DBs (`*.db`), vector storage (`qdrant_storage/`), and Next.js build artifacts (`.next/`).
- [x] Root `package.json` and `vercel.json` allow seamless deployment directly from the root repository or from `frontend/`.
- [x] Next.js build verified (`next build --webpack` compiles with zero errors).
- [x] Backend CORS supports both custom domains and `*.vercel.app` preview branches.

