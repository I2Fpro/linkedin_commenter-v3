#!/usr/bin/env python3
"""
Script de démarrage pour le backend LinkedIn AI Commenter
HTTPS géré par Traefik en production
"""

import uvicorn
import os
import sys

def main():
    """Démarre le serveur FastAPI"""

    print("🚀 Démarrage du backend LinkedIn AI Commenter...")
    print("🔒 HTTPS géré par Traefik")
    print("📚 Documentation API: /docs")
    print("❤️  Health check: /health")
    print("-" * 50)

    # Vérifier les variables d'environnement
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Variable OPENAI_API_KEY manquante dans .env")

    if not os.getenv('GOOGLE_CLIENT_ID'):
        print("⚠️  Variable GOOGLE_CLIENT_ID manquante dans .env")

    print()

    try:
        # Démarrer le serveur HTTP (Traefik gère le HTTPS)
        uvicorn.run(
            "fastapi_backend:app",
            host="0.0.0.0",
            port=8443,
            reload=True,  # Redémarrage automatique en cas de modification
            log_level="info",
            # Configuration pour améliorer la gestion des connexions
            timeout_keep_alive=5,
            limit_concurrency=100,
            limit_max_requests=1000
        )
    except KeyboardInterrupt:
        print("\n👋 Arrêt du serveur...")
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        print()
        print("🔧 Solutions possibles:")
        print("   - Assurez-vous que le port 8443 n'est pas utilisé")
        print("   - Vérifiez les variables d'environnement")
        sys.exit(1)

if __name__ == "__main__":
    main()