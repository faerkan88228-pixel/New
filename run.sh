#!/usr/bin/env bash
# OmniNexus Studio Startup Script
set -e

PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

echo "=================================================="
echo " Starting OmniNexus Studio (Agent, Voice, Android)"
echo "=================================================="
echo " Binding to http://${HOST}:${PORT}"
echo " Workspace: $(pwd)"
echo "=================================================="

exec python3 -m uvicorn app.main:app --host "${HOST}" --port "${PORT}"
