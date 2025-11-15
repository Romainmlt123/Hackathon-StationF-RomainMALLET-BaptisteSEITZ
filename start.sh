#!/usr/bin/env bash
set -euo pipefail

# ========================================
# HACKATHON STATION F - START SCRIPT
# ========================================
# Start the realtime voice agent with optional ngrok tunneling

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$ROOT_DIR/.env"

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
TRANSPORT=${TRANSPORT:-twilio}

# Optional: Start ngrok for Twilio webhook testing
if command -v ngrok >/dev/null 2>&1 && [ -n "${NGROK_AUTH_TOKEN-}" ]; then
  echo "🌐 Starting ngrok tunnel on port $PORT..."
  ngrok http $PORT > /dev/null &
  sleep 2
  echo "✅ Ngrok running. Get your public URL from: http://localhost:4040"
fi

# Start the Pipecat bot
echo "🚀 Starting Realtime Voice Agent..."
echo "   Transport: $TRANSPORT"
echo "   Host: $HOST"
echo "   Port: $PORT"
echo ""

exec python -m app.main --transport "$TRANSPORT" --port "$PORT" --host "$HOST"
