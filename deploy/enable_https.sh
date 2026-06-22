#!/usr/bin/env bash
#
# Attach a domain + free HTTPS (Let's Encrypt) to an already-deployed TripGraph.
# REQUIRED for .app domains, which browsers force onto HTTPS (HSTS preload).
#
# Prereq: DNS A records for the domain (and www) must already point at this
# droplet's IP and have propagated. Check with:  dig +short tripgraph.app
#
# Usage (run as root on the droplet, AFTER deploy.sh has run once):
#     ./enable_https.sh tripgraph.app you@email.com
#
set -euo pipefail

DOMAIN="${1:-}"
EMAIL="${2:-}"
APP_DIR="/opt/tripgraph"
BACKEND_PORT="8000"

if [[ -z "$DOMAIN" || -z "$EMAIL" ]]; then
  echo "Usage: ./enable_https.sh <domain> <email>"
  echo "Example: ./enable_https.sh tripgraph.app me@iisc.ac.in"
  exit 1
fi

echo "==> Verifying DNS points here before requesting a cert"
RESOLVED="$(dig +short "$DOMAIN" | tail -1 || true)"
MYIP="$(curl -4 -fsSL ifconfig.me || true)"   # force IPv4 — droplet also has IPv6
echo "    $DOMAIN resolves to: ${RESOLVED:-<nothing>}"
echo "    this droplet IP is : ${MYIP:-<unknown>}"
if [[ -n "$RESOLVED" && -n "$MYIP" && "$RESOLVED" != "$MYIP" ]]; then
  echo "    ⚠️  DNS does not point here yet. Wait for propagation and re-run."
  echo "        (Let's Encrypt will fail until $DOMAIN -> $MYIP.)"
  exit 1
fi

echo "==> [1/4] Installing certbot"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y certbot python3-certbot-nginx

echo "==> [2/4] Pointing nginx at $DOMAIN"
cat > /etc/nginx/sites-available/tripgraph <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    root $APP_DIR/frontend/dist;
    index index.html;

    location / { try_files \$uri \$uri/ /index.html; }
    location /api/ {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_read_timeout 120s;
    }
    location /health { proxy_pass http://127.0.0.1:$BACKEND_PORT; }
}
EOF
ln -sf /etc/nginx/sites-available/tripgraph /etc/nginx/sites-enabled/tripgraph
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "==> [3/4] Rebuilding frontend to call https://$DOMAIN"
GMAPS_KEY="$(grep -E '^VITE_GOOGLE_MAPS_API_KEY=' "$APP_DIR/.env" | tail -1 | cut -d= -f2- || true)"
cat > "$APP_DIR/frontend/.env" <<EOF
VITE_API_URL=https://$DOMAIN
VITE_GOOGLE_MAPS_API_KEY=$GMAPS_KEY
EOF
cd "$APP_DIR/frontend" && npm run build

echo "==> [4/4] Requesting + installing the Let's Encrypt certificate"
ufw allow 443/tcp >/dev/null 2>&1 || true
certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" \
  --non-interactive --agree-tos -m "$EMAIL" --redirect

echo ""
echo "============================================================"
echo "  ✅ HTTPS live:  https://$DOMAIN"
echo "     Auto-renew is handled by certbot's systemd timer."
echo "     Test renewal: certbot renew --dry-run"
echo "============================================================"
