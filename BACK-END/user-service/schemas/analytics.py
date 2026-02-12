from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import json


class AnalyticsEventCreate(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=100)
    properties: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None

    @field_validator('properties')
    @classmethod
    def validate_properties_size(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        serialized = json.dumps(v)
        max_size = 50_000  # 50 KB limit
        if len(serialized) > max_size:
            raise ValueError(f"Properties exceed {max_size} bytes (got {len(serialized)})")
        return v

    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if not v.replace('_', '').isalnum():
            raise ValueError("event_type must be alphanumeric with underscores")
        return v.lower()


class AnalyticsEventResponse(BaseModel):
    success: bool
    event_id: uuid.UUID
    timestamp: datetime
