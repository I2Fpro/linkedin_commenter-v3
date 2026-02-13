"""
Partition Manager for Analytics Events

Phase 01 - Task 01-01: Automatic partition management
Gere la creation automatique des partitions futures (2 mois d'avance)
et la purge des anciennes partitions (retention 90 jours).

Scheduled via APScheduler:
- create_analytics_partitions: Daily at 2:00 AM
- purge_old_analytics: Monthly on the 1st at 3:00 AM
"""
import structlog
from sqlalchemy import text
from database import engine


logger = structlog.get_logger(__name__)


async def create_analytics_partitions():
    """
    Execute SQL function to create future analytics partitions.

    Creates partitions for the next 2 months if they don't already exist.
    Called daily by APScheduler to ensure partitions are always ready.

    Never raises exceptions to avoid crashing the scheduler.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT analytics.create_future_partitions()"))
            await conn.commit()
            logger.info("analytics_partitions_created", action="create_future_partitions")
    except Exception as e:
        logger.error("analytics_partitions_creation_failed", error=str(e), exc_info=True)


async def purge_old_analytics():
    """
    Execute SQL function to purge old analytics partitions.

    Drops partitions older than 90 days (retention period).
    Called monthly by APScheduler to maintain storage limits.

    Never raises exceptions to avoid crashing the scheduler.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT analytics.purge_old_partitions(90)"))
            await conn.commit()
            logger.info("analytics_partitions_purged", retention_days=90)
    except Exception as e:
        logger.error("analytics_partitions_purge_failed", error=str(e), exc_info=True)
