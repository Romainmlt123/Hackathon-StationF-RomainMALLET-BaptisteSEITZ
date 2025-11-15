"""Voice pipeline assembly: STT -> LLM -> TTS streaming.

This module provides a `start_voice_agent(websocket, stream_sid)`
entrypoint that ties together:
 - transport (Twilio ConversationRelay via WebSocket)
 - VAD (voice activity detection) hooks (placeholder)
 - STT (placeholder / short example using Whisper or Twilio STT)
 - LLM service integration (Mistral via `MistralLLMService`)
 - TTS streaming (ElevenLabs via `ElevenLabsTTSService`)

The implementation focuses on clarity and extendability. Network
operations are executed in background threads where appropriate to
avoid blocking the event loop.
"""
from __future__ import annotations

import os
import base64
import json
import asyncio
from typing import AsyncIterable, Optional
from loguru import logger
from fastapi import WebSocket, WebSocketDisconnect
from app.config import config as settings

import requests


class MistralLLMService:
    """Simple wrapper for calling a Mistral-like LLM API.

    This class uses blocking HTTP calls executed via the default
    threadpool executor so it can be called from async code.
    Replace the endpoint and payload shape to match the real Mistral API.
    """

    def __init__(self, api_key: str, model: str = "mistral-instruct", system_prompt: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt or settings.SYSTEM_PROMPT or "You are a helpful voice assistant."
        # Prefer configured endpoint, otherwise fall back to a sensible default.
        self.endpoint = settings.MISTRAL_API_URL or "https://api.mistral.ai/v1/generate"

    def _build_payload(self, user_text: str) -> dict:
        return {
            "model": self.model,
            "input": f"{self.system_prompt}\nUser: {user_text}",
            "max_tokens": 512,
        }

    def _call_api(self, payload: dict) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        logger.debug("Calling Mistral API at {} with payload keys {}", self.endpoint, list(payload.keys()))
        resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # Best-effort extraction: real API may differ
        if isinstance(data, dict):
            # try common shapes
            text = data.get("text") or data.get("result") or json.dumps(data)
        else:
            text = str(data)
        return text

    async def generate(self, user_text: str) -> str:
        payload = self._build_payload(user_text)
        return await asyncio.to_thread(self._call_api, payload)


class ElevenLabsTTSService:
    """Wrapper to stream audio from ElevenLabs TTS.

    The `stream_audio` method returns an async iterator yielding raw
    audio chunks (bytes). The endpoint URL and streaming method may
    need to be adapted to ElevenLabs' real streaming API.
    """

    def __init__(self, api_key: str, voice_id: str, model: str = "eleven_multilingual_v1"):
        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model
        self.base_url = settings.ELEVENLABS_API_URL or "https://api.elevenlabs.io/v1"

    def _call_stream(self, text: str) -> requests.Response:
        url = f"{self.base_url}/text-to-speech/{self.voice_id}/stream"
        headers = {"xi-api-key": self.api_key, "Accept": "audio/mpeg"}
        payload = {"text": text, "model": self.model}
        logger.debug("Calling ElevenLabs TTS stream endpoint {}", url)
        # NOTE: some ElevenLabs endpoints stream audio; here we request chunked
        return requests.post(url, headers=headers, json=payload, stream=True, timeout=30)

    async def stream_audio(self, text: str) -> AsyncIterable[bytes]:
        """Stream audio bytes from ElevenLabs as an async generator.

        Each yielded value is a chunk of the audio bytes to forward to
        the Twilio socket.
        """
        def blocking() -> requests.Response:
            return self._call_stream(text)

        resp = await asyncio.to_thread(blocking)
        try:
            resp.raise_for_status()
        except Exception as e:
            logger.exception("ElevenLabs TTS error: {}", e)
            raise

        # Iterate over response chunks in a thread to avoid blocking
        for chunk in resp.iter_content(chunk_size=4096):
            if chunk:
                yield chunk


async def start_voice_agent(websocket: WebSocket, stream_sid: str) -> None:
    """Main pipeline runner for a single Twilio call session.

    Workflow (simplified):
    - Accept the WebSocket
    - Wait for incoming audio frames (base64 encoded) from Twilio
    - Convert frames to a single buffer or streaming STT
    - Send transcribed text to Mistral LLM
    - Stream TTS audio back to Twilio via the same WebSocket

    This implementation is intentionally minimal and focuses on
    demonstrating where integrations plug in. Replace STT and transport
    handling with the real Pipecat ConversationRelay types in the
    next iteration.
    """
    # Accept and signal connected
    await websocket.accept()
    logger.info("on_client_connected stream_sid={}", stream_sid)

    # Load API keys from central settings
    mistral_key = settings.MISTRAL_API_KEY or ""
    eleven_key = settings.ELEVENLABS_API_KEY or ""
    eleven_voice = settings.ELEVENLABS_VOICE_ID_DEFAULT

    if not mistral_key or not eleven_key:
        logger.warning("Missing API keys for Mistral or ElevenLabs. Pipeline will run in dry-mode.")

    llm = MistralLLMService(mistral_key, system_prompt=settings.SYSTEM_PROMPT)
    tts = ElevenLabsTTSService(eleven_key, voice_id=eleven_voice)

    try:
        # Main receive loop: Twilio ConversationRelay sends JSON events.
        while True:
            message = await websocket.receive_text()
            # Example Twilio media event (pseudo): {"type":"media","payload":"<base64>"}
            try:
                ev = json.loads(message)
            except Exception:
                logger.debug("Received non-json message: {}", message)
                continue

            ev_type = ev.get("type")
            if ev_type == "media":
                b64 = ev.get("payload") or ev.get("media") or ev.get("audio")
                if not b64:
                    logger.debug("Media event without payload")
                    continue

                # Decode audio (PCM or other format depending on Twilio)
                audio_bytes = base64.b64decode(b64)

                # TODO: replace this placeholder STT with a streaming Whisper/Twilio STT
                # For MVP we do a naive placeholder to illustrate
                logger.debug("Received audio bytes ({} bytes)", len(audio_bytes))
                # Placeholder transcription
                transcribed = "[transcribed speech placeholder]"

                # Call LLM to get response text
                logger.info("Calling LLM for stream_sid={} transcript='{}'", stream_sid, transcribed)
                try:
                    response_text = await llm.generate(transcribed)
                except Exception as e:
                    logger.exception("LLM generation failed: {}", e)
                    response_text = "Désolé, je rencontre un problème technique."

                logger.info("LLM returned: {}", response_text)

                # Stream TTS back to the socket as binary audio frames
                try:
                    async for audio_chunk in tts.stream_audio(response_text):
                        # Send raw audio bytes back to Twilio. The ConversationRelay
                        # expects a specific framing (e.g. a JSON message with base64
                        # audio). We'll send a minimal wrapper here; adapt to your
                        # Pipecat transport in the next integration step.
                        payload = {"type": "audio", "payload": base64.b64encode(audio_chunk).decode()}
                        await websocket.send_text(json.dumps(payload))
                except Exception as e:
                    logger.exception("TTS streaming failed: {}", e)

            elif ev_type == "event" and ev.get("name") == "disconnect":
                logger.info("Client requested disconnect: {}", stream_sid)
                break
            else:
                logger.debug("Unhandled event type: {}", ev_type)

    except WebSocketDisconnect:
        logger.info("Client disconnected: {}", stream_sid)
    except Exception as exc:
        logger.exception("Unhandled pipeline error for {}: {}", stream_sid, exc)
    finally:
        logger.info("on_client_disconnected stream_sid={}", stream_sid)
        try:
            await websocket.close()
        except Exception:
            pass
