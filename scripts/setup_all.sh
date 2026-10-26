#!/usr/bin/env bash
# ==============================================================================
# NetSentinel — Automated One-Step Setup & Dependency Installer
# Sets up Python virtual environment, installs backend & frontend dependencies,
# and verifies database tables.
# ==============================================================================
set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo -e "${BOLD}${CYAN}================================================================${NC}"
echo -e "${BOLD}${CYAN}           NetSentinel — One-Step Environment Setup             ${NC}"
echo -e "${BOLD}${CYAN}================================================================${NC}"

# 1. PATH setup for Node
if [ -d "/home/dardmaan/.nodejs/bin" ]; then
    export PATH="/home/dardmaan/.nodejs/bin:$PATH"
elif [ -d "$HOME/.nodejs/bin" ]; then
    export PATH="$HOME/.nodejs/bin:$PATH"
fi

# 2. Check Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] python3 is required but not installed.${NC}" >&2
    exit 1
fi
echo -e "${GREEN}[1/4] Python 3 found:${NC} $(python3 --version)"

# 3. Virtual Environment setup
if [ ! -d "$ROOT_DIR/.venv" ]; then
    echo -e "${YELLOW}[2/4] Creating Python virtual environment in .venv...${NC}"
    python3 -m venv "$ROOT_DIR/.venv"
else
    echo -e "${GREEN}[2/4] Python virtual environment exists (.venv).${NC}"
fi

PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
PIP_BIN="$ROOT_DIR/.venv/bin/pip"

# Install/update backend requirements
echo -e "${YELLOW}[*] Installing/verifying backend dependencies via pip...${NC}"
"$PIP_BIN" install -r "$ROOT_DIR/requirements.txt"

# 4. Frontend dependencies
echo -e "\n${GREEN}[3/4] Checking Node.js and npm...${NC}"
if ! command -v npm >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] npm not found. Please install Node.js 18+ or check PATH.${NC}" >&2
    exit 1
fi
echo -e "      Node: $(node -v) | npm: $(npm -v)"
echo -e "${YELLOW}[*] Installing frontend dependencies via npm...${NC}"
(cd "$ROOT_DIR/frontend" && npm install --silent)

# 5. Database verification
echo -e "\n${GREEN}[4/4] Verifying SQLite database and tables...${NC}"
"$PYTHON_BIN" -c "
import asyncio
from backend.app.database import engine, Base
from backend.app.models import *

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init_db())
"
echo -e "${GREEN}[✓] Database schema verified successfully.${NC}"

echo -e "\n${BOLD}${GREEN}================================================================${NC}"
echo -e "${BOLD}${GREEN}        NetSentinel setup is complete and ready to run!        ${NC}"
echo -e "${BOLD}${GREEN}================================================================${NC}"
echo -e "  To start the application, simply run:  ${BOLD}${CYAN}./start.sh${NC}"
echo -e "  Or to run in background:              ${BOLD}${CYAN}./start.sh --background${NC}"
echo -e "  To stop anytime:                      ${BOLD}${CYAN}./stop.sh${NC}\n"
