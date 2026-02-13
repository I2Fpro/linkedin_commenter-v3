"""
V3 Story 3.1 - Schemas Pydantic pour les endpoints admin.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict
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
    name: Optional[str] = None  # Nom decrypte pour l'admin
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


class AnalyticsSummaryResponse(BaseModel):
    """Reponse du resume analytics global."""
    period: str
    users_by_role: Dict[str, int]
    total_comments_generated: int
    total_cost_eur: str
    active_trials: int
    trend_comments: Optional[float] = None
    trend_cost: Optional[float] = None


class UserConsumptionItem(BaseModel):
    """Detail de consommation par utilisateur."""
    user_id: UUID
    email: str
    role: str
    generation_count: int
    total_tokens: int
    cost_eur: str
    last_generation: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserConsumptionResponse(BaseModel):
    """Reponse de la consommation par utilisateur."""
    items: List[UserConsumptionItem]
    total_users: int
    period: str


class UserGenerationItem(BaseModel):
    """Detail d'une generation de commentaire."""
    timestamp: datetime
    mode: Optional[str] = None
    language: Optional[str] = None
    tokens_input: int
    tokens_output: int
    cost_eur: str
    comment_preview: Optional[str] = None


class UserGenerationsResponse(BaseModel):
    """Reponse du drill-down des generations d'un utilisateur."""
    items: List[UserGenerationItem]
    total: int
    skip: int
    limit: int
    has_more: bool
