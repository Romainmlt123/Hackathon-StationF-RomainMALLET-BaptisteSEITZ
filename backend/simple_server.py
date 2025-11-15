"""
Backend API simple pour recevoir les webhooks ElevenLabs et logger les conversations.
Plus besoin de Pipecat - tout est géré par ElevenLabs Conversational AI.
"""
import os
import sys
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from loguru import logger

# Configuration logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("server.log", rotation="10 MB", level="INFO")

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv()


# ========== Modèles Pydantic ==========

class TranscriptEntry(BaseModel):
    speaker: str
    text: str
    timestamp: str


class ElevenLabsWebhook(BaseModel):
    """Modèle pour recevoir les webhooks ElevenLabs"""
    conversation_id: str
    agent_id: str
    status: str  # started, in_progress, completed, failed
    transcript: Optional[list[TranscriptEntry]] = []
    metadata: Optional[dict] = {}
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    caller_number: Optional[str] = None


# ========== FastAPI App ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Backend API démarré")
    yield
    logger.info("🛑 Backend API arrêté")


app = FastAPI(
    title="Voice Agent Backend API",
    description="API pour logger les conversations de l'agent vocal ElevenLabs",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, restreindre aux domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Helper pour authentification ==========

def verify_api_key(x_api_key: str = Header(...)) -> bool:
    """Vérifie la clé API"""
    expected_key = os.getenv("API_KEY", "hSar6wEenqfJGb_RwrfDu3b5S1VWBqSpxj5xWCnR9KY")
    
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return True


# ========== Endpoints ==========

@app.get("/")
async def root():
    """Page d'accueil"""
    return {
        "service": "Voice Agent Backend API",
        "status": "running",
        "endpoints": {
            "health": "GET /health",
            "elevenlabs_webhook": "POST /webhook/elevenlabs",
            "test_log": "POST /api/calls/log"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/webhook/elevenlabs")
async def elevenlabs_webhook(
    webhook_data: ElevenLabsWebhook,
    request: Request,
    x_api_key: str = Header(None)
):
    """
    Webhook endpoint pour recevoir les événements d'ElevenLabs.
    
    ElevenLabs enverra les données de conversation ici.
    """
    # Authentification optionnelle
    if x_api_key:
        verify_api_key(x_api_key)
    
    logger.info(f"📞 Webhook ElevenLabs reçu : {webhook_data.conversation_id}")
    logger.info(f"   Status: {webhook_data.status}")
    logger.info(f"   Transcript: {len(webhook_data.transcript)} messages")
    
    # Afficher le transcript dans les logs
    for entry in webhook_data.transcript:
        logger.info(f"   {entry.speaker}: {entry.text}")
    
    # TODO: Sauvegarder dans Supabase
    # db = get_db()
    # await db.create_call_log(...)
    
    return {
        "status": "received",
        "conversation_id": webhook_data.conversation_id,
        "message": "Webhook traité avec succès"
    }


@app.post("/api/calls/log")
async def log_call_manual(
    request: Request,
    x_api_key: str = Header(...)
):
    """
    Endpoint pour logger manuellement un appel (test).
    """
    verify_api_key(x_api_key)
    
    body = await request.json()
    
    logger.info(f"📝 Log manuel reçu : {body}")
    
    # TODO: Sauvegarder dans Supabase
    
    return {
        "status": "logged",
        "data": body
    }


@app.get("/api/calls/{business_id}")
async def get_business_calls(
    business_id: str,
    x_api_key: str = Header(...)
):
    """
    Récupérer les appels d'un business (pour le frontend).
    """
    verify_api_key(x_api_key)
    
    logger.info(f"📊 Récupération des appels pour : {business_id}")
    
    # TODO: Récupérer depuis Supabase
    # db = get_db()
    # calls = await db.get_calls_by_business(business_id)
    
    # Pour l'instant, retourner des données de test
    return {
        "total": 0,
        "calls": [],
        "message": "Connectez Supabase pour voir les vraies données"
    }


# ========== Démarrage ==========

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8765))
    
    logger.info(f"🚀 Démarrage du serveur sur le port {port}")
    logger.info("")
    logger.info("📡 Endpoints disponibles :")
    logger.info(f"   - POST http://localhost:{port}/webhook/elevenlabs")
    logger.info(f"   - POST http://localhost:{port}/api/calls/log")
    logger.info(f"   - GET  http://localhost:{port}/api/calls/{{business_id}}")
    logger.info("")
    logger.info("🔑 Clé API configurée : " + os.getenv("API_KEY", "non configurée")[:20] + "...")
    logger.info("")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
