#!/usr/bin/env bash
#
# TripGraph one-shot droplet deploy (Ubuntu 22.04/24.04, demo-over-IP).
#
# Serves the built frontend AND proxies /api + /health to the backend through
# nginx on port 80 — so the browser sees a single origin (http://DROPLET_IP)
# and the backend's localhost-only CORS never gets in the way.
#
# Usage (run as root on the droplet):
#     ./deploy.sh <DROPLET_PUBLIC_IP>
#
# Re-running is safe: it pulls latest code, rebuilds, and restarts services.
#
set -euo pipefail

PUBLIC_HOST="${1:-}"
if [[ -z "$PUBLIC_HOST" ]]; then
  echo "ERROR: pass the droplet's public IP, e.g.  ./deploy.sh 159.89.1.2"
  exit 1
fi

APP_DIR="/opt/tripgraph"
REPO="https://github.com/uzzidamn/TripGraph.git"
BRANCH="integrations_v2"
BACKEND_PORT="8000"   # internal only; nginx is the public face on :80

echo "==> [1/7] Installing system packages (python, node 20, nginx, git)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3-venv python3-pip nginx git curl ufw
# Node 20 from NodeSource (Ubuntu's apt node is too old for Vite)
if ! command -v node >/dev/null 2>&1 || [[ "$(node -v | cut -dv -f2 | cut -d. -f1)" -lt 18 ]]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi

echo "==> [2/7] Fetching code ($BRANCH) into $APP_DIR"
if [[ -d "$APP_DIR/.git" ]]; then
  git -C "$APP_DIR" fetch origin "$BRANCH"
  git -C "$APP_DIR" checkout "$BRANCH"
  git -C "$APP_DIR" reset --hard "origin/$BRANCH"
else
  git clone --branch "$BRANCH" "$REPO" "$APP_DIR"
fi

echo "==> [3/7] Checking for backend secrets (.env)"
if [[ ! -f "$APP_DIR/.env" ]]; then
  cat <<EOF

  ⛔ $APP_DIR/.env is missing — it holds your API keys and is NOT in git.
     From your LAPTOP, copy your local .env up to the droplet, then re-run:

         scp -i ~/.ssh/id_ed25519_do "/path/to/Project/.env" root@$PUBLIC_HOST:$APP_DIR/.env

EOF
  exit 1
fi

echo "==> [4/7] Backend: virtualenv + dependencies"
cd "$APP_DIR"
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip -q
./.venv/bin/pip install -q -r backend/requirements.txt

echo "==> [5/7] Frontend: build static bundle pointed at http://$PUBLIC_HOST"
# Pull the client Google Maps key out of the root .env so the build can embed it.
GMAPS_KEY="$(grep -E '^VITE_GOOGLE_MAPS_API_KEY=' "$APP_DIR/.env" | tail -1 | cut -d= -f2- || true)"
cat > "$APP_DIR/frontend/.env" <<EOF
VITE_API_URL=http://$PUBLIC_HOST
VITE_GOOGLE_MAPS_API_KEY=$GMAPS_KEY
EOF
cd "$APP_DIR/frontend"
npm install
npm run build   # outputs to frontend/dist

echo "==> [6/7] systemd service for the backend (uvicorn on 127.0.0.1:$BACKEND_PORT)"
cat > /etc/systemd/system/tripgraph-backend.service <<EOF
[Unit]
Description=TripGraph FastAPI backend
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port $BACKEND_PORT
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable tripgraph-backend
systemctl restart tripgraph-backend

echo "==> [7/7] nginx: serve frontend + proxy /api and /health to the backend"
cat > /etc/nginx/sites-available/tripgraph <<EOF
server {
    listen 80 default_server;
    server_name _;

    root $APP_DIR/frontend/dist;
    index index.html;

    # SPA: unknown paths fall back to index.html
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API + health → uvicorn
    location /api/ {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_read_timeout 120s;
    }
    location /health {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
    }
}
EOF
ln -sf /etc/nginx/sites-available/tripgraph /etc/nginx/sites-enabled/tripgraph
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

echo "==> Firewall: allow SSH + HTTP"
ufw allow OpenSSH >/dev/null 2>&1 || true
ufw allow 80/tcp  >/dev/null 2>&1 || true
yes | ufw enable  >/dev/null 2>&1 || true

echo ""
echo "============================================================"
echo "  ✅ TripGraph is live:   http://$PUBLIC_HOST"
echo "     Backend health:      http://$PUBLIC_HOST/health"
echo ""
echo "  Logs:    journalctl -u tripgraph-backend -f"
echo "  Redeploy after a git push:   ./deploy.sh $PUBLIC_HOST"
echo "============================================================"
