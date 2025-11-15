# 🐧 Guide d'installation WSL (Windows Subsystem for Linux)

## ⚠️ Prérequis WSL

Si vous utilisez **WSL sur Windows**, suivez ces étapes avant de lancer le projet.

### 1️⃣ Installer les dépendances système

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip build-essential ffmpeg libsndfile1
```

### 2️⃣ Lancement automatique

Le script `./start.sh` est maintenant **compatible WSL** et va :
- Détecter `python3` automatiquement
- Créer un virtualenv `.venv`
- Installer les dépendances
- Lancer le serveur

**Commande unique :**
```bash
./start.sh
```

### 3️⃣ Accès depuis Windows

Une fois le serveur lancé sur WSL, vous pouvez y accéder depuis Windows :

```
http://localhost:8765
```

### 4️⃣ Utiliser ngrok avec WSL

**Option A : Installer ngrok dans WSL**
```bash
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Configurer votre token
ngrok config add-authtoken VOTRE_TOKEN

# Lancer le tunnel
ngrok http 8765
```

**Option B : Utiliser ngrok Windows**
- Téléchargez ngrok pour Windows : https://ngrok.com/download
- Lancez-le depuis PowerShell/CMD :
  ```powershell
  ngrok http 8765
  ```

### 5️⃣ Problèmes courants WSL

#### "Command 'python' not found"
✅ **Solution** : Le script utilise automatiquement `python3`

#### "externally-managed-environment"
✅ **Solution** : Le script crée automatiquement un venv

#### Port 8765 déjà utilisé
```bash
# Trouver et tuer le processus
lsof -ti:8765 | xargs kill -9

# Ou changer le port dans .env
PORT=8888
```

#### Firewall Windows bloque ngrok
- Ouvrir les paramètres Windows Defender
- Autoriser ngrok.exe dans le pare-feu

---

## 🚀 Installation complète WSL (étape par étape)

```bash
# 1. Cloner le dépôt
cd ~
git clone https://github.com/Romainmlt123/Hackathon-StationF-RomainMALLET-BaptisteSEITZ.git
cd Hackathon-StationF-RomainMALLET-BaptisteSEITZ
git checkout Romain

# 2. Installer les dépendances système
sudo apt update && sudo apt install -y python3-venv python3-pip build-essential ffmpeg libsndfile1

# 3. Configurer les clés API
cp .env.template .env
nano .env  # ou vim

# 4. Lancer le serveur (tout est automatique)
./start.sh
```

Le serveur démarre sur `http://localhost:8765` 🎉

---

## 📝 Logs et debug WSL

```bash
# Voir les logs en temps réel
tail -f server.log

# Vérifier que le serveur tourne
ps aux | grep "python.*server.py"

# Tester l'endpoint health
curl http://localhost:8765/health
```

---

## 🔄 Redémarrage rapide

```bash
# Arrêter le serveur
pkill -f "python.*server.py"

# Relancer
./start.sh
```
