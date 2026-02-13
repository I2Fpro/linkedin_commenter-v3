"""
V3 Story 3.1 - Router admin pour le monitoring.
Endpoints proteges par require_admin (whitelist ADMIN_EMAILS).
"""
import logging
import math
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal

from database import get_db
from models import User, RoleType, UsageLog
from schemas.admin import (
    PremiumCountResponse, PremiumUserDetail, TokenUsageResponse, TokenUsageDetail,
    AnalyticsSummaryResponse, UserConsumptionItem, UserConsumptionResponse,
    UserGenerationItem, UserGenerationsResponse,
    UsageDistributionItem, UsageDistributionResponse,
    UsageFeatureAdoptionItem, UsageFeatureAdoptionResponse,
    UsageByRoleItem, UsageByRoleResponse,
    UsageTrendsItem, UsageTrendsResponse,
    UserDetailResponse, UserUpdateRequest, RoleHistoryItem
)
from utils.admin_auth import require_admin
from utils.role_manager import RoleManager
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

    # Recuperer les totaux de la periode precedente via daily_summary (event_count par event_type)
    previous_totals_query = text("""
        SELECT
            COALESCE(SUM(CASE WHEN event_type = 'comment_generated' THEN event_count ELSE 0 END), 0) AS prev_generations
        FROM analytics.daily_summary
        WHERE date BETWEEN (CURRENT_DATE - 2 * :days * INTERVAL '1 day')
          AND (CURRENT_DATE - :days * INTERVAL '1 day')
    """)
    previous_result = db.execute(previous_totals_query, {"days": days}).fetchone()
    prev_generations = int(previous_result.prev_generations)
    # Tokens pour la periode precedente : requete directe sur events
    prev_tokens_query = text("""
        SELECT
            COALESCE(SUM(CAST(properties->>'tokens_input' AS INTEGER)), 0) AS prev_input,
            COALESCE(SUM(CAST(properties->>'tokens_output' AS INTEGER)), 0) AS prev_output
        FROM analytics.events
        WHERE event_type = 'comment_generated'
          AND created_at BETWEEN (CURRENT_TIMESTAMP - 2 * :days * INTERVAL '1 day')
          AND (CURRENT_TIMESTAMP - :days * INTERVAL '1 day')
    """)
    prev_tokens_result = db.execute(prev_tokens_query, {"days": days}).fetchone()
    prev_input = int(prev_tokens_result.prev_input)
    prev_output = int(prev_tokens_result.prev_output)

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


@router.get("/usage/distributions", response_model=UsageDistributionResponse)
async def get_usage_distributions(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Retourne la distribution des parametres d'usage (mode, language, etc.).

    Requiert:
    - Authentification JWT valide (401 si absent)
    - Email dans ADMIN_EMAILS (403 si non admin)

    Returns:
        UsageDistributionResponse: Distribution des parametres d'usage
    """
    distributions_query = text("""
        SELECT dimension, value, usage_count, percentage
        FROM analytics.usage_parameter_distribution
        ORDER BY dimension, usage_count DESC
    """)
    distributions_result = db.execute(distributions_query).fetchall()

    items = [
        UsageDistributionItem(
            dimension=row.dimension,
            value=row.value,
            usage_count=row.usage_count,
            percentage=float(row.percentage)
        )
        for row in distributions_result
    ]

    logger.info(f"Admin {current_user.id} consulte usage/distributions: {len(items)} items")

    return UsageDistributionResponse(items=items)


@router.get("/usage/feature-adoption", response_model=UsageFeatureAdoptionResponse)
async def get_usage_feature_adoption(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Retourne l'adoption des features (web search, quote, custom prompt, news).

    Requiert:
    - Authentification JWT valide (401 si absent)
    - Email dans ADMIN_EMAILS (403 si non admin)

    Returns:
        UsageFeatureAdoptionResponse: Taux d'adoption des features
    """
    adoption_query = text("""
        SELECT feature_name, generations_with_feature, total_generations, adoption_rate, success_rate
        FROM analytics.usage_feature_adoption
        ORDER BY adoption_rate DESC
    """)
    adoption_result = db.execute(adoption_query).fetchall()

    items = [
        UsageFeatureAdoptionItem(
            feature_name=row.feature_name,
            generations_with_feature=row.generations_with_feature,
            total_generations=row.total_generations,
            adoption_rate=float(row.adoption_rate),
            success_rate=float(row.success_rate) if row.success_rate is not None else None
        )
        for row in adoption_result
    ]

    logger.info(f"Admin {current_user.id} consulte usage/feature-adoption: {len(items)} items")

    return UsageFeatureAdoptionResponse(items=items)


@router.get("/usage/by-role", response_model=UsageByRoleResponse)
async def get_usage_by_role(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Retourne l'usage par role (FREE vs PREMIUM).

    Requiert:
    - Authentification JWT valide (401 si absent)
    - Email dans ADMIN_EMAILS (403 si non admin)

    Returns:
        UsageByRoleResponse: Metriques d'usage par role
    """
    by_role_query = text("""
        SELECT role, metric_type, dimension, value, count
        FROM analytics.usage_by_role
        ORDER BY role, metric_type, dimension
    """)
    by_role_result = db.execute(by_role_query).fetchall()

    items = [
        UsageByRoleItem(
            role=row.role,
            metric_type=row.metric_type,
            dimension=row.dimension,
            value=row.value,
            count=row.count
        )
        for row in by_role_result
    ]

    logger.info(f"Admin {current_user.id} consulte usage/by-role: {len(items)} items")

    return UsageByRoleResponse(items=items)


@router.get("/usage/trends", response_model=UsageTrendsResponse)
async def get_usage_trends(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Retourne les tendances d'usage hebdomadaires (12 dernieres semaines).

    Requiert:
    - Authentification JWT valide (401 si absent)
    - Email dans ADMIN_EMAILS (403 si non admin)

    Returns:
        UsageTrendsResponse: Tendances hebdomadaires des features
    """
    trends_query = text("""
        SELECT week_start_date, dimension, value, usage_count, growth_rate
        FROM analytics.usage_trends_weekly
        WHERE week_start_date >= (CURRENT_DATE - INTERVAL '12 weeks')
          AND dimension IN ('feature_web_search', 'feature_include_quote', 'feature_custom_prompt', 'feature_news_enrichment')
        ORDER BY dimension, week_start_date ASC
    """)
    trends_result = db.execute(trends_query).fetchall()

    items = [
        UsageTrendsItem(
            week_start_date=row.week_start_date,
            dimension=row.dimension,
            value=row.value,
            usage_count=row.usage_count,
            growth_rate=float(row.growth_rate) if row.growth_rate is not None else None
        )
        for row in trends_result
    ]

    logger.info(f"Admin {current_user.id} consulte usage/trends: {len(items)} items")

    return UsageTrendsResponse(items=items)


# --- CRUD Utilisateurs ---

@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Retourne le detail complet d'un utilisateur pour l'admin."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouve")

    now = datetime.now(timezone.utc)

    # Calculer jours restants trial/grace
    trial_days_remaining = None
    if user.trial_ends_at and user.trial_ends_at > now and user.role == RoleType.PREMIUM:
        trial_days_remaining = math.ceil((user.trial_ends_at - now).total_seconds() / 86400)

    grace_days_remaining = None
    if user.grace_ends_at and user.grace_ends_at > now and user.role == RoleType.MEDIUM:
        grace_days_remaining = math.ceil((user.grace_ends_at - now).total_seconds() / 86400)

    # Historique des roles
    role_history_entries = RoleManager.get_user_role_history(db, user.id, limit=20)
    role_history = [
        RoleHistoryItem(
            changed_at=entry.changed_at,
            old_role=entry.old_role.value if entry.old_role else None,
            new_role=entry.new_role.value,
            changed_by=entry.changed_by,
            reason=entry.reason
        )
        for entry in role_history_entries
    ]

    logger.info(f"Admin {current_user.id} consulte detail user {user_id}")

    return UserDetailResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_active=user.is_active,
        subscription_status=user.subscription_status,
        stripe_customer_id=user.stripe_customer_id,
        stripe_subscription_id=user.stripe_subscription_id,
        trial_started_at=user.trial_started_at,
        trial_ends_at=user.trial_ends_at,
        grace_ends_at=user.grace_ends_at,
        trial_days_remaining=trial_days_remaining,
        grace_days_remaining=grace_days_remaining,
        linkedin_profile_captured=user.linkedin_profile_captured_at is not None,
        created_at=user.created_at,
        updated_at=user.updated_at,
        role_history=role_history
    )


@router.patch("/users/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: str,
    update: UserUpdateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Modifie un utilisateur (role, trial, grace, is_active)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouve")

    admin_email = current_user.email
    changes = []

    # Changement de role
    if update.role is not None and update.role != user.role.value:
        new_role = RoleType(update.role)
        RoleManager.change_user_role(
            db=db,
            user=user,
            new_role=new_role,
            changed_by=admin_email,
            reason=f"Changement manuel par admin",
            meta_data={"source": "admin_crud"}
        )
        changes.append(f"role: {user.role.value} -> {update.role}")

    # Modification trial_ends_at
    if update.trial_ends_at is not None:
        old_val = user.trial_ends_at
        user.trial_ends_at = update.trial_ends_at
        changes.append(f"trial_ends_at: {old_val} -> {update.trial_ends_at}")

    # Modification grace_ends_at
    if update.grace_ends_at is not None:
        old_val = user.grace_ends_at
        user.grace_ends_at = update.grace_ends_at
        changes.append(f"grace_ends_at: {old_val} -> {update.grace_ends_at}")

    # Modification is_active
    if update.is_active is not None and update.is_active != user.is_active:
        user.is_active = update.is_active
        changes.append(f"is_active: {not update.is_active} -> {update.is_active}")

    if changes:
        db.commit()
        db.refresh(user)
        logger.info(f"Admin {current_user.id} a modifie user {user_id}: {', '.join(changes)}")
    else:
        logger.info(f"Admin {current_user.id} PATCH user {user_id}: aucun changement")

    # Retourner le detail mis a jour (reutilise la logique de get_user_detail)
    return await get_user_detail(user_id, current_user, db)
