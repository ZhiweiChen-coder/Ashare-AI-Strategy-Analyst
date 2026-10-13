# Oracle VM Backend Deployment

This directory contains the backend-only deployment files for Oracle Cloud.

## Topology

- Oracle VM runs FastAPI only
- Vercel runs Next.js frontend
- Cloudflare points public domains to Vercel
- Oracle is used as the API origin

Recommended DNS layout:

- `openashare.com` -> Vercel
- `www.openashare.com` -> Vercel
- `api.openashare.com` -> Oracle VM public IP

## Files

- `.env.backend.example`: runtime variables for the backend
- `openashare-backend.service`: systemd unit for FastAPI
- `openashare-nginx.conf`: Nginx reverse proxy for the backend

`openashare-frontend.service` is kept only as a reference artifact and is not part of the recommended deployment path.

## Backend environment

Copy the example into `/opt/openashare/backend/.env` and fill in real values:

```env
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-flash
SEC_USER_AGENT="OpenAshare research contact@example.com"
FINNHUB_API_KEY=

DATA_COUNT=1250
MONITOR_DB_PATH=/opt/openashare/backend/data/monitor.db

NEWS_TRACKING_ENABLED=true
FUND_FLOW_TRACKING_ENABLED=true
WEB_SEARCH_ENABLED=true

MONITOR_ENABLED=false
MONITOR_INTERVAL_SECONDS=300
ALERT_MIN_PRIORITY=3

API_HOST=127.0.0.1
API_PORT=8000
API_WORKERS=1
OPENASHARE_PUBLIC_BETA=true

CORS_ALLOWED_ORIGINS=https://openashare.com,https://www.openashare.com,https://your-project.vercel.app
```

## Installation

1. Install dependencies on a host with Python 3.12 (the current backend was validated with Python 3.12):

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip build-essential nginx certbot python3-certbot-nginx
```

2. Clone the repository:

```bash
sudo mkdir -p /opt/openashare
sudo chown -R ubuntu:ubuntu /opt/openashare
cd /opt/openashare
git clone <your-repo-url> backend
cd backend
```

3. Install backend dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements_api.txt
```

4. Configure `.env`:

```bash
cp deploy/oracle/.env.backend.example .env
nano .env
```

5. Start the backend:

```bash
chmod +x scripts/run_api_prod.sh
./scripts/run_api_prod.sh
```

6. Install the systemd unit:

```bash
sudo cp deploy/oracle/openashare-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable openashare-backend
sudo systemctl restart openashare-backend
sudo systemctl status openashare-backend
```

7. Install Nginx:

```bash
# Replace api.openashare.com in the config if your API uses another domain.
sudo certbot certonly --nginx -d api.openashare.com
sudo cp deploy/oracle/openashare-nginx.conf /etc/nginx/conf.d/openashare.conf
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
```

## Verification

Use the health endpoint to verify the source server:

```bash
curl http://127.0.0.1:8000/healthz
curl https://api.openashare.com/healthz
```

Expected response:

```json
{"status":"ok"}
```

## Upgrading an existing VM

Connect using your existing Oracle VM hostname and SSH key. Ubuntu images use `ubuntu`; Oracle Linux images typically use `opc`. Substitute your known values; no host or private key is stored in this repository:

```bash
ssh -i <path-to-oracle-key> <vm-user>@<oracle-host>
```

On the VM, inspect the current checkout before changing anything:

```bash
cd /opt/openashare/backend
git status --short
git rev-parse HEAD
./.venv/bin/python --version
sudo systemctl status openashare-backend --no-pager
sudo nginx -t
curl -fsS http://127.0.0.1:8000/healthz
```

Review remote changes rather than overwriting them. Record the current revision and retain a protected backup of the runtime `.env`, persistent `data/`, systemd unit and Nginx configuration. Use the reviewed release commit once it is available on the remote repository; do not deploy a revision that omits new untracked source files.

Then update the existing checkout and environment:

```bash
git fetch origin
git checkout <reviewed-release-commit>
./.venv/bin/python -m pip install -r requirements_api.txt
./.venv/bin/python -m pytest tests/test_api_app.py tests/test_research_availability.py -q
chmod +x scripts/run_api_prod.sh
```

Edit the existing `.env` in place. Keep actual credentials and `MONITOR_DB_PATH`; do not copy the example over an existing runtime file. Ensure `SUPABASE_REQUIRE_AUTH=true`, `OPENASHARE_PUBLIC_BETA=true`, loopback binding, the current model identifier and quoted identifying SEC header are configured. The real contact address remains only in the runtime file.

Apply the reviewed service and proxy configuration:

```bash
sudo cp deploy/oracle/openashare-backend.service /etc/systemd/system/
sudo cp deploy/oracle/openashare-nginx.conf /etc/nginx/conf.d/openashare.conf
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl restart openashare-backend
sudo systemctl reload nginx
sudo systemctl status openashare-backend --no-pager
curl -fsS http://127.0.0.1:8000/healthz
curl -fsS http://127.0.0.1:8000/api/agent/capabilities
curl -fsS https://api.openashare.com/healthz
curl -fsS https://api.openashare.com/api/agent/capabilities
```

The capability response must show `quick_available=true`, `deep_available=false` and `deep_unavailable_reason="public_beta_suspended"`. This metadata route is intentionally public. Private routes and the API schema remain protected; an unauthenticated request should return 401:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' https://api.openashare.com/openapi.json
```

On the protected frontend staging build, sign in and verify a Deep request returns 503 before any credit reservation or model request, while one explicitly bounded Quick research request streams and saves normally. Do not place an access token in shell history or in documentation. Verify English/Chinese notices, watchlist persistence and cancellation. Restore the previous code and service configuration if checks fail, preserving runtime credentials and persistent data.

### Deep research during the public beta

Deep research is temporarily unavailable in this beta release. The restriction applies to the UI, hosted Next routes and direct authenticated Oracle requests. It does not require a database migration and does not delete existing Deep reports. Local development without hosted auth or `OPENASHARE_PUBLIC_BETA=true` retains Deep.

The Vercel proxy is now configured for Quick's 180-second backend deadline with a 300-second platform limit. Apex/www browsers currently call Oracle directly, so re-enabling Deep also requires Oracle verification rather than relying only on the Vercel plan. A future reviewed release can restore Deep after confirming the 540-second workflow, proxy/streaming limits, cancellation and an agreed spending allowance. No paid trial or production deployment is performed by these checks unless separately authorized.

## Production gates

- Set `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, and `SUPABASE_REQUIRE_AUTH=true`. When enabled, every `/api/*` request except `/health` and `/healthz` requires a valid Supabase bearer token.
- Keep `API_HOST=127.0.0.1`; do not expose Uvicorn port `8000` in the Oracle security list. Open only `80` for certificate issuance and `443` for the public API.
- Nginx adds a coarse IP rate limit; the backend applies a second per-user limit through `CLOUD_RATE_LIMIT_*`.
- The cloud API rejects `PUT /api/settings`; model credentials remain server-owned. Local development without Supabase keeps the local settings flow.
- Run `chmod +x scripts/run_api_prod.sh` after cloning, or store the executable bit in Git, before enabling the systemd service.
- Install the current `requirements_api.txt` in the backend environment; updating the frontend alone does not update research tools.
- Apply and validate the Nginx configuration. Its 600-second idle timeout supports quiet stages within the 540-second Deep research deadline.
- Set `OPENASHARE_PUBLIC_BETA=true`. Hosted authentication also suspends Deep by default; the API rejects it before credit reservation. `GET /api/agent/capabilities` exposes only global availability metadata.
- Complete the coordinated release checklist in [deployment-readiness.md](../../docs/deployment-readiness.md) before promoting the frontend.
