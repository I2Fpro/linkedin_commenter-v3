"""
V3 Story 3.1 - Authentification admin via whitelist email.
Decorateur @require_admin pour proteger les endpoints admin.
"""
import os
import re
import logging
from fastapi import Depends, HTTPException, status
from auth import get_current_user
from models import User

logger = logging.getLogger(__name__)

# Pattern simple pour validation email (RFC 5322 simplifie)
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def is_valid_email(email: str) -> bool:
    """Valide le format d'une adresse email."""
    return bool(EMAIL_PATTERN.match(email))


def get_admin_emails() -> list[str]:
    """
    Recupere la liste des emails admin depuis la variable d'environnement.
    Format: emails separes par des virgules.
    Filtre les emails invalides et log un warning.
    """
    admin_emails_str = os.getenv("ADMIN_EMAILS", "")
    if not admin_emails_str:
        return []

    valid_emails = []
    for email in admin_emails_str.split(","):
        email = email.strip().lower()
        if email:
            if is_valid_email(email):
                valid_emails.append(email)
            else:
                logger.warning(f"ADMIN_EMAILS contient un email invalide ignore: {email}")

    return valid_emails


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency FastAPI pour verifier que l'utilisateur est admin.
    Utilise comme: Depends(require_admin)

    Raises:
        HTTPException 403 si l'utilisateur n'est pas admin
    """
    admin_emails = get_admin_emails()

    if not admin_emails:
        logger.warning("ADMIN_EMAILS non configure - acces admin refuse")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acces refuse - configuration admin manquante"
        )

    user_email = current_user.email.lower() if current_user.email else ""

    if user_email not in admin_emails:
        logger.warning(f"Tentative d'acces admin non autorise: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acces refuse - vous n'etes pas administrateur"
        )

    logger.info(f"Acces admin autorise pour: {current_user.id}")
    return current_user
