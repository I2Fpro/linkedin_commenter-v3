"""
V3 Story 3.1 - Router admin pour le monitoring.
Endpoints proteges par require_admin (whitelist ADMIN_EMAILS).
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User, RoleType, UsageLog
from schemas.admin import PremiumCountResponse, PremiumUserDetail, TokenUsageResponse, TokenUsageDetail
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


@router.get("/token-usage", response_model=TokenUsageResponse)
async def get_token_usage(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Retourne la consommation de tokens OpenAI par utilisateur.

    Requiert:
    - Authentification JWT valide (401 si absent)
    - Email dans ADMIN_EMAILS (403 si non admin)

    Les donnees proviennent de usage_logs.meta_data (JSONB)
    avec les champs tokens_input, tokens_output, model.

    Returns:
        TokenUsageResponse: Liste des utilisateurs avec leur consommation,
        triee par consommation totale decroissante.

    TODO (Code Review 3.2):
    - H2: Ajouter pagination pour eviter OOM avec beaucoup de logs (skip/limit params)
    - M3: Ajouter rate limiting (slowapi) pour proteger contre les abus
    """
    # Recuperer tous les usage_logs avec meta_data contenant des tokens
    # TODO H2: Pagination - actuellement charge tous les logs en memoire
    logs = db.query(UsageLog).filter(
        UsageLog.meta_data.isnot(None)
    ).all()

    # Agreger par user_id
    user_stats = {}
    for log in logs:
        if not log.meta_data:
            continue

        user_id = str(log.user_id)
        tokens_input = log.meta_data.get("tokens_input", 0) or 0
        tokens_output = log.meta_data.get("tokens_output", 0) or 0
        model = log.meta_data.get("model", "")

        if user_id not in user_stats:
            user_stats[user_id] = {
                "user_id": log.user_id,
                "total_tokens_input": 0,
                "total_tokens_output": 0,
                "generation_count": 0,
                "models": set(),
                "last_generation": None
            }

        stats = user_stats[user_id]
        stats["total_tokens_input"] += tokens_input
        stats["total_tokens_output"] += tokens_output
        stats["generation_count"] += 1
        if model:
            stats["models"].add(model)
        # Fix M2: Gerer le cas ou log.timestamp est None (donnees legacy V2)
        if log.timestamp and (stats["last_generation"] is None or log.timestamp > stats["last_generation"]):
            stats["last_generation"] = log.timestamp

    # Construire la liste des details
    details = []
    total_tokens_all = 0
    for stats in user_stats.values():
        total = stats["total_tokens_input"] + stats["total_tokens_output"]
        total_tokens_all += total
        details.append(TokenUsageDetail(
            user_id=stats["user_id"],
            total_tokens_input=stats["total_tokens_input"],
            total_tokens_output=stats["total_tokens_output"],
            total_tokens=total,
            generation_count=stats["generation_count"],
            # Fix M1: Ordre deterministe pour eviter des reponses API inconsistantes
            models_used=sorted(stats["models"]),
            last_generation=stats["last_generation"]
        ))

    # Trier par consommation totale decroissante (AC #2)
    details.sort(key=lambda x: x.total_tokens, reverse=True)

    logger.info(f"Admin {current_user.id} a consulte le token-usage: {len(details)} utilisateurs")

    return TokenUsageResponse(
        users=details,
        total_users=len(details),
        total_tokens_all=total_tokens_all
    )
