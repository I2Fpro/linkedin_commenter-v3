# LinkedIn AI Commenter - Setup Dev Local (Clef en main)

Guide complet pour lancer le projet en local sur un nouveau PC.

---

## Prerequis a installer

| Logiciel | Installation | Verification |
|----------|-------------|-------------|
| **Docker Desktop** | [docker.com/download](https://www.docker.com/products/docker-desktop/) | `docker --version` |
| **Git** | [git-scm.com](https://git-scm.com/) | `git --version` |
| **Git Bash** | Inclus avec Git for Windows | Chercher "Git Bash" dans le menu demarrer |
| **mkcert** | `choco install mkcert` ou `scoop install mkcert` | `mkcert --version` |
| **Chrome** | [chrome.com](https://www.google.com/chrome/) | - |
| **Python 3.11+** | [python.org](https://www.python.org/) (optionnel, pour generer les cles) | `python --version` |

### Comptes et cles API necessaires

| Service | Ce qu'il faut | Ou le trouver |
|---------|---------------|---------------|
| **OpenAI** | Cle API (`sk-...`) | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| **Google Cloud** | 2 clients OAuth (Extension Chrome + Application Web) | [console.cloud.google.com](https://console.cloud.google.com/) → APIs & Services → Credentials |
| **Stripe** | Cle test (`sk_test_...`), webhook secret, price IDs | [dashboard.stripe.com/test/apikeys](https://dashboard.stripe.com/test/apikeys) |

---

## Etape 1 : Cloner le repo

```bash
git clone <URL_DU_REPO>
cd linkedin_commenter-v3/GIT
```

### 1.1 Activer le pre-commit hook

```bash
git config core.hooksPath hooks
```

Ce hook bloque automatiquement tout commit contenant des URLs `*.local.dev` dans les fichiers front-end. Il t'oblige a repasser en mode PLACEHOLDER avant de committer.

> **Contourner ponctuellement** (si tu sais ce que tu fais) : `git commit --no-verify`

---

## Etape 2 : Setup Traefik local

Traefik sert de reverse proxy local avec HTTPS, comme en production.

### 2.1 Creer le dossier Traefik

```bash
mkdir -p D:/DEV/traefik/certs
```

> Le dossier `D:\DEV\traefik\` contient deja les fichiers `traefik.yml` et `docker-compose.yml` si tu as suivi le setup initial.

### 2.2 Installer le CA mkcert

```bash
mkcert -install
```

Cela installe le certificat racine dans le trust store Windows et Chrome. Les navigateurs feront confiance aux certificats generes par mkcert.

### 2.3 Generer les certificats SSL

```bash
cd D:/DEV/traefik/certs
mkcert -cert-file local.crt -key-file local.key "*.local.dev" "local.dev"
```

Resultat : `local.crt` et `local.key` dans `D:\DEV\traefik\certs\`.
Validite : 3 ans.

### 2.4 Creer le reseau Docker `proxy`

```bash
docker network create proxy
```

> Si le reseau existe deja, cette commande affichera une erreur (ignorable).

### 2.5 Lancer Traefik

```bash
cd D:/DEV/traefik
docker compose up -d
```

Verification :
```bash
docker ps | grep traefik
# Doit afficher le container en status "Up"
```

Dashboard Traefik : [http://localhost:8080](http://localhost:8080)

---

## Etape 3 : Fichier hosts Windows

Ouvrir un **terminal admin** (PowerShell ou CMD en tant qu'administrateur) et executer :

```powershell
Add-Content -Path "C:\Windows\System32\drivers\etc\hosts" -Value "`n# LinkedIn AI Commenter - Local Dev`n127.0.0.1 ai.local.dev`n127.0.0.1 users.local.dev`n127.0.0.1 site.local.dev"
```

Ou ajouter manuellement ces lignes a `C:\Windows\System32\drivers\etc\hosts` :

```
# LinkedIn AI Commenter - Local Dev
127.0.0.1 ai.local.dev
127.0.0.1 users.local.dev
127.0.0.1 site.local.dev
```

Verification :
```bash
ping ai.local.dev
# Doit repondre depuis 127.0.0.1
```

---

## Etape 4 : Configurer les variables d'environnement

### 4.1 Copier le template

```bash
cd GIT/BACK-END
cp .env.local.template .env.local
```

### 4.2 Generer les cles de securite

```bash
# JWT Secret (32+ caracteres)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Encryption Key (Fernet)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

> Si `cryptography` n'est pas installe : `pip install cryptography`

### 4.3 Remplir `.env.local`

Ouvrir `BACK-END/.env.local` et remplacer toutes les valeurs `CHANGE_ME_*` :

| Variable | Ou la trouver |
|----------|--------------|
| `JWT_SECRET` | Genere ci-dessus |
| `ENCRYPTION_KEY` | Genere ci-dessus |
| `GOOGLE_CLIENT_ID` | Google Cloud Console → Client OAuth "Extension Chrome" |
| `GOOGLE_CLIENT_ID_WEB` | Google Cloud Console → Client OAuth "Application Web" |
| `OPENAI_API_KEY` | OpenAI Dashboard |
| `STRIPE_SECRET_KEY` | Stripe Dashboard (mode test) |
| `STRIPE_WEBHOOK_SECRET` | Stripe Dashboard → Webhooks |
| `STRIPE_PRICE_MEDIUM_MONTHLY` | Stripe Dashboard → Products → Price ID |
| `STRIPE_PRICE_PREMIUM_MONTHLY` | Stripe Dashboard → Products → Price ID |

---

## Etape 5 : Lancer le backend

```bash
cd GIT/BACK-END
docker compose -f docker-compose.dev.yml --env-file .env.local up --build
```

Premier lancement : les images Docker sont buildees (peut prendre quelques minutes).
Lancements suivants : retirer `--build` pour aller plus vite.

### Ordre de demarrage automatique

```
postgres (pg_isready) → redis (redis-cli ping) → user-service (/health) → ai-service (/health)
site-internet (independant)
```

### Verification

```bash
curl https://ai.local.dev/health
# → {"status": "healthy"}

curl https://users.local.dev/health
# → {"status": "healthy"}

curl https://ai.local.dev/config/complete
# → JSON de configuration complete
```

---

## Etape 6 : Configurer l'extension Chrome

### 6.1 Activer le mode DEV (placeholders -> URLs locales)

Ouvrir **Git Bash** et executer :

```bash
cd linkedin_commenter-v3/GIT
bash scripts/toggle-env.sh dev
```

Le script remplace les 20 placeholders `__VAR__` par les URLs locales dans 8 fichiers front-end.

> **Voir aussi :** [Basculer entre modes DEV et PLACEHOLDER](#basculer-entre-modes-dev-et-placeholder)

### 6.2 Charger l'extension dans Chrome

1. Ouvrir `chrome://extensions/`
2. Activer le **Mode developpeur** (toggle en haut a droite)
3. Cliquer **"Charger l'extension non empaquetee"**
4. Selectionner le dossier `GIT/FRONT-END/`
5. **Noter l'Extension ID** affiche (ex: `abcdefghijklmnopqrstuvwxyz`)

### 6.3 Configurer Google OAuth

Dans [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials :

1. **Client OAuth "Extension Chrome"** :
   - Type : Application Chrome
   - Application ID : coller l'Extension ID note ci-dessus
   - Le Client ID de ce client = `GOOGLE_CLIENT_ID` dans `.env.local`

2. **Client OAuth "Application Web"** :
   - Type : Application Web
   - Origines autorisees : `https://ai.local.dev`, `https://users.local.dev`
   - Le Client ID de ce client = `GOOGLE_CLIENT_ID_WEB` dans `.env.local`

> **Important** : Toujours charger l'extension depuis le **meme dossier** pour que l'Extension ID reste stable.

---

## Etape 7 : Verification end-to-end

1. Backend demarre sans erreur → `docker compose logs -f`
2. `curl https://ai.local.dev/health` → `{"status": "healthy"}`
3. `curl https://users.local.dev/health` → `{"status": "healthy"}`
4. Extension visible dans `chrome://extensions/` avec status "Active"
5. Se connecter via Google OAuth dans le popup de l'extension
6. Aller sur [linkedin.com](https://www.linkedin.com)
7. Boutons de generation visibles sous les posts
8. Generer un commentaire → reponse AI affichee

---

## Commandes utiles

```bash
# Voir les logs de tous les services
cd GIT/BACK-END
docker compose -f docker-compose.dev.yml logs -f

# Logs d'un seul service
docker compose -f docker-compose.dev.yml logs -f ai-service
docker compose -f docker-compose.dev.yml logs -f user-service

# Redemarrer un service
docker compose -f docker-compose.dev.yml restart user-service

# Arreter tout
docker compose -f docker-compose.dev.yml down

# Arreter et supprimer les volumes (reset DB)
docker compose -f docker-compose.dev.yml down -v

# Rebuild un seul service
docker compose -f docker-compose.dev.yml up --build ai-service

# Acces direct a la DB
psql postgresql://linkedin_user:dev_password_local@localhost:5432/linkedin_ai_db

# Acces Redis
redis-cli -h localhost -p 6379
```

---

## Troubleshooting

### Traefik Exit code 127
**Cause :** `traefik.yml` est un dossier au lieu d'un fichier.
**Fix :** Supprimer le dossier et recreer le fichier :
```bash
rmdir D:\DEV\traefik\traefik.yml
# Puis recreer le fichier traefik.yml (voir Etape 2)
```

### OAuth "bad client id" ou "Authorization Error"
**Cause :** L'Extension ID dans Google Cloud Console ne correspond pas a l'extension chargee.
**Fix :** Verifier que l'Application ID dans le client OAuth Chrome correspond a l'ID visible dans `chrome://extensions/`.

### CORS errors dans la console Chrome
**Cause :** `ALLOWED_ORIGINS` dans `.env.local` ne contient pas la bonne origine.
**Fix :** Verifier que `ALLOWED_ORIGINS` contient `chrome-extension://*` et les URLs `*.local.dev`.

### Certificat non reconnu / NET::ERR_CERT_AUTHORITY_INVALID
**Cause :** Le CA mkcert n'est pas dans le trust store.
**Fix :** Relancer `mkcert -install` et redemarrer Chrome.

### Port already in use
**Cause :** Un autre service utilise le port 5432, 6379, 8443 ou 8444.
**Fix :** `netstat -ano | findstr :5432` pour identifier le process, puis le stopper.

### Les services ne demarrent pas (depends_on timeout)
**Cause :** PostgreSQL ou Redis n'est pas healthy.
**Fix :** Verifier les logs : `docker compose -f docker-compose.dev.yml logs postgres`

### apply-env.sh ne fonctionne pas
**Cause :** Le script utilise `declare -A` (bash 4+), incompatible avec CMD/PowerShell.
**Fix :** Utiliser **Git Bash** ou **WSL** pour executer le script.

### Revenir aux placeholders avant un commit
```bash
cd GIT
bash scripts/toggle-env.sh placeholder
```

---

## Basculer entre modes DEV et PLACEHOLDER

Le script `scripts/toggle-env.sh` permet de basculer instantanement l'extension entre les deux modes :

```bash
# Voir le mode actuel
bash scripts/toggle-env.sh status

# Activer le mode DEV (URLs locales)
bash scripts/toggle-env.sh dev

# Restaurer les placeholders (pour commit / CI)
bash scripts/toggle-env.sh placeholder
```

| Mode | Fichiers contiennent | Quand l'utiliser |
|------|---------------------|-----------------|
| **DEV** | `https://ai.local.dev`, `https://users.local.dev`, etc. | Developpement local |
| **PLACEHOLDER** | `__AI_API_URL__`, `__USERS_API_URL__`, etc. | Avant un commit / push |

Le script traite 8 fichiers et 20 remplacements (4 placeholders x occurrences multiples).

> **Rappel :** Toujours repasser en mode PLACEHOLDER avant de committer pour ne pas polluer le repo avec des URLs locales.
