"""
V3 Story 3.1 - Router admin pour le monitoring.
Endpoints proteges par require_admin (whitelist ADMIN_EMAILS).
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User, RoleType
from schemas.admin import PremiumCountResponse, PremiumUserDetail
from utils.admin_auth import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/premium-count", response_model=PremiumCountResponse)
async def get_premium_count(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Retourne le nombre d'utilisateurs premium actifs avec leurs details.

    Requiert:
    - Authentification JWT valide (401 si absent)
    - Email dans ADMIN_EMAILS (403 si non admin)

    Returns:
        PremiumCountResponse: count + liste des details (id, created_at, subscription_status)
    """
    # Requeter les utilisateurs PREMIUM actifs
    premium_users = db.query(User).filter(
        User.role == RoleType.PREMIUM,
        User.is_active == True
    ).order_by(User.created_at.desc()).all()

    # Construire la liste des details (sans donnees chiffrees email/name)
    details = [
        PremiumUserDetail(
            id=user.id,
            created_at=user.created_at,
            subscription_status=user.subscription_status
        )
        for user in premium_users
    ]

    logger.info(f"Admin {current_user.id} a consulte le compteur premium: {len(details)} utilisateurs")

    return PremiumCountResponse(
        count=len(details),
        details=details
    )
