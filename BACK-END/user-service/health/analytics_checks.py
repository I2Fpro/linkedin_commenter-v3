"""
Checks de sante pour le systeme analytics.

2 checks passifs :
1. Volume d'events : alerte si 0 events en 24h
2. Partitions futures : alerte si <2 mois de partitions creees

Usage: GET /health/analytics (sans auth)
"""

import structlog
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = structlog.get_logger(__name__)


def check_events_volume(db: Session) -> dict:
    """Verifie qu'au moins 1 event a ete insere dans les dernieres 24h."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        result = db.execute(
            text("SELECT COUNT(*) FROM analytics.events WHERE timestamp >= :cutoff"),
            {"cutoff": cutoff}
        ).scalar()
        event_count = result or 0
        if event_count > 0:
            return {"status": "healthy", "count": event_count, "threshold": "> 0", "message": "Events flowing normally"}
        else:
            return {"status": "unhealthy", "count": 0, "threshold": "> 0", "message": "No events in last 24h - collection may be broken"}
    except Exception as e:
        logger.error("health_check_events_failed", error=str(e))
        return {"status": "unhealthy", "count": -1, "threshold": "> 0", "message": f"Check failed: {str(e)}"}


def check_future_partitions(db: Session) -> dict:
    """Verifie qu'il existe au moins 2 mois de partitions futures."""
    try:
        now = datetime.now(timezone.utc)
        current_year_month = now.strftime("%Y_%m")
        result = db.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'analytics' AND tablename LIKE 'events_%' ORDER BY tablename")
        ).fetchall()
        partition_names = [row[0] for row in result]
        future_count = sum(1 for name in partition_names if name.replace("events_", "") > current_year_month)
        if future_count >= 2:
            return {"status": "healthy", "future_partitions": future_count, "total_partitions": len(partition_names), "threshold": ">= 2 future months", "message": f"{future_count} future partitions ready"}
        else:
            return {"status": "degraded", "future_partitions": future_count, "total_partitions": len(partition_names), "threshold": ">= 2 future months", "message": f"Only {future_count} future partition(s) - need at least 2"}
    except Exception as e:
        logger.error("health_check_partitions_failed", error=str(e))
        return {"status": "unhealthy", "future_partitions": -1, "total_partitions": -1, "threshold": ">= 2 future months", "message": f"Check failed: {str(e)}"}
