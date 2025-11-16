"""
Script pour créer un appel de test avec une réservation
"""
import requests
import json
from datetime import datetime, timedelta

# Configuration
BACKEND_URL = "http://localhost:8765/webhook/elevenlabs"
API_KEY = "hSar6wEenqfJGb_RwrfDu3b5S1VWBqSpxj5xWCnR9KY"

# Créer un timestamp pour "il y a 2 jours"
two_days_ago = datetime.now() - timedelta(days=2)
call_start = two_days_ago
call_end = call_start + timedelta(minutes=3, seconds=45)

# Données de l'appel - Réservation pour 4 personnes
call_data = {
    "conversation_id": f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}",
    "agent_id": "agent_6301ka40ge0dfyrbx84ebjpg898k",
    "status": "done",
    "started_at": call_start.isoformat(),
    "ended_at": call_end.isoformat(),
    "transcript": [
        {
            "speaker": "agent",
            "text": "Good evening and welcome to The Ritz Paris. This is Sophie speaking. How may I assist you this evening?",
            "timestamp": call_start.isoformat()
        },
        {
            "speaker": "user",
            "text": "Hello Sophie, I would like to make a reservation for dinner please.",
            "timestamp": (call_start + timedelta(seconds=8)).isoformat()
        },
        {
            "speaker": "agent",
            "text": "Of course, I would be delighted to assist you with your reservation. For which date would you like to book, and how many guests will be joining you?",
            "timestamp": (call_start + timedelta(seconds=15)).isoformat()
        },
        {
            "speaker": "user",
            "text": "I need a table for 4 people for tomorrow evening at 8:30 PM if possible.",
            "timestamp": (call_start + timedelta(seconds=28)).isoformat()
        },
        {
            "speaker": "agent",
            "text": "Perfect! A table for four guests tomorrow evening at eight thirty. Let me check our availability at L'Espadon, our signature restaurant. May I have your name for the reservation?",
            "timestamp": (call_start + timedelta(seconds=38)).isoformat()
        },
        {
            "speaker": "user",
            "text": "Yes, it's Marie Dubois. D-U-B-O-I-S.",
            "timestamp": (call_start + timedelta(seconds=52)).isoformat()
        },
        {
            "speaker": "agent",
            "text": "Thank you, Madame Dubois. I have excellent news - we have availability for four guests tomorrow evening at eight thirty at L'Espadon. Would you prefer a table near the window or in our main dining area?",
            "timestamp": (call_start + timedelta(seconds=62)).isoformat()
        },
        {
            "speaker": "user",
            "text": "Near the window would be wonderful, thank you!",
            "timestamp": (call_start + timedelta(seconds=78)).isoformat()
        },
        {
            "speaker": "agent",
            "text": "Excellent choice! I've reserved a window table for you. May I have a contact number in case we need to reach you regarding your reservation?",
            "timestamp": (call_start + timedelta(seconds=85)).isoformat()
        },
        {
            "speaker": "user",
            "text": "Yes of course, it's 06 45 78 92 31.",
            "timestamp": (call_start + timedelta(seconds=98)).isoformat()
        },
        {
            "speaker": "agent",
            "text": "Perfect, Madame Dubois. Your reservation is confirmed for four guests tomorrow evening at eight thirty PM at L'Espadon, window table. We will contact you at zero six four five seven eight nine two three one if needed. Do you have any dietary restrictions or special requests we should be aware of?",
            "timestamp": (call_start + timedelta(seconds=107)).isoformat()
        },
        {
            "speaker": "user",
            "text": "One of my guests is vegetarian, if that's possible to note.",
            "timestamp": (call_start + timedelta(seconds=130)).isoformat()
        },
        {
            "speaker": "agent",
            "text": "Absolutely, I have noted that one guest requires vegetarian options. Our chef will be delighted to prepare a special vegetarian menu. Is there anything else I can assist you with today?",
            "timestamp": (call_start + timedelta(seconds=138)).isoformat()
        },
        {
            "speaker": "user",
            "text": "No that's perfect, thank you so much Sophie!",
            "timestamp": (call_start + timedelta(seconds=155)).isoformat()
        },
        {
            "speaker": "agent",
            "text": "You're very welcome, Madame Dubois! We look forward to welcoming you and your guests tomorrow evening. Have a wonderful day!",
            "timestamp": (call_start + timedelta(seconds=161)).isoformat()
        },
        {
            "speaker": "user",
            "text": "Thank you, goodbye!",
            "timestamp": (call_start + timedelta(seconds=172)).isoformat()
        }
    ],
    "metadata": {
        "caller_number": "+33645789231",
        "duration": 225,  # 3 minutes 45 secondes
        "call_sid": "CAb22fa80ca56d3bdc2e9992488ed3425c",
        "direction": "inbound"
    }
}

print("📞 Création d'un appel de test avec réservation...")
print(f"� Numéro: {call_data['metadata']['caller_number']}")
print(f"👥 Réservation: 4 personnes à 8:30 PM")
print(f"📅 Date: {call_start.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"💬 Messages: {len(call_data['transcript'])}")

# Envoyer au backend
headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

response = requests.post(BACKEND_URL, json=call_data, headers=headers)

if response.status_code == 200:
    print("✅ Appel créé avec succès!")
    print(f"Response: {response.json()}")
else:
    print(f"❌ Erreur: {response.status_code}")
    print(f"Response: {response.text}")
