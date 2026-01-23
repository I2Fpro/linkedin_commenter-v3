"""
Module de chiffrement/déchiffrement pour les données sensibles en base de données.
Utilise Fernet (cryptographie symétrique) avec la clé définie dans ENCRYPTION_KEY.
"""

import os
from typing import Optional
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv("../.env")
load_dotenv()

class EncryptionManager:
    """Gestionnaire de chiffrement/déchiffrement des données sensibles."""

    def __init__(self):
        """Initialise le gestionnaire avec la clé de chiffrement depuis .env"""
        encryption_key = os.getenv("ENCRYPTION_KEY")

        if not encryption_key:
            raise ValueError(
                "ENCRYPTION_KEY n'est pas définie dans les variables d'environnement. "
                "Veuillez définir cette clé dans le fichier .env"
            )

        try:
            self.fernet = Fernet(encryption_key.encode())
        except Exception as e:
            raise ValueError(
                f"La clé ENCRYPTION_KEY n'est pas valide. "
                f"Utilisez Fernet.generate_key() pour générer une nouvelle clé. Erreur: {str(e)}"
            )

    def encrypt(self, data: str) -> Optional[str]:
        """
        Chiffre une chaîne de caractères.

        Args:
            data: La chaîne à chiffrer

        Returns:
            La chaîne chiffrée en base64, ou None si data est None
        """
        if data is None:
            return None

        try:
            encrypted_bytes = self.fernet.encrypt(data.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            raise ValueError(f"Erreur lors du chiffrement: {str(e)}")

    def decrypt(self, encrypted_data: str) -> Optional[str]:
        """
        Déchiffre une chaîne de caractères chiffrée.

        Args:
            encrypted_data: La chaîne chiffrée à déchiffrer

        Returns:
            La chaîne déchiffrée, ou None si encrypted_data est None
        """
        if encrypted_data is None:
            return None

        try:
            decrypted_bytes = self.fernet.decrypt(encrypted_data.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            raise ValueError(f"Erreur lors du déchiffrement: {str(e)}")

    def encrypt_if_not_none(self, data: Optional[str]) -> Optional[str]:
        """
        Chiffre une chaîne seulement si elle n'est pas None.
        Utile pour les champs optionnels.

        Args:
            data: La chaîne à chiffrer ou None

        Returns:
            La chaîne chiffrée ou None
        """
        return self.encrypt(data) if data is not None else None

    def decrypt_if_not_none(self, encrypted_data: Optional[str]) -> Optional[str]:
        """
        Déchiffre une chaîne seulement si elle n'est pas None.
        Utile pour les champs optionnels.

        Args:
            encrypted_data: La chaîne chiffrée ou None

        Returns:
            La chaîne déchiffrée ou None
        """
        return self.decrypt(encrypted_data) if encrypted_data is not None else None


# Instance globale du gestionnaire de chiffrement
encryption_manager = EncryptionManager()


def encrypt_field(value: str) -> Optional[str]:
    """
    Fonction helper pour chiffrer un champ.

    Args:
        value: La valeur à chiffrer

    Returns:
        La valeur chiffrée
    """
    return encryption_manager.encrypt(value)


def decrypt_field(encrypted_value: str) -> Optional[str]:
    """
    Fonction helper pour déchiffrer un champ.

    Args:
        encrypted_value: La valeur chiffrée

    Returns:
        La valeur déchiffrée
    """
    return encryption_manager.decrypt(encrypted_value)


def generate_encryption_key() -> str:
    """
    Génère une nouvelle clé de chiffrement Fernet.
    Cette fonction est utile pour générer une nouvelle clé à placer dans .env

    Returns:
        Une nouvelle clé de chiffrement encodée en base64
    """
    return Fernet.generate_key().decode()


if __name__ == "__main__":
    # Test du module
    print("Test du module de chiffrement/déchiffrement")
    print("=" * 50)

    # Test avec une donnée
    test_data = "Données sensibles à protéger"
    print(f"Données originales: {test_data}")

    encrypted = encrypt_field(test_data)
    print(f"Données chiffrées: {encrypted}")

    decrypted = decrypt_field(encrypted)
    print(f"Données déchiffrées: {decrypted}")

    assert test_data == decrypted, "Le déchiffrement ne correspond pas aux données originales!"
    print("\n✓ Test réussi!")

    # Génération d'une nouvelle clé (commenté car ne doit être fait qu'une fois)
    # print(f"\nNouvelle clé générée: {generate_encryption_key()}")
