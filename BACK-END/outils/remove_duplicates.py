"""
Script pour supprimer les utilisateurs en double en conservant la version la plus récente
"""
import sys
import os
from pathlib import Path
from collections import defaultdict

# Ajouter le répertoire user-service au path pour importer les modules
sys.path.insert(0, str(Path(__file__).parent / "user-service"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, RoleType, Base
from database import get_db, engine

def remove_duplicate_users():
    """Supprime les utilisateurs en double en conservant la version la plus récente"""

    # Créer une session
    db = next(get_db())

    try:
        # Récupérer tous les utilisateurs
        all_users = db.query(User).all()

        print(f"📊 Total d'utilisateurs dans la base: {len(all_users)}")
        print()

        # Grouper par email (déchiffré)
        users_by_email = defaultdict(list)

        for user in all_users:
            # L'email est automatiquement déchiffré par SQLAlchemy
            users_by_email[user.email].append(user)

        print(f"📧 Nombre d'emails uniques: {len(users_by_email)}")
        print()

        # Identifier les doublons
        duplicates_found = False
        users_to_delete = []

        for email, users in users_by_email.items():
            if len(users) > 1:
                duplicates_found = True
                # Trier par date de création (plus récent en premier)
                users_sorted = sorted(users, key=lambda u: u.created_at, reverse=True)

                print(f"⚠️  Doublons trouvés pour: {email}")
                print(f"   Nombre de copies: {len(users)}")

                # Garder le plus récent
                keep_user = users_sorted[0]
                print(f"   ✅ CONSERVER: ID {keep_user.id} (créé le {keep_user.created_at})")

                # Supprimer les autres
                for user in users_sorted[1:]:
                    print(f"   ❌ SUPPRIMER: ID {user.id} (créé le {user.created_at})")
                    users_to_delete.append(user)

                print()

        if not duplicates_found:
            print("✅ Aucun doublon trouvé!")
            return

        # Supprimer les doublons
        if users_to_delete:
            print(f"\n🗑️  Suppression de {len(users_to_delete)} utilisateur(s) en double...")

            # D'abord, migrer ou supprimer les données liées
            for email, users in users_by_email.items():
                if len(users) > 1:
                    users_sorted = sorted(users, key=lambda u: u.created_at, reverse=True)
                    keep_user = users_sorted[0]

                    # Pour chaque utilisateur à supprimer
                    for old_user in users_sorted[1:]:
                        # Transférer les usage_logs vers le nouvel utilisateur
                        from models import UsageLog
                        logs_to_migrate = db.query(UsageLog).filter(UsageLog.user_id == old_user.id).all()

                        if logs_to_migrate:
                            print(f"   📊 Migration de {len(logs_to_migrate)} logs de {old_user.id} vers {keep_user.id}")
                            for log in logs_to_migrate:
                                log.user_id = keep_user.id

                        # Transférer les subscriptions vers le nouvel utilisateur
                        from models import Subscription
                        subs_to_migrate = db.query(Subscription).filter(Subscription.user_id == old_user.id).all()

                        if subs_to_migrate:
                            print(f"   📋 Migration de {len(subs_to_migrate)} subscriptions de {old_user.id} vers {keep_user.id}")
                            for sub in subs_to_migrate:
                                sub.user_id = keep_user.id

            # Commit les migrations
            db.commit()

            # Maintenant supprimer les utilisateurs en double
            for user in users_to_delete:
                db.delete(user)

            db.commit()

            print(f"✅ {len(users_to_delete)} utilisateur(s) supprimé(s) avec succès!")

            # Afficher le résumé final
            remaining_users = db.query(User).all()
            print(f"\n📊 Résumé final:")
            print(f"   Utilisateurs restants: {len(remaining_users)}")

            # Grouper par email pour vérification
            final_emails = set()
            for user in remaining_users:
                final_emails.add(user.email)

            print(f"   Emails uniques: {len(final_emails)}")
            print()
            print("📋 Liste des utilisateurs conservés:")
            for user in sorted(remaining_users, key=lambda u: u.created_at, reverse=True):
                print(f"   - {user.email} ({user.role.value}) - ID: {user.id}")

    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de la suppression des doublons: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Suppression des utilisateurs en double...\n")
    remove_duplicate_users()
