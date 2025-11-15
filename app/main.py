"""Entrypoint WebSocket server for the realtime voice agent.

This module exposes a FastAPI app with a WebSocket endpoint that
accepts Twilio ConversationRelay connections and hands each call to
the voice pipeline (`start_voice_agent`).

Notes:
- The code is resilient if Pipecat is not installed locally. It will
  still run the FastAPI server; the pipeline contains stubs that call
  external APIs (Mistral, ElevenLabs) and should be wired to the
  real Pipecat transports in the next iteration.
"""
from typing import Optional
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from loguru import logger

from app.pipeline import start_voice_agent
from app.config import Config
from app.routes import router as admin_router


# Load configuration at import time so other modules can import Config via
# app.config and the same instance will be available.
config = Config()


def configure_logging() -> None:
    # Configure loguru using the level from config
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level=config.LOG_LEVEL)


configure_logging()

app = FastAPI(title="Realtime Voice Agent - Pipecat Hackathon MVP")
app.include_router(admin_router, prefix="/admin")


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Starting Realtime Voice Agent server")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("Shutting down Realtime Voice Agent server")


@app.websocket("/ws/{stream_sid}")
async def websocket_endpoint(websocket: WebSocket, stream_sid: str) -> None:
    """WebSocket endpoint for a Twilio ConversationRelay connection.

    Each new connection corresponds to one phone call (session). We
    accept the socket, log the connection event, and delegate the
    heavy lifting to `start_voice_agent` which runs the audio -> STT ->
    LLM -> TTS pipeline and streams audio back into the socket.
    """
    client = websocket.client
    logger.info("on_client_connected stream_sid={} client={}", stream_sid, client)
    try:
        await start_voice_agent(websocket, stream_sid)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: stream_sid={}", stream_sid)
    except Exception as exc:
        logger.exception("Unhandled exception in voice agent for {}: {}", stream_sid, exc)
        try:
            # attempt to notify client then close
            await websocket.send_text("error:internal")
            await websocket.close()
        except Exception:
            pass


if __name__ == "__main__":
    # Use the config values for host/port
    uvicorn.run("app.main:app", host=config.HOST, port=config.PORT, reload=False)
