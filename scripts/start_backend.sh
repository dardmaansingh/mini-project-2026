#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "=== Starting NetSentinel FastAPI Backend ==="
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

exec python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
