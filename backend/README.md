# Aritioz AI backend

FastAPI service exposing `GET /health`, `GET /api/models`, and `POST /api/chat`.
Gemini, NVIDIA/Nemotron, and local Ollama are selected through server-only
environment variables. In `auto` mode, temporary provider failures fall through
the configured order; explicit provider requests never silently switch.

The Work workspace can read and save existing text files and run the fixed
`npm test`, lint, TypeScript, and build commands when `WORKSPACE_ROOT` points to
a local project and `APP_ENV=development`. It stays disabled in production and
when no workspace root is configured. `.git`, dependency/build folders, hidden
files, and `.env*` files are excluded. Saves require the user to press Save;
commands are selected and launched explicitly from the workspace UI. For local
frontend/backend development, set `NEXT_PUBLIC_AI_BACKEND_URL=http://127.0.0.1:8000`,
`ALLOWED_ORIGINS=http://localhost:3000`, `APP_ENV=development`, and
`WORKSPACE_ROOT=/absolute/path/to/project` in the root `.env` before starting
the frontend and backend.

## Local setup

From the project root:

```bash
sudo apt install python3-venv
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
# For local Work mode, set APP_ENV=development and WORKSPACE_ROOT to the project directory.
# Add only the provider keys/models you intend to use.
PYTHONPATH=backend uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The backend starts even if hosted-provider keys are absent. Ollama is only
reported available when `/api/tags` returns an installed model. To run the
frontend separately, set `NEXT_PUBLIC_AI_BACKEND_URL=http://127.0.0.1:8000`
before building it and include the frontend origin in `ALLOWED_ORIGINS`.

## Verify

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/models
curl -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Explain AI agents simply","provider":"auto"}'
PYTHONPATH=backend pytest backend/tests -q
```

Without valid keys or a running Ollama model, `/api/chat` correctly returns a
sanitized `503` response.

## Persistence, authentication, and migrations

The optional persistence layer uses SQLAlchemy async with Supabase PostgreSQL.
Set `DATABASE_URL`, `SUPABASE_URL`, and either `SUPABASE_JWT_SECRET` (HS256
projects) or a Supabase URL that exposes JWKS. The service never sends
`SUPABASE_SERVICE_ROLE_KEY` to the browser. Redis, storage, and embeddings are
optional in local development and fail closed for protected operations.

From `backend/`, with the backend virtual environment active:

```bash
alembic upgrade head
alembic current
alembic history
```

Generate future migrations with `alembic revision -m "describe the change"`.
The migration enables `pgvector` and creates users, organizations, memberships,
workspaces, conversations, messages, files, document chunks, usage logs, and
subscription-ready tables. Persistent chat is available at
`POST /api/conversations/{conversation_id}/chat` with a Supabase bearer token;
all conversation, file, and vector queries enforce organization/workspace
membership on the backend.

## VPS deployment

On Ubuntu/Debian, replace `YOUR_REPOSITORY_URL` and `YOUR_DOMAIN` before
running the relevant commands. Keep `.env` off Git and never paste keys into
Nginx or frontend configuration.

```bash
sudo apt update
sudo apt install -y git nginx python3-venv
# Install Node.js 22.13 or newer using your approved Node.js distribution.
node --version
npm --version
sudo useradd --system --home /opt/aritioz --shell /usr/sbin/nologin aritioz
sudo git clone YOUR_REPOSITORY_URL /opt/aritioz
sudo chown -R aritioz:aritioz /opt/aritioz
sudo -u aritioz python3 -m venv /opt/aritioz/.venv
sudo -u aritioz /opt/aritioz/.venv/bin/pip install --requirement /opt/aritioz/backend/requirements.txt
sudo -u aritioz npm --prefix /opt/aritioz ci
sudo -u aritioz npm --prefix /opt/aritioz run build:vps
sudo -u aritioz cp /opt/aritioz/.env.example /opt/aritioz/.env
sudo chmod 640 /opt/aritioz/.env
sudo chown aritioz:aritioz /opt/aritioz/.env
sudoedit /opt/aritioz/.env
cd /opt/aritioz
sudo cp backend/deploy/aritioz-api.service /etc/systemd/system/
sudo cp backend/deploy/aritioz-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now aritioz-api aritioz-web
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:3000/
sudo cp backend/deploy/nginx-aritioz.conf /etc/nginx/sites-available/aritioz
sudoedit /etc/nginx/sites-available/aritioz
sudo ln -s /etc/nginx/sites-available/aritioz /etc/nginx/sites-enabled/aritioz
sudo nginx -t && sudo systemctl reload nginx
sudo systemctl status --no-pager aritioz-api
sudo systemctl status --no-pager aritioz-web
```

Run the copy commands from `/opt/aritioz`, or use absolute source paths. The
service binds to loopback because Nginx is the public entry point. Proxy headers
remain disabled; Nginx is used only for routing and TLS termination.

### Domain and HTTPS

Do not install the TLS template until a real DNS record and certificate exist.
After DNS points at the VPS, either obtain a certificate using your chosen ACME
client or install an existing certificate. Then copy
`backend/deploy/nginx-aritioz-tls.conf.example`, replace all three placeholders
(`YOUR_DOMAIN`, `CERTIFICATE_FULLCHAIN_PATH`, and
`CERTIFICATE_PRIVATE_KEY_PATH`), and validate before reload:

```bash
sudo cp /opt/aritioz/backend/deploy/nginx-aritioz-tls.conf.example /etc/nginx/sites-available/aritioz
sudoedit /etc/nginx/sites-available/aritioz
sudo nginx -t
sudo systemctl reload nginx
curl --fail https://YOUR_DOMAIN/health
```

The frontend deployment must serve the same origin or set
`NEXT_PUBLIC_AI_BACKEND_URL=https://YOUR_DOMAIN` at build time. Set
`ALLOWED_ORIGINS=https://YOUR_DOMAIN` in `/opt/aritioz/.env` when frontend and
API origins differ.
