"""
Materialized view refresh utilities for admin analytics.
"""
import structlog
from sqlalchemy import text
from database import engine

logger = structlog.get_logger(__name__)


def refresh_admin_materialized_views():
    """
    Refresh admin analytics materialized views concurrently.

    This function is called by the scheduler every hour to update:
    - analytics.daily_summary
    - analytics.user_consumption

    Uses REFRESH MATERIALIZED VIEW CONCURRENTLY to avoid locking tables.
    Errors are logged but do not crash the scheduler.
    """
    try:
        with engine.connect() as conn:
            logger.info("materialized_views_refresh_started", context="admin_analytics")

            # Refresh daily_summary
            conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.daily_summary"))
            logger.info("materialized_view_refreshed", view="analytics.daily_summary")

            # Refresh user_consumption
            conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.user_consumption"))
            logger.info("materialized_view_refreshed", view="analytics.user_consumption")

            conn.commit()
            logger.info("materialized_views_refresh_complete", views_refreshed=2)

    except Exception as e:
        logger.error("materialized_views_refresh_failed", error=str(e), exc_info=True)
