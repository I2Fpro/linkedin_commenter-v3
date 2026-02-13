"""
V3 Story 3.1 - Router admin pour le monitoring.
Endpoints proteges par require_admin (whitelist ADMIN_EMAILS).
"""
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal

from database import get_db
from models import User, RoleType, UsageLog
from schemas.admin import (
    PremiumCountResponse, PremiumUserDetail, TokenUsageResponse, TokenUsageDetail,
    AnalyticsSummaryResponse, UserConsumptionItem, UserConsumptionResponse,
    UserGenerationItem, UserGenerationsResponse
)
from utils.admin_auth import require_admin
from utils.cost_calculator import calculate_cost_eur

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

    # Pre-charger les noms des utilisateurs (decryptes automatiquement par le modele)
    user_ids = set(log.user_id for log in logs if log.meta_data)
    users_map = {}
    if user_ids:
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        users_map = {user.id: user.name for user in users}

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
                "name": users_map.get(log.user_id, None),
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
            name=stats["name"],
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


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Retourne le resume analytics global (KPIs) pour la periode.

    Requiert:
    - Authentification JWT valide (401 si absent)
    - Email dans ADMIN_EMAILS (403 si non admin)

    Args:
        period: Periode (7d, 30d, 90d)

    Returns:
        AnalyticsSummaryResponse: Resume avec KPIs, couts, trends
    """
    days = int(period.rstrip('d'))

    # 1. Compter les utilisateurs par role
    users_by_role_query = text("""
        SELECT role, COUNT(*) as count
        FROM public.users
        WHERE is_active = true
        GROUP BY role
    """)
    users_by_role_result = db.execute(users_by_role_query).fetchall()
    users_by_role = {row.role: row.count for row in users_by_role_result}

    # 2. Recuperer les totaux de generations et tokens de la periode courante
    totals_query = text("""
        SELECT
            COALESCE(SUM(generation_count), 0) AS total_generations,
            COALESCE(SUM(total_tokens_input), 0) AS total_input,
            COALESCE(SUM(total_tokens_output), 0) AS total_output
        FROM analytics.user_consumption
        WHERE last_generation >= CURRENT_DATE - :days * INTERVAL '1 day'
           OR last_generation IS NULL
    """)
    totals_result = db.execute(totals_query, {"days": days}).fetchone()
    total_generations = int(totals_result.total_generations)
    total_input = int(totals_result.total_input)
    total_output = int(totals_result.total_output)

    # 3. Calculer le cout EUR total
    if total_input > 0 or total_output > 0:
        total_cost_eur = calculate_cost_eur(total_input, total_output)
    else:
        total_cost_eur = "0.00"

    # 4. Compter les essais actifs
    active_trials_query = text("""
        SELECT COUNT(*) as count
        FROM public.users
        WHERE trial_started_at IS NOT NULL
          AND trial_ends_at > CURRENT_TIMESTAMP
          AND role = 'PREMIUM'
    """)
    active_trials_result = db.execute(active_trials_query).fetchone()
    active_trials = int(active_trials_result.count)

    # 5. Calculer les trends (periode N vs N-1)
    trend_comments = None
    trend_cost = None

    # Recuperer les totaux de la periode precedente
    previous_totals_query = text("""
        SELECT
            COALESCE(SUM(daily_generations), 0) AS prev_generations,
            COALESCE(SUM(daily_tokens_input), 0) AS prev_input,
            COALESCE(SUM(daily_tokens_output), 0) AS prev_output
        FROM analytics.daily_summary
        WHERE date BETWEEN (CURRENT_DATE - 2 * :days * INTERVAL '1 day')
          AND (CURRENT_DATE - :days * INTERVAL '1 day')
    """)
    previous_result = db.execute(previous_totals_query, {"days": days}).fetchone()
    prev_generations = int(previous_result.prev_generations)
    prev_input = int(previous_result.prev_input)
    prev_output = int(previous_result.prev_output)

    # Trend comments
    if prev_generations > 0:
        trend_comments = ((total_generations - prev_generations) / prev_generations) * 100

    # Trend cost
    if prev_input > 0 or prev_output > 0:
        prev_cost_eur_str = calculate_cost_eur(prev_input, prev_output)
        prev_cost_eur = Decimal(prev_cost_eur_str)
        curr_cost_eur = Decimal(total_cost_eur)
        if prev_cost_eur > 0:
            trend_cost = float(((curr_cost_eur - prev_cost_eur) / prev_cost_eur) * 100)

    logger.info(f"Admin {current_user.id} a consulte analytics/summary: period={period}")

    return AnalyticsSummaryResponse(
        period=period,
        users_by_role=users_by_role,
        total_comments_generated=total_generations,
        total_cost_eur=total_cost_eur,
        active_trials=active_trials,
        trend_comments=trend_comments,
        trend_cost=trend_cost
    )


@router.get("/users/consumption", response_model=UserConsumptionResponse)
async def get_users_consumption(
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Retourne la consommation par utilisateur pour la periode.

    Requiert:
    - Authentification JWT valide (401 si absent)
    - Email dans ADMIN_EMAILS (403 si non admin)

    Args:
        period: Periode (7d, 30d, 90d)

    Returns:
        UserConsumptionResponse: Liste des utilisateurs avec consommation
    """
    days = int(period.rstrip('d'))

    # Query analytics.user_consumption avec filtre periode
    consumption_query = text("""
        SELECT
            user_id,
            role,
            generation_count,
            total_tokens_input,
            total_tokens_output,
            last_generation
        FROM analytics.user_consumption
        WHERE last_generation >= CURRENT_DATE - :days * INTERVAL '1 day'
           OR generation_count = 0
        ORDER BY (total_tokens_input + total_tokens_output) DESC
    """)
    consumption_result = db.execute(consumption_query, {"days": days}).fetchall()

    # Recuperer les user_ids pour charger les emails decryptes via ORM
    user_ids = [row.user_id for row in consumption_result]
    users_map = {}
    if user_ids:
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        users_map = {user.id: user.email for user in users}

    # Construire les items
    items = []
    for row in consumption_result:
        cost_eur = calculate_cost_eur(row.total_tokens_input, row.total_tokens_output)
        total_tokens = row.total_tokens_input + row.total_tokens_output

        items.append(UserConsumptionItem(
            user_id=row.user_id,
            email=users_map.get(row.user_id, "unknown@example.com"),
            role=row.role,
            generation_count=row.generation_count,
            total_tokens=total_tokens,
            cost_eur=cost_eur,
            last_generation=row.last_generation
        ))

    logger.info(f"Admin {current_user.id} a consulte users/consumption: period={period}, users={len(items)}")

    return UserConsumptionResponse(
        items=items,
        total_users=len(items),
        period=period
    )


@router.get("/users/{user_id}/generations", response_model=UserGenerationsResponse)
async def get_user_generations(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Retourne le drill-down des generations d'un utilisateur.

    Requiert:
    - Authentification JWT valide (401 si absent)
    - Email dans ADMIN_EMAILS (403 si non admin)

    Args:
        user_id: UUID de l'utilisateur
        skip: Nombre d'elements a sauter (pagination)
        limit: Nombre max d'elements a retourner (max 100)

    Returns:
        UserGenerationsResponse: Liste des generations avec pagination
    """
    # Query les events avec limite +1 pour detecter has_more
    limit_plus_one = limit + 1

    generations_query = text("""
        SELECT
            timestamp,
            properties->>'mode' AS mode,
            properties->>'language' AS language,
            COALESCE((properties->>'tokens_input')::INTEGER, 0) AS tokens_input,
            COALESCE((properties->>'tokens_output')::INTEGER, 0) AS tokens_output,
            properties->>'generated_comment' AS comment_preview
        FROM analytics.events
        WHERE user_id = :user_id AND event_type = 'comment_generated'
        ORDER BY timestamp DESC
        LIMIT :limit_plus_one OFFSET :skip
    """)
    generations_result = db.execute(
        generations_query,
        {"user_id": user_id, "limit_plus_one": limit_plus_one, "skip": skip}
    ).fetchall()

    # Compter le total
    count_query = text("""
        SELECT COUNT(*) as total
        FROM analytics.events
        WHERE user_id = :user_id AND event_type = 'comment_generated'
    """)
    count_result = db.execute(count_query, {"user_id": user_id}).fetchone()
    total = int(count_result.total)

    # Detecter has_more
    has_more = len(generations_result) > limit
    rows_to_return = generations_result[:limit]

    # Construire les items
    items = []
    for row in rows_to_return:
        cost_eur = calculate_cost_eur(row.tokens_input, row.tokens_output)

        # Tronquer le commentaire a 100 chars + "..."
        comment_preview = row.comment_preview
        if comment_preview and len(comment_preview) > 100:
            comment_preview = comment_preview[:100] + "..."

        items.append(UserGenerationItem(
            timestamp=row.timestamp,
            mode=row.mode,
            language=row.language,
            tokens_input=row.tokens_input,
            tokens_output=row.tokens_output,
            cost_eur=cost_eur,
            comment_preview=comment_preview
        ))

    logger.info(f"Admin {current_user.id} a consulte user {user_id} generations: total={total}, skip={skip}, limit={limit}")

    return UserGenerationsResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=has_more
    )
