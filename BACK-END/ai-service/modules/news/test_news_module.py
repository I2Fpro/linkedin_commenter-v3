"""
Tests unitaires pour le module News v2.2
Ces tests sont des exemples de validation - pas encore automatisés

Pour exécuter manuellement :
python test_news_module.py
"""
import asyncio
import os
from cache_manager import news_cache
from metrics import news_metrics
from news_logger import news_logger
from database import news_db
from service import news_processor


async def test_cache_manager():
    """Test du cache Redis"""
    print("\n🧪 Test Cache Manager")

    # Test 1: Set cache
    url = "https://test.com/news/1"
    success = news_cache.set_cached(url, {"title": "Test", "lang": "fr"})
    assert success, "❌ Échec set_cached"
    print("✅ set_cached fonctionne")

    # Test 2: Is cached
    is_cached = news_cache.is_cached(url)
    assert is_cached, "❌ Échec is_cached"
    print("✅ is_cached fonctionne")

    # Test 3: Get metadata
    metadata = news_cache.get_cached_metadata(url)
    assert metadata is not None, "❌ Échec get_cached_metadata"
    assert metadata["url"] == url, "❌ URL incorrecte dans metadata"
    print(f"✅ get_cached_metadata fonctionne: {metadata}")

    # Test 4: Refresh TTL
    refreshed = news_cache.refresh_ttl(url)
    assert refreshed, "❌ Échec refresh_ttl"
    print("✅ refresh_ttl fonctionne")

    # Test 5: Invalidate
    invalidated = news_cache.invalidate(url)
    assert invalidated, "❌ Échec invalidate"
    is_cached_after = news_cache.is_cached(url)
    assert not is_cached_after, "❌ URL encore en cache après invalidation"
    print("✅ invalidate fonctionne")

    # Test 6: Cache stats
    stats = news_cache.get_cache_stats()
    assert stats["status"] == "connected", "❌ Redis non connecté"
    print(f"✅ get_cache_stats fonctionne: {stats}")

    print("✅ Cache Manager : TOUS LES TESTS PASSÉS")


async def test_metrics():
    """Test des métriques"""
    print("\n🧪 Test Metrics")

    # Test 1: Record processing time
    news_metrics.record_processing_time(920.5)
    news_metrics.record_processing_time(1050.3)
    news_metrics.record_processing_time(780.1)
    print("✅ record_processing_time fonctionne")

    # Test 2: Get avg
    avg = news_metrics.get_avg_processing_time()
    assert avg > 0, "❌ Moyenne nulle"
    print(f"✅ get_avg_processing_time: {avg:.2f}ms")

    # Test 3: Increment counters
    news_metrics.increment_total_processed()
    news_metrics.increment_cache_hit()
    news_metrics.increment_cache_miss()
    news_metrics.increment_processed_today()
    print("✅ Incrémentations fonctionnent")

    # Test 4: Get stats
    stats = news_metrics.get_all_stats()
    assert stats["total_processed"] > 0, "❌ total_processed nul"
    assert stats["cache_hits"] > 0, "❌ cache_hits nul"
    print(f"✅ get_all_stats fonctionne: {stats}")

    print("✅ Metrics : TOUS LES TESTS PASSÉS")


async def test_logger():
    """Test du logging"""
    print("\n🧪 Test Logger")

    # Test 1: Log processing success
    news_logger.log_processing(
        "https://test.com/news/1",
        "success",
        duration_ms=920.5,
        metadata={"lang": "fr", "title": "Test"}
    )
    print("✅ log_processing (success) fonctionne")

    # Test 2: Log processing error
    news_logger.log_processing(
        "https://test.com/news/2",
        "error",
        duration_ms=1500.0,
        error="HTTP 404",
        metadata={"lang": "en"}
    )
    print("✅ log_processing (error) fonctionne")

    # Test 3: Log processing cached
    news_logger.log_processing(
        "https://test.com/news/3",
        "cached",
        metadata={"lang": "fr"}
    )
    print("✅ log_processing (cached) fonctionne")

    # Test 4: Get recent logs
    recent_logs = news_logger.get_recent_logs(limit=10)
    assert len(recent_logs) >= 3, f"❌ Pas assez de logs: {len(recent_logs)}"
    print(f"✅ get_recent_logs fonctionne: {len(recent_logs)} logs")

    # Test 5: Get error logs
    error_logs = news_logger.get_error_logs(limit=5)
    assert len(error_logs) >= 1, "❌ Pas de logs d'erreur"
    print(f"✅ get_error_logs fonctionne: {len(error_logs)} erreurs")

    print("✅ Logger : TOUS LES TESTS PASSÉS")


async def test_database():
    """Test des méthodes de base de données"""
    print("\n🧪 Test Database")

    # Connecter à la DB
    await news_db.connect()

    # Test 1: URL exists
    url = "https://test-db.com/news/1"
    exists = await news_db.url_exists(url)
    print(f"✅ url_exists fonctionne: {exists}")

    # Test 2: Insert news
    if not exists:
        news_id = await news_db.insert_news(
            url=url,
            title="Test DB News",
            summary="This is a test summary",
            lang="en",
            embedding=[0.1] * 1536  # Fake embedding
        )
        print(f"✅ insert_news fonctionne: ID={news_id}")

    # Test 3: Get news by URL
    news_item = await news_db.get_news_by_url(url)
    assert news_item is not None, "❌ News item non trouvé"
    assert news_item["url"] == url, "❌ URL incorrecte"
    print(f"✅ get_news_by_url fonctionne: {news_item['title']}")

    # Test 4: Update processing metadata
    await news_db.update_processing_metadata(
        url=url,
        processing_time_ms=920.5,
        retry_count=0
    )
    print("✅ update_processing_metadata fonctionne")

    # Test 5: Log processing
    await news_db.log_processing(
        url=url,
        status="success",
        duration_ms=920.5,
        metadata={"lang": "en", "title": "Test"}
    )
    print("✅ log_processing (DB) fonctionne")

    # Test 6: Get stats from DB
    stats = await news_db.get_stats_from_db()
    assert "total_news" in stats, "❌ Stats incomplètes"
    print(f"✅ get_stats_from_db fonctionne: {stats}")

    # Test 7: Get all news
    all_news = await news_db.get_all_news(limit=5)
    assert len(all_news) > 0, "❌ Aucune actualité en base"
    print(f"✅ get_all_news fonctionne: {len(all_news)} actus")

    await news_db.close()
    print("✅ Database : TOUS LES TESTS PASSÉS")


async def test_service_integration():
    """Test d'intégration du service complet"""
    print("\n🧪 Test Service Integration")

    # Connecter à la DB
    await news_db.connect()

    # Test 1: Process URL (simulé - ne pas scraper réellement)
    # Ce test nécessiterait de mocker OpenAI et httpx
    print("⚠️ Test process_url nécessite mocking (pas implémenté)")

    # Test 2: Search similar news
    results = await news_processor.search_similar_news(
        query="artificial intelligence employment",
        lang="en",
        limit=3
    )
    print(f"✅ search_similar_news fonctionne: {len(results)} résultats")

    await news_db.close()
    print("✅ Service Integration : TESTS PASSÉS")


async def run_all_tests():
    """Exécute tous les tests"""
    print("=" * 60)
    print("🚀 Lancement des tests du module News v2.2")
    print("=" * 60)

    try:
        await test_cache_manager()
        await test_metrics()
        await test_logger()
        await test_database()
        await test_service_integration()

        print("\n" + "=" * 60)
        print("✅ TOUS LES TESTS SONT PASSÉS !")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ ÉCHEC DU TEST: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")
        raise


if __name__ == "__main__":
    # Configuration pour les tests
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
    os.environ.setdefault("DATABASE_URL", "postgresql://linkedin_user:linkedinai_secure_password_2024@localhost:5432/linkedin_ai_db")
    os.environ.setdefault("NEWS_TTL_HOURS", "48")
    os.environ.setdefault("DEBUG_NEWS", "false")
    os.environ.setdefault("MAX_NEWS_CONCURRENCY", "5")
    os.environ.setdefault("OPENAI_API_KEY", "sk-test-key")

    # Lancer les tests
    asyncio.run(run_all_tests())
