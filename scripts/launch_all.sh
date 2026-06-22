#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS_DIR="$REPO_ROOT/scripts"
LOG_DIR="$REPO_ROOT/.run_logs"
PID_DIR="$REPO_ROOT/.run_pids"

mkdir -p "$LOG_DIR" "$PID_DIR"
cd "$REPO_ROOT"

echo "[all] Starting TripGraph services..."

# Ensure helper scripts exist
for f in "$SCRIPTS_DIR/launch_neo4j.sh" "$SCRIPTS_DIR/launch_backend.sh" "$SCRIPTS_DIR/launch_frontend.sh"; do
  if [[ ! -x "$f" ]]; then
    echo "[all] ERROR: Missing or non-executable script: $f"
    echo "[all] Run: chmod +x scripts/launch_neo4j.sh scripts/launch_backend.sh scripts/launch_frontend.sh"
    exit 1
  fi
done

# Start Neo4j first (blocking until ready or fail)
"$SCRIPTS_DIR/launch_neo4j.sh"

# Start backend in background
if pgrep -f "uvicorn backend.main:app" >/dev/null 2>&1; then
  echo "[all] Backend already running; skipping start"
else
  echo "[all] Starting backend (log: $LOG_DIR/backend.log)"
  nohup "$SCRIPTS_DIR/launch_backend.sh" > "$LOG_DIR/backend.log" 2>&1 &
  echo $! > "$PID_DIR/backend_launcher.pid"
fi

# Wait for backend readiness
backend_ready="false"
for i in $(seq 1 30); do
  if no_proxy=localhost,127.0.0.1 curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    backend_ready="true"
    break
  fi
  sleep 2
done

if [[ "$backend_ready" != "true" ]]; then
  echo "[all] ERROR: Backend did not become healthy at http://localhost:8000/health"
  echo "[all] Check logs: $LOG_DIR/backend.log"
  exit 1
fi

# Start frontend in background
if pgrep -f "vite --host 0.0.0.0" >/dev/null 2>&1 || pgrep -f "npm run dev -- --host 0.0.0.0" >/dev/null 2>&1; then
  echo "[all] Frontend already running; skipping start"
else
  echo "[all] Starting frontend (log: $LOG_DIR/frontend.log)"
  nohup "$SCRIPTS_DIR/launch_frontend.sh" > "$LOG_DIR/frontend.log" 2>&1 &
  echo $! > "$PID_DIR/frontend_launcher.pid"
fi

# Wait for frontend readiness
frontend_ready="false"
for i in $(seq 1 30); do
  if no_proxy=localhost,127.0.0.1 curl -sf http://localhost:5173 >/dev/null 2>&1; then
    frontend_ready="true"
    break
  fi
  sleep 2
done

if [[ "$frontend_ready" != "true" ]]; then
  echo "[all] ERROR: Frontend did not become reachable at http://localhost:5173"
  echo "[all] Check logs: $LOG_DIR/frontend.log"
  exit 1
fi

echo "[all] READY"
echo "[all] Frontend: http://localhost:5173"
echo "[all] Backend : http://localhost:8000"
echo "[all] Docs    : http://localhost:8000/docs"
echo "[all] Neo4j   : http://localhost:7474"
echo "[all] Logs    : $LOG_DIR"
