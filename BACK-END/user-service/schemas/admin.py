"""
V3 Story 3.1 - Schemas Pydantic pour les endpoints admin.
"""
from pydantic import BaseModel
from datetime import datetime, date
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


class UsageDistributionItem(BaseModel):
    """Item de distribution des parametres d'usage."""
    dimension: str
    value: str
    usage_count: int
    percentage: float


class UsageDistributionResponse(BaseModel):
    """Reponse de la distribution des parametres d'usage."""
    items: List[UsageDistributionItem]


class UsageFeatureAdoptionItem(BaseModel):
    """Item d'adoption des features."""
    feature_name: str
    generations_with_feature: int
    total_generations: int
    adoption_rate: float
    success_rate: Optional[float] = None


class UsageFeatureAdoptionResponse(BaseModel):
    """Reponse de l'adoption des features."""
    items: List[UsageFeatureAdoptionItem]


class UsageByRoleItem(BaseModel):
    """Item d'usage par role."""
    role: str
    metric_type: str
    dimension: str
    value: str
    count: int


class UsageByRoleResponse(BaseModel):
    """Reponse de l'usage par role."""
    items: List[UsageByRoleItem]


class UsageTrendsItem(BaseModel):
    """Item de tendances d'usage hebdomadaires."""
    week_start_date: date
    dimension: str
    value: str
    usage_count: int
    previous_week_count: Optional[int] = None
    growth_rate: Optional[float] = None


class UsageTrendsResponse(BaseModel):
    """Reponse des tendances d'usage hebdomadaires."""
    items: List[UsageTrendsItem]


# --- CRUD Utilisateurs ---

class RoleHistoryItem(BaseModel):
    """Entree dans l'historique des changements de role."""
    changed_at: datetime
    old_role: Optional[str] = None
    new_role: str
    changed_by: Optional[str] = None
    reason: Optional[str] = None


class UserDetailResponse(BaseModel):
    """Detail complet d'un utilisateur pour l'admin."""
    id: UUID
    email: str
    name: Optional[str] = None
    role: str
    is_active: bool
    subscription_status: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    trial_started_at: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None
    grace_ends_at: Optional[datetime] = None
    trial_days_remaining: Optional[int] = None
    grace_days_remaining: Optional[int] = None
    linkedin_profile_captured: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    role_history: List[RoleHistoryItem] = []

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """Requete de modification d'un utilisateur par l'admin."""
    role: Optional[str] = None
    trial_ends_at: Optional[datetime] = None
    grace_ends_at: Optional[datetime] = None
    is_active: Optional[bool] = None
