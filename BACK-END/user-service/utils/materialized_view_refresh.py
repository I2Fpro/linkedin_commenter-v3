"""
Materialized view refresh utilities for admin analytics.
"""
import logging
from sqlalchemy import text
from database import engine

logger = logging.getLogger(__name__)


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
            logger.info("Starting refresh of admin materialized views")

            # Refresh daily_summary
            conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.daily_summary"))
            logger.info("Refreshed analytics.daily_summary")

            # Refresh user_consumption
            conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.user_consumption"))
            logger.info("Refreshed analytics.user_consumption")

            conn.commit()
            logger.info("Admin materialized views refresh completed successfully")

    except Exception as e:
        logger.error(f"Failed to refresh admin materialized views: {e}", exc_info=True)
