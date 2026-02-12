from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import engine, Base
from routers import users, subscriptions, permissions, auth, stripe, blacklist, admin
from posthog_service import posthog_service
from utils.partition_manager import create_analytics_partitions, purge_old_analytics
from version import VERSION
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger le .env principal du projet
load_dotenv("../.env")  # Référencer le .env principal
load_dotenv()  # Puis le .env local si il existe

# Log de l'état de PostHog au démarrage
logger.info(f"PostHog initialized: enabled={posthog_service.enabled}, api_key={'***' if posthog_service.api_key else 'NOT SET'}")

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
    scheduler.start()
    logger.info("Analytics scheduler started")

    yield

    # Shutdown
    scheduler.shutdown()
    logger.info("Analytics scheduler stopped")
    # Shutdown PostHog gracefully
    posthog_service.shutdown()

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

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service", "version": VERSION}

@app.get("/")
async def root():
    return {"message": "LinkedIn AI Commenter - User Service", "version": VERSION}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )