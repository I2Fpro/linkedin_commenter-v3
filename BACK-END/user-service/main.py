from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from routers import users, subscriptions, permissions, auth, stripe, blacklist, admin, analytics, trial
from utils.partition_manager import create_analytics_partitions, purge_old_analytics
from utils.trial_manager import check_trial_expirations
from utils.materialized_view_refresh import refresh_admin_materialized_views
from version import VERSION
from health.analytics_checks import check_events_volume, check_future_partitions

# Charger le .env principal du projet
load_dotenv("../.env")  # Référencer le .env principal
load_dotenv()  # Puis le .env local si il existe

# Configuration du logging structure
from logging_config import configure_logging
import structlog

configure_logging()
logger = structlog.get_logger(__name__)


# APScheduler instance for analytics partition management
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)

    # Configure and start analytics scheduler
    scheduler.add_job(
        create_analytics_partitions,
        trigger=CronTrigger(hour=2, minute=0),
        id="create_partitions",
        name="Create future analytics partitions",
        replace_existing=True
    )
    scheduler.add_job(
        purge_old_analytics,
        trigger=CronTrigger(day=1, hour=3, minute=0),
        id="purge_old_partitions",
        name="Purge old analytics partitions",
        replace_existing=True
    )
    # Trial expiration cron job (Phase 2)
    scheduler.add_job(
        check_trial_expirations,
        trigger=CronTrigger(hour=1, minute=0),
        id="check_trial_expirations",
        name="Check and process expired trials and grace periods",
        replace_existing=True
    )
    # Admin materialized views refresh (Phase 3)
    scheduler.add_job(
        refresh_admin_materialized_views,
        trigger=CronTrigger(minute=0),
        id="refresh_admin_views",
        name="Refresh admin analytics materialized views",
        replace_existing=True
    )
    scheduler.start()
    logger.info("scheduler_started", service="user-service", version=VERSION)

    yield

    # Shutdown
    scheduler.shutdown()
    logger.info("scheduler_stopped", service="user-service")

app = FastAPI(
    title="LinkedIn AI Commenter - User Service",
    description="Service de gestion des utilisateurs et des permissions",
    version=VERSION,
    lifespan=lifespan,
    redirect_slashes=False  # Fix 307 redirect issue with trailing slashes
)

# Configuration CORS depuis les variables d'environnement
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
cors_credentials = os.getenv("CORS_CREDENTIALS", "false").lower() == "true"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["subscriptions"])
app.include_router(permissions.router, prefix="/api/permissions", tags=["permissions"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(stripe.router, prefix="/api/stripe", tags=["stripe"])
app.include_router(blacklist.router, prefix="/api/blacklist", tags=["blacklist"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(trial.router, prefix="/api/trial", tags=["trial"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service", "version": VERSION}

@app.get("/health/analytics")
async def health_check_analytics(db: Session = Depends(get_db)):
    checks = {
        "events_last_24h": check_events_volume(db),
        "future_partitions": check_future_partitions(db)
    }
    statuses = [c["status"] for c in checks.values()]
    if all(s == "healthy" for s in statuses):
        overall = "healthy"
    elif "unhealthy" in statuses:
        overall = "unhealthy"
    else:
        overall = "degraded"

    response = {
        "status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "user-service",
        "checks": checks
    }
    status_code = status.HTTP_200_OK if overall == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=response, status_code=status_code)

@app.get("/")
async def root():
    return {"message": "LinkedIn AI Commenter - User Service", "version": VERSION}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )