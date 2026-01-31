"""
Schemas Pydantic pour la blacklist - Story 2.1 Epic 2.
Gestion des entrees de blacklist pour les utilisateurs Premium.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List


class BlacklistEntryCreate(BaseModel):
    """Schema pour ajouter une entree a la blacklist."""
    blocked_name: str = Field(..., min_length=1, max_length=255, description="Nom de la personne a bloquer")
    blocked_profile_url: Optional[str] = Field(None, max_length=512, description="URL du profil LinkedIn (optionnel)")


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
