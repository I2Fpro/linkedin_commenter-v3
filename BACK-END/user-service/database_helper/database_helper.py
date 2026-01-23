"""
Module d'aide pour la gestion de la base de données utilisateurs.
Fournit des fonctions pour créer, lire, mettre à jour, supprimer des utilisateurs,
ainsi que pour détecter et nettoyer les doublons.

Toutes les données sensibles (email, name, google_id) sont automatiquement
chiffrées/déchiffrées via le système EncryptedString.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Literal, Tuple, Any
from datetime import datetime, timedelta
import uuid as uuid_module
import re
from collections import defaultdict

# Ajouter le répertoire user-service au path
sys.path.insert(0, str(Path(__file__).parent / "user-service"))

from sqlalchemy import create_engine, func, and_, or_, distinct
from sqlalchemy.orm import sessionmaker, Session
from tabulate import tabulate
from dotenv import load_dotenv

# Import des modèles et utilitaires
from models import User, RoleType, Subscription, UsageLog, Base
from database import get_db, engine
from utils.encryption import encryption_manager

# Charger les variables d'environnement
load_dotenv()


class DatabaseHelper:
    """
    Classe principale pour gérer les opérations sur la base de données utilisateurs.
    Toutes les opérations respectent le chiffrement automatique des données sensibles.
    """

    def __init__(self):
        """Initialise le helper avec une connexion à la base de données."""
        self.engine = engine
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def _get_session(self) -> Session:
        """Crée une nouvelle session de base de données."""
        return self.SessionLocal()

    # ============================================================================
    # SECTION 1: CRÉATION D'UTILISATEURS
    # ============================================================================

    def create_user(
        self,
        email: str,
        name: Optional[str] = None,
        role: RoleType = RoleType.FREE,
        google_id: Optional[str] = None,
        is_active: bool = True
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Crée un nouvel utilisateur dans la base de données.

        Args:
            email: Adresse email de l'utilisateur (sera chiffrée)
            name: Nom de l'utilisateur (sera chiffré)
            role: Rôle de l'utilisateur (FREE, MEDIUM, PREMIUM)
            google_id: ID Google de l'utilisateur (sera chiffré)
            is_active: Si l'utilisateur est actif

        Returns:
            Tuple (success: bool, message: str, user: Optional[User])
        """
        db = self._get_session()
        try:
            # Vérifier si l'email existe déjà
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                return False, f"❌ L'utilisateur avec l'email {email} existe déjà (ID: {existing_user.id})", None

            # Créer le nouvel utilisateur
            new_user = User(
                email=email,
                name=name,
                google_id=google_id,
                role=role,
                is_active=is_active
            )

            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            return True, f"✅ Utilisateur créé avec succès (ID: {new_user.id})", new_user

        except Exception as e:
            db.rollback()
            return False, f"❌ Erreur lors de la création: {str(e)}", None
        finally:
            db.close()

    def create_users_batch(
        self,
        users_data: List[Dict[str, Any]]
    ) -> Tuple[int, int, List[str]]:
        """
        Crée plusieurs utilisateurs en une seule transaction.

        Args:
            users_data: Liste de dictionnaires avec les données utilisateurs
                       Format: [{"email": "...", "name": "...", "role": RoleType.FREE}, ...]

        Returns:
            Tuple (created: int, skipped: int, messages: List[str])
        """
        db = self._get_session()
        created_count = 0
        skipped_count = 0
        messages = []

        try:
            for user_data in users_data:
                email = user_data.get("email")
                if not email:
                    messages.append("⚠️  Email manquant, utilisateur ignoré")
                    skipped_count += 1
                    continue

                # Vérifier si l'utilisateur existe
                existing = db.query(User).filter(User.email == email).first()
                if existing:
                    messages.append(f"⚠️  {email} existe déjà, ignoré")
                    skipped_count += 1
                    continue

                # Créer l'utilisateur
                new_user = User(
                    email=email,
                    name=user_data.get("name"),
                    google_id=user_data.get("google_id"),
                    role=user_data.get("role", RoleType.FREE),
                    is_active=user_data.get("is_active", True)
                )
                db.add(new_user)
                created_count += 1
                messages.append(f"✅ {email} créé")

            db.commit()
            return created_count, skipped_count, messages

        except Exception as e:
            db.rollback()
            return 0, len(users_data), [f"❌ Erreur: {str(e)}"]
        finally:
            db.close()

    # ============================================================================
    # SECTION 2: LECTURE ET RECHERCHE
    # ============================================================================

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Recherche un utilisateur par son email.

        Args:
            email: Email à rechercher (sera chiffré pour la comparaison)

        Returns:
            User ou None si non trouvé
        """
        db = self._get_session()
        try:
            user = db.query(User).filter(User.email == email).first()
            if user:
                # Force le déchargement pour que les données restent accessibles
                db.expunge(user)
            return user
        finally:
            db.close()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Recherche un utilisateur par son ID.

        Args:
            user_id: UUID de l'utilisateur (string ou UUID)

        Returns:
            User ou None si non trouvé
        """
        db = self._get_session()
        try:
            if isinstance(user_id, str):
                user_id = uuid_module.UUID(user_id)
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                db.expunge(user)
            return user
        finally:
            db.close()

    def list_all_users(
        self,
        show_inactive: bool = False,
        role_filter: Optional[RoleType] = None
    ) -> List[User]:
        """
        Liste tous les utilisateurs.

        Args:
            show_inactive: Inclure les utilisateurs inactifs
            role_filter: Filtrer par rôle spécifique

        Returns:
            Liste d'utilisateurs (données déchiffrées automatiquement)
        """
        db = self._get_session()
        try:
            query = db.query(User)

            if not show_inactive:
                query = query.filter(User.is_active == True)

            if role_filter:
                query = query.filter(User.role == role_filter)

            users = query.order_by(User.created_at.desc()).all()

            # Expunge pour garder les données accessibles
            for user in users:
                db.expunge(user)

            return users
        finally:
            db.close()

    def list_users_by_role(self, role: RoleType) -> List[User]:
        """
        Liste tous les utilisateurs d'un rôle spécifique.

        Args:
            role: Rôle à filtrer (FREE, MEDIUM, PREMIUM)

        Returns:
            Liste d'utilisateurs
        """
        return self.list_all_users(show_inactive=False, role_filter=role)

    def get_user_stats(self) -> Dict[str, Any]:
        """
        Génère des statistiques sur les utilisateurs.

        Returns:
            Dictionnaire avec les stats (total, par rôle, actifs/inactifs)
        """
        db = self._get_session()
        try:
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.is_active == True).count()
            inactive_users = total_users - active_users

            # Stats par rôle
            by_role = {}
            for role in RoleType:
                count = db.query(User).filter(User.role == role).count()
                by_role[role.value] = count

            return {
                "total_users": total_users,
                "active": active_users,
                "inactive": inactive_users,
                "by_role": by_role
            }
        finally:
            db.close()

    def get_user_usage_history(
        self,
        email_or_id: str,
        days: int = 30
    ) -> Tuple[Optional[User], List[UsageLog]]:
        """
        Récupère l'historique d'utilisation d'un utilisateur.

        Args:
            email_or_id: Email ou ID de l'utilisateur
            days: Nombre de jours d'historique

        Returns:
            Tuple (user: User, logs: List[UsageLog])
        """
        db = self._get_session()
        try:
            # Trouver l'utilisateur
            user = self._find_user(db, email_or_id)
            if not user:
                return None, []

            # Récupérer les logs
            since_date = datetime.utcnow() - timedelta(days=days)
            logs = db.query(UsageLog).filter(
                and_(
                    UsageLog.user_id == user.id,
                    UsageLog.timestamp >= since_date
                )
            ).order_by(UsageLog.timestamp.desc()).all()

            db.expunge(user)
            for log in logs:
                db.expunge(log)

            return user, logs
        finally:
            db.close()

    # ============================================================================
    # SECTION 3: MISE À JOUR ET SUPPRESSION
    # ============================================================================

    def update_user_role(
        self,
        email_or_id: str,
        new_role: RoleType
    ) -> Tuple[bool, str]:
        """
        Met à jour le rôle d'un utilisateur.

        Args:
            email_or_id: Email ou ID de l'utilisateur
            new_role: Nouveau rôle (FREE, MEDIUM, PREMIUM)

        Returns:
            Tuple (success: bool, message: str)
        """
        db = self._get_session()
        try:
            user = self._find_user(db, email_or_id)
            if not user:
                return False, f"❌ Utilisateur non trouvé: {email_or_id}"

            old_role = user.role
            user.role = new_role
            db.commit()

            return True, f"✅ Rôle mis à jour: {old_role.value} → {new_role.value}"

        except Exception as e:
            db.rollback()
            return False, f"❌ Erreur: {str(e)}"
        finally:
            db.close()

    def toggle_user_status(
        self,
        email_or_id: str,
        is_active: bool
    ) -> Tuple[bool, str]:
        """
        Active ou désactive un utilisateur.

        Args:
            email_or_id: Email ou ID de l'utilisateur
            is_active: True pour activer, False pour désactiver

        Returns:
            Tuple (success: bool, message: str)
        """
        db = self._get_session()
        try:
            user = self._find_user(db, email_or_id)
            if not user:
                return False, f"❌ Utilisateur non trouvé: {email_or_id}"

            user.is_active = is_active
            db.commit()

            status = "activé" if is_active else "désactivé"
            return True, f"✅ Utilisateur {status}"

        except Exception as e:
            db.rollback()
            return False, f"❌ Erreur: {str(e)}"
        finally:
            db.close()

    def delete_user(
        self,
        email_or_id: str,
        force: bool = False
    ) -> Tuple[bool, str]:
        """
        Supprime un utilisateur de la base de données.

        Args:
            email_or_id: Email ou ID de l'utilisateur
            force: Si False, demande confirmation

        Returns:
            Tuple (success: bool, message: str)
        """
        db = self._get_session()
        try:
            user = self._find_user(db, email_or_id)
            if not user:
                return False, f"❌ Utilisateur non trouvé: {email_or_id}"

            user_email = user.email
            user_id = user.id

            # Confirmation
            if not force:
                print(f"\n⚠️  ATTENTION: Suppression de l'utilisateur")
                print(f"   Email: {user_email}")
                print(f"   ID: {user_id}")
                print(f"   Rôle: {user.role.value}")
                response = input("\n   Confirmer la suppression? (y/N): ")
                if response.lower() != 'y':
                    return False, "❌ Suppression annulée"

            # Supprimer (cascade sur subscriptions et usage_logs)
            db.delete(user)
            db.commit()

            return True, f"✅ Utilisateur {user_email} supprimé"

        except Exception as e:
            db.rollback()
            return False, f"❌ Erreur: {str(e)}"
        finally:
            db.close()

    # ============================================================================
    # SECTION 4: DÉTECTION DE DOUBLONS
    # ============================================================================

    def find_duplicate_emails(self) -> List[Dict[str, Any]]:
        """
        Détecte les emails en doublon dans la base.

        Returns:
            Liste de dictionnaires avec les doublons trouvés
        """
        db = self._get_session()
        try:
            # Récupérer tous les utilisateurs
            users = db.query(User).all()

            # Grouper par email (déchiffré)
            email_groups = defaultdict(list)
            for user in users:
                email_groups[user.email].append(user)

            # Filtrer les doublons
            duplicates = []
            for email, user_list in email_groups.items():
                if len(user_list) > 1:
                    duplicates.append({
                        "email": email,
                        "count": len(user_list),
                        "users": [
                            {
                                "id": str(user.id),
                                "name": user.name,
                                "role": user.role.value,
                                "created_at": user.created_at,
                                "is_active": user.is_active
                            }
                            for user in user_list
                        ]
                    })

            return duplicates

        finally:
            db.close()

    def find_duplicate_google_ids(self) -> List[Dict[str, Any]]:
        """
        Détecte les google_id en doublon dans la base.

        Returns:
            Liste de dictionnaires avec les doublons trouvés
        """
        db = self._get_session()
        try:
            # Récupérer tous les utilisateurs avec google_id
            users = db.query(User).filter(User.google_id.isnot(None)).all()

            # Grouper par google_id (déchiffré)
            google_id_groups = defaultdict(list)
            for user in users:
                if user.google_id:  # Double vérification
                    google_id_groups[user.google_id].append(user)

            # Filtrer les doublons
            duplicates = []
            for google_id, user_list in google_id_groups.items():
                if len(user_list) > 1:
                    duplicates.append({
                        "google_id": google_id,
                        "count": len(user_list),
                        "users": [
                            {
                                "id": str(user.id),
                                "email": user.email,
                                "name": user.name,
                                "role": user.role.value,
                                "created_at": user.created_at
                            }
                            for user in user_list
                        ]
                    })

            return duplicates

        finally:
            db.close()

    def find_all_duplicates(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Détecte tous les types de doublons.

        Returns:
            Dictionnaire avec email_duplicates et google_id_duplicates
        """
        return {
            "email_duplicates": self.find_duplicate_emails(),
            "google_id_duplicates": self.find_duplicate_google_ids()
        }

    # ============================================================================
    # SECTION 5: NETTOYAGE DE DOUBLONS
    # ============================================================================

    def cleanup_duplicates(
        self,
        strategy: Literal['keep_newest', 'keep_oldest', 'keep_most_active'] = 'keep_newest',
        dry_run: bool = True
    ) -> Tuple[int, List[str]]:
        """
        Nettoie les doublons selon une stratégie.

        Args:
            strategy: Stratégie de nettoyage
                     - 'keep_newest': Garde le plus récent
                     - 'keep_oldest': Garde le plus ancien
                     - 'keep_most_active': Garde celui avec le plus d'usage
            dry_run: Si True, simule sans supprimer

        Returns:
            Tuple (deleted_count: int, messages: List[str])
        """
        db = self._get_session()
        deleted_count = 0
        messages = []

        try:
            duplicates = self.find_duplicate_emails()

            if not duplicates:
                messages.append("✅ Aucun doublon trouvé")
                return 0, messages

            messages.append(f"\n{'[DRY RUN] ' if dry_run else ''}Nettoyage de {len(duplicates)} groupe(s) de doublons\n")

            for dup in duplicates:
                email = dup["email"]
                user_ids = [u["id"] for u in dup["users"]]

                # Charger les utilisateurs complets
                users = db.query(User).filter(User.id.in_([uuid_module.UUID(uid) for uid in user_ids])).all()

                # Déterminer quel utilisateur garder
                keep_user = self._select_user_to_keep(users, strategy, db)
                to_delete = [u for u in users if u.id != keep_user.id]

                messages.append(f"📧 {email} ({len(users)} doublons)")
                messages.append(f"   ✅ Garde: {keep_user.id} (créé: {keep_user.created_at})")

                for user in to_delete:
                    messages.append(f"   ❌ Supprime: {user.id} (créé: {user.created_at})")
                    if not dry_run:
                        # Fusionner les historiques d'usage avant suppression
                        db.execute(
                            UsageLog.__table__.update()
                            .where(UsageLog.user_id == user.id)
                            .values(user_id=keep_user.id)
                        )
                        db.delete(user)
                        deleted_count += 1

                messages.append("")

            if not dry_run:
                db.commit()
                messages.append(f"✅ {deleted_count} utilisateur(s) supprimé(s)")
            else:
                messages.append(f"ℹ️  [DRY RUN] {deleted_count} utilisateur(s) auraient été supprimés")

            return deleted_count, messages

        except Exception as e:
            db.rollback()
            messages.append(f"❌ Erreur: {str(e)}")
            return 0, messages
        finally:
            db.close()

    def _select_user_to_keep(
        self,
        users: List[User],
        strategy: str,
        db: Session
    ) -> User:
        """
        Sélectionne l'utilisateur à garder selon la stratégie.

        Args:
            users: Liste des utilisateurs en doublon
            strategy: Stratégie de sélection
            db: Session de base de données

        Returns:
            L'utilisateur à conserver
        """
        if strategy == 'keep_newest':
            return max(users, key=lambda u: u.created_at)
        elif strategy == 'keep_oldest':
            return min(users, key=lambda u: u.created_at)
        elif strategy == 'keep_most_active':
            # Compter les usages de chaque utilisateur
            usage_counts = {}
            for user in users:
                count = db.query(UsageLog).filter(UsageLog.user_id == user.id).count()
                usage_counts[user.id] = count
            return max(users, key=lambda u: usage_counts[u.id])
        else:
            # Par défaut, garder le plus récent
            return max(users, key=lambda u: u.created_at)

    def remove_duplicate(
        self,
        email_or_id: str,
        confirm: bool = False
    ) -> Tuple[bool, str]:
        """
        Supprime un utilisateur spécifique identifié comme doublon.

        Args:
            email_or_id: Email ou ID de l'utilisateur à supprimer
            confirm: Si True, supprime sans demander confirmation

        Returns:
            Tuple (success: bool, message: str)
        """
        return self.delete_user(email_or_id, force=confirm)

    # ============================================================================
    # SECTION 6: VALIDATION ET SANTÉ
    # ============================================================================

    def verify_encryption_integrity(self) -> Tuple[bool, List[str]]:
        """
        Vérifie que le chiffrement/déchiffrement fonctionne correctement.

        Returns:
            Tuple (all_ok: bool, messages: List[str])
        """
        messages = []
        all_ok = True

        try:
            # Test 1: Vérifier la clé de chiffrement
            test_data = "test_encryption_data"
            encrypted = encryption_manager.encrypt(test_data)
            decrypted = encryption_manager.decrypt(encrypted)

            if decrypted == test_data:
                messages.append("✅ Clé de chiffrement valide")
            else:
                messages.append("❌ Problème avec la clé de chiffrement")
                all_ok = False

            # Test 2: Tester avec un utilisateur réel
            db = self._get_session()
            try:
                user = db.query(User).first()
                if user:
                    # Vérifier qu'on peut lire les données chiffrées
                    email = user.email  # Déchiffré automatiquement
                    name = user.name
                    google_id = user.google_id

                    if email and '@' in email:
                        messages.append("✅ Déchiffrement des emails fonctionne")
                    else:
                        messages.append("⚠️  Problème potentiel avec le déchiffrement des emails")
                        all_ok = False
                else:
                    messages.append("ℹ️  Aucun utilisateur dans la base pour tester")
            finally:
                db.close()

        except Exception as e:
            messages.append(f"❌ Erreur lors de la vérification: {str(e)}")
            all_ok = False

        return all_ok, messages

    def validate_database_health(self) -> Dict[str, Any]:
        """
        Effectue une validation complète de la santé de la base.

        Returns:
            Dictionnaire avec les résultats de validation
        """
        db = self._get_session()
        try:
            health = {}

            # 1. Vérifier le chiffrement
            encryption_ok, _ = self.verify_encryption_integrity()
            health["encryption_ok"] = encryption_ok

            # 2. Compter les doublons
            email_dups = self.find_duplicate_emails()
            google_id_dups = self.find_duplicate_google_ids()
            health["email_duplicates_count"] = len(email_dups)
            health["google_id_duplicates_count"] = len(google_id_dups)

            # 3. Vérifier les enregistrements orphelins
            total_users = db.query(User).count()
            total_subscriptions = db.query(Subscription).count()
            total_usage_logs = db.query(UsageLog).count()

            # Subscriptions orphelines
            orphaned_subs = db.query(Subscription).filter(
                ~Subscription.user_id.in_(db.query(User.id))
            ).count()

            # Usage logs orphelins
            orphaned_logs = db.query(UsageLog).filter(
                ~UsageLog.user_id.in_(db.query(User.id))
            ).count()

            health["total_users"] = total_users
            health["total_subscriptions"] = total_subscriptions
            health["total_usage_logs"] = total_usage_logs
            health["orphaned_subscriptions"] = orphaned_subs
            health["orphaned_usage_logs"] = orphaned_logs

            # 4. Vérifier les emails invalides
            users = db.query(User).all()
            invalid_emails = []
            for user in users:
                if user.email and not self._is_valid_email(user.email):
                    invalid_emails.append(user.email)

            health["invalid_emails_count"] = len(invalid_emails)
            health["invalid_emails"] = invalid_emails[:5]  # Limiter à 5 exemples

            return health

        finally:
            db.close()

    def check_orphaned_records(self) -> Dict[str, List[str]]:
        """
        Identifie les enregistrements orphelins (sans utilisateur parent).

        Returns:
            Dictionnaire avec les IDs des enregistrements orphelins
        """
        db = self._get_session()
        try:
            orphaned = {
                "subscriptions": [],
                "usage_logs": []
            }

            # Subscriptions orphelines
            orphaned_subs = db.query(Subscription).filter(
                ~Subscription.user_id.in_(db.query(User.id))
            ).all()
            orphaned["subscriptions"] = [str(sub.id) for sub in orphaned_subs]

            # Usage logs orphelins
            orphaned_logs = db.query(UsageLog).filter(
                ~UsageLog.user_id.in_(db.query(User.id))
            ).all()
            orphaned["usage_logs"] = [str(log.id) for log in orphaned_logs]

            return orphaned

        finally:
            db.close()

    def generate_health_report(self) -> str:
        """
        Génère un rapport de santé complet en format texte.

        Returns:
            Rapport formaté en string
        """
        health = self.validate_database_health()
        stats = self.get_user_stats()

        report = []
        report.append("\n" + "=" * 60)
        report.append("📊 RAPPORT DE SANTÉ DE LA BASE DE DONNÉES")
        report.append("=" * 60)

        # Section 1: Statistiques générales
        report.append("\n📈 STATISTIQUES GÉNÉRALES")
        report.append(f"   Total utilisateurs: {stats['total_users']}")
        report.append(f"   Actifs: {stats['active']}")
        report.append(f"   Inactifs: {stats['inactive']}")
        report.append(f"\n   Par rôle:")
        for role, count in stats['by_role'].items():
            report.append(f"      - {role}: {count}")

        # Section 2: Chiffrement
        report.append(f"\n🔐 CHIFFREMENT")
        report.append(f"   Statut: {'✅ OK' if health['encryption_ok'] else '❌ PROBLÈME'}")

        # Section 3: Doublons
        report.append(f"\n👥 DOUBLONS")
        total_dups = health['email_duplicates_count'] + health['google_id_duplicates_count']
        if total_dups == 0:
            report.append(f"   ✅ Aucun doublon détecté")
        else:
            report.append(f"   ⚠️  {health['email_duplicates_count']} doublon(s) d'email")
            report.append(f"   ⚠️  {health['google_id_duplicates_count']} doublon(s) de google_id")

        # Section 4: Enregistrements orphelins
        report.append(f"\n🗑️  ENREGISTREMENTS ORPHELINS")
        total_orphans = health['orphaned_subscriptions'] + health['orphaned_usage_logs']
        if total_orphans == 0:
            report.append(f"   ✅ Aucun enregistrement orphelin")
        else:
            report.append(f"   ⚠️  {health['orphaned_subscriptions']} subscription(s) orpheline(s)")
            report.append(f"   ⚠️  {health['orphaned_usage_logs']} usage log(s) orphelin(s)")

        # Section 5: Validation des emails
        report.append(f"\n📧 VALIDATION DES EMAILS")
        if health['invalid_emails_count'] == 0:
            report.append(f"   ✅ Tous les emails sont valides")
        else:
            report.append(f"   ⚠️  {health['invalid_emails_count']} email(s) invalide(s)")
            if health['invalid_emails']:
                report.append(f"   Exemples: {', '.join(health['invalid_emails'])}")

        # Section 6: Verdict global
        report.append(f"\n{'=' * 60}")
        all_ok = (
            health['encryption_ok'] and
            total_dups == 0 and
            total_orphans == 0 and
            health['invalid_emails_count'] == 0
        )
        if all_ok:
            report.append("✅ BASE DE DONNÉES EN BONNE SANTÉ")
        else:
            report.append("⚠️  PROBLÈMES DÉTECTÉS - ACTION RECOMMANDÉE")
        report.append("=" * 60 + "\n")

        return "\n".join(report)

    # ============================================================================
    # SECTION 7: FONCTIONS UTILITAIRES INTERNES
    # ============================================================================

    def _find_user(self, db: Session, email_or_id: str) -> Optional[User]:
        """
        Trouve un utilisateur par email ou ID.

        Args:
            db: Session de base de données
            email_or_id: Email ou UUID de l'utilisateur

        Returns:
            User ou None
        """
        # Essayer comme UUID
        try:
            user_uuid = uuid_module.UUID(email_or_id)
            return db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            # Sinon, rechercher par email
            return db.query(User).filter(User.email == email_or_id).first()

    def _is_valid_email(self, email: str) -> bool:
        """
        Valide le format d'un email.

        Args:
            email: Email à valider

        Returns:
            True si valide, False sinon
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


# ============================================================================
# FONCTIONS UTILITAIRES D'AFFICHAGE
# ============================================================================

def print_user_table(users: List[User], show_google_id: bool = False):
    """
    Affiche une liste d'utilisateurs dans un tableau formaté.

    Args:
        users: Liste d'utilisateurs à afficher
        show_google_id: Afficher la colonne google_id
    """
    if not users:
        print("\nℹ️  Aucun utilisateur à afficher\n")
        return

    headers = ["ID", "Email", "Name", "Role", "Active", "Created"]
    if show_google_id:
        headers.insert(3, "Google ID")

    table_data = []
    for user in users:
        row = [
            str(user.id)[:8] + "...",  # Tronquer l'UUID
            user.email or "N/A",
            user.name or "N/A",
            user.role.value,
            "✅" if user.is_active else "❌",
            user.created_at.strftime("%Y-%m-%d")
        ]
        if show_google_id:
            row.insert(3, (user.google_id[:12] + "...") if user.google_id else "N/A")

        table_data.append(row)

    print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"\nTotal: {len(users)} utilisateur(s)\n")


def print_stats_summary(stats: Dict[str, Any]):
    """
    Affiche un résumé des statistiques.

    Args:
        stats: Dictionnaire de statistiques
    """
    print("\n" + "=" * 50)
    print("📊 STATISTIQUES UTILISATEURS")
    print("=" * 50)
    print(f"\nTotal: {stats['total_users']}")
    print(f"Actifs: {stats['active']}")
    print(f"Inactifs: {stats['inactive']}")
    print(f"\nPar rôle:")
    for role, count in stats['by_role'].items():
        percentage = (count / stats['total_users'] * 100) if stats['total_users'] > 0 else 0
        print(f"  {role:8s}: {count:3d} ({percentage:5.1f}%)")
    print("=" * 50 + "\n")


def print_duplicates_report(duplicates: Dict[str, List[Dict[str, Any]]]):
    """
    Affiche un rapport détaillé des doublons.

    Args:
        duplicates: Dictionnaire avec email_duplicates et google_id_duplicates
    """
    email_dups = duplicates.get("email_duplicates", [])
    google_id_dups = duplicates.get("google_id_duplicates", [])

    total = len(email_dups) + len(google_id_dups)

    if total == 0:
        print("\n✅ Aucun doublon détecté\n")
        return

    print("\n" + "=" * 60)
    print(f"⚠️  DOUBLONS DÉTECTÉS: {total}")
    print("=" * 60)

    # Doublons d'email
    if email_dups:
        print(f"\n📧 DOUBLONS D'EMAIL: {len(email_dups)}")
        for dup in email_dups:
            print(f"\n   Email: {dup['email']} ({dup['count']} occurrences)")
            for i, user in enumerate(dup['users'], 1):
                marker = "⭐" if i == 1 else "  "
                print(f"   {marker} {i}. ID: {user['id'][:8]}... | "
                      f"Créé: {user['created_at'].strftime('%Y-%m-%d')} | "
                      f"Rôle: {user['role']} | "
                      f"{'Actif' if user['is_active'] else 'Inactif'}")

    # Doublons de google_id
    if google_id_dups:
        print(f"\n🔑 DOUBLONS DE GOOGLE_ID: {len(google_id_dups)}")
        for dup in google_id_dups:
            print(f"\n   Google ID: {dup['google_id'][:12]}... ({dup['count']} occurrences)")
            for i, user in enumerate(dup['users'], 1):
                marker = "⭐" if i == 1 else "  "
                print(f"   {marker} {i}. {user['email']} | "
                      f"Créé: {user['created_at'].strftime('%Y-%m-%d')} | "
                      f"Rôle: {user['role']}")

    print("\n" + "=" * 60 + "\n")


def print_usage_history(user: User, logs: List[UsageLog]):
    """
    Affiche l'historique d'utilisation d'un utilisateur.

    Args:
        user: Utilisateur
        logs: Liste des logs d'usage
    """
    print("\n" + "=" * 60)
    print(f"📊 HISTORIQUE D'UTILISATION")
    print("=" * 60)
    print(f"\nUtilisateur: {user.email}")
    print(f"Rôle: {user.role.value}")
    print(f"Nombre d'actions: {len(logs)}")

    if not logs:
        print("\nℹ️  Aucune utilisation enregistrée\n")
        return

    # Grouper par feature
    by_feature = defaultdict(int)
    for log in logs:
        by_feature[log.feature] += 1

    print(f"\nPar fonctionnalité:")
    for feature, count in sorted(by_feature.items(), key=lambda x: x[1], reverse=True):
        print(f"  {feature:30s}: {count:3d}")

    # Dernières actions
    print(f"\nDernières actions (max 10):")
    for log in logs[:10]:
        print(f"  {log.timestamp.strftime('%Y-%m-%d %H:%M')} - {log.feature}")

    print("=" * 60 + "\n")


# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================

if __name__ == "__main__":
    print("🔧 Module Database Helper chargé avec succès!\n")
    print("Créez une instance avec: helper = DatabaseHelper()\n")
    print("Fonctions disponibles:")
    print("  - create_user(), create_users_batch()")
    print("  - get_user_by_email(), get_user_by_id()")
    print("  - list_all_users(), list_users_by_role()")
    print("  - get_user_stats(), get_user_usage_history()")
    print("  - update_user_role(), toggle_user_status(), delete_user()")
    print("  - find_duplicate_emails(), find_duplicate_google_ids()")
    print("  - cleanup_duplicates(), remove_duplicate()")
    print("  - verify_encryption_integrity(), validate_database_health()")
    print("  - generate_health_report()")
    print("\nFonctions d'affichage:")
    print("  - print_user_table(), print_stats_summary()")
    print("  - print_duplicates_report(), print_usage_history()")
