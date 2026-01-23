"""
Script pour créer les utilisateurs initiaux dans la base de données
"""
import sys
import os
from pathlib import Path

# Ajouter le répertoire user-service au path pour importer les modules
sys.path.insert(0, str(Path(__file__).parent / "user-service"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, RoleType, Base
from database import get_db, engine
from utils.role_manager import RoleManager
import uuid

def create_users():
    """Crée les 3 utilisateurs initiaux avec leurs rôles respectifs"""

    # Créer les tables si elles n'existent pas
    Base.metadata.create_all(bind=engine)

    # Créer une session
    db = next(get_db())

    try:
        # Définir les utilisateurs à créer
        users_data = [
            {
                "email": "isshia.inapogui@gmail.com",
                "name": "Isshia Inapogui",
                "role": RoleType.MEDIUM
            },
            {
                "email": "i2frl.test@gmail.com",
                "name": "I2 Test",
                "role": RoleType.FREE
            },
            {
                "email": "i2frl.pro@gmail.com",
                "name": "I2 Pro",
                "role": RoleType.PREMIUM
            },
            {
                "email": "tanguy.dray@gmail.com",
                "name": "Tanguy Dray",
                "role": RoleType.MEDIUM
            },
            {
                "email": "alexandrefedotov94@gmail.com",
                "name": "Alexandre Fedotov",
                "role": RoleType.MEDIUM
            },
            {
                "email": "yendhi.wamba@gmail.com",
                "name": "Yendhi Wamba",
                "role": RoleType.MEDIUM
            },
            {
                "email": "framinet.fabien@gmail.com",
                "name": "Fabien Framinet",
                "role": RoleType.MEDIUM
            },
            {
                "email": "florianroullierlenoir@gmail.com",
                "name": "Florian Roullier Lenoir",
                "role": RoleType.MEDIUM
            }
        ]

        created_users = []

        for user_data in users_data:
            # Vérifier si l'utilisateur existe déjà
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()

            if existing_user:
                print(f"⚠️  L'utilisateur {user_data['email']} existe déjà (ID: {existing_user.id})")
                print(f"   Rôle actuel: {existing_user.role.value}")
                continue

            # Créer le nouvel utilisateur
            new_user = User(
                email=user_data["email"],
                name=user_data["name"],
                role=user_data["role"],
                is_active=True
            )

            db.add(new_user)
            db.flush()  # Pour obtenir l'ID

            # Enregistrer le rôle initial dans l'historique
            RoleManager.record_initial_role(
                db=db,
                user=new_user,
                reason="Création initiale de l'utilisateur",
                meta_data={"source": "create_initial_users.py"}
            )

            created_users.append(new_user)
            print(f"✅ Utilisateur créé: {user_data['email']}")
            print(f"   ID: {new_user.id}")
            print(f"   Nom: {new_user.name}")
            print(f"   Rôle: {new_user.role.value}")
            print()

        # Valider toutes les créations
        db.commit()

        print(f"\n🎉 {len(created_users)} utilisateur(s) créé(s) avec succès!")

        # Afficher un récapitulatif
        if created_users:
            print("\n📊 Récapitulatif:")
            for user in created_users:
                print(f"   - {user.email} ({user.role.value})")

    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de la création des utilisateurs: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Création des utilisateurs initiaux...\n")
    create_users()
