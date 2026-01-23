"""
Script d'exemple montrant comment utiliser database_helper.py

⚠️ IMPORTANT POUR CLAUDE:
Ce script interagit avec la BASE DE DONNÉES RÉELLE (production).
Il utilise les VRAIES données utilisateurs, pas des exemples fictifs.

Usage depuis Docker (OBLIGATOIRE):
    docker exec linkedin_ai_user_service python /app/example_database_helper.py
    docker exec linkedin_ai_user_service python /app/example_database_helper.py cleanup
    docker exec linkedin_ai_user_service python /app/example_database_helper.py migrate
    docker exec linkedin_ai_user_service python /app/example_database_helper.py export

Ce script démontre les principales fonctionnalités du module DatabaseHelper
avec les utilisateurs réels actuellement dans la base de données.
"""

from database_helper import (
    DatabaseHelper,
    print_user_table,
    print_stats_summary,
    print_duplicates_report,
    print_usage_history
)
from models import RoleType


def main():
    """Exemples d'utilisation du DatabaseHelper."""

    # Créer une instance du helper
    helper = DatabaseHelper()

    print("\n" + "="*70)
    print("🚀 EXEMPLES D'UTILISATION DE DATABASE_HELPER")
    print("="*70)

    # ========================================================================
    # EXEMPLE 1: Créer un utilisateur (COMMENTÉ - décommenter pour tester)
    # ========================================================================
    print("\n📝 EXEMPLE 1: Créer un utilisateur")
    print("-" * 70)
    print("ℹ️  Décommentez le code ci-dessous pour créer un nouvel utilisateur RÉEL")
    print("⚠️  Cela ajoutera un utilisateur dans la base de données de production!")

    # Décommenter pour créer un utilisateur:
    # success, message, user = helper.create_user(
    #     email="nouveau@example.com",
    #     name="Nouvel Utilisateur",
    #     role=RoleType.FREE,
    #     is_active=True
    # )
    # print(message)

    # ========================================================================
    # EXEMPLE 2: Lister tous les utilisateurs RÉELS
    # ========================================================================
    print("\n📋 EXEMPLE 2: Lister tous les utilisateurs RÉELS de la base")
    print("-" * 70)

    users = helper.list_all_users(show_inactive=False)
    print(f"\n✅ Utilisateurs actifs trouvés: {len(users)}")
    print_user_table(users)

    # ========================================================================
    # EXEMPLE 3: Afficher les statistiques
    # ========================================================================
    print("\n📊 EXEMPLE 3: Statistiques globales")
    print("-" * 70)

    stats = helper.get_user_stats()
    print_stats_summary(stats)

    # ========================================================================
    # EXEMPLE 4: Rechercher un utilisateur RÉEL
    # ========================================================================
    print("\n🔍 EXEMPLE 4: Rechercher un utilisateur RÉEL par email")
    print("-" * 70)

    # Utiliser un email qui existe vraiment dans la base
    test_email = "isshia.inapogui@gmail.com"
    print(f"🔎 Recherche de: {test_email}")

    user = helper.get_user_by_email(test_email)
    if user:
        print(f"\n✅ Utilisateur trouvé:")
        print(f"   Email: {user.email}")
        print(f"   Nom: {user.name}")
        print(f"   Rôle: {user.role.value}")
        print(f"   ID: {user.id}")
    else:
        print(f"❌ Utilisateur {test_email} non trouvé")
        print("ℹ️  Astuce: Listez d'abord les utilisateurs pour voir les emails disponibles")

    # ========================================================================
    # EXEMPLE 5: Mettre à jour un rôle
    # ========================================================================
    print("\n✏️  EXEMPLE 5: Mettre à jour un rôle")
    print("-" * 70)

    # Décommenter pour tester:
    # success, message = helper.update_user_role("exemple@test.com", RoleType.PREMIUM)
    # print(message)
    print("ℹ️  Décommentez le code pour tester la mise à jour de rôle")

    # ========================================================================
    # EXEMPLE 6: Détecter les doublons
    # ========================================================================
    print("\n👥 EXEMPLE 6: Détecter les doublons")
    print("-" * 70)

    duplicates = helper.find_all_duplicates()
    print_duplicates_report(duplicates)

    # ========================================================================
    # EXEMPLE 7: Nettoyer les doublons (DRY RUN)
    # ========================================================================
    print("\n🧹 EXEMPLE 7: Nettoyer les doublons (simulation)")
    print("-" * 70)

    deleted_count, messages = helper.cleanup_duplicates(
        strategy='keep_newest',
        dry_run=True  # Mode simulation
    )
    for msg in messages:
        print(msg)

    # ========================================================================
    # EXEMPLE 8: Vérifier l'intégrité du chiffrement
    # ========================================================================
    print("\n🔐 EXEMPLE 8: Vérifier l'intégrité du chiffrement")
    print("-" * 70)

    encryption_ok, messages = helper.verify_encryption_integrity()
    for msg in messages:
        print(msg)

    # ========================================================================
    # EXEMPLE 9: Rapport de santé complet
    # ========================================================================
    print("\n🏥 EXEMPLE 9: Rapport de santé de la base")
    print("-" * 70)

    report = helper.generate_health_report()
    print(report)

    # ========================================================================
    # EXEMPLE 10: Historique d'utilisation d'un utilisateur RÉEL
    # ========================================================================
    print("\n📈 EXEMPLE 10: Historique d'utilisation d'un utilisateur RÉEL")
    print("-" * 70)

    test_email = "isshia.inapogui@gmail.com"
    print(f"🔎 Récupération de l'historique pour: {test_email}")

    user, logs = helper.get_user_usage_history(test_email, days=30)
    if user:
        print_usage_history(user, logs)
    else:
        print(f"❌ Utilisateur {test_email} non trouvé")

    # ========================================================================
    # EXEMPLE 11: Créer plusieurs utilisateurs en batch
    # ========================================================================
    print("\n📦 EXEMPLE 11: Créer plusieurs utilisateurs en batch")
    print("-" * 70)

    # Décommenter pour tester:
    # users_batch = [
    #     {"email": "batch1@test.com", "name": "Batch User 1", "role": RoleType.FREE},
    #     {"email": "batch2@test.com", "name": "Batch User 2", "role": RoleType.MEDIUM},
    #     {"email": "batch3@test.com", "name": "Batch User 3", "role": RoleType.PREMIUM}
    # ]
    # created, skipped, messages = helper.create_users_batch(users_batch)
    # print(f"✅ {created} créé(s), {skipped} ignoré(s)")
    # for msg in messages:
    #     print(f"   {msg}")
    print("ℹ️  Décommentez le code pour tester la création en batch")

    # ========================================================================
    # EXEMPLE 12: Lister par rôle
    # ========================================================================
    print("\n🎭 EXEMPLE 12: Lister les utilisateurs PREMIUM")
    print("-" * 70)

    premium_users = helper.list_users_by_role(RoleType.PREMIUM)
    if premium_users:
        print_user_table(premium_users)
    else:
        print("ℹ️  Aucun utilisateur PREMIUM")

    # ========================================================================
    # FIN
    # ========================================================================
    print("\n" + "="*70)
    print("✅ EXEMPLES TERMINÉS")
    print("="*70)
    print("\nPour plus d'informations, consultez la documentation dans database_helper.py\n")


# ============================================================================
# EXEMPLES DE CAS D'USAGE SPÉCIFIQUES
# ============================================================================

def exemple_nettoyage_doublons_reel():
    """
    Exemple de nettoyage réel de doublons (avec confirmation).
    ATTENTION: Cette fonction supprime réellement des données!
    """
    helper = DatabaseHelper()

    print("\n⚠️  NETTOYAGE RÉEL DES DOUBLONS")
    print("="*70)
    print("Cette opération va supprimer des utilisateurs en doublon.")

    # D'abord, afficher les doublons
    duplicates = helper.find_all_duplicates()
    print_duplicates_report(duplicates)

    total_dups = len(duplicates.get("email_duplicates", [])) + len(duplicates.get("google_id_duplicates", []))

    if total_dups == 0:
        print("\n✅ Aucun doublon à nettoyer\n")
        return

    # Demander confirmation
    response = input("\n⚠️  Voulez-vous nettoyer les doublons? (y/N): ")
    if response.lower() != 'y':
        print("❌ Nettoyage annulé\n")
        return

    # Choisir la stratégie
    print("\nStratégies disponibles:")
    print("  1. keep_newest - Garder le plus récent")
    print("  2. keep_oldest - Garder le plus ancien")
    print("  3. keep_most_active - Garder celui avec le plus d'usage")

    strategy_choice = input("\nChoisissez une stratégie (1-3, défaut=1): ") or "1"
    strategy_map = {
        "1": "keep_newest",
        "2": "keep_oldest",
        "3": "keep_most_active"
    }
    strategy = strategy_map.get(strategy_choice, "keep_newest")

    # Exécuter le nettoyage
    deleted_count, messages = helper.cleanup_duplicates(
        strategy=strategy,
        dry_run=False  # ATTENTION: Suppression réelle!
    )

    for msg in messages:
        print(msg)


def exemple_migration_utilisateur():
    """
    Exemple de migration d'un utilisateur FREE vers PREMIUM.
    """
    helper = DatabaseHelper()

    email = input("Email de l'utilisateur à migrer vers PREMIUM: ")

    # Vérifier que l'utilisateur existe
    user = helper.get_user_by_email(email)
    if not user:
        print(f"❌ Utilisateur {email} non trouvé")
        return

    print(f"\nUtilisateur trouvé:")
    print(f"   Email: {user.email}")
    print(f"   Rôle actuel: {user.role.value}")

    # Confirmer
    response = input(f"\nMigrer vers PREMIUM? (y/N): ")
    if response.lower() != 'y':
        print("❌ Migration annulée")
        return

    # Mettre à jour
    success, message = helper.update_user_role(email, RoleType.PREMIUM)
    print(message)


def exemple_export_utilisateurs():
    """
    Exemple d'export de tous les utilisateurs avec leurs infos.
    """
    helper = DatabaseHelper()

    print("\n📊 EXPORT DES UTILISATEURS")
    print("="*70)

    users = helper.list_all_users(show_inactive=True)

    print(f"\nNombre total d'utilisateurs: {len(users)}")
    print_user_table(users, show_google_id=True)

    # Détails par utilisateur
    for user in users:
        print(f"\n{'='*70}")
        print(f"Email: {user.email}")
        print(f"Nom: {user.name}")
        print(f"Google ID: {user.google_id or 'N/A'}")
        print(f"Rôle: {user.role.value}")
        print(f"Actif: {'Oui' if user.is_active else 'Non'}")
        print(f"Créé le: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mis à jour le: {user.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")

        # Afficher l'usage
        _, logs = helper.get_user_usage_history(user.email, days=30)
        print(f"Actions (30 derniers jours): {len(logs)}")


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "cleanup":
            exemple_nettoyage_doublons_reel()
        elif command == "migrate":
            exemple_migration_utilisateur()
        elif command == "export":
            exemple_export_utilisateurs()
        else:
            print(f"❌ Commande inconnue: {command}")
            print("\nCommandes disponibles:")
            print("  python example_database_helper.py           - Exemples de base")
            print("  python example_database_helper.py cleanup   - Nettoyer les doublons")
            print("  python example_database_helper.py migrate   - Migrer un utilisateur")
            print("  python example_database_helper.py export    - Exporter les utilisateurs")
    else:
        # Mode par défaut: exemples de base
        main()
