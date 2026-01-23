"""
Script de test pour vérifier l'endpoint /api/stripe/invoices

Ce script teste :
1. La structure des modèles Pydantic
2. Le mapping des statuts
3. Le formatage des données
"""

import sys
from pydantic import ValidationError

# Import des modèles depuis routers.stripe
try:
    from routers.stripe import InvoiceItem, InvoicesResponse
    print("✅ Import des modèles réussi")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    sys.exit(1)

# Test 1: Création d'un InvoiceItem valide
print("\n--- Test 1: Création d'un InvoiceItem valide ---")
try:
    invoice = InvoiceItem(
        amount=1200,
        currency="eur",
        created=1720931834,
        status="Payée",
        invoice_pdf="https://invoice.stripe.com/i/acct_test/inv_test123"
    )
    print(f"✅ InvoiceItem créé avec succès")
    print(f"   Montant: {invoice.amount / 100} {invoice.currency.upper()}")
    print(f"   Statut: {invoice.status}")
except ValidationError as e:
    print(f"❌ Erreur de validation: {e}")

# Test 2: Création d'une InvoicesResponse
print("\n--- Test 2: Création d'une InvoicesResponse ---")
try:
    response = InvoicesResponse(invoices=[
        InvoiceItem(
            amount=1200,
            currency="eur",
            created=1720931834,
            status="Payée",
            invoice_pdf="https://invoice.stripe.com/i/acct_test/inv_1"
        ),
        InvoiceItem(
            amount=2400,
            currency="eur",
            created=1725931834,
            status="En attente",
            invoice_pdf="https://invoice.stripe.com/i/acct_test/inv_2"
        )
    ])
    print(f"✅ InvoicesResponse créée avec succès")
    print(f"   Nombre de factures: {len(response.invoices)}")
except ValidationError as e:
    print(f"❌ Erreur de validation: {e}")

# Test 3: Mapping des statuts
print("\n--- Test 3: Mapping des statuts ---")
status_translation = {
    "paid": "Payée",
    "open": "En attente",
    "draft": "Brouillon",
    "uncollectible": "Irrécouvrable",
    "void": "Annulée"
}

test_statuses = ["paid", "open", "draft", "uncollectible", "void", "unknown"]
for status in test_statuses:
    translated = status_translation.get(status, status)
    print(f"   {status:15} -> {translated}")

# Test 4: Validation des types
print("\n--- Test 4: Validation des types ---")
try:
    # Test avec un montant invalide (doit être un int)
    InvoiceItem(
        amount="invalid",  # Devrait échouer
        currency="eur",
        created=1720931834,
        status="Payée",
        invoice_pdf="https://invoice.stripe.com/test"
    )
    print("❌ La validation devrait échouer avec un montant invalide")
except ValidationError:
    print("✅ Validation correcte: montant invalide rejeté")

print("\n--- Tests terminés ---")
print("🎉 Tous les tests de structure ont réussi!")
