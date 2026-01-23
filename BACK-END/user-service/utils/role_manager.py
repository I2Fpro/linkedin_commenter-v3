"""
Gestionnaire pour les changements de rôle des utilisateurs.
Enregistre automatiquement l'historique des changements dans la table role_change_history.
"""

from sqlalchemy.orm import Session
from typing import Optional
import uuid
from models import User, RoleType, RoleChangeHistory


class RoleManager:
    """
    Gestionnaire pour les changements de rôle avec traçabilité.
    """

    @staticmethod
    def change_user_role(
        db: Session,
        user: User,
        new_role: RoleType,
        changed_by: Optional[str] = None,
        reason: Optional[str] = None,
        meta_data: Optional[dict] = None
    ) -> RoleChangeHistory:
        """
        Change le rôle d'un utilisateur et enregistre le changement dans l'historique.

        Args:
            db: Session de base de données
            user: L'utilisateur dont on change le rôle
            new_role: Le nouveau rôle à attribuer
            changed_by: Email ou ID de l'admin qui fait le changement (optionnel)
            reason: Raison du changement (optionnel)
            meta_data: Métadonnées supplémentaires (optionnel)

        Returns:
            L'entrée d'historique créée

        Raises:
            ValueError: Si le nouveau rôle est le même que l'ancien
        """
        old_role = user.role

        # Vérifier si le rôle change vraiment
        if old_role == new_role:
            raise ValueError(f"L'utilisateur {user.email} a déjà le rôle {new_role.value}")

        # Créer l'entrée d'historique
        history_entry = RoleChangeHistory(
            id=uuid.uuid4(),
            user_id=user.id,
            old_role=old_role,
            new_role=new_role,
            changed_by=changed_by,
            reason=reason,
            meta_data=meta_data
        )

        # Mettre à jour le rôle de l'utilisateur
        user.role = new_role

        # Ajouter l'entrée d'historique à la session
        db.add(history_entry)
        db.flush()  # Pour obtenir l'ID si nécessaire

        return history_entry

    @staticmethod
    def record_initial_role(
        db: Session,
        user: User,
        reason: Optional[str] = "Création initiale de l'utilisateur",
        meta_data: Optional[dict] = None
    ) -> RoleChangeHistory:
        """
        Enregistre le rôle initial d'un nouvel utilisateur dans l'historique.

        Args:
            db: Session de base de données
            user: L'utilisateur nouvellement créé
            reason: Raison de l'attribution du rôle initial
            meta_data: Métadonnées supplémentaires (optionnel)

        Returns:
            L'entrée d'historique créée
        """
        history_entry = RoleChangeHistory(
            id=uuid.uuid4(),
            user_id=user.id,
            old_role=None,  # NULL pour la création initiale
            new_role=user.role,
            changed_by=None,
            reason=reason,
            meta_data=meta_data
        )

        db.add(history_entry)
        db.flush()

        return history_entry

    @staticmethod
    def get_user_role_history(
        db: Session,
        user_id: uuid.UUID,
        limit: Optional[int] = None
    ) -> list:
        """
        Récupère l'historique des changements de rôle d'un utilisateur.

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            limit: Nombre maximum d'entrées à retourner (optionnel)

        Returns:
            Liste des entrées d'historique, triées par date (plus récent en premier)
        """
        query = db.query(RoleChangeHistory).filter(
            RoleChangeHistory.user_id == user_id
        ).order_by(RoleChangeHistory.changed_at.desc())

        if limit:
            query = query.limit(limit)

        return query.all()

    @staticmethod
    def get_role_change_summary(db: Session, user_id: uuid.UUID) -> dict:
        """
        Récupère un résumé des changements de rôle d'un utilisateur.

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur

        Returns:
            Dictionnaire avec le résumé:
            {
                "total_changes": int,
                "current_role": str,
                "initial_role": str,
                "last_change_date": datetime,
                "changes": list
            }
        """
        history = RoleManager.get_user_role_history(db, user_id)

        if not history:
            return {
                "total_changes": 0,
                "current_role": None,
                "initial_role": None,
                "last_change_date": None,
                "changes": []
            }

        # Le premier dans la liste est le plus récent
        most_recent = history[0]
        # Le dernier dans la liste est le plus ancien (création initiale)
        initial = history[-1]

        return {
            "total_changes": len(history),
            "current_role": most_recent.new_role.value,
            "initial_role": initial.new_role.value if initial.old_role is None else initial.old_role.value,
            "last_change_date": most_recent.changed_at,
            "changes": [
                {
                    "from": entry.old_role.value if entry.old_role else None,
                    "to": entry.new_role.value,
                    "date": entry.changed_at,
                    "changed_by": entry.changed_by,
                    "reason": entry.reason
                }
                for entry in history
            ]
        }
