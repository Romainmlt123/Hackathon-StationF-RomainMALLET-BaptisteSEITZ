"""Script de test pour voir le format de l'API ElevenLabs"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Récupérer la liste des conversations
print("=" * 80)
print("LISTE DES CONVERSATIONS")
print("=" * 80)
url = "https://api.elevenlabs.io/v1/convai/conversations"
headers = {"xi-api-key": ELEVENLABS_API_KEY}
response = requests.get(url, headers=headers)
conversations = response.json()

print(f"\nFormat de la réponse: {type(conversations)}")
if isinstance(conversations, list):
    print(f"Nombre de conversations: {len(conversations)}")
    if len(conversations) > 0:
        print(f"\nPremière conversation (résumé):")
        first_conv = conversations[0]
        print(json.dumps(first_conv, indent=2))
        conv_id = first_conv.get("conversation_id") or first_conv.get("id")
else:
    print(json.dumps(conversations, indent=2)[:500])
    if "conversations" in conversations:
        conv_id = conversations["conversations"][0].get("conversation_id") or conversations["conversations"][0].get("id")

# Récupérer les détails d'une conversation
print("\n" + "=" * 80)
print(f"DÉTAILS DE LA CONVERSATION: {conv_id}")
print("=" * 80)
detail_url = f"https://api.elevenlabs.io/v1/convai/conversations/{conv_id}"
detail_response = requests.get(detail_url, headers=headers)
details = detail_response.json()

print(json.dumps(details, indent=2))
