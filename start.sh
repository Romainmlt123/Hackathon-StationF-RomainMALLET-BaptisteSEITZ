#!/usr/bin/env bash
set -euo pipefail

# Simple start script that loads .env (if present) and runs the app.
# If ngrok is installed and the NGROK_AUTH_TOKEN env var is set, this
# will start ngrok on the configured port to expose the server for Twilio.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$ROOT_DIR/.env"

if [ -f "$ENV_FILE" ]; then
  echo "Loading environment from $ENV_FILE"
  # shellcheck source=/dev/null
  set -o allexport
  source "$ENV_FILE"
  set +o allexport
fi

PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

if command -v ngrok >/dev/null 2>&1 && [ -n "${NGROK_AUTH_TOKEN-}" ]; then
  echo "Starting ngrok on port $PORT"
  ngrok http $PORT &
  sleep 1
fi

echo "Starting uvicorn on $HOST:$PORT"
exec uvicorn app.main:app --host "$HOST" --port "$PORT"
