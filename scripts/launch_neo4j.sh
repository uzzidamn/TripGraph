#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "[neo4j] Starting Neo4j service..."

if ! command -v systemctl >/dev/null 2>&1; then
  echo "[neo4j] ERROR: systemctl is not available on this host."
  exit 1
fi

if ! systemctl list-unit-files | grep -q '^neo4j.service'; then
  echo "[neo4j] ERROR: neo4j.service not found. Install Neo4j first."
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "[neo4j] ERROR: curl is required for readiness checks."
  exit 1
fi

sudo systemctl start neo4j

echo "[neo4j] Waiting for HTTP endpoint on localhost:7474..."
for i in $(seq 1 30); do
  if no_proxy=localhost,127.0.0.1 curl -sf http://localhost:7474 >/dev/null 2>&1; then
    echo "[neo4j] READY: http://localhost:7474"
    echo "[neo4j] BOLT : bolt://localhost:7687"
    exit 0
  fi
  sleep 2
done

echo "[neo4j] ERROR: Neo4j did not become ready in time."
sudo systemctl status neo4j --no-pager | sed -n '1,20p'
exit 1
