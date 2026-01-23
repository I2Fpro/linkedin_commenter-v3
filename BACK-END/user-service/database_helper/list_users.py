#!/usr/bin/env python3
"""
Script pour lister les utilisateurs RÉELS de la base de données.

Usage:
    docker exec linkedin_ai_user_service python /app/list_users.py          # Liste complète
    docker exec linkedin_ai_user_service python /app/list_users.py stats    # Statistiques
    docker exec linkedin_ai_user_service python /app/list_users.py duplicates # Doublons

⚠️ IMPORTANT: Ce script utilise les VRAIES données de la base de données de production.
"""

import sys
from pathlib import Path

# Ajouter le répertoire user-service au path
sys.path.insert(0, str(Path(__file__).parent / "user-service"))

from database_helper import (
    DatabaseHelper,
    print_user_table,
    print_stats_summary,
    print_duplicates_report
)


def main():
    """Point d'entrée principal."""

    helper = DatabaseHelper()

    # Déterminer le mode d'affichage
    mode = sys.argv[1] if len(sys.argv) > 1 else "list"

    if mode == "stats":
        # Afficher seulement les statistiques
        print("\n" + "="*70)
        print("📊 STATISTIQUES DES UTILISATEURS RÉELS")
        print("="*70)
        stats = helper.get_user_stats()
        print_stats_summary(stats)

    elif mode == "duplicates":
        # Afficher seulement les doublons
        print("\n" + "="*70)
        print("🔍 DÉTECTION DES DOUBLONS")
        print("="*70)
        duplicates = helper.find_all_duplicates()
        print_duplicates_report(duplicates)

    else:
        # Affichage complet par défaut
        print("\n" + "="*70)
        print("📋 LISTE COMPLÈTE DES UTILISATEURS RÉELS")
        print("="*70)

        # Lister tous les utilisateurs (y compris inactifs)
        users = helper.list_all_users(show_inactive=True)
        print(f"\n✅ Nombre total d'utilisateurs dans la base: {len(users)}\n")

        # Afficher le tableau
        print_user_table(users, show_google_id=True)

        # Afficher les détails
        print("\n" + "="*70)
        print("📝 DÉTAILS PAR UTILISATEUR")
        print("="*70)

        for i, user in enumerate(users, 1):
            print(f"\n[{i}/{len(users)}] ID: {user.id}")
            print(f"    📧 Email: {user.email}")
            print(f"    👤 Nom: {user.name or 'N/A'}")
            print(f"    🔑 Google ID: {user.google_id or 'N/A'}")
            print(f"    🎭 Rôle: {user.role.value}")
            print(f"    ✅ Actif: {'Oui' if user.is_active else 'Non'}")
            print(f"    📅 Créé le: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    🔄 Mis à jour: {user.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")

        # Statistiques résumées
        print("\n" + "="*70)
        print("📊 STATISTIQUES RÉSUMÉES")
        print("="*70)
        stats = helper.get_user_stats()
        print_stats_summary(stats)

        # Vérifier les doublons
        print("\n" + "="*70)
        print("🔍 VÉRIFICATION DES DOUBLONS")
        print("="*70)
        duplicates = helper.find_all_duplicates()
        print_duplicates_report(duplicates)

        # Rapport de santé
        print("\n" + "="*70)
        print("🏥 RAPPORT DE SANTÉ DE LA BASE")
        print("="*70)
        report = helper.generate_health_report()
        print(report)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}", file=sys.stderr)
        sys.exit(1)
