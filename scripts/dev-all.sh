#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

if [[ ! -x .venv/bin/python ]]; then
  echo "Missing Python environment at .venv. Create it with: python3 -m venv .venv" >&2
  exit 1
fi

if ! .venv/bin/python -c 'import fastapi, uvicorn' >/dev/null 2>&1; then
  echo "Backend dependencies are missing. Install them with: python3 -m pip install --target .venv/lib/python3.12/site-packages -r backend/requirements.txt" >&2
  exit 1
fi

# Reload the API in development so newly-added routes (such as authentication)
# are served without leaving an old FastAPI process running.
PYTHONPATH=backend .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend &
backend_pid=$!

for attempt in {1..30}; do
  if curl --silent --fail --max-time 1 http://127.0.0.1:8000/health >/dev/null; then break; fi
  if ! kill -0 "$backend_pid" 2>/dev/null; then
    echo "Backend exited before becoming ready." >&2
    wait "$backend_pid"
    exit 1
  fi
  sleep 1
done
if ! curl --silent --fail --max-time 1 http://127.0.0.1:8000/health >/dev/null; then
  echo "Backend did not become ready on http://127.0.0.1:8000." >&2
  exit 1
fi

cleanup() {
  kill "$backend_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

exec npm run dev:frontend
