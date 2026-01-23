#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Script simple pour lister les utilisateurs de la base de données.

POUR CLAUDE :
===============
Ce script DOIT être exécuté via Docker depuis le conteneur linkedin_ai_user_service.

COMMANDE CORRECTE :
    cd d:\DEV\GIT\Ai_Commentary\BACK-END
    MSYS_NO_PATHCONV=1 docker exec linkedin_ai_user_service python /app/list_users_simple.py

    Ou sur PowerShell/CMD/Linux/Mac :
    docker exec linkedin_ai_user_service python /app/list_users_simple.py

NE PAS FAIRE :
    python list_users_simple.py
    python d:\DEV\GIT\Ai_Commentary\BACK-END\user-service\list_users_simple.py

RAISON : La base PostgreSQL utilise le hostname 'postgres' qui n'existe que
dans le réseau Docker. Exécuter en dehors de Docker provoquera l'erreur :
"could not translate host name 'postgres' to address"

Pour plus d'informations :
- Voir CLAUDE_QUICK_HELP.md à la racine du projet
- Voir database_helper/DATABASE_HELPER_README.md pour la documentation complète
"""

import sys
import os
from pathlib import Path

# Configuration de l'encodage pour Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from models import User, RoleType
from database import get_db

def main():
    """Liste tous les utilisateurs."""
    print("\n" + "="*70)
    print("📋 LISTE DES UTILISATEURS")
    print("="*70 + "\n")

    db = next(get_db())
    try:
        users = db.query(User).order_by(User.created_at.desc()).all()

        if not users:
            print("❌ Aucun utilisateur trouvé dans la base de données.\n")
            return

        print(f"✅ Nombre total d'utilisateurs: {len(users)}\n")

        for i, user in enumerate(users, 1):
            print(f"[{i}] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"    📧 Email: {user.email}")
            print(f"    👤 Nom: {user.name or 'N/A'}")
            print(f"    🔑 ID: {user.id}")
            print(f"    🎭 Rôle: {user.role.value}")
            print(f"    ✅ Actif: {'Oui' if user.is_active else 'Non'}")
            print(f"    🔑 Google ID: {user.google_id[:20] + '...' if user.google_id else 'N/A'}")
            print(f"    📅 Créé le: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    🔄 Mis à jour: {user.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print()

        # Statistiques par rôle
        print("="*70)
        print("📊 STATISTIQUES PAR RÔLE")
        print("="*70)
        for role in RoleType:
            count = sum(1 for u in users if u.role == role)
            if count > 0:
                print(f"    {role.value:10s}: {count} utilisateur(s)")
        print()

    finally:
        db.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
