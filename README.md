# Aritioz

A next-generation AI ecosystem for e-commerce, leveraging autonomous agents,
smart B2B/B2C sourcing, and intelligent workflow automation to scale global
digital retail.

This repository contains the Aritioz AI workspace website built with React,
Vite, and Vinext, plus an optional Python backend under `backend/`.

## Getting started

Requirements: Node.js 22.13 or newer.

```bash
npm install
npm run dev
```

`npm run dev` starts both the frontend and the local FastAPI backend. The
backend dependencies must be installed in `.venv` first:

```bash
python3 -m pip install --target .venv/lib/python3.12/site-packages -r backend/requirements.txt
```

For the backend, copy `backend/.env.example` to `backend/.env` and fill in
local credentials. Never commit real secrets or API keys.

### Email/password authentication

The login and registration dialogs use the backend's JWT endpoints and the
`users` table. Set a PostgreSQL `DATABASE_URL` and a random `JWT_SECRET` in
`backend/.env`, then apply the migrations before starting the backend:

```bash
cd backend
../.venv/bin/alembic upgrade head
```

Generate the JWT secret with `openssl rand -hex 32`. It must remain server-side;
do not add it to a `NEXT_PUBLIC_` variable. New accounts are stored with a
PBKDF2 password hash and receive a seven-day bearer token by default.

## Checks

```bash
npm test
npm run lint
```

## Repository

https://github.com/aritioz9235-commits/Aritioz
