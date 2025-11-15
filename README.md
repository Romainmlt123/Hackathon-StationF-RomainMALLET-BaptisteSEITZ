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

```
Appel Twilio → WebSocket
    ↓
[ElevenLabs STT] → Transcription
    ↓
[Mistral LLM] → Génération réponse
    ↓
[ElevenLabs TTS] → Synthèse vocale
    ↓
Audio → Appelant
```

**Technologies :**
- **Pipecat** : Framework de pipeline audio temps réel
- **FastAPI** : Transport WebSocket pour Twilio
- **Mistral API** : LLM français performant
- **ElevenLabs** : STT + TTS ultra-réaliste

---

## 📦 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/Romainmlt123/Hackathon-StationF-RomainMALLET-BaptisteSEITZ.git
cd Hackathon-StationF-RomainMALLET-BaptisteSEITZ
git checkout Romain
```

### 2. Créer un environnement virtuel

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer les clés API

```bash
cp .env.template .env
```

Éditez `.env` et ajoutez vos clés :

```env
MISTRAL_API_KEY=your_mistral_key
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=your_voice_id
```

---

## 🚀 Lancement

### Mode local (développement)

```bash
./start.sh
```

Ou directement avec Python :

```bash
python -m app.main --transport twilio --port 8765
```

### Avec ngrok (pour tester avec Twilio)

1. **Installez [ngrok](https://ngrok.com/)**
   ```bash
   # Ubuntu/Debian
   curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
   echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
   sudo apt update && sudo apt install ngrok
   
   # Ou téléchargez depuis https://ngrok.com/download
   ```

2. **Authentifiez-vous**
   ```bash
   ngrok config add-authtoken VOTRE_TOKEN_NGROK
   ```

3. **Lancez le serveur**
   ```bash
   ./start.sh
   ```

4. **Dans un autre terminal, lancez ngrok**
   ```bash
   ngrok http 8765
   ```
   
   Copiez l'URL affichée (ex: `https://abc123.ngrok-free.app`)

5. **Configurez Twilio Console**
   - Allez sur https://console.twilio.com/
   - **Phone Numbers → Manage → Active Numbers**
   - Cliquez sur votre numéro
   - Section **Voice Configuration** :
     - **A CALL COMES IN** → Webhook
     - URL : `https://abc123.ngrok-free.app/incoming-call`
     - Method : **HTTP POST**
   - Cliquez **Save**

6. **Appelez votre numéro Twilio** 📞
   - L'agent IA va répondre automatiquement !
   - Vous pouvez converser en temps réel

### Avec Docker

```bash
docker build -t voice-agent .
docker run -p 8765:8765 --env-file .env voice-agent
```

---

## 📁 Structure du projet

```
Hackathon-StationF-RomainMALLET-BaptisteSEITZ/
├── app/
│   ├── __init__.py
│   ├── main.py          # Point d'entrée principal (pipeline Pipecat)
│   └── config.py        # Configuration centralisée (pydantic)
├── .env.template        # Template de configuration
├── requirements.txt     # Dépendances Python
├── start.sh             # Script de démarrage
├── Dockerfile           # Image Docker
└── README.md            # Ce fichier
```

---

## 🔧 Configuration avancée

### Personnaliser le prompt système

Éditez `SYSTEM_PROMPT` dans `.env` :

```env
SYSTEM_PROMPT=Tu es Marie, assistante virtuelle de l'entreprise XYZ. Tu dois...
```

### Changer la voix ElevenLabs

1. Allez sur [ElevenLabs Voice Lab](https://elevenlabs.io/app/voice-lab)
2. Choisissez ou clonez une voix
3. Copiez le `voice_id`
4. Mettez-le dans `ELEVENLABS_VOICE_ID`

### Utiliser un autre LLM

Modifiez `app/main.py` ligne 75 :

```python
llm = MistralLLMService(
    api_key=os.getenv("MISTRAL_API_KEY"),
    model="mistral-large-latest",  # ou mistral-medium-latest
)
```

---

## 🧪 Tests

### Tester localement sans Twilio

```bash
python -m app.main --transport daily --room-url <DAILY_ROOM_URL>
```

### Tester avec Twilio (appel réel)

1. **Achetez un numéro Twilio** (si pas déjà fait)
   - https://console.twilio.com/us1/develop/phone-numbers/manage/search

2. **Lancez le serveur + ngrok**
   ```bash
   # Terminal 1
   ./start.sh
   
   # Terminal 2
   ngrok http 8765
   ```

3. **Configurez le webhook Twilio**
   - URL : `https://votre-url-ngrok.ngrok-free.app/incoming-call`
   - Method : POST

4. **Appelez votre numéro Twilio** 📱
   - L'agent IA répond en français
   - Conversation en temps réel < 1 seconde de latence
   
5. **Vérifiez les logs**
   ```bash
   # Vous devriez voir :
   # 📞 Incoming call: +33612345678 → +33987654321
   # 🔌 WebSocket connected: CA1234567890abcdef
   # 🎙️ [STT] Bonjour, comment allez-vous ?
   # 🤖 [LLM] Je vais très bien, merci ! Comment puis-je vous aider ?
   # 🔊 [TTS] Streaming audio...
   ```

---

## 📊 Logs et debug

Les logs sont gérés par `loguru`. Niveau configurable via `.env` :

```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

---

## 🚧 Roadmap / TODO

- [ ] Ajouter support multi-langue (détection automatique)
- [ ] Intégrer base de données (historique des appels)
- [ ] Dashboard admin (Next.js)
- [ ] Déploiement Cloud Run / Render
- [ ] Webhooks pour notifier fin d'appel
- [ ] Support fonction calling (réservation, prise de RDV)

---

## 🤝 Contribution

Projet réalisé dans le cadre du **Pioneers AI Lab Hackathon @ Station F**.

**Équipe :**
- Romain MALLET
- Baptiste SEITZ

---

## 📄 Licence

MIT License

---

## 📚 Ressources

- [Documentation Pipecat](https://docs.pipecat.ai/)
- [Mistral API](https://docs.mistral.ai/)
- [ElevenLabs API](https://docs.elevenlabs.io/)
- [Twilio Docs](https://www.twilio.com/docs)
