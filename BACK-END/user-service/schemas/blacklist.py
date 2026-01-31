"""
Schemas Pydantic pour la blacklist - Story 2.1 Epic 2.
Gestion des entrees de blacklist pour les utilisateurs Premium.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional, List
import re


class BlacklistEntryCreate(BaseModel):
    """Schema pour ajouter une entree a la blacklist."""
    blocked_name: str = Field(..., min_length=1, max_length=255, description="Nom de la personne a bloquer")
    blocked_profile_url: Optional[str] = Field(None, max_length=512, description="URL du profil LinkedIn (optionnel)")

    @field_validator('blocked_profile_url')
    @classmethod
    def validate_linkedin_url(cls, v: Optional[str]) -> Optional[str]:
        """Valide que l'URL est une URL LinkedIn valide (ou None)."""
        if v is None or v == '':
            return None
        # Pattern pour URLs LinkedIn profil ou company
        linkedin_pattern = r'^https?://(www\.)?linkedin\.com/(in|company)/[a-zA-Z0-9\-_%]+/?.*$'
        if not re.match(linkedin_pattern, v):
            raise ValueError('URL doit etre un profil LinkedIn valide (linkedin.com/in/... ou linkedin.com/company/...)')
        return v


class BlacklistEntryResponse(BaseModel):
    """Schema pour la reponse d'une entree blacklist."""
    id: UUID
    blocked_name: str
    blocked_profile_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class BlacklistListResponse(BaseModel):
    """Schema pour la liste complete de la blacklist."""
    entries: List[BlacklistEntryResponse]
    count: int


class BlacklistCheckResponse(BaseModel):
    """Schema pour la verification si une personne est blacklistee."""
    is_blacklisted: bool
    blocked_name: str
