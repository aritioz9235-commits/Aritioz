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

## Checks

```bash
npm test
npm run lint
```

## Repository

https://github.com/aritioz9235-commits/Aritioz
