"""
Router FastAPI pour les endpoints trial.

Phase 02 - Plan 02-02: Endpoints trial
- POST /api/trial/capture-linkedin-profile : Capture profil + demarre trial
- GET /api/trial/status : Etat du trial
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from database import get_db
from auth import get_current_user
from models import User
from schemas.trial import (
    LinkedInProfileCaptureRequest,
    LinkedInProfileCaptureResponse,
    TrialStatusResponse
)
from utils.trial_manager import TrialManager, track_trial_event

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

    # Track analytics events (non-blocking)
    event_type = "trial_started" if result["trial_granted"] else "trial_denied"
    properties = {
        "reason": result.get("reason"),
        "role": result["role"]
    }
    if result["trial_granted"]:
        properties["trial_duration_days"] = 30

    track_trial_event(
        db=db,
        user_id=str(current_user.id),
        event_type=event_type,
        properties=properties
    )

    # Track linkedin_profile_captured event separement (si profil capture)
    if not result.get("already_captured") and result.get("reason") != "profile_already_used":
        track_trial_event(
            db=db,
            user_id=str(current_user.id),
            event_type="linkedin_profile_captured",
            properties={"is_first_capture": True}
        )

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
