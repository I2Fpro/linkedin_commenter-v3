
"""
Configuration centralisée (variables d'environnement uniquement).
- OPENAI_API_KEY: clé API OpenAI (obligatoire)
- GOOGLE_CLIENT_ID: Client ID OAuth 2.0 Google pour extension Chrome (obligatoire)
- GOOGLE_CLIENT_ID_WEB: Client ID OAuth 2.0 Google pour site web (obligatoire)
- OPENAI_MODEL: nom du modèle OpenAI (optionnel, défaut: gpt-4o-mini)
- HOST/PORT: binding FastAPI (optionnels)
"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement (.env si présent)
load_dotenv()

# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY manquante (définir dans l'environnement ou .env)")

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# --- Tavily (Web Search) ---
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
# Note: TAVILY_API_KEY est optionnel - si absent, la recherche web sera desactivee

# --- Google OAuth ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
if not GOOGLE_CLIENT_ID:
    raise ValueError("GOOGLE_CLIENT_ID manquante (définir dans l'environnement ou .env)")

# Client ID pour le site web (séparé de l'extension Chrome)
GOOGLE_CLIENT_ID_WEB = os.getenv("GOOGLE_CLIENT_ID_WEB")
if not GOOGLE_CLIENT_ID_WEB:
    raise ValueError("GOOGLE_CLIENT_ID_WEB manquante (définir dans l'environnement ou .env)")

# --- Server ---
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8443"))

def validate_environment():
    """
    Valide la présence des variables d'environnement essentielles.
    Retourne True si tout est correct.
    """
    # Les erreurs sont levées au dessus si manquantes
    print("✅ Configuration validée")
    print(f"🐳 Serveur: {HOST}:{PORT}")
    # V3 Story 1.4 - Afficher le statut de la recherche web
    if TAVILY_API_KEY:
        print("🌐 Recherche web: activée (Tavily)")
    else:
        print("⚠️ Recherche web: désactivée (TAVILY_API_KEY non configurée)")
    return True

if __name__ == "__main__":
    validate_environment()
