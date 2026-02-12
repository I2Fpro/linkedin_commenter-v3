"""
Schemas Pydantic pour les endpoints trial.

Phase 02 - Plan 02-02: Schemas trial
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re


class LinkedInProfileCaptureRequest(BaseModel):
    """Request pour capturer un profil LinkedIn."""
    linkedin_profile_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Identifiant LinkedIn extrait de l'URL /in/{profile_id}/"
    )

    @field_validator('linkedin_profile_id')
    @classmethod
    def validate_linkedin_profile_id(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r'^[a-z0-9\-]+$', v):
            raise ValueError(
                "linkedin_profile_id invalide. "
                "Seuls les lettres minuscules, chiffres et tirets sont autorises."
            )
        if v == 'me':
            raise ValueError(
                "linkedin_profile_id ne peut pas etre 'me'. "
                "Utilisez l'identifiant reel du profil."
            )
        return v


class LinkedInProfileCaptureResponse(BaseModel):
    """Response apres capture du profil LinkedIn."""
    trial_granted: bool
    already_captured: bool = False
    role: str
    trial_ends_at: Optional[datetime] = None
    grace_ends_at: Optional[datetime] = None
    reason: Optional[str] = None


class TrialStatusResponse(BaseModel):
    """Response pour le status du trial."""
    has_trial: bool
    has_linkedin_profile: bool
    role: str
    trial_started_at: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None
    grace_ends_at: Optional[datetime] = None
    trial_days_remaining: Optional[int] = None
    grace_days_remaining: Optional[int] = None
    trial_active: bool = False
    grace_active: bool = False
    trial_expired: bool = False
