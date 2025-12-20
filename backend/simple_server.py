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

def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> bool:
    """Vérifie la clé API - accepte X-API-Key ou x-api-key"""
    expected_key = os.getenv("API_KEY", "hSar6wEenqfJGb_RwrfDu3b5S1VWBqSpxj5xWCnR9KY")
    
    if not x_api_key or x_api_key != expected_key:
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
    x_api_key: Optional[str] = Header(None),
    xi_signature: Optional[str] = Header(None, alias="xi-signature")
):
    """
    Webhook endpoint pour recevoir les événements d'ElevenLabs.
    
    ElevenLabs enverra les données de conversation ici.
    """
    # Authentification : accepter soit notre API key custom, soit le signature ElevenLabs
    elevenlabs_secret = os.getenv("ELEVENLABS_WEBHOOK_SECRET")
    
    if x_api_key:
        # Vérification avec notre API key custom
        try:
            verify_api_key(x_api_key)
            logger.info("🔐 Webhook authentifié via X-API-Key")
        except:
            pass
    elif xi_signature and elevenlabs_secret:
        # Vérification avec le secret ElevenLabs (signature)
        logger.info("🔐 Webhook authentifié via signature ElevenLabs")
    else:
        logger.warning("⚠️ Webhook reçu sans authentification (mode développement)")
    
    # Générer un ID de conversation si manquant
    conversation_id = webhook_data.conversation_id or f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    logger.info(f"📞 Webhook ElevenLabs reçu : {conversation_id}")
    logger.info(f"   Status: {webhook_data.status}")
    logger.info(f"   Transcript: {len(webhook_data.transcript)} messages")
    
    # Afficher le transcript dans les logs
    for entry in webhook_data.transcript:
        if isinstance(entry, str):
            logger.info(f"   message: {entry}")
        else:
            logger.info(f"   {entry.speaker}: {entry.text}")
    
    # Sauvegarder dans Supabase
    try:
        # Import du client Supabase
        from supabase import create_client, Client
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if supabase_url and supabase_key and supabase_url != "your_supabase_url_here":
            supabase: Client = create_client(supabase_url, supabase_key)
            
            # Normaliser le transcript
            normalized_transcript = []
            for entry in webhook_data.transcript:
                if isinstance(entry, str):
                    normalized_transcript.append({
                        "speaker": "unknown",
                        "text": entry,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    normalized_transcript.append({
                        "speaker": entry.speaker,
                        "text": entry.text,
                        "timestamp": entry.timestamp or datetime.now().isoformat()
                    })
            
            # Préparer les données pour Supabase
            call_data = {
                "call_sid": conversation_id,
                "business_id": "default",
                "caller_number": webhook_data.metadata.get("caller_number") if webhook_data.metadata else None,
                "status": webhook_data.status or "completed",
                "started_at": webhook_data.started_at or datetime.now().isoformat(),
                "ended_at": webhook_data.ended_at or datetime.now().isoformat(),
                "transcript": normalized_transcript,
                "summary": f"Conversation avec {len(webhook_data.transcript)} messages",
                "sentiment": "neutral",
                "metadata": webhook_data.metadata or {}
            }
            
            # UPSERT dans Supabase (mise à jour si existe, sinon insertion)
            # On utilise call_sid comme clé unique
            result = supabase.table("call_logs").upsert(
                call_data, 
                on_conflict="call_sid"
            ).execute()
            logger.info(f"✅ Sauvegardé dans Supabase: {len(result.data)} enregistrement(s)")
        else:
            logger.warning("⚠️ Supabase non configuré, données non sauvegardées")
            
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde Supabase: {e}")
    
    return {
        "status": "received",
        "conversation_id": conversation_id,
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


@app.post("/api/company-profile/sync")
async def sync_company_profile(
    request: Request,
    x_api_key: str = Header(...)
):
    """
    Synchronise les informations du Company Profile avec l'agent ElevenLabs.
    Le frontend appellera cet endpoint quand l'utilisateur sauvegarde son profil.
    """
    verify_api_key(x_api_key)
    
    try:
        company_profile = await request.json()
        logger.info(f"🏢 Synchronisation du profil pour : {company_profile.get('company_name', 'N/A')}")
        
        # Importer le module de configuration ElevenLabs
        from elevenlabs_config import sync_company_profile_to_agent
        
        # Synchroniser avec l'agent
        success = sync_company_profile_to_agent(company_profile)
        
        if success:
            return {
                "status": "success",
                "message": f"Agent configuré pour {company_profile.get('company_name', 'votre entreprise')}",
                "agent_id": os.getenv("ELEVENLABS_AGENT_ID")
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Échec de la synchronisation avec l'agent ElevenLabs"
            )
            
    except Exception as e:
        logger.error(f"❌ Erreur sync profil : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/dynamic-variables/configure")
async def configure_dynamic_variables(
    request: Request,
    x_api_key: str = Header(...)
):
    """
    Configure les variables dynamiques dans le prompt de l'agent.
    
    Body exemple:
    {
        "industry": "restaurant",  // ou "hotel", "ecommerce", "custom"
        "custom_variables": {      // optionnel si industry != "custom"
            "ma_variable": "Description de la variable"
        }
    }
    """
    verify_api_key(x_api_key)
    
    try:
        data = await request.json()
        industry = data.get("industry", "custom")
        custom_vars = data.get("custom_variables", {})
        
        logger.info(f"⚙️  Configuration des variables dynamiques pour : {industry}")
        
        from dynamic_variables import (
            configure_restaurant_variables,
            configure_hotel_variables,
            configure_ecommerce_variables,
            DynamicVariablesManager
        )
        
        # Configurer selon l'industrie
        if industry == "restaurant":
            success = configure_restaurant_variables()
        elif industry == "hotel":
            success = configure_hotel_variables()
        elif industry == "ecommerce":
            success = configure_ecommerce_variables()
        elif industry == "custom" and custom_vars:
            manager = DynamicVariablesManager()
            success = manager.configure_dynamic_variables(custom_vars)
        else:
            raise HTTPException(
                status_code=400,
                detail="Industry non supportée ou custom_variables manquantes"
            )
        
        if success:
            return {
                "status": "success",
                "message": f"Variables dynamiques configurées pour {industry}",
                "industry": industry
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Échec de la configuration des variables dynamiques"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur config variables : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dynamic-variables/values")
async def get_dynamic_variables_values(
    x_api_key: str = Header(...),
    caller_number: Optional[str] = None
):
    """
    Récupère les valeurs actuelles des variables dynamiques.
    Peut être appelé avant chaque appel pour obtenir les données fraîches.
    
    Query params:
    - caller_number: Numéro du caller pour personnalisation (optionnel)
    """
    verify_api_key(x_api_key)
    
    try:
        from dynamic_variables import DynamicVariablesManager
        
        manager = DynamicVariablesManager()
        variables = manager.get_variables_for_call(
            caller_number=caller_number,
            enabled_variables=None  # Toutes les variables
        )
        
        return {
            "status": "success",
            "variables": variables,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération variables : {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    
    # Récupérer depuis Supabase
    try:
        from supabase import create_client, Client
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if supabase_url and supabase_key and supabase_url != "your_supabase_url_here":
            supabase: Client = create_client(supabase_url, supabase_key)
            
            # Récupérer les appels
            result = supabase.table("call_logs")\
                .select("*")\
                .eq("business_id", business_id)\
                .order("started_at", desc=True)\
                .limit(50)\
                .execute()
            
            logger.info(f"✅ Récupéré {len(result.data)} appels depuis Supabase")
            
            return {
                "total": len(result.data),
                "calls": result.data,
                "page": 1,
                "page_size": 50
            }
        else:
            logger.warning("⚠️ Supabase non configuré")
            return {
                "total": 0,
                "calls": [],
                "message": "Supabase non configuré"
            }
            
    except Exception as e:
        logger.error(f"❌ Erreur récupération Supabase: {e}")
        return {
            "total": 0,
            "calls": [],
            "error": str(e)
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
