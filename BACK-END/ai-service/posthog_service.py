"""
PostHog Analytics Service for AI Service
Handles event tracking and analytics for the AI service
"""

import os
import logging
from typing import Optional, Dict, Any
from posthog import Posthog
from functools import wraps
import time

logger = logging.getLogger(__name__)


class PostHogService:
    """Service for managing PostHog analytics"""

    def __init__(self):
        self.api_key = os.getenv("POSTHOG_API_KEY")
        self.host = os.getenv("POSTHOG_HOST", "https://eu.i.posthog.com")  # Cloud EU par défaut
        self.enabled = os.getenv("POSTHOG_ENABLED", "true").lower() == "true"

        if self.enabled and self.api_key and self.api_key != "your_posthog_api_key_here":
            try:
                self.client = Posthog(
                    project_api_key=self.api_key,
                    host=self.host,
                    timeout=3  # 3 secondes de timeout
                )
                logger.info(f"PostHog initialized successfully with host: {self.host}")
            except Exception as e:
                logger.error(f"Failed to initialize PostHog: {e}")
                self.enabled = False
                self.client = None
        else:
            logger.info("PostHog is disabled or API key not configured")
            self.enabled = False
            self.client = None

    def capture(
        self,
        distinct_id: str,
        event: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Capture an event in PostHog

        Args:
            distinct_id: Unique identifier for the user (user_id)
            event: Event name
            properties: Additional event properties
        """
        if not self.enabled or not self.client:
            return

        try:
            # Add default properties
            event_properties = properties or {}
            event_properties["service"] = "ai-service"
            event_properties["environment"] = os.getenv("ENVIRONMENT", "development")

            self.client.capture(
                distinct_id=distinct_id,
                event=event,
                properties=event_properties
            )

            # Force immediate flush to ensure events are sent
            self.client.flush()

            logger.info(f"PostHog event captured and flushed: {event} for user: {distinct_id}")
        except Exception as e:
            logger.error(f"Failed to capture PostHog event {event}: {e}")

    def identify(
        self,
        distinct_id: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Identify a user in PostHog

        Args:
            distinct_id: Unique identifier for the user
            properties: User properties
        """
        if not self.enabled or not self.client:
            return

        try:
            self.client.identify(
                distinct_id=distinct_id,
                properties=properties or {}
            )

            # Force immediate flush to ensure identification is sent
            self.client.flush()

            logger.info(f"PostHog user identified and flushed: {distinct_id}")
        except Exception as e:
            logger.error(f"Failed to identify user in PostHog: {e}")

    def track_api_request(
        self,
        user_id: str,
        endpoint: str,
        method: str,
        duration_ms: Optional[float] = None,
        status_code: Optional[int] = None,
        error: Optional[str] = None
    ) -> None:
        """Track an API request"""
        properties = {
            "endpoint": endpoint,
            "method": method,
        }

        if duration_ms is not None:
            properties["duration_ms"] = duration_ms
        if status_code is not None:
            properties["status_code"] = status_code
        if error:
            properties["error"] = error
            properties["success"] = False
        else:
            properties["success"] = True

        self.capture(
            distinct_id=user_id,
            event="api_request",
            properties=properties
        )

    def track_generation_completed(
        self,
        user_id: str,
        model: str,
        processing_time_ms: float,
        success: bool = True,
        status_code: Optional[int] = None,
        error: Optional[str] = None,
        tokens_used: Optional[int] = None
    ) -> None:
        """Track a generation completed event (server-side)"""
        properties = {
            "model": model,
            "processing_time_ms": processing_time_ms,
            "success": success
        }

        if status_code is not None:
            properties["status_code"] = status_code
        if error:
            properties["error"] = error
        if tokens_used is not None:
            properties["tokens_used"] = tokens_used

        self.capture(
            distinct_id=user_id,
            event="generation_completed",
            properties=properties
        )

    # Alias pour compatibilité
    def track_comment_generation(
        self,
        user_id: str,
        generation_type: str,
        model: str,
        processing_time_ms: float,
        tokens_used: Optional[int] = None,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Track a comment generation event (alias for generation_completed)"""
        self.track_generation_completed(
            user_id=user_id,
            model=model,
            processing_time_ms=processing_time_ms,
            success=success,
            error=error,
            tokens_used=tokens_used
        )

    def track_comment_generated(
        self,
        user_id: str,
        properties: Dict[str, Any]
    ) -> None:
        """
        Track a comment_generated event with complete properties

        Événement standardisé pour les dashboards PostHog.
        Propriétés attendues:
        - plan (FREE|MEDIUM|PREMIUM)
        - language (langue des commentaires)
        - interface_lang (langue de l'interface)
        - tone, emotion, style
        - options_count (nombre d'options générées)
        - is_comment (True si commentaire, False si post)
        - duration_ms (temps de génération)
        - success (True/False)
        - status_code (200, 500, etc.)
        - source ("backend" ou "frontend")

        Args:
            user_id: Identifiant utilisateur anonyme (SHA-256)
            properties: Dictionnaire de propriétés pour l'événement
        """
        # Ajouter des propriétés par défaut
        event_properties = {
            "service": "ai-service",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "source": "backend",  # Par défaut backend
            **properties
        }

        self.capture(
            distinct_id=user_id,
            event="comment_generated",
            properties=event_properties
        )

    def track_quota_check(
        self,
        user_id: str,
        plan: str,
        quota_remaining: int,
        quota_limit: int
    ) -> None:
        """Track a quota check event"""
        self.capture(
            distinct_id=user_id,
            event="user_quota_checked",
            properties={
                "plan": plan,
                "quota_remaining": quota_remaining,
                "quota_limit": quota_limit,
                "quota_percentage": (quota_remaining / quota_limit * 100) if quota_limit > 0 else 0
            }
        )

    def track_error(
        self,
        user_id: str,
        endpoint: Optional[str] = None,
        error_code: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Track a server error event"""
        properties = {}

        if endpoint:
            properties["endpoint"] = endpoint
        if error_code:
            properties["code"] = error_code
        if error_message:
            properties["message"] = error_message

        self.capture(
            distinct_id=user_id,
            event="server_error",
            properties=properties
        )

    def probe(self) -> None:
        """
        Send a probe event to verify PostHog connection
        Should be called at service startup
        """
        if not self.enabled or not self.client:
            logger.info("PostHog probe skipped (disabled)")
            return

        try:
            self.capture(
                distinct_id="server-probe",
                event="backend_boot",
                properties={
                    "service": "ai-service",
                    "timestamp": int(time.time())
                }
            )
            logger.info("✅ PostHog probe sent successfully")
        except Exception as e:
            logger.error(f"Failed to send PostHog probe: {e}")

    def shutdown(self) -> None:
        """Shutdown PostHog client gracefully"""
        if self.enabled and self.client:
            try:
                self.client.shutdown()
                logger.info("PostHog client shutdown successfully")
            except Exception as e:
                logger.error(f"Error shutting down PostHog client: {e}")


# Global instance
posthog_service = PostHogService()


# Safe capture function (Plan v3)
def capture_safe(
    ph: Optional[Posthog],
    distinct_id: str,
    event: str,
    props: Optional[Dict[str, Any]] = None
) -> None:
    """
    Safe capture function with error handling

    Args:
        ph: PostHog client instance (can be None)
        distinct_id: User ID
        event: Event name
        props: Event properties
    """
    if not ph:
        return

    try:
        ph.capture(distinct_id=distinct_id, event=event, properties=props or {})
    except Exception as e:
        logger.warning(f"PostHog capture failed: {e}")

# Send probe at module load (startup)
posthog_service.probe()


def track_endpoint(endpoint_name: str):
    """
    Decorator to automatically track API endpoint calls

    Usage:
        @track_endpoint("/generate/comment")
        async def generate_comment(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            status_code = 200
            user_id = "anonymous"

            try:
                # Try to extract user_id from kwargs or args
                for arg in args:
                    if hasattr(arg, 'state') and hasattr(arg.state, 'user_id'):
                        user_id = arg.state.user_id
                        break

                # Execute the function
                result = await func(*args, **kwargs)
                return result

            except Exception as e:
                error = str(e)
                status_code = 500
                raise

            finally:
                duration_ms = (time.time() - start_time) * 1000
                posthog_service.track_api_request(
                    user_id=user_id,
                    endpoint=endpoint_name,
                    method="POST",
                    duration_ms=duration_ms,
                    status_code=status_code,
                    error=error
                )

        return wrapper
    return decorator
