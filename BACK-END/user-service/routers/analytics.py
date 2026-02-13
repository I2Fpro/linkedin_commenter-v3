from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
import uuid
import json
import logging

from database import get_db
from auth import find_user_by_email
from models import User
from schemas.analytics import AnalyticsEventCreate, AnalyticsEventResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/track", response_model=AnalyticsEventResponse)
async def track_event(
    event: AnalyticsEventCreate,
    db: Session = Depends(get_db)
):
    """Track an analytics event. Uses email for internal service-to-service auth."""
    user = find_user_by_email(db, event.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    event_id = uuid.uuid4()
    event_timestamp = event.timestamp or datetime.now(timezone.utc)

    try:
        db.execute(
            text("""
                INSERT INTO analytics.events (id, user_id, event_type, properties, timestamp)
                VALUES (:id, :user_id, :event_type, CAST(:properties AS jsonb), :timestamp)
            """),
            {
                "id": str(event_id),
                "user_id": str(user.id),
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
