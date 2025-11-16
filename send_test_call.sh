#!/bin/bash
# Script pour envoyer un appel de test au dashboard

TIMESTAMP=$(date +%s)

curl -X POST http://localhost:8765/webhook/elevenlabs \
  -H "X-API-Key: hSar6wEenqfJGb_RwrfDu3b5S1VWBqSpxj5xWCnR9KY" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id":"call-'$TIMESTAMP'",
    "agent_id":"Agent-IA-Hackathon",
    "status":"completed",
    "started_at":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "ended_at":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "transcript":[
      {"speaker":"assistant","text":"Bonjour, merci d'\''avoir appelé. Comment puis-je vous aider ?","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"},
      {"speaker":"user","text":"Bonjour, je souhaite des informations sur vos services.","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"},
      {"speaker":"assistant","text":"Bien sûr ! Nous proposons plusieurs services. Pourriez-vous préciser ce qui vous intéresse ?","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"},
      {"speaker":"user","text":"Je suis intéressé par votre solution d'\''accueil téléphonique.","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"},
      {"speaker":"assistant","text":"Excellent choix ! Notre solution permet d'\''automatiser votre accueil avec une IA conversationnelle. Je vous envoie la documentation par email.","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}
    ],
    "metadata":{"caller_number":"+33612345678","duration":185}
  }'

echo ""
echo "✅ Appel de test envoyé avec succès !"
