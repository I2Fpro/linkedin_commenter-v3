# LinkedIn AI Commenter - CI/CD Pipeline & Deployment Guide

## Architecture Overview

### Project Structure

```
GIT/
├── .github/workflows/          # CI/CD GitHub Actions
│   ├── cd-preprod.yml          # Auto-deploy on push to main
│   ├── cd-prod.yml             # Auto-deploy on tag v*.*.*
│   └── deploy-manual.yml       # Manual deploy (preprod or prod)
├── BACK-END/
│   ├── ai-service/             # FastAPI - AI comment generation (port 8443)
│   ├── user-service/           # FastAPI - Auth, users, Stripe (port 8444)
│   ├── database/               # PostgreSQL + migrations
│   └── docker-compose.yml      # Docker Compose for VPS deployment
├── FRONT-END/                  # Chrome Extension (Manifest V3)
├── SITE-INTERNET/              # Landing page + account management (Nginx)
├── MONITORING/                 # Health check & usage scripts
└── scripts/
    └── apply-env.sh            # Placeholder replacement script
```

### Services & Ports

| Service | Container | Port interne | Technologie |
|---------|-----------|-------------|-------------|
| AI Service | `linkedin_ai_service` | 8443 | Python/FastAPI/Uvicorn |
| User Service | `linkedin_ai_user_service` | 8444 | Python/FastAPI/Uvicorn |
| PostgreSQL | `linkedin_ai_postgres` | 5432 | PostgreSQL + pgvector |
| Redis | `linkedin_ai_redis` | 6379 | Redis 7 Alpine |
| Website | `linkedin_ai_website` | 80 | Nginx |

### Networking

- **Traefik** (reverse proxy externe, réseau `proxy`) gère le SSL (Let's Encrypt) et le routage par hostname
- Les services ne sont **pas exposés directement** sur le VPS (pas de `ports:`, uniquement `expose:`)
- Communication inter-services via le réseau Docker `linkedin_ai_network`

---

## Environments

### URLs par environnement

| | Preprod | Prod |
|--|---------|------|
| **Site** | `https://ai-linkedin.iry-entreprise.fr` | `https://linkedinaicommenter.com` |
| **Users API** | `https://users.api.ai-linkedin.iry-entreprise.fr` | `https://users.api.linkedinaicommenter.com` |
| **AI API** | `https://ai.api.ai-linkedin.iry-entreprise.fr` | `https://ai.api.linkedinaicommenter.com` |

### Secrets GitHub (par environnement)

Les secrets suivent la convention `SECRET_NAME_PREPROD` / `SECRET_NAME_PROD` :

| Secret | Description |
|--------|-------------|
| `SSH_HOST_PREPROD` / `SSH_HOST_PROD` | IP du VPS |
| `SSH_PRIVATE_KEY_PREPROD` / `SSH_PRIVATE_KEY_PROD` | Clé SSH pour déploiement |
| `SSH_USER` | Utilisateur SSH (commun) |
| `AI_API_URL_PREPROD` / `AI_API_URL_PROD` | URL de l'API AI |
| `USERS_API_URL_PREPROD` / `USERS_API_URL_PROD` | URL de l'API Users |
| `SITE_URL_PREPROD` / `SITE_URL_PROD` | URL du site |
| `GOOGLE_CLIENT_ID_PREPROD` / `GOOGLE_CLIENT_ID_PROD` | OAuth Client ID (type Extension Chrome) |
| `GOOGLE_CLIENT_ID_WEB_PREPROD` / `GOOGLE_CLIENT_ID_WEB_PROD` | OAuth Client ID (type Application Web) |
| `STRIPE_SECRET_KEY_PREPROD` / `STRIPE_SECRET_KEY_PROD` | Clé secrète Stripe |
| `STRIPE_WEBHOOK_SECRET_PREPROD` / `STRIPE_WEBHOOK_SECRET_PROD` | Webhook secret Stripe |
| `STRIPE_PRICE_MEDIUM_MONTHLY` | Price ID Stripe plan Medium |
| `STRIPE_PRICE_PREMIUM_MONTHLY` | Price ID Stripe plan Premium |
| `POSTGRES_PASSWORD` | Mot de passe PostgreSQL |
| `JWT_SECRET` | Secret pour tokens JWT |
| `ENCRYPTION_KEY` | Clé de chiffrement des données sensibles |
| `OPENAI_API_KEY` | Clé API OpenAI |
| `GHCR_PAT` | Personal Access Token pour GHCR |
| `CHROME_EXTENSION_ID_PREPROD` / `CHROME_EXTENSION_ID_PROD` | Extension ID Chrome Web Store |
| `CHROME_CLIENT_ID` | Client ID pour Chrome Web Store API |
| `CHROME_CLIENT_SECRET` | Client Secret pour Chrome Web Store API |
| `CHROME_REFRESH_TOKEN` | Refresh token pour Chrome Web Store API |

---

## Workflows CI/CD

### 1. CD Preprod (`cd-preprod.yml`)

**Trigger :** Push sur la branche `main`

**Ce qu'il fait :**
1. **Build backend** : Build les 4 images Docker (ai-service, user-service, website, postgres) et push vers GHCR avec tags `preprod` et `SHA`
2. **Deploy VPS** : SSH sur le VPS preprod, crée le `.env`, pull les images, `docker compose up -d`
3. **Build extension** : Applique les variables d'env, package en ZIP, upload sur Chrome Web Store (sans publier, `continue-on-error: true`)
4. **Summary** : Affiche le résumé dans GitHub Actions

**Particularités :**
- Chrome Web Store upload peut échouer (normal en preprod, pas de publish)
- L'artifact de l'extension est disponible pendant 30 jours

### 2. CD Prod (`cd-prod.yml`)

**Trigger :** Push d'un tag `v*.*.*` (ex: `v10.0.5`)

**Ce qu'il fait :**
1. **Build backend** : Build les 4 images Docker et push vers GHCR avec tags `prod`, `VERSION` et `latest`
2. **Deploy VPS** : SSH sur le VPS prod, crée le `.env`, pull les images, `docker compose up -d`
3. **Build extension** : Package et **publie** sur Chrome Web Store (`publish: true`)
4. **GitHub Release** : Crée une release avec le ZIP de l'extension et release notes auto-générées

**Particularités :**
- La version du manifest est mise à jour automatiquement depuis le tag via `jq`
- L'artifact est conservé 90 jours

### 3. Deploy Manual (`deploy-manual.yml`)

**Trigger :** Manuel via GitHub Actions (workflow_dispatch)

**Paramètres :**
| Paramètre | Options | Description |
|-----------|---------|-------------|
| `environment` | `preprod` / `prod` | Environnement cible |
| `version` | string (défaut: `main`) | Branche, tag ou SHA à déployer |
| `deploy_backend` | boolean | Déployer les services backend |
| `deploy_extension` | boolean | Déployer l'extension Chrome |

**Usage :** Redéployer sans pusher de code, ou déployer une version spécifique.

---

## Comment déployer

### Deployer en Preprod

```bash
# Modifier le code, puis :
git add .
git commit -m "Description des changements"
git push origin main
```

Le workflow `cd-preprod.yml` se déclenche automatiquement.

### Deployer en Prod

```bash
# 1. S'assurer que les changements sont sur main
git push origin main

# 2. Créer et pusher un tag
git tag v10.0.X
git push origin v10.0.X
```

Le workflow `cd-prod.yml` se déclenche automatiquement.

### Deployer sur les deux en même temps

```bash
git add .
git commit -m "Description"
git push origin main && git tag v10.0.X && git push origin v10.0.X
```

### Deployer manuellement

1. GitHub → Actions → **Deploy Manual**
2. "Run workflow" → choisir l'environnement et les options
3. Lancer

### Bumper la version du manifest

Avant de déployer, mettre à jour `FRONT-END/manifest.json` :
```json
"version": "10.0.X"
```
Le tag doit correspondre : `v10.0.X`

---

## Système de remplacement des variables d'environnement

### Placeholders

Le script `scripts/apply-env.sh` remplace les placeholders dans les fichiers source avant le build :

| Placeholder | Variable d'environnement |
|-------------|--------------------------|
| `__AI_API_URL__` | `AI_API_URL` |
| `__USERS_API_URL__` | `USERS_API_URL` |
| `__SITE_URL__` | `SITE_URL` |
| `__GOOGLE_CLIENT_ID__` | `GOOGLE_CLIENT_ID` |
| `__GOOGLE_CLIENT_ID_WEB__` | `GOOGLE_CLIENT_ID_WEB` |
| `__STRIPE_WEBHOOK_SECRET__` | `STRIPE_WEBHOOK_SECRET` |
| `__ALLOWED_ORIGINS__` | Composé automatiquement |
| `__CORS_CREDENTIALS__` | `true` |

### Types de fichiers traités

`.js`, `.jsx`, `.ts`, `.tsx`, `.py`, `.html`, `.css`, `.json`, `.yml`, `.yaml`, `.env*`

---

## Docker Compose (VPS)

Les images sont pullées depuis GHCR (pas de build local sur le VPS).

### Dépendances de démarrage

```
postgres (healthcheck: pg_isready)
    ↓
redis (healthcheck: redis-cli ping)
    ↓
user-service (healthcheck: HTTP GET /health sur :8444)
    ↓
ai-service (healthcheck: HTTP GET /health sur :8443)

site-internet (indépendant, healthcheck: curl localhost)
```

### Commandes utiles sur le VPS

```bash
# Se connecter au VPS
ssh deploy@<IP_VPS>

# Aller dans le dossier du projet
cd /home/deploy/I2F/PROJETS/LINKEDIN_COMMENTER/linkedin_commenter-v3

# Voir les logs
docker compose logs -f
docker compose logs -f user-service
docker compose logs -f ai-service

# Redémarrer un service
docker compose restart user-service

# Voir l'état des conteneurs
docker compose ps

# Recréer les conteneurs (après pull)
docker compose pull && docker compose up -d --remove-orphans

# Nettoyer les anciennes images
docker system prune -f
```

---

## Google OAuth - Configuration

### Clients OAuth (Google Cloud Console)

Chaque environnement a 2 types de clients OAuth :

| Client | Type | Usage |
|--------|------|-------|
| LinkedIn AI Commenter - PREPROD | Extension Chrome | OAuth dans l'extension (manifest `oauth2.client_id`) |
| LinkedIn AI Backend - PREPROD | Application Web | Validation des tokens côté backend |
| LinkedIn AI Commenter - PROD | Extension Chrome | OAuth dans l'extension |
| LinkedIn AI Backend - PROD | Application Web | Validation des tokens côté backend |

### Extension IDs et OAuth

Chaque client "Extension Chrome" est lié à un **Application ID** (Extension ID). Cet ID est différent selon le mode de chargement :

| Mode | Extension ID | Stable ? |
|------|-------------|----------|
| Unpacked (dossier local) | Généré depuis le chemin du dossier | Oui, si même dossier |
| Chrome Web Store | Attribué par Google | Oui, fixe |

**Pour tester en local :** Toujours charger l'extension depuis le **même dossier** (ex: `C:\Extensions\linkedin-preprod\`).

Un client OAuth Chrome Extension ne supporte qu'**un seul Application ID**. Créer des clients séparés pour dev/preprod/prod.

---

## Chrome Web Store

### Publication

| Env | Upload | Publish | Extension ID Secret |
|-----|--------|---------|---------------------|
| Preprod | Oui (continue-on-error) | Non | `CHROME_EXTENSION_ID_PREPROD` |
| Prod | Oui | Oui | `CHROME_EXTENSION_ID_PROD` |

### Tester l'extension avant publication

1. Télécharger l'artifact depuis GitHub → Actions → dernier run → **Artifacts** (en bas de page)
2. Dézipper dans un dossier fixe
3. Chrome → `chrome://extensions` → Mode développeur → Charger l'extension non empaquetée
4. S'assurer que l'Extension ID est bien configuré dans le client OAuth Google

### Privacy Policy

Page requise par le Chrome Web Store : `/privacy.html` sur le site.

---

## Monitoring

| Script | Emplacement | Description |
|--------|-------------|-------------|
| `check_services.sh` | `MONITORING/` | Vérifie l'état des services |
| `daily_usage.py` | `MONITORING/` | Rapport d'utilisation quotidien |

---

## Troubleshooting

### Erreur OAuth "bad client id"

**Cause :** L'Extension ID configuré dans Google Cloud Console ne correspond pas à l'extension installée.
**Fix :** Vérifier que l'Application ID dans le client OAuth correspond à l'Extension ID visible dans `chrome://extensions`.

### Les containers ne répondent pas en curl depuis le VPS

**Cause :** Les services ne sont pas exposés sur le VPS, ils passent par Traefik.
**Fix :** Tester via les URLs publiques (ex: `curl https://users.api.ai-linkedin.iry-entreprise.fr/health`).

### Workflow Chrome Web Store échoue en preprod

**Cause :** Normal - le publish n'est pas activé en preprod (`continue-on-error: true`).
**Fix :** Pas d'action requise, c'est le comportement attendu.

### Tag déjà existant

```bash
# Supprimer le tag local et distant, puis recréer
git tag -d v10.0.X
git push origin --delete v10.0.X
git tag v10.0.X
git push origin v10.0.X
```
