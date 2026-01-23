"""
Utilitaire d'identification utilisateur anonyme
Génère un identifiant unique et anonyme à partir d'un email (SHA-256)
Conforme RGPD - Ne stocke jamais l'email brut
"""

import hashlib
from typing import Optional


def anon_id_from_email(email: Optional[str]) -> str:
    """
    Génère un identifiant anonyme à partir d'un email

    Args:
        email: Adresse email de l'utilisateur

    Returns:
        Hash SHA-256 de l'email normalisé (minuscules, sans espaces)

    Example:
        >>> anon_id_from_email("user@example.com")
        'b4c9a289323b...'
    """
    if not email:
        return "anonymous"

    # Normaliser l'email: minuscules, sans espaces
    normalized = email.strip().lower()

    # Encoder en UTF-8 et calculer le SHA-256
    email_bytes = normalized.encode("utf-8")
    hash_obj = hashlib.sha256(email_bytes)

    # Retourner le hash en hexadécimal
    return hash_obj.hexdigest()


def resolve_distinct_id(request_body: dict, current_user: dict) -> str:
    """
    Résout le distinct_id pour PostHog en utilisant l'ordre de priorité:
    1. user_id envoyé par le frontend (déjà hashé)
    2. Email du current_user hashé côté backend (fallback)
    3. "anonymous" si aucune info disponible

    Args:
        request_body: Corps de la requête (peut contenir user_id)
        current_user: Informations utilisateur authentifié (peut contenir email)

    Returns:
        Identifiant distinct pour PostHog
    """
    # Priorité 1: user_id du frontend (déjà hashé)
    if request_body.get("user_id"):
        return request_body["user_id"]

    # Priorité 2: Hash de l'email du backend
    email = current_user.get("email")
    if email:
        return anon_id_from_email(email)

    # Fallback: anonymous
    return "anonymous"
