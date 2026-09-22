# Aritioz AI backend

FastAPI service exposing `GET /health`, `GET /api/models`, and `POST /api/chat`.
Gemini, NVIDIA/Nemotron, and local Ollama are selected through server-only
environment variables. In `auto` mode, temporary provider failures fall through
the configured order; explicit provider requests never silently switch.

## Local setup

From the project root:

```bash
sudo apt install python3-venv
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
# Edit .env and add only the provider keys/models you intend to use.
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
