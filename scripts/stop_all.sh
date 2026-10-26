#!/usr/bin/env bash
# ==============================================================================
# NetSentinel — Stop All Services
# Terminates both FastAPI Backend and Vite Frontend cleanly, freeing ports.
# ==============================================================================

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo -e "${BOLD}${CYAN}=== Stopping NetSentinel Services ===${NC}"

# Kill from PID files if stored
if [ -f "$ROOT_DIR/.netsentinel_backend.pid" ]; then
    BPID=$(cat "$ROOT_DIR/.netsentinel_backend.pid" 2>/dev/null)
    if [ -n "$BPID" ] && kill -0 "$BPID" 2>/dev/null; then
        echo -e "${YELLOW}[*] Stopping backend (PID $BPID)...${NC}"
        kill "$BPID" 2>/dev/null || true
    fi
    rm -f "$ROOT_DIR/.netsentinel_backend.pid"
fi

if [ -f "$ROOT_DIR/.netsentinel_frontend.pid" ]; then
    FPID=$(cat "$ROOT_DIR/.netsentinel_frontend.pid" 2>/dev/null)
    if [ -n "$FPID" ] && kill -0 "$FPID" 2>/dev/null; then
        echo -e "${YELLOW}[*] Stopping frontend (PID $FPID)...${NC}"
        kill "$FPID" 2>/dev/null || true
    fi
    rm -f "$ROOT_DIR/.netsentinel_frontend.pid"
fi

# Ensure ports 8000 and 5173 are freed
if command -v fuser >/dev/null 2>&1; then
    fuser -k 8000/tcp >/dev/null 2>&1 || true
    fuser -k 5173/tcp >/dev/null 2>&1 || true
elif command -v lsof >/dev/null 2>&1; then
    PIDS=$(lsof -ti :8000,5173 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        kill -9 $PIDS >/dev/null 2>&1 || true
    fi
fi

# Fallback pkill on names
pkill -f "uvicorn backend.app.main:app" >/dev/null 2>&1 || true
pkill -f "vite --host 127.0.0.1" >/dev/null 2>&1 || true

sleep 0.5
echo -e "${GREEN}[✓] Ports 8000 and 5173 are free. All NetSentinel services stopped.${NC}"
