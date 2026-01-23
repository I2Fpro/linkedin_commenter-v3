
"""
Configuration centralisée (variables d'environnement uniquement).
- OPENAI_API_KEY: clé API OpenAI (obligatoire)
- GOOGLE_CLIENT_ID: Client ID OAuth 2.0 Google (obligatoire pour Chrome identity)
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

# --- Google OAuth ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
if not GOOGLE_CLIENT_ID:
    raise ValueError("GOOGLE_CLIENT_ID manquante (définir dans l'environnement ou .env)")

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
    return True

if __name__ == "__main__":
    validate_environment()
