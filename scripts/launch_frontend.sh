#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/frontend"

if [[ ! -d "$FRONTEND_DIR" ]]; then
  echo "[frontend] ERROR: frontend directory not found at $FRONTEND_DIR"
  exit 1
fi

echo "[frontend] Checking Node/npm dependencies..."

if [[ -s "$HOME/.nvm/nvm.sh" ]]; then
  export NVM_DIR="$HOME/.nvm"
  # shellcheck disable=SC1090
  . "$NVM_DIR/nvm.sh"
fi

if ! command -v node >/dev/null 2>&1; then
  echo "[frontend] ERROR: node is not installed or not on PATH."
  echo "[frontend] If using nvm, install with: nvm install 20"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[frontend] ERROR: npm is not available."
  exit 1
fi

cd "$FRONTEND_DIR"

if [[ ! -d node_modules ]]; then
  echo "[frontend] node_modules not found. Running npm install..."
  npm install
fi

echo "[frontend] Launching Vite at http://localhost:5173"
exec npm run dev -- --host 0.0.0.0
