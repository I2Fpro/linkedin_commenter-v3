"""
V3 Story 3.1 - Schemas Pydantic pour les endpoints admin.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from uuid import UUID


class PremiumUserDetail(BaseModel):
    """Detail d'un utilisateur premium."""
    id: UUID
    created_at: datetime
    subscription_status: Optional[str] = None

    class Config:
        from_attributes = True


class PremiumCountResponse(BaseModel):
    """Reponse du compteur d'utilisateurs premium."""
    count: int
    details: List[PremiumUserDetail]


class TokenUsageDetail(BaseModel):
    """Detail de consommation de tokens par utilisateur."""
    user_id: UUID
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_tokens: int = 0  # input + output
    generation_count: int = 0
    models_used: List[str] = []  # Liste des modeles utilises
    last_generation: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenUsageResponse(BaseModel):
    """Reponse du suivi de consommation de tokens."""
    users: List[TokenUsageDetail]
    total_users: int
    total_tokens_all: int  # Total global pour reference
