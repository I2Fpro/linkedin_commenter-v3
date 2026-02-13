"""
Configuration du logging structure avec structlog.

Dual mode:
- Production (ENVIRONMENT=production): JSON logs pour parsing automatique
- Development (ENVIRONMENT=development): Pretty console logs avec couleurs

Usage:
    from logging_config import configure_logging, get_logger

    configure_logging()  # Auto-detection via ENVIRONMENT
    logger = get_logger(__name__)
    logger.info("message", key1="value1", key2=123)
"""
import logging
import sys
import os
import structlog


def configure_logging(dev_mode=None):
    """
    Configure structlog avec dual mode JSON/pretty.

    Args:
        dev_mode (bool, optional): Force dev mode (True) ou prod mode (False).
            Si None, auto-detection via ENVIRONMENT env var.
    """
    if dev_mode is None:
        env = os.getenv("ENVIRONMENT", "development").lower()
        dev_mode = env == "development"

    # Shared processors for both modes
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if dev_mode:
        # Development mode: pretty console output with colors
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        # Production mode: JSON output for log aggregation
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


def get_logger(name):
    """
    Raccourci pour obtenir un logger structlog.

    Args:
        name (str): Nom du logger (generalement __name__)

    Returns:
        structlog.BoundLogger: Logger configure
    """
    return structlog.get_logger(name)
