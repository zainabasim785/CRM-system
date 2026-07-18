# Frontend

Next.js 15 client for the FastAPI reception backend.

## Stack

- Next.js 15 + TypeScript
- Tailwind CSS + shadcn-style UI primitives
- Framer Motion
- Axios
- React Hook Form + Zod

## Setup

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000

Set `NEXT_PUBLIC_API_URL` to your backend (default `http://localhost:8000`).

## Pages

| Route | Uses |
|-------|------|
| `/` | Landing |
| `/login` | `POST /api/v1/auth/login` |
| `/register` | `POST /api/v1/auth/register` |
| `/chat` | `POST /api/v1/reception/message` (+ browser voice) |
| `/book` | Same reception endpoint via structured form → NL message |
| `/dashboard` | `GET /api/v1/auth/me`, calendar connect/status/disconnect |

No fake appointment lists or analytics — those APIs do not exist on the backend yet.
