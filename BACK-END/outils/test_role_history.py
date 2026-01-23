"""
Script de test pour vérifier le fonctionnement de l'historique des changements de rôle
"""
import sys
import os
from pathlib import Path

# Ajouter le répertoire user-service au path pour importer les modules
sys.path.insert(0, str(Path(__file__).parent / "user-service"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, RoleType, Base, RoleChangeHistory
from database import get_db, engine
from utils.role_manager import RoleManager
import uuid

def test_role_history():
    """Test de l'historique des changements de rôle"""

    db = next(get_db())

    try:
        print("🧪 Test de l'historique des changements de rôle\n")
        print("=" * 60)

        # 1. Créer un utilisateur de test
        print("\n1️⃣  Création d'un utilisateur de test...")
        test_user = User(
            email="test_role_history@example.com",
            name="Test Role History",
            role=RoleType.FREE,
            is_active=True
        )

        db.add(test_user)
        db.flush()

        # Enregistrer le rôle initial
        RoleManager.record_initial_role(
            db=db,
            user=test_user,
            reason="Test de l'historique des rôles"
        )

        print(f"✅ Utilisateur créé: {test_user.email}")
        print(f"   ID: {test_user.id}")
        print(f"   Rôle initial: {test_user.role.value}")

        # 2. Changer le rôle FREE -> MEDIUM
        print("\n2️⃣  Changement de rôle FREE -> MEDIUM...")
        RoleManager.change_user_role(
            db=db,
            user=test_user,
            new_role=RoleType.MEDIUM,
            changed_by="admin@example.com",
            reason="Upgrade pour test"
        )
        print(f"✅ Rôle changé: {test_user.role.value}")

        # 3. Changer le rôle MEDIUM -> PREMIUM
        print("\n3️⃣  Changement de rôle MEDIUM -> PREMIUM...")
        RoleManager.change_user_role(
            db=db,
            user=test_user,
            new_role=RoleType.PREMIUM,
            changed_by="admin@example.com",
            reason="Upgrade premium pour test"
        )
        print(f"✅ Rôle changé: {test_user.role.value}")

        db.commit()

        # 4. Récupérer l'historique
        print("\n4️⃣  Récupération de l'historique des changements...")
        history = RoleManager.get_user_role_history(db, test_user.id)

        print(f"\n📊 Historique complet ({len(history)} entrées):")
        print("-" * 60)
        for i, entry in enumerate(history, 1):
            print(f"\n   Entrée {i}:")
            print(f"   - De: {entry.old_role.value if entry.old_role else 'NULL (création)'}")
            print(f"   - Vers: {entry.new_role.value}")
            print(f"   - Date: {entry.changed_at}")
            print(f"   - Par: {entry.changed_by or 'N/A'}")
            print(f"   - Raison: {entry.reason or 'N/A'}")

        # 5. Récupérer le résumé
        print("\n5️⃣  Résumé des changements de rôle...")
        summary = RoleManager.get_role_change_summary(db, test_user.id)

        print("\n📈 Résumé:")
        print("-" * 60)
        print(f"   Total de changements: {summary['total_changes']}")
        print(f"   Rôle initial: {summary['initial_role']}")
        print(f"   Rôle actuel: {summary['current_role']}")
        print(f"   Dernier changement: {summary['last_change_date']}")

        # 6. Nettoyage - Supprimer l'utilisateur de test
        print("\n6️⃣  Nettoyage...")
        db.delete(test_user)
        db.commit()
        print("✅ Utilisateur de test supprimé")

        print("\n" + "=" * 60)
        print("🎉 Tous les tests ont réussi!")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_role_history()
