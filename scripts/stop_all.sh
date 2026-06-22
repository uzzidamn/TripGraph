#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "[stop] Stopping TripGraph processes..."

# Stop backend process if running
pkill -f "uvicorn backend.main:app" >/dev/null 2>&1 || true

# Stop frontend process variants if running
pkill -f "vite --host 0.0.0.0" >/dev/null 2>&1 || true
pkill -f "npm run dev -- --host 0.0.0.0" >/dev/null 2>&1 || true

# Stop Neo4j service if systemd and service exist
if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files | grep -q '^neo4j.service'; then
  sudo systemctl stop neo4j || true
fi

echo "[stop] Verifying shutdown status..."

backend_left="$(ps -ef | grep -E "uvicorn backend.main:app" | grep -v grep || true)"
frontend_left="$(ps -ef | grep -E "vite --host 0.0.0.0|npm run dev -- --host 0.0.0.0" | grep -v grep || true)"

if [[ -n "$backend_left" ]]; then
  echo "[stop] WARNING: backend process still running"
  echo "$backend_left"
else
  echo "[stop] Backend stopped"
fi

if [[ -n "$frontend_left" ]]; then
  echo "[stop] WARNING: frontend process still running"
  echo "$frontend_left"
else
  echo "[stop] Frontend stopped"
fi

if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files | grep -q '^neo4j.service'; then
  neo4j_state="$(systemctl is-active neo4j || true)"
  echo "[stop] Neo4j service state: $neo4j_state"
fi

echo "[stop] Done."
