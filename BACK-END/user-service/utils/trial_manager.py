"""
Gestionnaire du cycle de vie trial Premium.

Phase 02 - Plan 02-02: Logique metier trial
Gere les transitions: FREE -> PREMIUM trial (30j) -> MEDIUM grace (3j) -> FREE

Anti-abus: Verification du hash SHA256 du linkedin_profile_id
avant d'accorder le trial.
"""

import logging
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models import User, RoleType
from utils.role_manager import RoleManager

logger = logging.getLogger(__name__)

# Constantes du trial
TRIAL_DURATION_DAYS = 30
GRACE_DURATION_DAYS = 3


def track_trial_event(
    db: Session,
    user_id: str,
    event_type: str,
    properties: dict = None
) -> None:
    """
    Track un event analytics lie au trial de facon non-blocking.

    Ne leve jamais d'exception. Les erreurs sont loguees en warning.
    """
    from sqlalchemy import text
    import json

    try:
        db.execute(
            text("""
                INSERT INTO analytics.events (id, user_id, event_type, properties, timestamp)
                VALUES (:id, :user_id, :event_type, :properties::jsonb, :timestamp)
            """),
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "event_type": event_type,
                "properties": json.dumps(properties or {}),
                "timestamp": datetime.now(timezone.utc)
            }
        )
        db.commit()
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        logger.warning(f"Analytics tracking failed for {event_type}: {e}")


class TrialManager:
    """
    Gestionnaire du cycle de vie trial Premium.

    Cycle: FREE -> (capture profil) -> PREMIUM trial 30j -> MEDIUM grace 3j -> FREE
    """

    @staticmethod
    def start_trial(
        db: Session,
        user: User,
        linkedin_profile_id: str
    ) -> dict:
        now = datetime.now(timezone.utc)
        profile_hash = User.hash_linkedin_profile_id(linkedin_profile_id)

        # Verifier si l'utilisateur a deja un trial en cours ou termine
        if user.trial_started_at is not None:
            logger.info(f"User {user.id}: trial deja demarre, idempotence")
            return {
                "trial_granted": False,
                "already_captured": True,
                "role": user.role.value,
                "trial_ends_at": user.trial_ends_at,
                "grace_ends_at": user.grace_ends_at,
                "reason": "profile_already_captured"
            }

        # Verifier si le profil LinkedIn est deja associe a un autre utilisateur (anti-abus)
        existing_user = db.query(User).filter(
            User.linkedin_profile_id_hash == profile_hash
        ).first()

        if existing_user and existing_user.id != user.id:
            logger.warning(
                f"Trial refuse pour user {user.id}: "
                f"linkedin_profile_id_hash deja utilise par user {existing_user.id}"
            )
            return {
                "trial_granted": False,
                "already_captured": False,
                "role": user.role.value,
                "trial_ends_at": None,
                "grace_ends_at": None,
                "reason": "profile_already_used"
            }

        # Stocker le profil LinkedIn
        user.linkedin_profile_id = linkedin_profile_id
        user.linkedin_profile_id_hash = profile_hash
        user.linkedin_profile_captured_at = now

        # Verifier si l'utilisateur peut beneficier du trial (doit etre FREE)
        if user.role != RoleType.FREE:
            logger.info(
                f"User {user.id}: profil capture mais pas de trial "
                f"(role actuel: {user.role.value})"
            )
            try:
                db.commit()
                db.refresh(user)
            except IntegrityError:
                db.rollback()
                logger.warning(f"IntegrityError pour user {user.id}: hash deja existant (race condition)")
                return {
                    "trial_granted": False,
                    "already_captured": False,
                    "role": user.role.value,
                    "trial_ends_at": None,
                    "grace_ends_at": None,
                    "reason": "profile_already_used"
                }

            return {
                "trial_granted": False,
                "already_captured": False,
                "role": user.role.value,
                "trial_ends_at": None,
                "grace_ends_at": None,
                "reason": "not_free_user"
            }

        # Demarrer le trial Premium
        trial_end = now + timedelta(days=TRIAL_DURATION_DAYS)
        user.trial_started_at = now
        user.trial_ends_at = trial_end

        try:
            RoleManager.change_user_role(
                db=db,
                user=user,
                new_role=RoleType.PREMIUM,
                changed_by="system:trial",
                reason="Trial Premium demarre (capture profil LinkedIn)",
                meta_data={
                    "trigger": "linkedin_profile_capture",
                    "trial_duration_days": TRIAL_DURATION_DAYS,
                    "trial_ends_at": trial_end.isoformat()
                }
            )
            db.commit()
            db.refresh(user)
        except IntegrityError:
            db.rollback()
            logger.warning(f"IntegrityError pour user {user.id}: hash deja existant (race condition)")
            return {
                "trial_granted": False,
                "already_captured": False,
                "role": user.role.value,
                "trial_ends_at": None,
                "grace_ends_at": None,
                "reason": "profile_already_used"
            }

        logger.info(
            f"Trial Premium demarre pour user {user.id}: "
            f"fin le {trial_end.isoformat()}"
        )

        return {
            "trial_granted": True,
            "already_captured": False,
            "role": RoleType.PREMIUM.value,
            "trial_ends_at": trial_end,
            "grace_ends_at": None,
            "reason": None
        }

    @staticmethod
    def expire_trial(db: Session, user: User) -> bool:
        now = datetime.now(timezone.utc)

        if user.role != RoleType.PREMIUM:
            logger.warning(f"User {user.id}: expire_trial appele mais role={user.role.value}")
            return False

        if user.trial_ends_at is None:
            logger.warning(f"User {user.id}: expire_trial appele mais trial_ends_at=None")
            return False

        if user.trial_ends_at > now:
            return False

        if user.stripe_subscription_id and user.subscription_status == "active":
            logger.info(
                f"User {user.id}: trial expire mais abonnement Stripe actif, "
                f"pas de transition"
            )
            user.trial_ends_at = None
            db.commit()
            return False

        grace_end = now + timedelta(days=GRACE_DURATION_DAYS)
        user.grace_ends_at = grace_end

        try:
            RoleManager.change_user_role(
                db=db,
                user=user,
                new_role=RoleType.MEDIUM,
                changed_by="system:trial_expiration",
                reason=f"Trial Premium expire apres {TRIAL_DURATION_DAYS} jours, passage en grace MEDIUM",
                meta_data={
                    "trigger": "trial_expired",
                    "grace_duration_days": GRACE_DURATION_DAYS,
                    "grace_ends_at": grace_end.isoformat()
                }
            )
            db.commit()
        except ValueError:
            user.grace_ends_at = grace_end
            db.commit()

        logger.info(
            f"Trial expire pour user {user.id}: PREMIUM -> MEDIUM grace, "
            f"fin grace le {grace_end.isoformat()}"
        )

        return True

    @staticmethod
    def expire_grace(db: Session, user: User) -> bool:
        now = datetime.now(timezone.utc)

        if user.role != RoleType.MEDIUM:
            logger.warning(f"User {user.id}: expire_grace appele mais role={user.role.value}")
            return False

        if user.grace_ends_at is None:
            logger.warning(f"User {user.id}: expire_grace appele mais grace_ends_at=None")
            return False

        if user.grace_ends_at > now:
            return False

        if user.stripe_subscription_id and user.subscription_status == "active":
            logger.info(
                f"User {user.id}: grace expire mais abonnement Stripe actif, "
                f"pas de transition"
            )
            user.grace_ends_at = None
            db.commit()
            return False

        try:
            RoleManager.change_user_role(
                db=db,
                user=user,
                new_role=RoleType.FREE,
                changed_by="system:grace_expiration",
                reason=f"Grace MEDIUM expiree apres {GRACE_DURATION_DAYS} jours, retour a FREE",
                meta_data={
                    "trigger": "grace_expired"
                }
            )
            db.commit()
        except ValueError:
            db.commit()

        logger.info(f"Grace expiree pour user {user.id}: MEDIUM -> FREE")

        return True

    @staticmethod
    def get_trial_status(user: User) -> dict:
        now = datetime.now(timezone.utc)
        result = {
            "has_trial": user.trial_started_at is not None,
            "has_linkedin_profile": user.linkedin_profile_captured_at is not None,
            "role": user.role.value,
            "trial_started_at": user.trial_started_at,
            "trial_ends_at": user.trial_ends_at,
            "grace_ends_at": user.grace_ends_at,
            "trial_days_remaining": None,
            "grace_days_remaining": None,
            "trial_active": False,
            "grace_active": False,
            "trial_expired": False
        }

        if user.trial_ends_at and user.trial_ends_at > now and user.role == RoleType.PREMIUM:
            remaining = (user.trial_ends_at - now).total_seconds()
            import math
            result["trial_days_remaining"] = math.ceil(remaining / 86400)
            result["trial_active"] = True

        elif user.grace_ends_at and user.grace_ends_at > now and user.role == RoleType.MEDIUM:
            remaining = (user.grace_ends_at - now).total_seconds()
            import math
            result["grace_days_remaining"] = math.ceil(remaining / 86400)
            result["grace_active"] = True

        elif user.trial_started_at is not None:
            result["trial_expired"] = True

        return result

    @staticmethod
    def check_and_transition_expired_trials(db: Session) -> dict:
        now = datetime.now(timezone.utc)
        stats = {
            "trials_expired": 0,
            "graces_expired": 0,
            "errors": 0
        }

        expired_trials = db.query(User).filter(
            User.trial_ends_at <= now,
            User.trial_ends_at.isnot(None),
            User.role == RoleType.PREMIUM
        ).all()

        for user in expired_trials:
            try:
                if TrialManager.expire_trial(db, user):
                    stats["trials_expired"] += 1
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Erreur expire_trial user {user.id}: {e}", exc_info=True)
                db.rollback()

        expired_graces = db.query(User).filter(
            User.grace_ends_at <= now,
            User.grace_ends_at.isnot(None),
            User.role == RoleType.MEDIUM
        ).all()

        for user in expired_graces:
            try:
                if TrialManager.expire_grace(db, user):
                    stats["graces_expired"] += 1
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Erreur expire_grace user {user.id}: {e}", exc_info=True)
                db.rollback()

        logger.info(
            f"Check expirations: {stats['trials_expired']} trials expires, "
            f"{stats['graces_expired']} graces expirees, "
            f"{stats['errors']} erreurs"
        )

        return stats

    @staticmethod
    def check_user_trial_inline(db: Session, user: User) -> None:
        now = datetime.now(timezone.utc)

        if (user.role == RoleType.PREMIUM
                and user.trial_ends_at
                and user.trial_ends_at <= now
                and not (user.stripe_subscription_id and user.subscription_status == "active")):
            logger.info(f"Fallback: expire trial pour user {user.id}")
            TrialManager.expire_trial(db, user)

        elif (user.role == RoleType.MEDIUM
                and user.grace_ends_at
                and user.grace_ends_at <= now
                and not (user.stripe_subscription_id and user.subscription_status == "active")):
            logger.info(f"Fallback: expire grace pour user {user.id}")
            TrialManager.expire_grace(db, user)
