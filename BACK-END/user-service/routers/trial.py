"""
Router FastAPI pour les endpoints trial.

Phase 02 - Plan 02-02: Endpoints trial
- POST /api/trial/capture-linkedin-profile : Capture profil + demarre trial
- GET /api/trial/status : Etat du trial
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
import uuid
import json
import logging

from database import get_db
from auth import get_current_user
from models import User
from schemas.trial import (
    LinkedInProfileCaptureRequest,
    LinkedInProfileCaptureResponse,
    TrialStatusResponse
)
from utils.trial_manager import TrialManager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/capture-linkedin-profile",
    response_model=LinkedInProfileCaptureResponse
)
async def capture_linkedin_profile(
    request: LinkedInProfileCaptureRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verification inline de l'expiration (fallback cron)
    TrialManager.check_user_trial_inline(db, current_user)
    db.refresh(current_user)

    result = TrialManager.start_trial(
        db=db,
        user=current_user,
        linkedin_profile_id=request.linkedin_profile_id
    )

    # Track analytics event (non-blocking)
    try:
        event_type = "trial_started" if result["trial_granted"] else "trial_denied"
        properties = {
            "reason": result.get("reason"),
            "role": result["role"]
        }
        if result["trial_granted"]:
            properties["trial_duration_days"] = 30

        db.execute(
            text("""
                INSERT INTO analytics.events (id, user_id, event_type, properties, timestamp)
                VALUES (:id, :user_id, :event_type, :properties::jsonb, :timestamp)
            """),
            {
                "id": str(uuid.uuid4()),
                "user_id": str(current_user.id),
                "event_type": event_type,
                "properties": json.dumps(properties),
                "timestamp": datetime.now(timezone.utc)
            }
        )
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Analytics tracking failed: {e}")

    # Track linkedin_profile_captured event separement (si profil capture)
    if not result.get("already_captured") and result.get("reason") != "profile_already_used":
        try:
            db.execute(
                text("""
                    INSERT INTO analytics.events (id, user_id, event_type, properties, timestamp)
                    VALUES (:id, :user_id, :event_type, :properties::jsonb, :timestamp)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "user_id": str(current_user.id),
                    "event_type": "linkedin_profile_captured",
                    "properties": json.dumps({
                        "is_first_capture": True
                    }),
                    "timestamp": datetime.now(timezone.utc)
                }
            )
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Analytics tracking (profile_captured) failed: {e}")

    return LinkedInProfileCaptureResponse(**result)


@router.get("/status", response_model=TrialStatusResponse)
async def get_trial_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    TrialManager.check_user_trial_inline(db, current_user)
    db.refresh(current_user)

    trial_status = TrialManager.get_trial_status(current_user)
    return TrialStatusResponse(**trial_status)
