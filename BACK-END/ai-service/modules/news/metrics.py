"""
Système de métriques pour le module News
- Moyenne glissante sur les 100 dernières opérations
- Compteurs de cache hits/misses
- Statistiques de performance
"""
import redis
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import deque
import json

logger = logging.getLogger(__name__)


class NewsMetrics:
    """Gestionnaire de métriques pour les actualités"""

    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.redis_client = None

        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("✅ Métriques Redis connectées")
        except Exception as e:
            logger.warning(f"⚠️ Redis non disponible pour métriques: {e}")

        # Stockage en mémoire pour moyenne glissante (fallback)
        self.processing_times = deque(maxlen=100)  # 100 dernières opérations
        self.total_processed = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.last_update = datetime.utcnow()

    def _get_key(self, metric_name: str) -> str:
        """Génère la clé Redis pour une métrique"""
        return f"news:metrics:{metric_name}"

    def record_processing_time(self, duration_ms: float) -> None:
        """
        Enregistre le temps de traitement d'une actualité

        Args:
            duration_ms: Durée en millisecondes
        """
        # Stockage en mémoire
        self.processing_times.append(duration_ms)

        # Stockage Redis (liste limitée à 100)
        if self.redis_client:
            try:
                key = self._get_key("processing_times")
                self.redis_client.lpush(key, duration_ms)
                self.redis_client.ltrim(key, 0, 99)  # Garder seulement les 100 derniers
            except Exception as e:
                logger.error(f"❌ Erreur enregistrement temps: {e}")

    def get_avg_processing_time(self) -> float:
        """Calcule la moyenne glissante des temps de traitement"""
        if self.redis_client:
            try:
                key = self._get_key("processing_times")
                times = self.redis_client.lrange(key, 0, -1)
                if times:
                    times_float = [float(t) for t in times]
                    return sum(times_float) / len(times_float)
            except Exception as e:
                logger.error(f"❌ Erreur calcul moyenne Redis: {e}")

        # Fallback sur mémoire locale
        if self.processing_times:
            return sum(self.processing_times) / len(self.processing_times)
        return 0.0

    def increment_total_processed(self) -> None:
        """Incrémente le compteur total d'actualités traitées"""
        self.total_processed += 1

        if self.redis_client:
            try:
                key = self._get_key("total_processed")
                self.redis_client.incr(key)
            except Exception as e:
                logger.error(f"❌ Erreur incrémentation total: {e}")

    def increment_cache_hit(self) -> None:
        """Incrémente le compteur de cache hits"""
        self.cache_hits += 1

        if self.redis_client:
            try:
                key = self._get_key("cache_hits")
                self.redis_client.incr(key)
            except Exception as e:
                logger.error(f"❌ Erreur incrémentation cache_hits: {e}")

    def increment_cache_miss(self) -> None:
        """Incrémente le compteur de cache misses"""
        self.cache_misses += 1

        if self.redis_client:
            try:
                key = self._get_key("cache_misses")
                self.redis_client.incr(key)
            except Exception as e:
                logger.error(f"❌ Erreur incrémentation cache_misses: {e}")

    def increment_processed_today(self) -> None:
        """Incrémente le compteur journalier avec expiration automatique"""
        if self.redis_client:
            try:
                # Clé avec date du jour
                today = datetime.utcnow().strftime("%Y-%m-%d")
                key = self._get_key(f"processed_today:{today}")

                # Incrémenter
                self.redis_client.incr(key)

                # Définir expiration à minuit + 24h (pour garder l'historique d'hier)
                tomorrow = datetime.utcnow() + timedelta(days=1)
                midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
                ttl_seconds = int((midnight - datetime.utcnow()).total_seconds()) + 86400

                self.redis_client.expire(key, ttl_seconds)
            except Exception as e:
                logger.error(f"❌ Erreur incrémentation journalière: {e}")

    def get_processed_today(self) -> int:
        """Récupère le nombre d'actualités traitées aujourd'hui"""
        if self.redis_client:
            try:
                today = datetime.utcnow().strftime("%Y-%m-%d")
                key = self._get_key(f"processed_today:{today}")
                count = self.redis_client.get(key)
                return int(count) if count else 0
            except Exception as e:
                logger.error(f"❌ Erreur récupération compteur journalier: {e}")
        return 0

    def get_total_processed(self) -> int:
        """Récupère le nombre total d'actualités traitées"""
        if self.redis_client:
            try:
                key = self._get_key("total_processed")
                count = self.redis_client.get(key)
                return int(count) if count else self.total_processed
            except Exception as e:
                logger.error(f"❌ Erreur récupération total: {e}")
        return self.total_processed

    def get_cache_hits(self) -> int:
        """Récupère le nombre de cache hits"""
        if self.redis_client:
            try:
                key = self._get_key("cache_hits")
                count = self.redis_client.get(key)
                return int(count) if count else self.cache_hits
            except Exception as e:
                logger.error(f"❌ Erreur récupération cache_hits: {e}")
        return self.cache_hits

    def get_cache_misses(self) -> int:
        """Récupère le nombre de cache misses"""
        if self.redis_client:
            try:
                key = self._get_key("cache_misses")
                count = self.redis_client.get(key)
                return int(count) if count else self.cache_misses
            except Exception as e:
                logger.error(f"❌ Erreur récupération cache_misses: {e}")
        return self.cache_misses

    def set_last_update(self) -> None:
        """Enregistre l'horodatage de la dernière mise à jour"""
        self.last_update = datetime.utcnow()

        if self.redis_client:
            try:
                key = self._get_key("last_update")
                self.redis_client.set(key, self.last_update.isoformat())
            except Exception as e:
                logger.error(f"❌ Erreur enregistrement last_update: {e}")

    def get_last_update(self) -> str:
        """Récupère l'horodatage de la dernière mise à jour"""
        if self.redis_client:
            try:
                key = self._get_key("last_update")
                timestamp = self.redis_client.get(key)
                if timestamp:
                    return timestamp
            except Exception as e:
                logger.error(f"❌ Erreur récupération last_update: {e}")

        return self.last_update.isoformat()

    def get_all_stats(self) -> Dict[str, Any]:
        """
        Récupère toutes les statistiques en une seule fois

        Returns:
            {
                "total_news": 187,
                "processed_today": 12,
                "avg_embedding_time_ms": 640.5,
                "cache_hits": 18,
                "cache_misses": 2,
                "last_update": "2025-10-25T18:42:00Z"
            }
        """
        return {
            "total_processed": self.get_total_processed(),
            "processed_today": self.get_processed_today(),
            "avg_processing_time_ms": round(self.get_avg_processing_time(), 2),
            "cache_hits": self.get_cache_hits(),
            "cache_misses": self.get_cache_misses(),
            "last_update": self.get_last_update()
        }

    def reset_stats(self) -> None:
        """Réinitialise toutes les statistiques (admin uniquement)"""
        if self.redis_client:
            try:
                # Supprimer toutes les clés de métriques
                pattern = "news:metrics:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                logger.info("🔄 Métriques réinitialisées")
            except Exception as e:
                logger.error(f"❌ Erreur reset stats: {e}")

        # Reset mémoire locale
        self.processing_times.clear()
        self.total_processed = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.last_update = datetime.utcnow()


# Instance globale
news_metrics = NewsMetrics()
