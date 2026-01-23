from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class RoleEnum(str, Enum):
    FREE = "FREE"
    MEDIUM = "MEDIUM"
    PREMIUM = "PREMIUM"

class SubscriptionStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class UserCreate(BaseModel):
    email: str
    name: Optional[str] = None
    google_id: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: Optional[str]
    google_id: Optional[str]
    role: RoleEnum
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class PermissionsResponse(BaseModel):
    role: RoleEnum
    daily_limit: int
    remaining_quota: int
    features: Dict[str, Any]
    allowed: bool
    message: Optional[str] = None

class GoogleUserInfo(BaseModel):
    email: str
    name: str
    google_id: str

class QuotaStatus(BaseModel):
    user_id: uuid.UUID
    role: RoleEnum
    daily_limit: int
    used_today: int
    remaining: int
    reset_time: datetime

class FeatureAccess(BaseModel):
    feature_name: str
    allowed: bool
    reason: Optional[str] = None