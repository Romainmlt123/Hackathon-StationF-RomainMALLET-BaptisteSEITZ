# 🎙️ Realtime Voice Agent — Hackathon Station F

> **Agent vocal IA temps réel** pour appels entrants Twilio  
> Pipeline: **ElevenLabs STT → Mistral LLM → ElevenLabs TTS**  
> Basé sur [Pipecat](https://github.com/pipecat-ai/pipecat)

---

## 🎯 Objectif

Créer un SaaS de téléphonie IA capable de :
- Recevoir des appels téléphoniques via **Twilio**
- Transcrire la voix en temps réel (**ElevenLabs STT**)
- Générer des réponses intelligentes (**Mistral LLM**)
- Renvoyer une voix synthétique naturelle (**ElevenLabs TTS**)

Chaque appel = une session indépendante avec contexte conversationnel.

---

## 🏗️ Architecture

# Hackathon — Voice Agent (ElevenLabs Agent + Backend + Frontend)

Ce dépôt contient une version simplifiée du projet de l'agent vocal :

 - Un backend FastAPI léger qui reçoit les webhooks d'ElevenLabs (agent)
 - Un frontend (dashboard) dans `frontend/lovable-ai-dashboard` pour afficher les appels
 - Le schéma SQL pour Supabase dans `backend/schema.sql`

Le but ici est d'utiliser l'agent ElevenLabs (conversational AI) pour gérer
STT/LLM/TTS, et d'enregistrer les conversations via un webhook sur le
backend. Plus besoin de Pipecat pour cette architecture.

## Quickstart (local)

Prérequis : Python 3.11+, Node.js (pour le frontend), ngrok (ou tunnel public)

1) Créez et activez un virtualenv

```bash
python -m venv .venv
source .venv/bin/activate
```

2) Installez les dépendances du backend

```bash
pip install -r backend/requirements.txt
```

3) Configurez les variables d'environnement

```bash
cp .env.template .env
# Éditez .env et remplissez au minimum :
# ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, API_KEY
```

4) Démarrez le backend

```bash
python backend/simple_server.py
```

Vous verrez le backend démarrer sur `http://localhost:8765`.

5) Exposez le backend publiquement (ngrok)

```bash
 # Authentifiez ngrok une seule fois (remplacez TOKEN)
 ngrok config add-authtoken YOUR_NGROK_TOKEN

 # Lancez le tunnel
 ngrok http 8765
```

Copiez l'URL HTTPS fournie par ngrok (ex: `https://abc123.ngrok-free.dev`).

6) Configurez l'agent ElevenLabs

 - Dans ElevenLabs Platform → Agents → Outils (Add webhook)
 - Méthode : POST
 - URL : `https://<YOUR_NGROK_URL>/webhook/elevenlabs`
 - Headers :
   - `X-API-Key: <API_KEY>`  (valeur = `API_KEY` dans votre `.env`)

ElevenLabs enverra les événements de conversation à ce webhook. Le
backend affichera les logs et (optionnellement) vous pourrez enregistrer
les appels dans Supabase.

## Frontend (dashboard)

Le frontend est situé dans `frontend/lovable-ai-dashboard`.

1) Installez Node.js (v16+ / 18+ recommandé)
2) Installez les dépendances et lancez le dev server

```bash
cd frontend/lovable-ai-dashboard
npm install
npm run dev
```

Par défaut le frontend attendra une API à `http://localhost:8765` —
configurez `VITE_API_URL` et `VITE_API_KEY` si nécessaire (voir le dossier
frontend pour `.env` ou `vite` instructions).

## Supabase

Le schéma SQL est dans `backend/schema.sql`. Exécutez-le dans l'éditeur
SQL de votre projet Supabase pour créer la table `call_logs`.

## Tester manuellement le webhook

Vous pouvez tester la réception côté backend avec curl :

```bash
curl -X POST https://<YOUR_NGROK_URL>/webhook/elevenlabs \
  -H "X-API-Key: <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"test","agent_id":"agent-1","status":"completed","transcript":[]}'
```

Le backend répondra par `{ "status": "received" }` et écrira le log.

## Rendre le dépôt propre

Ce README remplace la documentation dispersée. Si vous voulez, je peux
supprimer les anciens fichiers de documentation (`backend/README.md`,
`SETUP_BACKEND.md`, `BACKEND_SUMMARY.md`) pour ne garder qu'un seul
documentation source — confirmez si vous voulez que je les supprime.

## Points importants

 - Clé API : `X-API-Key` est utilisée pour authentifier les webhooks. Mettez
   une valeur forte dans `.env` (API_KEY).
 - Si vous préférez utiliser Twilio pour recevoir des appels, on peut
   connecter Twilio au webhook ElevenLabs (ou directement au backend) —
   dites-moi et j'adapte la doc.

---

Si vous voulez que j'efface les autres fichiers docs maintenant, dites
"Supprime les anciens docs" et je m'en occupe.
