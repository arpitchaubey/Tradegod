# 🚀 TRADE GOD — Production Deployment Guide

This guide covers deploying the **TRADE GOD** AI Trading Engine (FastAPI Backend + Live Telegram Bot + Next.js Frontend).

---

## 🏗️ Architecture Overview
- **Backend & Telegram Bot**: Deployed on **Render.com** or **Railway.app** (Python 3.11 web service).
- **Frontend**: Deployed on **Vercel.com** (Next.js 15 App Router).

---

## Step 1: Deploy Backend & Telegram Bot (Render.com)

1. Go to [Render Dashboard](https://dashboard.render.com/) and sign in with your GitHub account.
2. Click **New +** → **Web Service**.
3. Select your GitHub repository: `arpitchaubey/Tradegod`.
4. Configure the Web Service settings:
   - **Name**: `tradegod-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Scroll to **Environment Variables** and add the following keys from your `.env`:
   - `TELEGRAM_BOT_TOKEN`: `8804382779:AAHISLzIbffQcJfRJG7oYaO_FtY6rtFVdZY`
   - `TELEGRAM_CHAT_ID`: `1432053067`
   - `TWELVE_DATA_API_KEY`: `f7c712ef92e24e41b92e8cd855731f39`
   - `OPENAI_API_KEY`: `sk-proj-...`
   - `GEMINI_API_KEY`: `AQ.Ab8...`
   - `DEFAULT_DATA_PROVIDER`: `twelvedata`
   - `DATABASE_URL`: `sqlite+aiosqlite:///./tradegod.db`
   - `ALLOWED_ORIGINS`: `https://frontend-phi-snowy-59.vercel.app,https://tradegod.vercel.app,http://localhost:3000`
6. Click **Create Web Service**.
7. Once deployed, Render will provide your live Backend URL:
   `https://tradegod-backend.onrender.com`

---

## Step 2: Deploy Frontend Dashboard (Vercel.com)

1. Go to [Vercel Dashboard](https://vercel.com/new) and log in with GitHub.
2. Import repository `arpitchaubey/Tradegod`.
3. Configure Project:
   - **Framework Preset**: Next.js
   - **Root Directory**: Select `frontend`
4. Add Environment Variable:
   - `NEXT_PUBLIC_API_BASE`: `https://tradegod-backend.onrender.com` (Your Render backend URL)
5. Click **Deploy**.
6. Vercel will build and launch your production dashboard URL:
   `https://tradegod.vercel.app`

---

## Step 3: Verify Telegram Live Bot
Once the Render backend is live, send `/status` or `/help` in Telegram chat to verify live responses.
