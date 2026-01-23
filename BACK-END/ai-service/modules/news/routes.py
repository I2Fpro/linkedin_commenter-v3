"""
Routes FastAPI pour le module News
- POST /news/register: Enregistrer des URLs d'actualités (avec batch optimisé)
- POST /news/vector-search: Recherche vectorielle
- GET /news/stats: Statistiques et métriques
- GET /news/debug/{url}: Debug d'une URL spécifique
- GET /news/health: Health check
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
import logging

from .models import (
    NewsRegisterRequest,
    NewsRegisterResponse,
    NewsSearchRequest,
    NewsSearchResponse,
    NewsSearchResult
)
from .service import news_processor
from .database import news_db
from .cache_manager import news_cache
from .metrics import news_metrics
from .news_logger import news_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["news"])


@router.post("/register", response_model=NewsRegisterResponse)
async def register_news(request: NewsRegisterRequest):
    """
    Enregistre des URLs d'actualités LinkedIn avec optimisations

    Nouveau comportement (v2.2+):
    - Vérification cache Redis (TTL 48h)
    - Vérification PostgreSQL
    - Traitement en parallèle (max 5 concurrents)
    - Retry logic avec backoff exponentiel
    - Métriques et logging

    Body:
    {
        "urls": ["https://linkedin.com/news/story/123", ...],
        "lang": "fr"
    }

    Response:
    {
        "registered": 2,
        "skipped": 1,
        "processed_urls": [...]
    }
    """
    logger.info(f"📥 Requête d'enregistrement: {len(request.urls)} URLs, langue: {request.lang}")

    try:
        # Utiliser la nouvelle méthode batch optimisée
        result = await news_processor.process_urls_batch(request.urls, request.lang)

        # Liste des URLs traitées
        processed_urls = []
        for url in request.urls:
            # Vérifier si l'URL a été traitée (cache ou DB)
            if news_cache.is_cached(url) or await news_db.url_exists(url):
                processed_urls.append(url)

        logger.info(f"📊 Résultat: {result['registered']} enregistrées, {result['skipped']} ignorées")

        return NewsRegisterResponse(
            registered=result["registered"],
            skipped=result["skipped"],
            processed_urls=processed_urls[:result["registered"]]  # Limiter à celles vraiment enregistrées
        )

    except Exception as e:
        logger.error(f"❌ Erreur lors de l'enregistrement: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'enregistrement des actualités: {str(e)}"
        )


@router.post("/vector-search", response_model=NewsSearchResponse)
async def vector_search(request: NewsSearchRequest):
    """
    Recherche vectorielle des actualités similaires

    Body:
    {
        "query": "marché de l'emploi dans l'IA",
        "lang": "fr",
        "limit": 3
    }

    Response:
    {
        "results": [
            {
                "url": "...",
                "title": "...",
                "summary": "...",
                "similarity": 0.87
            }
        ]
    }
    """
    logger.info(f"🔍 Recherche vectorielle: '{request.query[:50]}...', langue: {request.lang}, limit: {request.limit}")

    try:
        # Effectuer la recherche
        results = await news_processor.search_similar_news(
            request.query,
            request.lang,
            request.limit
        )

        # Convertir en modèle Pydantic
        search_results = [
            NewsSearchResult(
                url=result["url"],
                title=result["title"],
                summary=result["summary"],
                similarity=result["similarity"]
            )
            for result in results
        ]

        logger.info(f"✅ {len(search_results)} résultats trouvés")

        return NewsSearchResponse(results=search_results)

    except Exception as e:
        logger.error(f"❌ Erreur recherche vectorielle: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la recherche: {str(e)}"
        )


@router.get("/stats")
async def get_news_stats():
    """
    Récupère les statistiques et métriques du module News

    Response:
    {
        "total_news": 187,
        "processed_today": 12,
        "avg_embedding_time_ms": 640.5,
        "cache_hits": 18,
        "cache_misses": 2,
        "last_update": "2025-10-25T18:42:00Z",
        "cache_info": {
            "cached_urls": 45,
            "ttl_hours": 48
        },
        "db_stats": {
            "failed_with_retry": 3
        }
    }
    """
    try:
        # Métriques Redis/mémoire
        metrics_stats = news_metrics.get_all_stats()

        # Statistiques DB
        db_stats = await news_db.get_stats_from_db()

        # Statistiques cache
        cache_stats = news_cache.get_cache_stats()

        # Fusionner toutes les stats
        combined_stats = {
            **metrics_stats,
            "total_news": db_stats.get("total_news", 0),  # Priorité à la DB
            "cache_info": {
                "status": cache_stats.get("status"),
                "cached_urls": cache_stats.get("cached_urls", 0),
                "ttl_hours": cache_stats.get("ttl_hours", 48)
            },
            "db_stats": {
                "failed_with_retry": db_stats.get("failed_with_retry", 0)
            }
        }

        # Override last_update si DB plus récente
        if db_stats.get("last_update"):
            combined_stats["last_update"] = db_stats["last_update"]

        logger.info(f"📊 Stats récupérées: {combined_stats.get('total_news')} actus, {combined_stats.get('cache_hits')} cache hits")

        return combined_stats

    except Exception as e:
        logger.error(f"❌ Erreur récupération stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des stats: {str(e)}"
        )


@router.get("/debug/{url:path}")
async def debug_news_by_url(url: str):
    """
    Récupère les détails complets d'une actualité par URL (pour debug)

    Response:
    {
        "url": "...",
        "title": "...",
        "summary": "...",
        "embedding_size": 1536,
        "embedding_preview": [0.023, -0.145, ...],  # 10 premières valeurs
        "scraped_at": "2025-10-25T18:32:00Z",
        "lang": "fr",
        "processing_time_ms": 920,
        "cached": false,
        "retry_count": 0,
        "last_error": null
    }
    """
    try:
        # Vérifier le cache
        cached = news_cache.is_cached(url)

        # Récupérer depuis la DB
        news_item = await news_db.get_news_by_url(url)

        if not news_item:
            raise HTTPException(
                status_code=404,
                detail=f"Actualité non trouvée: {url}"
            )

        # Préparer la réponse
        embedding = news_item.get("embedding")
        embedding_preview = None
        embedding_size = 0

        if embedding:
            if isinstance(embedding, list):
                embedding_size = len(embedding)
                embedding_preview = embedding[:10]  # Premiers 10 valeurs
            else:
                # Peut-être une string, essayer de parser
                try:
                    import json
                    embedding_list = json.loads(str(embedding))
                    embedding_size = len(embedding_list)
                    embedding_preview = embedding_list[:10]
                except:
                    embedding_size = 0
                    embedding_preview = None

        response = {
            "url": news_item.get("url"),
            "title": news_item.get("title"),
            "summary": news_item.get("summary"),
            "embedding_size": embedding_size,
            "embedding_preview": embedding_preview,
            "scraped_at": news_item.get("scraped_at").isoformat() if news_item.get("scraped_at") else None,
            "lang": news_item.get("lang"),
            "processing_time_ms": news_item.get("processing_time_ms"),
            "cached": cached,
            "retry_count": news_item.get("retry_count", 0),
            "last_error": news_item.get("last_error"),
            "processed": news_item.get("processed", False)
        }

        logger.info(f"🔍 Debug URL: {url} (cached={cached})")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur debug URL {url}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


@router.get("/health")
async def news_health():
    """Vérifie la santé du module news"""
    try:
        # Vérifier la connexion à la base
        if not news_db.pool:
            return {
                "status": "error",
                "message": "Base de données non connectée",
                "components": {
                    "database": "disconnected",
                    "redis": "unknown",
                    "processor": "unknown"
                }
            }

        # Compter les actualités en base
        all_news = await news_db.get_all_news(limit=1)

        # Vérifier Redis
        cache_stats = news_cache.get_cache_stats()
        redis_status = cache_stats.get("status", "unknown")

        # Vérifier les métriques
        metrics_stats = news_metrics.get_all_stats()

        return {
            "status": "ok",
            "components": {
                "database": "connected",
                "redis": redis_status,
                "processor": "initialized"
            },
            "stats": {
                "total_news": metrics_stats.get("total_processed", 0),
                "cached_urls": cache_stats.get("cached_urls", 0),
                "cache_hits": metrics_stats.get("cache_hits", 0)
            }
        }
    except Exception as e:
        logger.error(f"❌ Health check échoué: {e}")
        return {
            "status": "error",
            "message": str(e),
            "components": {
                "database": "error",
                "redis": "error",
                "processor": "error"
            }
        }


@router.get("/debug/all")
async def debug_all_news(
    lang: Optional[str] = Query(None, description="Filtrer par langue (fr, en)"),
    limit: int = Query(10, description="Nombre max de résultats", ge=1, le=100)
):
    """
    [DEBUG] Récupère toutes les actualités en base
    Utile pour vérifier le contenu de la base
    """
    try:
        news = await news_db.get_all_news(lang=lang, limit=limit)

        # Nettoyer les embeddings pour l'affichage (trop volumineux)
        for item in news:
            if "embedding" in item and item["embedding"]:
                # Compter les dimensions
                try:
                    if isinstance(item["embedding"], list):
                        dim_count = len(item["embedding"])
                    else:
                        dim_count = "unknown"
                    item["embedding"] = f"[{dim_count} dimensions]"
                except:
                    item["embedding"] = "[embedding présent]"

        return {
            "count": len(news),
            "filters": {"lang": lang, "limit": limit},
            "news": news
        }
    except Exception as e:
        logger.error(f"❌ Erreur debug: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/logs")
async def debug_recent_logs(limit: int = Query(50, description="Nombre de logs", ge=1, le=200)):
    """
    [DEBUG] Récupère les logs récents depuis news_logs.json
    """
    try:
        logs = news_logger.get_recent_logs(limit=limit)
        return {
            "count": len(logs),
            "logs": logs
        }
    except Exception as e:
        logger.error(f"❌ Erreur récupération logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/errors")
async def debug_error_logs(limit: int = Query(20, description="Nombre d'erreurs", ge=1, le=100)):
    """
    [DEBUG] Récupère uniquement les logs d'erreur
    """
    try:
        error_logs = news_logger.get_error_logs(limit=limit)
        return {
            "count": len(error_logs),
            "errors": error_logs
        }
    except Exception as e:
        logger.error(f"❌ Erreur récupération error logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
