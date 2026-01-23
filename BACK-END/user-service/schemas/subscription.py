from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .user import RoleEnum, SubscriptionStatusEnum
import uuid

class SubscriptionCreate(BaseModel):
    user_id: uuid.UUID
    plan: RoleEnum
    end_date: Optional[datetime] = None

class SubscriptionUpdate(BaseModel):
    plan: Optional[RoleEnum] = None
    status: Optional[SubscriptionStatusEnum] = None
    end_date: Optional[datetime] = None

class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    plan: RoleEnum
    status: SubscriptionStatusEnum
    start_date: datetime
    end_date: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UpgradeRequest(BaseModel):
    target_plan: RoleEnum

class UsageLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    feature: str
    timestamp: datetime
    metadata: Optional[dict] = None
    
    class Config:
        from_attributes = True