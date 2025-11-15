"""Admin routes for the Realtime Voice Agent (health, simple status).

This module is intentionally small and non-sensitive. It can be
expanded later to expose active sessions, metrics or simple controls.
"""
from fastapi import APIRouter
from loguru import logger

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    logger.debug("Health check requested")
    return {"status": "ok"}


@router.get("/info")
async def info() -> dict:
    # Return a minimal info payload. Avoid leaking secrets.
    return {"service": "realtime-voice-agent", "version": "0.1.0"}
