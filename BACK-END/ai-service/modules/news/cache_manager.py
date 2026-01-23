"""
Gestion du cache Redis pour le module News
- Cache des URLs traitées avec TTL configurable
- Évite le retraitement inutile des actualités
"""
import redis
import os
import logging
from typing import Optional, Dict, Any
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class NewsCacheManager:
    """Gestionnaire de cache Redis pour les actualités"""

    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.ttl_hours = int(os.getenv("NEWS_TTL_HOURS", "48"))
        self.ttl_seconds = self.ttl_hours * 3600

        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            self.client.ping()
            logger.info(f"✅ Connexion Redis établie (TTL: {self.ttl_hours}h)")
        except Exception as e:
            logger.error(f"❌ Erreur connexion Redis: {e}")
            self.client = None

    def _get_cache_key(self, url: str) -> str:
        """Génère la clé de cache pour une URL"""
        return f"news:cache:{url}"

    def is_cached(self, url: str) -> bool:
        """Vérifie si une URL est en cache"""
        if not self.client:
            return False

        try:
            key = self._get_cache_key(url)
            exists = self.client.exists(key)
            return bool(exists)
        except Exception as e:
            logger.error(f"❌ Erreur vérification cache: {e}")
            return False

    def set_cached(self, url: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Marque une URL comme traitée dans le cache

        Args:
            url: L'URL de l'actualité
            metadata: Métadonnées optionnelles (title, lang, etc.)
        """
        if not self.client:
            return False

        try:
            key = self._get_cache_key(url)
            value = {
                "url": url,
                "cached_at": datetime.utcnow().isoformat(),
                **(metadata or {})
            }

            # SETEX = SET with EXpiration
            self.client.setex(
                key,
                self.ttl_seconds,
                json.dumps(value)
            )
            logger.debug(f"✅ URL mise en cache: {url} (TTL: {self.ttl_hours}h)")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur mise en cache: {e}")
            return False

    def get_cached_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """Récupère les métadonnées d'une URL en cache"""
        if not self.client:
            return None

        try:
            key = self._get_cache_key(url)
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"❌ Erreur récupération cache: {e}")
            return None

    def refresh_ttl(self, url: str) -> bool:
        """
        Prolonge la durée de vie d'une URL en cache
        Utile quand l'URL existe en DB mais a expiré du cache
        """
        if not self.client:
            return False

        try:
            key = self._get_cache_key(url)
            if self.client.exists(key):
                self.client.expire(key, self.ttl_seconds)
                logger.debug(f"🔄 TTL rafraîchi pour: {url}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Erreur refresh TTL: {e}")
            return False

    def invalidate(self, url: str) -> bool:
        """Supprime une URL du cache (forcer le retraitement)"""
        if not self.client:
            return False

        try:
            key = self._get_cache_key(url)
            deleted = self.client.delete(key)
            if deleted:
                logger.info(f"🗑️ URL supprimée du cache: {url}")
            return bool(deleted)
        except Exception as e:
            logger.error(f"❌ Erreur suppression cache: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """Récupère des statistiques sur le cache"""
        if not self.client:
            return {
                "status": "disconnected",
                "cached_urls": 0
            }

        try:
            # Compter les clés news:cache:*
            pattern = "news:cache:*"
            keys = self.client.keys(pattern)

            return {
                "status": "connected",
                "cached_urls": len(keys),
                "ttl_hours": self.ttl_hours,
                "redis_info": {
                    "used_memory_human": self.client.info("memory").get("used_memory_human"),
                    "connected_clients": self.client.info("clients").get("connected_clients")
                }
            }
        except Exception as e:
            logger.error(f"❌ Erreur stats cache: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Instance globale
news_cache = NewsCacheManager()
