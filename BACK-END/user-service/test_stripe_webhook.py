#!/usr/bin/env python3
"""
Script de test pour l'endpoint webhook Stripe

Ce script permet de tester l'endpoint webhook en simulant des événements Stripe.

Usage:
    python test_stripe_webhook.py

Note: Pour des tests plus avancés, utilisez la Stripe CLI:
    stripe listen --forward-to localhost:8444/api/stripe/webhook
    stripe trigger checkout.session.completed
"""

import requests
import json
import time
import hmac
import hashlib

# Configuration
BASE_URL = "__USERS_API_URL__"
WEBHOOK_ENDPOINT = f"{BASE_URL}/api/stripe/webhook"

# NOTE: Pour que ce script fonctionne, vous devez avoir le STRIPE_WEBHOOK_SECRET
# Pour les tests en local, vous pouvez utiliser la Stripe CLI qui génère les signatures automatiquement
# stripe listen --forward-to localhost:8444/api/stripe/webhook


def create_stripe_signature(payload: str, secret: str, timestamp: int = None) -> str:
    """
    Créer une signature Stripe valide pour le webhook

    Args:
        payload: Le corps de la requête (JSON string)
        secret: Le webhook secret Stripe
        timestamp: Timestamp Unix (ou None pour utiliser l'heure actuelle)

    Returns:
        La signature au format attendu par Stripe
    """
    if timestamp is None:
        timestamp = int(time.time())

    # Créer le signed payload
    signed_payload = f"{timestamp}.{payload}"

    # Calculer la signature HMAC
    signature = hmac.new(
        secret.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Retourner le header au format Stripe
    return f"t={timestamp},v1={signature}"


def test_checkout_completed():
    """
    Tester l'événement checkout.session.completed
    """
    print("\n" + "="*60)
    print("🧪 Test: checkout.session.completed")
    print("="*60)

    # Événement simulé
    event = {
        "id": "evt_test_webhook_checkout_completed",
        "object": "event",
        "api_version": "2023-10-16",
        "created": int(time.time()),
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_a1b2c3d4e5f6",
                "object": "checkout.session",
                "customer": "cus_test_customer_123",
                "subscription": "sub_test_subscription_123",
                "mode": "subscription",
                "status": "complete",
                "metadata": {
                    "user_id": "ecdae139-df45-4401-8ec2-e4a93a15817a",  # Remplacer par un vrai user_id
                    "email": "test@example.com",
                    "plan": "medium"
                }
            }
        }
    }

    payload = json.dumps(event, separators=(',', ':'))

    print(f"\n📤 Envoi de l'événement vers: {WEBHOOK_ENDPOINT}")
    print(f"📋 Type d'événement: {event['type']}")
    print(f"🆔 Event ID: {event['id']}")

    try:
        # NOTE: Pour un vrai test avec signature, décommentez ci-dessous et ajoutez votre secret
        # webhook_secret = "whsec_your_webhook_secret"
        # signature = create_stripe_signature(payload, webhook_secret)
        # headers = {
        #     "stripe-signature": signature,
        #     "content-type": "application/json"
        # }

        # Pour le test sans signature (si l'endpoint accepte les requêtes de test)
        headers = {
            "content-type": "application/json"
        }

        response = requests.post(
            WEBHOOK_ENDPOINT,
            data=payload,
            headers=headers,
            timeout=10
        )

        print(f"\n✅ Statut de la réponse: {response.status_code}")
        print(f"📝 Réponse: {response.text}")

        if response.status_code == 200:
            print("\n✅ Webhook traité avec succès!")
        else:
            print(f"\n❌ Erreur: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Erreur de connexion: {str(e)}")


def test_invoice_paid():
    """
    Tester l'événement invoice.paid
    """
    print("\n" + "="*60)
    print("🧪 Test: invoice.paid")
    print("="*60)

    event = {
        "id": "evt_test_webhook_invoice_paid",
        "object": "event",
        "api_version": "2023-10-16",
        "created": int(time.time()),
        "type": "invoice.paid",
        "data": {
            "object": {
                "id": "in_test_invoice_123",
                "object": "invoice",
                "customer": "cus_test_customer_123",
                "subscription": "sub_test_subscription_123",
                "status": "paid",
                "amount_paid": 999,
                "currency": "eur"
            }
        }
    }

    payload = json.dumps(event, separators=(',', ':'))

    print(f"\n📤 Envoi de l'événement vers: {WEBHOOK_ENDPOINT}")
    print(f"📋 Type d'événement: {event['type']}")
    print(f"🆔 Event ID: {event['id']}")

    try:
        headers = {"content-type": "application/json"}

        response = requests.post(
            WEBHOOK_ENDPOINT,
            data=payload,
            headers=headers,
            timeout=10
        )

        print(f"\n✅ Statut de la réponse: {response.status_code}")
        print(f"📝 Réponse: {response.text}")

        if response.status_code == 200:
            print("\n✅ Webhook traité avec succès!")
        else:
            print(f"\n❌ Erreur: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Erreur de connexion: {str(e)}")


def test_subscription_deleted():
    """
    Tester l'événement customer.subscription.deleted
    """
    print("\n" + "="*60)
    print("🧪 Test: customer.subscription.deleted")
    print("="*60)

    event = {
        "id": "evt_test_webhook_subscription_deleted",
        "object": "event",
        "api_version": "2023-10-16",
        "created": int(time.time()),
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_test_subscription_123",
                "object": "subscription",
                "customer": "cus_test_customer_123",
                "status": "canceled",
                "cancel_at_period_end": False,
                "canceled_at": int(time.time())
            }
        }
    }

    payload = json.dumps(event, separators=(',', ':'))

    print(f"\n📤 Envoi de l'événement vers: {WEBHOOK_ENDPOINT}")
    print(f"📋 Type d'événement: {event['type']}")
    print(f"🆔 Event ID: {event['id']}")

    try:
        headers = {"content-type": "application/json"}

        response = requests.post(
            WEBHOOK_ENDPOINT,
            data=payload,
            headers=headers,
            timeout=10
        )

        print(f"\n✅ Statut de la réponse: {response.status_code}")
        print(f"📝 Réponse: {response.text}")

        if response.status_code == 200:
            print("\n✅ Webhook traité avec succès!")
        else:
            print(f"\n❌ Erreur: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Erreur de connexion: {str(e)}")


def main():
    """
    Fonction principale pour exécuter tous les tests
    """
    print("\n" + "="*60)
    print("🚀 Démarrage des tests webhook Stripe")
    print("="*60)
    print("\n⚠️  IMPORTANT:")
    print("   - Ces tests envoient des événements fictifs à votre endpoint")
    print("   - Pour des tests avec signature, utilisez la Stripe CLI:")
    print("     stripe listen --forward-to localhost:8444/api/stripe/webhook")
    print("     stripe trigger checkout.session.completed")
    print("\n")

    input("Appuyez sur Entrée pour commencer les tests...")

    # Exécuter les tests
    test_checkout_completed()

    time.sleep(2)

    test_invoice_paid()

    time.sleep(2)

    test_subscription_deleted()

    print("\n" + "="*60)
    print("✅ Tests terminés!")
    print("="*60)
    print("\n💡 Prochaines étapes:")
    print("   1. Vérifier les logs du service user-service")
    print("   2. Vérifier la base de données (table stripe_events)")
    print("   3. Vérifier que les utilisateurs ont été mis à jour")
    print("   4. Tester avec de vrais événements via Stripe CLI")
    print("\n")


if __name__ == "__main__":
    main()
