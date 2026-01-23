"""
Module News - Enrichissement des commentaires avec les actualités LinkedIn

v2.2+ Features:
- Cache Redis avec TTL configurable
- Retry logic avec backoff exponentiel
- Parallélisation (max 5 concurrents)
- Métriques en temps réel (moyenne glissante)
- Logging structuré (JSON + debug)
- Endpoints de monitoring (/stats, /debug)
"""

from .routes import router
from .database import news_db
from .service import news_processor
from .cache_manager import news_cache
from .metrics import news_metrics
from .news_logger import news_logger

__all__ = [
    "router",
    "news_db",
    "news_processor",
    "news_cache",
    "news_metrics",
    "news_logger"
]
