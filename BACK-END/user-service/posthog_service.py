"""
PostHog Analytics Service for User Service
Handles event tracking and analytics for the user service
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
            event_properties["service"] = "user-service"
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

    def set_person_properties(
        self,
        user_id: str,
        properties: Dict[str, Any]
    ) -> None:
        """
        Set person properties (alias for identify for semantic clarity)

        Args:
            user_id: Unique identifier for the user
            properties: User properties to set
        """
        self.identify(distinct_id=user_id, properties=properties)

    def track_user_registration(
        self,
        user_id: str,
        plan: str = "FREE",
        registration_method: str = "google_oauth2"
    ) -> None:
        """Track a new user registration (server-side event) - RGPD compliant (no email)"""
        # Identifier l'utilisateur avec ses propriétés (SANS email)
        self.identify(
            distinct_id=user_id,
            properties={
                "plan": plan,
                "role": plan,  # role = plan par défaut
                "registration_method": registration_method
            }
        )

        # Capturer l'événement de registration (serveur) - SANS email
        self.capture(
            distinct_id=user_id,
            event="user_registered_server",
            properties={
                "user_id": user_id,
                "registration_method": registration_method
            }
        )

    def track_user_login(
        self,
        user_id: str,
        plan: str = "FREE",
        role: Optional[str] = None
    ) -> None:
        """Track a user login event (server-side) - RGPD compliant (no email)"""
        # Mettre à jour les person properties à chaque login (SANS email)
        self.identify(
            distinct_id=user_id,
            properties={
                "plan": plan,
                "role": role or plan
            }
        )

        # Capturer l'événement de login (serveur) - SANS email
        self.capture(
            distinct_id=user_id,
            event="user_login_server",
            properties={
                "user_id": user_id
            }
        )

    def track_subscription_created(
        self,
        user_id: str,
        plan: str,
        billing_cycle: str = "monthly",
        amount: float = 0
    ) -> None:
        """Track a subscription creation"""
        self.capture(
            distinct_id=user_id,
            event="subscription_created",
            properties={
                "plan": plan,
                "billing_cycle": billing_cycle,
                "amount": amount
            }
        )

    def track_subscription_updated(
        self,
        user_id: str,
        old_plan: str,
        new_plan: str,
        provider: Optional[str] = None,
        status: Optional[str] = None
    ) -> None:
        """Track a subscription update"""
        properties = {
            "plan": new_plan,
            "previous_plan": old_plan
        }

        if provider:
            properties["provider"] = provider
        if status:
            properties["status"] = status

        self.capture(
            distinct_id=user_id,
            event="subscription_updated",
            properties=properties
        )

        # Mettre à jour les person properties
        self.set_person_properties(
            user_id=user_id,
            properties={
                "plan": new_plan,
                "role": new_plan
            }
        )

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

    def track_quota_check(
        self,
        user_id: str,
        remaining: int,
        used: int,
        limit: int
    ) -> None:
        """Track a quota check (server-side event)"""
        self.capture(
            distinct_id=user_id,
            event="quota_check_server",
            properties={
                "remaining": remaining,
                "used": used,
                "limit": limit
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
                    "service": "user-service",
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
        @track_endpoint("/auth/login")
        async def login(request: Request):
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
