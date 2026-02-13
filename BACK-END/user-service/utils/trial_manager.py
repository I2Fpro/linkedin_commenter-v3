"""
Gestionnaire du cycle de vie trial Premium.

Phase 02 - Plan 02-02: Logique metier trial
Gere les transitions: FREE -> PREMIUM trial (30j) -> MEDIUM grace (3j) -> FREE

Anti-abus: Verification du hash SHA256 du linkedin_profile_id
avant d'accorder le trial.
"""

import structlog
import hashlib
import uuid
import os
import math
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models import User, RoleType
from utils.role_manager import RoleManager
from notifications.email_sender import send_trial_email
from notifications.templates import (
    get_trial_expiring_soon_html,
    get_grace_started_html,
    get_grace_expired_html,
)
from utils.encryption import EncryptionManager

logger = structlog.get_logger(__name__)

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
        logger.warning("analytics_tracking_failed", event_type=event_type, error=str(e))


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
            logger.info("trial_already_started", user_id=str(user.id), reason="idempotence")
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
                "trial_refused_profile_duplicate",
                user_id=str(user.id),
                existing_user_id=str(existing_user.id),
                reason="linkedin_profile_id_hash_already_used"
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
                "profile_captured_no_trial",
                user_id=str(user.id),
                current_role=user.role.value,
                reason="not_free_user"
            )
            try:
                db.commit()
                db.refresh(user)
            except IntegrityError:
                db.rollback()
                logger.warning("integrity_error_race_condition", user_id=str(user.id), context="profile_capture_not_free")
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
            logger.warning("integrity_error_race_condition", user_id=str(user.id), context="trial_start")
            return {
                "trial_granted": False,
                "already_captured": False,
                "role": user.role.value,
                "trial_ends_at": None,
                "grace_ends_at": None,
                "reason": "profile_already_used"
            }

        logger.info(
            "trial_premium_started",
            user_id=str(user.id),
            trial_ends_at=trial_end.isoformat(),
            duration_days=TRIAL_DURATION_DAYS
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
            logger.warning("expire_trial_invalid_role", user_id=str(user.id), current_role=user.role.value)
            return False

        if user.trial_ends_at is None:
            logger.warning("expire_trial_missing_end_date", user_id=str(user.id))
            return False

        if user.trial_ends_at > now:
            return False

        if user.stripe_subscription_id and user.subscription_status == "active":
            logger.info(
                "trial_expired_but_subscribed",
                user_id=str(user.id),
                subscription_id=user.stripe_subscription_id,
                action="no_transition"
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

        # Track trial_expired event
        track_trial_event(
            db=db,
            user_id=str(user.id),
            event_type="trial_expired",
            properties={
                "trial_duration_days": TRIAL_DURATION_DAYS,
                "from_role": "PREMIUM",
                "to_role": "MEDIUM"
            }
        )

        # Track grace_started event
        track_trial_event(
            db=db,
            user_id=str(user.id),
            event_type="grace_started",
            properties={
                "grace_duration_days": GRACE_DURATION_DAYS,
                "grace_ends_at": grace_end.isoformat()
            }
        )

        logger.info(
            "trial_expired_grace_started",
            user_id=str(user.id),
            from_role="PREMIUM",
            to_role="MEDIUM",
            grace_ends_at=grace_end.isoformat(),
            grace_duration_days=GRACE_DURATION_DAYS
        )

        # Envoi email grace_started (non-bloquant)
        try:
            encryption_manager = EncryptionManager()
            user_email = encryption_manager.decrypt(user.email) if user.email else None
            user_name = encryption_manager.decrypt(user.name) if user.name else "utilisateur"

            if user_email:
                upgrade_url = os.getenv(
                    "STRIPE_SUCCESS_URL",
                    "https://linkedinaicommenter.com/account/subscription.html"
                )
                html_body = get_grace_started_html(
                    user_name=user_name,
                    grace_days=GRACE_DURATION_DAYS,
                    upgrade_url=upgrade_url
                )
                send_trial_email(
                    to_email=user_email,
                    subject="Période de grâce activée - LinkedIn AI Commenter",
                    html_body=html_body
                )
        except Exception as e:
            logger.warning("email_send_error_grace_started", user_id=str(user.id), error=str(e))

        return True

    @staticmethod
    def expire_grace(db: Session, user: User) -> bool:
        now = datetime.now(timezone.utc)

        if user.role != RoleType.MEDIUM:
            logger.warning("expire_grace_invalid_role", user_id=str(user.id), current_role=user.role.value)
            return False

        if user.grace_ends_at is None:
            logger.warning("expire_grace_missing_end_date", user_id=str(user.id))
            return False

        if user.grace_ends_at > now:
            return False

        if user.stripe_subscription_id and user.subscription_status == "active":
            logger.info(
                "grace_expired_but_subscribed",
                user_id=str(user.id),
                subscription_id=user.stripe_subscription_id,
                action="no_transition"
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

        # Track grace_expired event
        track_trial_event(
            db=db,
            user_id=str(user.id),
            event_type="grace_expired",
            properties={
                "grace_duration_days": GRACE_DURATION_DAYS,
                "from_role": "MEDIUM",
                "to_role": "FREE"
            }
        )

        logger.info(
            "grace_expired_back_to_free",
            user_id=str(user.id),
            from_role="MEDIUM",
            to_role="FREE",
            grace_duration_days=GRACE_DURATION_DAYS
        )

        # Envoi email grace_expired (non-bloquant)
        try:
            encryption_manager = EncryptionManager()
            user_email = encryption_manager.decrypt(user.email) if user.email else None
            user_name = encryption_manager.decrypt(user.name) if user.name else "utilisateur"

            if user_email:
                upgrade_url = os.getenv(
                    "STRIPE_SUCCESS_URL",
                    "https://linkedinaicommenter.com/account/subscription.html"
                )
                html_body = get_grace_expired_html(
                    user_name=user_name,
                    upgrade_url=upgrade_url
                )
                send_trial_email(
                    to_email=user_email,
                    subject="Retour au plan FREE - LinkedIn AI Commenter",
                    html_body=html_body
                )
        except Exception as e:
            logger.warning("email_send_error_grace_expired", user_id=str(user.id), error=str(e))

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
            "reminders_sent": 0,
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
                logger.error("expire_trial_error", user_id=str(user.id), error=str(e), exc_info=True)
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
                logger.error("expire_grace_error", user_id=str(user.id), error=str(e), exc_info=True)
                db.rollback()

        # Rappel J-3 pour les trials Premium qui expirent bientôt
        reminder_date = now + timedelta(days=3)
        users_expiring_soon = db.query(User).filter(
            User.role == RoleType.PREMIUM,
            User.trial_ends_at.isnot(None),
            User.trial_ends_at <= reminder_date,
            User.trial_ends_at > now,
            User.trial_reminder_sent_at.is_(None)
        ).all()

        encryption_manager = EncryptionManager()
        for user in users_expiring_soon:
            try:
                # Calcul des jours restants
                remaining = (user.trial_ends_at - now).total_seconds()
                days_left = math.ceil(remaining / 86400)

                # Déchiffrement email/name
                user_email = encryption_manager.decrypt(user.email) if user.email else None
                user_name = encryption_manager.decrypt(user.name) if user.name else "utilisateur"

                if user_email:
                    upgrade_url = os.getenv(
                        "STRIPE_SUCCESS_URL",
                        "https://linkedinaicommenter.com/account/subscription.html"
                    )
                    html_body = get_trial_expiring_soon_html(
                        user_name=user_name,
                        days_left=days_left,
                        upgrade_url=upgrade_url
                    )
                    email_sent = send_trial_email(
                        to_email=user_email,
                        subject=f"Votre essai Premium expire dans {days_left} jours",
                        html_body=html_body
                    )

                    if email_sent:
                        user.trial_reminder_sent_at = now
                        db.commit()
                        stats["reminders_sent"] += 1
                        logger.info(
                            "trial_reminder_sent",
                            user_id=str(user.id),
                            days_left=days_left
                        )
            except Exception as e:
                stats["errors"] += 1
                logger.error("trial_reminder_error", user_id=str(user.id), error=str(e), exc_info=True)
                try:
                    db.rollback()
                except Exception:
                    pass

        logger.info(
            "check_expirations_complete",
            trials_expired=stats["trials_expired"],
            graces_expired=stats["graces_expired"],
            reminders_sent=stats["reminders_sent"],
            errors=stats["errors"]
        )

        return stats

    @staticmethod
    def check_user_trial_inline(db: Session, user: User) -> None:
        now = datetime.now(timezone.utc)

        if (user.role == RoleType.PREMIUM
                and user.trial_ends_at
                and user.trial_ends_at <= now
                and not (user.stripe_subscription_id and user.subscription_status == "active")):
            logger.info("fallback_expire_trial", user_id=str(user.id))
            TrialManager.expire_trial(db, user)

        elif (user.role == RoleType.MEDIUM
                and user.grace_ends_at
                and user.grace_ends_at <= now
                and not (user.stripe_subscription_id and user.subscription_status == "active")):
            logger.info("fallback_expire_grace", user_id=str(user.id))
            TrialManager.expire_grace(db, user)


# --- Fonction cron (appelee par APScheduler) ---

async def check_trial_expirations():
    """
    Cron job quotidien pour scanner et traiter les expirations trial/grace.

    Appele par APScheduler a 1:00 AM UTC.
    Cree sa propre session DB (hors cycle FastAPI).
    Ne leve jamais d'exception pour ne pas crasher le scheduler.
    """
    from database import SessionLocal

    logger.info("cron_trial_expirations_started")

    db = SessionLocal()
    try:
        stats = TrialManager.check_and_transition_expired_trials(db)

        # Track analytics event recapitulatif
        if stats["trials_expired"] > 0 or stats["graces_expired"] > 0:
            track_trial_event(
                db=db,
                user_id="00000000-0000-0000-0000-000000000000",
                event_type="cron_trial_expirations",
                properties={
                    "trials_expired": stats["trials_expired"],
                    "graces_expired": stats["graces_expired"],
                    "errors": stats["errors"]
                }
            )

        logger.info(
            "cron_trial_expirations_complete",
            trials_expired=stats["trials_expired"],
            graces_expired=stats["graces_expired"],
            errors=stats["errors"]
        )

    except Exception as e:
        logger.error("cron_trial_expirations_error", error=str(e), exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()
