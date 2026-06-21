#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "[backend] Checking dependencies..."

if [[ ! -f ".env" ]]; then
  echo "[backend] ERROR: .env is missing. Run: cp .env.example .env"
  exit 1
fi

if [[ ! -d ".venv" ]]; then
  echo "[backend] ERROR: .venv is missing. Create and install dependencies first."
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if ! command -v python >/dev/null 2>&1; then
  echo "[backend] ERROR: python not found in virtual environment."
  exit 1
fi

if ! python -c "import uvicorn" >/dev/null 2>&1; then
  echo "[backend] ERROR: uvicorn is not installed in .venv."
  echo "[backend] Run: source .venv/bin/activate && pip install -r backend/requirements.txt"
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "[backend] ERROR: curl is required for readiness checks."
  exit 1
fi

if ! no_proxy=localhost,127.0.0.1 curl -sf http://localhost:7474 >/dev/null 2>&1; then
  echo "[backend] WARNING: Neo4j endpoint http://localhost:7474 not reachable."
  echo "[backend] Start it first: ./scripts/launch_neo4j.sh"
fi

if grep -q '^GOOGLE_API_KEY=your_gemini_api_key_here' .env; then
  echo "[backend] WARNING: GOOGLE_API_KEY appears to be placeholder in .env"
fi

echo "[backend] Launching FastAPI at http://localhost:8000"
exec no_proxy=localhost,127.0.0.1 uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
