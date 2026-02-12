from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
import uuid
import json
import logging

from database import get_db
from auth import get_current_user
from models import User
from schemas.analytics import AnalyticsEventCreate, AnalyticsEventResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/track", response_model=AnalyticsEventResponse)
async def track_event(
    event: AnalyticsEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track an analytics event for the current user."""
    event_id = uuid.uuid4()
    event_timestamp = event.timestamp or datetime.now(timezone.utc)

    try:
        db.execute(
            text("""
                INSERT INTO analytics.events (id, user_id, event_type, properties, timestamp)
                VALUES (:id, :user_id, :event_type, :properties::jsonb, :timestamp)
            """),
            {
                "id": str(event_id),
                "user_id": str(current_user.id),
                "event_type": event.event_type,
                "properties": json.dumps(event.properties),
                "timestamp": event_timestamp
            }
        )
        db.commit()

        return AnalyticsEventResponse(
            success=True,
            event_id=event_id,
            timestamp=event_timestamp
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to track analytics event: {e}")
        raise HTTPException(status_code=500, detail="Failed to track event")
