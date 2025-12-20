"""
Script pour synchroniser les conversations ElevenLabs vers le backend
Ce script interroge l'API ElevenLabs toutes les 30 secondes et envoie les nouvelles conversations au backend
"""

import os
import time
import requests
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
BACKEND_URL = "http://localhost:8765/webhook/elevenlabs"
API_KEY = os.getenv("API_KEY")
AGENT_ID = "Agent-IA-Hackathon"  # Remplacez par votre agent ID si différent

# Stocker les IDs des conversations déjà synchronisées
synced_conversations = set()

def get_conversations():
    """Récupère les conversations depuis l'API ElevenLabs"""
    url = "https://api.elevenlabs.io/v1/convai/conversations"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # L'API peut retourner directement une liste ou un objet avec une clé conversations
            if isinstance(data, list):
                return data
            else:
                return data.get("conversations", [])
        else:
            logger.error(f"Erreur API ElevenLabs: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des conversations: {e}")
        return []

def get_conversation_details(conversation_id):
    """Récupère les détails d'une conversation spécifique"""
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Erreur récupération conversation {conversation_id}: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return None

def send_to_backend(conversation_data):
    """Envoie les données de conversation au backend"""
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(BACKEND_URL, json=conversation_data, headers=headers)
        if response.status_code == 200:
            logger.success(f"✅ Conversation {conversation_data.get('conversation_id')} synchronisée")
            return True
        else:
            logger.error(f"Erreur backend: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Erreur envoi backend: {e}")
        return False

def format_conversation(conv_details):
    """Formate les données ElevenLabs pour le backend"""
    # Extraire le transcript
    transcript = []
    
    # L'API retourne transcript comme liste de dict avec 'role' et 'message'
    transcript_data = conv_details.get("transcript", [])
    
    # Récupérer le timestamp de début pour calculer les timestamps absolus
    metadata = conv_details.get("metadata", {})
    start_time = metadata.get("start_time_unix_secs", 0)
    
    for msg in transcript_data:
        if isinstance(msg, dict):
            # Calculer le timestamp absolu
            time_offset = msg.get("time_in_call_secs", 0)
            timestamp = datetime.fromtimestamp(start_time + time_offset).isoformat() if start_time else datetime.now().isoformat()
            
            # S'assurer que text n'est jamais None/null
            message_text = msg.get("message")
            if message_text is None:
                message_text = ""
            
            transcript.append({
                "speaker": msg.get("role", "unknown"),  # "agent" ou "user"
                "text": str(message_text),  # Convertir explicitement en string
                "timestamp": timestamp
            })
    
    # Extraire le numéro de téléphone depuis metadata.phone_call
    phone_data = metadata.get("phone_call") or {}
    caller_number = phone_data.get("external_number") if isinstance(phone_data, dict) else None
    
    # Calculer started_at et ended_at en format ISO
    started_at = datetime.fromtimestamp(start_time).isoformat() if start_time else None
    call_duration = metadata.get("call_duration_secs", 0)
    ended_at = datetime.fromtimestamp(start_time + call_duration).isoformat() if start_time else None
    
    # Formater pour le backend
    return {
        "conversation_id": conv_details.get("conversation_id"),
        "agent_id": conv_details.get("agent_id", AGENT_ID),
        "status": conv_details.get("status", "in_progress"),  # "done" ou "in_progress"
        "started_at": started_at,
        "ended_at": ended_at,
        "transcript": transcript,
        "metadata": {
            "caller_number": caller_number,
            "duration": call_duration,
            "call_sid": phone_data.get("call_sid"),
            "direction": phone_data.get("direction")
        }
    }

def sync_loop():
    """Boucle principale de synchronisation"""
    logger.info("🚀 Démarrage de la synchronisation ElevenLabs")
    logger.info(f"📡 Backend: {BACKEND_URL}")
    logger.info(f"⏰ Intervalle: 30 secondes")
    
    while True:
        try:
            # Récupérer toutes les conversations
            conversations = get_conversations()
            logger.info(f"📞 {len(conversations)} conversations trouvées")
            
            # Traiter les nouvelles conversations
            new_count = 0
            for conv in conversations:
                # Gérer si conv est un dict ou autre type
                if isinstance(conv, dict):
                    conv_id = conv.get("conversation_id") or conv.get("id")
                else:
                    logger.warning(f"Format inattendu: {type(conv)}")
                    continue
                
                if not conv_id:
                    continue
                
                # Vérifier si déjà synchronisée
                if conv_id in synced_conversations:
                    continue
                
                # Récupérer les détails
                details = get_conversation_details(conv_id)
                if details:
                    # Formater et envoyer
                    formatted = format_conversation(details)
                    if send_to_backend(formatted):
                        synced_conversations.add(conv_id)
                        new_count += 1
            
            if new_count > 0:
                logger.success(f"✨ {new_count} nouvelles conversations synchronisées")
            
            # Attendre 30 secondes
            time.sleep(30)
            
        except KeyboardInterrupt:
            logger.info("🛑 Arrêt de la synchronisation")
            break
        except Exception as e:
            logger.error(f"❌ Erreur dans la boucle: {e}")
            time.sleep(30)

if __name__ == "__main__":
    if not ELEVENLABS_API_KEY:
        logger.error("❌ ELEVENLABS_API_KEY non configurée dans .env")
        exit(1)
    
    sync_loop()
