"""
Types SQLAlchemy personnalisés pour le chiffrement automatique des colonnes.
"""

from sqlalchemy.types import TypeDecorator, String
from typing import Optional
from utils.encryption import encryption_manager


class EncryptedString(TypeDecorator):
    """
    Type de colonne SQLAlchemy qui chiffre/déchiffre automatiquement les données.

    Usage dans un modèle:
        email = Column(EncryptedString(255), nullable=False)

    Les données seront automatiquement:
    - Chiffrées avant insertion/mise à jour en base
    - Déchiffrées lors de la lecture depuis la base
    """

    impl = String
    cache_ok = True

    def __init__(self, length=None, **kwargs):
        """
        Initialise le type de colonne chiffrée.

        Args:
            length: Longueur maximale de la colonne (doit être suffisante pour les données chiffrées)
        """
        # Les données chiffrées sont plus longues que les données originales
        # On recommande au moins 512 caractères pour les champs chiffrés
        if length and length < 512:
            length = 512
        super().__init__(length, **kwargs)

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """
        Appelé lors de l'insertion/mise à jour en base.
        Chiffre la valeur avant de la stocker.

        Args:
            value: La valeur non chiffrée
            dialect: Le dialecte SQL

        Returns:
            La valeur chiffrée
        """
        if value is None:
            return None

        return encryption_manager.encrypt(value)

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """
        Appelé lors de la lecture depuis la base.
        Déchiffre la valeur avant de la retourner.

        Args:
            value: La valeur chiffrée stockée en base
            dialect: Le dialecte SQL

        Returns:
            La valeur déchiffrée
        """
        if value is None:
            return None

        return encryption_manager.decrypt(value)
