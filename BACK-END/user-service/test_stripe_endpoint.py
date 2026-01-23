"""
Script de test pour l'endpoint Stripe create-checkout-session

Pour exécuter ce test:
1. Assurez-vous que le backend user-service est lancé
2. Ayez un token JWT valide d'un utilisateur
3. Exécutez: python test_stripe_endpoint.py

Ce script teste:
- La création d'une session de checkout pour le plan Medium
- La création d'une session de checkout pour le plan Premium
- La gestion des erreurs (plan invalide)
"""

import httpx
import asyncio
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv("../.env")

# Configuration
BASE_URL = os.getenv("USER_SERVICE_EXTERNAL_URL", "http://localhost:8444")
# ATTENTION: Remplacez ce token par un vrai token JWT obtenu après authentification
JWT_TOKEN = "VOTRE_TOKEN_JWT_ICI"

async def test_create_checkout_session(plan: str):
    """
    Teste la création d'une session de paiement Stripe
    """
    url = f"{BASE_URL}/api/stripe/create-checkout-session"

    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "plan": plan
    }

    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)

            print(f"\n{'='*60}")
            print(f"Test: Création de session Stripe pour le plan {plan.upper()}")
            print(f"{'='*60}")
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Succès!")
                print(f"Session ID: {data.get('session_id')}")
                print(f"Checkout URL: {data.get('checkout_url')}")
            else:
                print(f"❌ Erreur!")
                print(f"Réponse: {response.text}")

        except Exception as e:
            print(f"❌ Exception: {str(e)}")

async def test_invalid_plan():
    """
    Teste la gestion des erreurs avec un plan invalide
    """
    url = f"{BASE_URL}/api/stripe/create-checkout-session"

    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "plan": "invalid_plan"
    }

    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)

            print(f"\n{'='*60}")
            print(f"Test: Plan invalide (devrait retourner 400)")
            print(f"{'='*60}")
            print(f"Status Code: {response.status_code}")

            if response.status_code == 400:
                print(f"✅ Erreur bien gérée!")
                print(f"Message: {response.json().get('detail')}")
            else:
                print(f"⚠️  Status code inattendu")
                print(f"Réponse: {response.text}")

        except Exception as e:
            print(f"❌ Exception: {str(e)}")

async def main():
    """
    Exécute tous les tests
    """
    if JWT_TOKEN == "VOTRE_TOKEN_JWT_ICI":
        print("⚠️  ATTENTION: Vous devez remplacer JWT_TOKEN par un vrai token dans le script!")
        print("Pour obtenir un token:")
        print("1. Authentifiez-vous via /api/auth/google")
        print("2. Récupérez le token JWT dans la réponse")
        print("3. Remplacez la valeur de JWT_TOKEN dans ce script")
        return

    print("\n🚀 Démarrage des tests de l'endpoint Stripe\n")

    # Test plan Medium
    await test_create_checkout_session("medium")

    # Test plan Premium
    await test_create_checkout_session("premium")

    # Test plan invalide
    await test_invalid_plan()

    print(f"\n{'='*60}")
    print("Tests terminés!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(main())
