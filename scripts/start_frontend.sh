#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR/frontend"

export PATH="/home/dardmaan/.nodejs/bin:$PATH"

echo "=== Starting NetSentinel Vite React Frontend ==="
exec npm run dev -- --host 127.0.0.1 --port 5173
