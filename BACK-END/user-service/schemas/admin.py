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
