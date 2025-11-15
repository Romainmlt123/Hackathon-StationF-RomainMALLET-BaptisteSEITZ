# Realtime Voice Agent — Pipecat Hackathon MVP

This repository contains a small FastAPI-based project demonstrating a realtime voice agent pipeline for Twilio ConversationRelay. It wires STT → LLM (Mistral) → TTS (ElevenLabs) and streams audio back to the caller.

Quick overview
- WebSocket endpoint: `/ws/{stream_sid}` — Twilio ConversationRelay connects here.
- Admin routes: `/admin/health`, `/admin/info`.
- Main pipeline: `app/pipeline.py` (stubs and service wrappers for Mistral & ElevenLabs).

Setup
1. Copy `.env.template` to `.env` and fill API keys:

```bash
cp .env.template .env
# Edit .env and add MISTRAL_API_KEY and ELEVENLABS_API_KEY
```

2. Install dependencies (recommended in a virtualenv):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Run locally:

```bash
./start.sh
```

Optionally, install `ngrok` and set `NGROK_AUTH_TOKEN` in your `.env` to expose the server to Twilio.

Notes & next steps
- The repository includes stubs for STT and assumes Twilio sends base64 audio frames over ConversationRelay. You should adapt the framing to Pipecat's ConversationRelay transport and replace the placeholder STT with a streaming Whisper/Twilio STT for low latency.
- Mistral and ElevenLabs service wrappers are provided but may need payload/URL adjustments to match the current upstream API contracts.

License: MIT
