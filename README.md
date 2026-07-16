# AI Reception Agent

An intelligent AI reception agent that handles visitor inquiries, checks business hours/availability, books appointments, and seamlessly escalates to human staff when needed.

## Architecture

```
CRM-system/
├── frontend/           # Next.js 14 (TypeScript) — deploys to Vercel
│   ├── app/            # App router pages & layout
│   ├── components/     # UI components (VoiceChatWidget, CallRing, ChatBubble)
│   ├── hooks/          # useVoiceAgent — state management & API calls
│   ├── lib/            # API client (configurable via NEXT_PUBLIC_API_URL)
│   └── types/          # TypeScript type definitions
├── backend/            # FastAPI + CrewAI (Python) — deploys to Render
│   ├── main.py         # API server with triage, booking, availability, follow-up endpoints
│   ├── requirements.txt
│   ├── Procfile        # Render start command
│   └── render.yaml     # Render blueprint
├── .env.example        # Required environment variables
└── .gitignore
```

## Features

- **Voice & Chat Interface** — visitors can speak or type their questions
- **Intent Triage** — classifies inquiries (hours, availability, booking, escalate)
- **Appointment Booking** — checks availability and confirms appointments
- **Human Escalation** — seamlessly transfers complex issues to staff
- **Configurable Backend URL** — set `NEXT_PUBLIC_API_URL` for any deployment

## Tech Stack

| Layer       | Technology                           |
|-------------|--------------------------------------|
| Frontend    | Next.js 14, TypeScript, Tailwind CSS |
| Backend     | FastAPI, CrewAI, Groq                |
| Database    | PostgreSQL (via SQLAlchemy)          |
| Calendar    | Google Calendar API                  |
| Deployment  | Vercel (frontend), Render (backend)  |

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/zainabasim785/CRM-system.git
cd CRM-system

# Backend
cd backend
python -m venv venv
venv\Scripts\activate     # Windows
pip install -r requirements.txt
cp ..\.env.example ..\.env   # Fill in your keys

# Frontend
cd ../frontend
npm install
```

### 2. Run Locally

**Backend** (terminal 1):
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

**Frontend** (terminal 2):
```bash
cd frontend
npm run dev
```

Visit `http://localhost:3000` — the widget connects to `http://localhost:8000`.

## Deployment

### Backend → Render (free tier)

1. Push the repo to GitHub
2. On [Render Dashboard](https://dashboard.render.com) → **New +** → **Web Service**
3. Connect your GitHub repo
4. Set:
   - **Name**: `ai-reception-agent-backend`
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
5. Add environment variables (see `.env.example`)
6. Click **Create Web Service**

### Frontend → Vercel

1. On [Vercel Dashboard](https://vercel.com) → **Add New** → **Project**
2. Import your GitHub repo
3. Set **Root Directory** to `frontend`
4. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = your Render backend URL (e.g. `https://ai-reception-agent-backend.onrender.com`)
5. Click **Deploy**

## Environment Variables

| Variable                     | Required | Description                              |
|------------------------------|----------|------------------------------------------|
| `GROQ_API_KEY`               | Yes      | Groq API key for LLM inference           |
| `GOOGLE_CALENDAR_CREDENTIALS`| Yes      | Google service-account JSON              |
| `DATABASE_URL`               | Yes      | PostgreSQL connection string             |
| `SECRET_KEY`                 | Yes      | JWT signing secret                       |
| `NEXT_PUBLIC_API_URL`        | Yes      | Backend URL (used by frontend)           |
| `CORS_ORIGINS`               | No       | Comma-separated allowed origins          |
| `LOG_LEVEL`                  | No       | Logging level (default: INFO)            |

---

Built with [Next.js](https://nextjs.org/), [FastAPI](https://fastapi.tiangolo.com/), [CrewAI](https://www.crewai.com/), and [Groq](https://groq.com/).