"""
Gestion de la base de données PostgreSQL avec pgvector
"""
import asyncpg
import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class NewsDatabase:
    """Gestion de la connexion et des requêtes à PostgreSQL avec pgvector"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://linkedin_user:password@postgres:5432/linkedin_ai_db"
        )

    async def connect(self):
        """Initialise le pool de connexions"""
        try:
            self.pool = await asyncpg.create_pool(
                self.db_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("✅ Connexion PostgreSQL établie")

            # Créer l'extension pgvector et la table si nécessaire
            await self.initialize_schema()
        except Exception as e:
            logger.error(f"❌ Erreur connexion PostgreSQL: {e}")
            raise

    async def close(self):
        """Ferme le pool de connexions"""
        if self.pool:
            await self.pool.close()
            logger.info("🔒 Connexion PostgreSQL fermée")

    async def initialize_schema(self):
        """Crée l'extension pgvector et la table news si nécessaire"""
        async with self.pool.acquire() as conn:
            try:
                # Créer l'extension pgvector
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                logger.info("✅ Extension pgvector activée")

                # Créer la table news
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS news (
                        id SERIAL PRIMARY KEY,
                        url TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        summary TEXT,
                        lang VARCHAR(10) NOT NULL DEFAULT 'fr',
                        embedding vector(1536),
                        scraped_at TIMESTAMP DEFAULT NOW(),
                        processed BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT NOW(),
                        processing_time_ms FLOAT,
                        retry_count INT DEFAULT 0,
                        last_error TEXT
                    );
                """)
                logger.info("✅ Table news créée ou déjà existante")

                # Créer un index pour la recherche vectorielle
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS news_embedding_idx
                    ON news USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                """)
                logger.info("✅ Index vectoriel créé")

                # Créer la table de logs de traitement
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS news_processing_log (
                        id SERIAL PRIMARY KEY,
                        url TEXT NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        duration_ms FLOAT,
                        error_message TEXT,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)

                # Index pour la table de logs
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_news_processing_url
                    ON news_processing_log(url);
                """)
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_news_processing_status
                    ON news_processing_log(status);
                """)
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_news_processing_created_at
                    ON news_processing_log(created_at DESC);
                """)
                logger.info("✅ Table news_processing_log créée")

            except Exception as e:
                logger.error(f"❌ Erreur initialisation schéma: {e}")
                raise

    async def url_exists(self, url: str) -> bool:
        """Vérifie si une URL existe déjà en base"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM news WHERE url = $1)",
                url
            )
            return result

    async def insert_news(
        self,
        url: str,
        title: str,
        summary: Optional[str],
        lang: str,
        embedding: Optional[List[float]] = None
    ) -> int:
        """Insère une nouvelle actualité"""
        async with self.pool.acquire() as conn:
            try:
                # Conversion de l'embedding en format PostgreSQL
                embedding_str = None
                if embedding:
                    embedding_str = "[" + ",".join(map(str, embedding)) + "]"

                news_id = await conn.fetchval(
                    """
                    INSERT INTO news (url, title, summary, lang, embedding, processed)
                    VALUES ($1, $2, $3, $4, $5::vector, $6)
                    ON CONFLICT (url) DO UPDATE
                    SET title = EXCLUDED.title,
                        summary = EXCLUDED.summary,
                        embedding = EXCLUDED.embedding,
                        processed = EXCLUDED.processed
                    RETURNING id
                    """,
                    url, title, summary, lang, embedding_str, True if embedding else False
                )
                logger.info(f"✅ Actualité insérée: {url} (ID: {news_id})")
                return news_id
            except Exception as e:
                logger.error(f"❌ Erreur insertion actualité: {e}")
                raise

    async def vector_search(
        self,
        query_embedding: List[float],
        lang: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Recherche les actualités les plus proches sémantiquement"""
        async with self.pool.acquire() as conn:
            try:
                # Conversion de l'embedding en format PostgreSQL
                embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

                rows = await conn.fetch(
                    """
                    SELECT
                        url,
                        title,
                        summary,
                        1 - (embedding <=> $1::vector) as similarity
                    FROM news
                    WHERE lang = $2 AND embedding IS NOT NULL
                    ORDER BY embedding <=> $1::vector
                    LIMIT $3
                    """,
                    embedding_str, lang, limit
                )

                results = [
                    {
                        "url": row["url"],
                        "title": row["title"],
                        "summary": row["summary"] or "",
                        "similarity": float(row["similarity"])
                    }
                    for row in rows
                ]

                logger.info(f"🔍 Recherche vectorielle: {len(results)} résultats trouvés")
                return results

            except Exception as e:
                logger.error(f"❌ Erreur recherche vectorielle: {e}")
                raise

    async def get_all_news(self, lang: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère toutes les actualités (pour debug)"""
        async with self.pool.acquire() as conn:
            if lang:
                rows = await conn.fetch(
                    "SELECT * FROM news WHERE lang = $1 ORDER BY created_at DESC LIMIT $2",
                    lang, limit
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM news ORDER BY created_at DESC LIMIT $1",
                    limit
                )

            return [dict(row) for row in rows]

    async def get_news_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Récupère une actualité par son URL"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM news WHERE url = $1",
                url
            )
            return dict(row) if row else None

    async def update_processing_metadata(
        self,
        url: str,
        processing_time_ms: Optional[float] = None,
        retry_count: Optional[int] = None,
        last_error: Optional[str] = None
    ) -> None:
        """Met à jour les métadonnées de traitement d'une actualité"""
        async with self.pool.acquire() as conn:
            updates = []
            params = [url]
            param_idx = 2

            if processing_time_ms is not None:
                updates.append(f"processing_time_ms = ${param_idx}")
                params.append(processing_time_ms)
                param_idx += 1

            if retry_count is not None:
                updates.append(f"retry_count = ${param_idx}")
                params.append(retry_count)
                param_idx += 1

            if last_error is not None:
                updates.append(f"last_error = ${param_idx}")
                params.append(last_error)
                param_idx += 1

            if updates:
                query = f"UPDATE news SET {', '.join(updates)} WHERE url = $1"
                await conn.execute(query, *params)

    async def log_processing(
        self,
        url: str,
        status: str,
        duration_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Enregistre un log de traitement dans la base"""
        async with self.pool.acquire() as conn:
            import json
            metadata_json = json.dumps(metadata) if metadata else None

            await conn.execute(
                """
                INSERT INTO news_processing_log (url, status, duration_ms, error_message, metadata)
                VALUES ($1, $2, $3, $4, $5::jsonb)
                """,
                url, status, duration_ms, error_message, metadata_json
            )

    async def get_stats_from_db(self) -> Dict[str, Any]:
        """Récupère les statistiques depuis la base de données"""
        async with self.pool.acquire() as conn:
            # Statistiques générales
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) FILTER (WHERE processed = true) as total_processed,
                    COUNT(*) FILTER (WHERE created_at::date = CURRENT_DATE) as processed_today,
                    AVG(processing_time_ms) FILTER (WHERE processing_time_ms IS NOT NULL) as avg_processing_time_ms,
                    COUNT(*) FILTER (WHERE retry_count > 0) as failed_with_retry,
                    MAX(scraped_at) as last_scraped_at
                FROM news
            """)

            return {
                "total_news": int(stats["total_processed"] or 0),
                "processed_today": int(stats["processed_today"] or 0),
                "avg_processing_time_ms": float(stats["avg_processing_time_ms"] or 0),
                "failed_with_retry": int(stats["failed_with_retry"] or 0),
                "last_update": stats["last_scraped_at"].isoformat() if stats["last_scraped_at"] else None
            }

    async def get_pending_retries(self, max_retries: int = 3) -> List[Dict[str, Any]]:
        """Récupère les URLs en échec qui peuvent être réessayées"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT url, title, lang, retry_count, last_error
                FROM news
                WHERE retry_count > 0 AND retry_count < $1 AND processed = false
                ORDER BY created_at ASC
                LIMIT 50
                """,
                max_retries
            )
            return [dict(row) for row in rows]


# Instance globale
news_db = NewsDatabase()
