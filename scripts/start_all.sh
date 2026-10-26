#!/usr/bin/env bash
# ==============================================================================
# NetSentinel — Unified Service Runner
# Starts both FastAPI Backend (8000) and Vite Frontend (5173) in one command.
#
# Usage:
#   ./start.sh              # Run in foreground with live logs (Ctrl+C to stop both)
#   ./start.sh --background # Run in background (stop with ./stop.sh)
# ==============================================================================
set -e

# ANSI Color Codes
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Ensure Node & npm in PATH
if [ -d "/home/dardmaan/.nodejs/bin" ]; then
    export PATH="/home/dardmaan/.nodejs/bin:$PATH"
elif [ -d "$HOME/.nodejs/bin" ]; then
    export PATH="$HOME/.nodejs/bin:$PATH"
fi

# Locate Python
if [ -f "$ROOT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
else
    echo -e "${RED}[ERROR] Python 3 not found. Please run ./setup.sh first.${NC}" >&2
    exit 1
fi

# Locate Node/npm
if ! command -v npm >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] npm not found in PATH. Please install Node.js 18+ or check PATH.${NC}" >&2
    exit 1
fi

# Ensure frontend dependencies exist
if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
    echo -e "${YELLOW}[!] frontend/node_modules not found. Running npm install...${NC}"
    (cd "$ROOT_DIR/frontend" && npm install)
fi

# Ensure log directory exists
mkdir -p "$ROOT_DIR/logs"

# Function to clean stale ports before starting
cleanup_stale_ports() {
    # Check port 8000 and 5173
    if command -v fuser >/dev/null 2>&1; then
        fuser -k 8000/tcp >/dev/null 2>&1 || true
        fuser -k 5173/tcp >/dev/null 2>&1 || true
    elif command -v lsof >/dev/null 2>&1; then
        local pids
        pids=$(lsof -ti :8000,5173 2>/dev/null || true)
        if [ -n "$pids" ]; then
            kill -9 $pids >/dev/null 2>&1 || true
        fi
    fi
}

cleanup_stale_ports

# Display banner
print_banner() {
    echo -e "${BOLD}${CYAN}================================================================${NC}"
    echo -e "${BOLD}${CYAN}           NetSentinel — Campus SOC & Traffic Monitor          ${NC}"
    echo -e "${BOLD}${CYAN}================================================================${NC}"
    echo -e "  ${GREEN}●${NC} ${BOLD}Frontend Dashboard:${NC}   ${CYAN}http://127.0.0.1:5173${NC}"
    echo -e "  ${GREEN}●${NC} ${BOLD}Backend REST API:${NC}     ${CYAN}http://127.0.0.1:8000${NC}"
    echo -e "  ${GREEN}●${NC} ${BOLD}Interactive API Docs:${NC} ${CYAN}http://127.0.0.1:8000/api/docs${NC}"
    echo -e "  ${GREEN}●${NC} ${BOLD}WebSocket Stream:${NC}     ${CYAN}ws://127.0.0.1:8000/ws/events${NC}"
    echo -e "${BOLD}${CYAN}================================================================${NC}"
}

# Daemon / Background Mode
if [[ "$1" == "--daemon" || "$1" == "-d" || "$1" == "--background" ]]; then
    print_banner
    echo -e "${YELLOW}[*] Launching NetSentinel services in the background...${NC}"

    # Start backend
    "$PYTHON_BIN" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload > "$ROOT_DIR/logs/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo "$BACKEND_PID" > "$ROOT_DIR/.netsentinel_backend.pid"

    # Start frontend
    (cd "$ROOT_DIR/frontend" && npm run dev -- --host 127.0.0.1 --port 5173) > "$ROOT_DIR/logs/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo "$FRONTEND_PID" > "$ROOT_DIR/.netsentinel_frontend.pid"

    sleep 1.5

    echo -e "${GREEN}[✓] Both services are now running in the background!${NC}"
    echo -e "    Backend PID:  ${BOLD}${BACKEND_PID}${NC}  (Logs: logs/backend.log)"
    echo -e "    Frontend PID: ${BOLD}${FRONTEND_PID}${NC}  (Logs: logs/frontend.log)"
    echo -e "    To stop:      ${BOLD}./stop.sh${NC}"
    exit 0
fi

# Foreground Mode (Unified live logging)
print_banner
echo -e "${YELLOW}[*] Starting Backend and Frontend simultaneously...${NC}"
echo -e "${YELLOW}[*] Press Ctrl+C at any time to shut down both services.${NC}\n"

# Start backend with colored prefix
"$PYTHON_BIN" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload 2>&1 | \
    sed -u "s/^/$(printf "${CYAN}[BACKEND]${NC}  ")/" &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$ROOT_DIR/.netsentinel_backend.pid"

# Start frontend with colored prefix
(cd "$ROOT_DIR/frontend" && npm run dev -- --host 127.0.0.1 --port 5173) 2>&1 | \
    sed -u "s/^/$(printf "${MAGENTA}[FRONTEND]${NC} ")/" &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$ROOT_DIR/.netsentinel_frontend.pid"

# Trap shutdown signals to terminate both children cleanly
shutdown_handler() {
    echo -e "\n${YELLOW}[!] Received stop signal. Shutting down NetSentinel services...${NC}"
    kill "$BACKEND_PID" 2>/dev/null || true
    kill "$FRONTEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
    wait "$FRONTEND_PID" 2>/dev/null || true
    rm -f "$ROOT_DIR/.netsentinel_backend.pid" "$ROOT_DIR/.netsentinel_frontend.pid"
    cleanup_stale_ports
    echo -e "${GREEN}[✓] All NetSentinel services stopped cleanly.${NC}"
    exit 0
}

trap shutdown_handler SIGINT SIGTERM EXIT

# Keep script waiting on children
wait
