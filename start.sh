#!/usr/bin/env bash
set -euo pipefail

# ========================================
# HACKATHON STATION F - START SCRIPT
# ========================================
# Start the realtime voice agent with optional ngrok tunneling

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$ROOT_DIR/.env"

# Detect Python command (python3 on WSL/Ubuntu, python elsewhere)
if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD=python
else
  echo "❌ Python not found. Please install Python 3.11+"
  exit 1
fi

echo "🐍 Using Python: $PYTHON_CMD ($($PYTHON_CMD --version))"

# Check/create virtual environment
VENV_DIR="$ROOT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "📦 Creating virtual environment..."
  $PYTHON_CMD -m venv "$VENV_DIR"
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install/upgrade dependencies if needed
if [ ! -f "$VENV_DIR/.installed" ]; then
  echo "📥 Installing dependencies..."
  pip install --upgrade pip
  pip install -r requirements.txt
  touch "$VENV_DIR/.installed"
fi

# Load .env if present
if [ -f "$ENV_FILE" ]; then
  echo "✅ Loading environment from $ENV_FILE"
  set -o allexport
  source "$ENV_FILE"
  set +o allexport
else
  echo "⚠️  No .env file found. Using default/system environment variables."
fi

PORT=${PORT:-8765}
HOST=${HOST:-0.0.0.0}

# Optional: Start ngrok for Twilio webhook testing
if command -v ngrok >/dev/null 2>&1 && [ -n "${NGROK_AUTH_TOKEN-}" ]; then
  echo "🌐 Starting ngrok tunnel on port $PORT..."
  ngrok http $PORT > /dev/null &
  sleep 2
  echo "✅ Ngrok running. Get your public URL from: http://localhost:4040"
fi

# Start the FastAPI server (includes Twilio webhook + WebSocket)
echo "🚀 Starting Realtime Voice Agent..."
echo "   Host: $HOST"
echo "   Port: $PORT"
echo ""
echo "📋 Configure Twilio webhook to point to:"
echo "   POST http://your-public-url/incoming-call"
echo ""

exec python backend/server.py
