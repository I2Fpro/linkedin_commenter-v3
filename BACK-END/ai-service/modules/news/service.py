"""
Service de traitement des actualités LinkedIn
- Scraping du contenu HTML
- Génération de résumés via OpenAI
- Génération d'embeddings
- Stockage en base de données
- Cache Redis avec TTL
- Retry logic avec backoff exponentiel
- Parallélisation avec semaphore
- Métriques et logging
"""
import logging
import httpx
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any
from openai import OpenAI
import os
import re
import asyncio
from datetime import datetime
import time

from .database import news_db
from .models import NewsArticle
from .cache_manager import news_cache
from .metrics import news_metrics
from .news_logger import news_logger

logger = logging.getLogger(__name__)


class NewsProcessor:
    """Processeur d'actualités LinkedIn avec optimisations"""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.embedding_model = "text-embedding-3-small"
        self.max_concurrency = int(os.getenv("MAX_NEWS_CONCURRENCY", "5"))
        self.max_retries = 3
        self.debug_mode = os.getenv("DEBUG_NEWS", "false").lower() == "true"

        # Semaphore pour limiter la parallélisation
        self.semaphore = asyncio.Semaphore(self.max_concurrency)

        logger.info(f"🧠 NewsProcessor initialisé (max_concurrency={self.max_concurrency}, debug={self.debug_mode})")

    async def scrape_linkedin_news(self, url: str, retry_attempt: int = 0) -> Optional[str]:
        """
        Scrape le contenu d'une page LinkedIn News avec retry logic

        Args:
            url: URL de l'actualité
            retry_attempt: Numéro de tentative (0 = première tentative)
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            }

            # Timeout avec backoff exponentiel
            timeout = 30.0 + (retry_attempt * 10)

            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # Supprimer les scripts et styles
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()

                # Tentative d'extraction du contenu principal
                content = None

                # Tentative 1: Recherche des balises article
                article = soup.find("article")
                if article:
                    content = article.get_text(separator=" ", strip=True)

                # Tentative 2: Recherche de divs avec classes communes LinkedIn
                if not content:
                    main_content = soup.find("div", class_=re.compile(r"(article|content|main|post)"))
                    if main_content:
                        content = main_content.get_text(separator=" ", strip=True)

                # Tentative 3: Extraction de tout le body
                if not content:
                    body = soup.find("body")
                    if body:
                        content = body.get_text(separator=" ", strip=True)

                # Nettoyage du contenu
                if content:
                    # Supprimer les espaces multiples
                    content = re.sub(r'\s+', ' ', content)
                    # Limiter à 3000 caractères pour le résumé
                    content = content[:3000].strip()

                    logger.info(f"✅ Scraping réussi: {url} ({len(content)} caractères)")

                    # Log debug du contenu
                    if self.debug_mode:
                        news_logger.log_scraping_debug(url, content, len(content))

                    return content
                else:
                    logger.warning(f"⚠️ Aucun contenu trouvé pour: {url}")
                    return None

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Too Many Requests
                logger.warning(f"⚠️ Rate limit atteint pour {url}, retry {retry_attempt + 1}/{self.max_retries}")
            else:
                logger.error(f"❌ Erreur HTTP {e.response.status_code} lors du scraping de {url}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"❌ Erreur HTTP lors du scraping de {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Erreur scraping {url}: {e}")
            raise

    def generate_summary(self, content: str, lang: str = "fr") -> Optional[str]:
        """
        Génère un résumé court du contenu via GPT
        """
        try:
            if lang == "en":
                system_prompt = "You are a professional summarizer. Create concise, informative summaries."
                user_prompt = f"""Summarize the following LinkedIn article in 2-3 sentences (max 100 words).
Focus on the key information and main message.

Content:
{content}

Summary:"""
            else:
                system_prompt = "Tu es un expert en résumé. Crée des résumés concis et informatifs."
                user_prompt = f"""Résume cet article LinkedIn en 2-3 phrases (max 100 mots).
Concentre-toi sur les informations clés et le message principal.

Contenu:
{content}

Résumé:"""

            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=150,
                temperature=0.5,
                timeout=30
            )

            summary = response.choices[0].message.content.strip()
            logger.info(f"✅ Résumé généré ({len(summary)} caractères)")

            # Log debug du prompt et résumé
            if self.debug_mode:
                news_logger.log_summary_debug(content[:200], system_prompt, user_prompt[:500], summary)

            return summary

        except Exception as e:
            logger.error(f"❌ Erreur génération résumé: {e}")
            return None

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Génère un embedding du texte via OpenAI
        """
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )

            embedding = response.data[0].embedding
            logger.info(f"✅ Embedding généré ({len(embedding)} dimensions)")

            # Log debug (sans le vecteur complet)
            if self.debug_mode:
                news_logger.log_embedding_debug(text[:200], text, len(embedding))

            return embedding

        except Exception as e:
            logger.error(f"❌ Erreur génération embedding: {e}")
            return None

    async def process_url_with_retry(
        self,
        url: str,
        title: str,
        lang: str = "fr"
    ) -> bool:
        """
        Traite une URL avec retry logic et backoff exponentiel

        Returns:
            True si traitement réussi, False sinon
        """
        start_time = time.time()

        for attempt in range(self.max_retries):
            try:
                # Étape 1: Scraping
                content = await self.scrape_linkedin_news(url, retry_attempt=attempt)
                if not content:
                    logger.warning(f"⚠️ Impossible de scraper {url}, tentative {attempt + 1}/{self.max_retries}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Backoff: 1s, 2s, 4s
                        continue
                    else:
                        # Dernier échec: insérer quand même avec seulement le titre
                        await news_db.insert_news(url, title, None, lang, None)
                        await news_db.update_processing_metadata(
                            url,
                            retry_count=self.max_retries,
                            last_error="Scraping failed after retries"
                        )
                        duration_ms = (time.time() - start_time) * 1000
                        news_logger.log_processing(url, "error", duration_ms, "Scraping failed", {"lang": lang, "retries": self.max_retries})
                        await news_db.log_processing(url, "error", duration_ms, "Scraping failed", {"lang": lang, "retries": self.max_retries})
                        return False

                # Étape 2: Résumé
                summary = self.generate_summary(content, lang)
                if not summary:
                    logger.warning(f"⚠️ Impossible de générer un résumé pour {url}")
                    summary = content[:200] + "..."

                # Étape 3: Embedding du résumé
                embedding = self.generate_embedding(summary)
                if not embedding:
                    logger.warning(f"⚠️ Impossible de générer un embedding pour {url}")

                # Étape 4: Stockage
                await news_db.insert_news(url, title, summary, lang, embedding)

                # Métadonnées de traitement
                duration_ms = (time.time() - start_time) * 1000
                await news_db.update_processing_metadata(url, processing_time_ms=duration_ms)

                # Logging
                news_logger.log_processing(url, "success", duration_ms, metadata={"lang": lang, "title": title})
                await news_db.log_processing(url, "success", duration_ms, metadata={"lang": lang, "title": title})

                # Métriques
                news_metrics.record_processing_time(duration_ms)
                news_metrics.increment_total_processed()
                news_metrics.increment_processed_today()
                news_metrics.set_last_update()

                logger.info(f"✅ Actualité traitée avec succès: {url} ({duration_ms:.0f}ms)")
                return True

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < self.max_retries - 1:
                    # Rate limit: attendre plus longtemps
                    backoff_time = (2 ** attempt) * 2  # 2s, 4s, 8s
                    logger.warning(f"⚠️ Rate limit, attente {backoff_time}s avant retry")
                    await asyncio.sleep(backoff_time)
                    continue
                else:
                    # Autre erreur HTTP ou dernier essai
                    error_msg = f"HTTP {e.response.status_code}"
                    duration_ms = (time.time() - start_time) * 1000
                    await news_db.update_processing_metadata(url, retry_count=attempt + 1, last_error=error_msg)
                    news_logger.log_processing(url, "error", duration_ms, error_msg, {"lang": lang, "attempt": attempt + 1})
                    await news_db.log_processing(url, "error", duration_ms, error_msg, {"lang": lang, "attempt": attempt + 1})
                    if attempt >= self.max_retries - 1:
                        return False

            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ Erreur traitement de {url} (tentative {attempt + 1}/{self.max_retries}): {e}")

                if attempt < self.max_retries - 1:
                    # Backoff exponentiel: 1s, 4s, 8s
                    backoff_time = 2 ** attempt
                    await asyncio.sleep(backoff_time)
                    continue
                else:
                    # Dernier échec
                    duration_ms = (time.time() - start_time) * 1000
                    try:
                        await news_db.insert_news(url, title, None, lang, None)
                        await news_db.update_processing_metadata(
                            url,
                            retry_count=self.max_retries,
                            last_error=error_msg[:500]
                        )
                    except:
                        pass
                    news_logger.log_processing(url, "error", duration_ms, error_msg, {"lang": lang, "retries": self.max_retries})
                    await news_db.log_processing(url, "error", duration_ms, error_msg, {"lang": lang, "retries": self.max_retries})
                    return False

        return False

    async def process_url(self, url: str, title: str, lang: str = "fr") -> bool:
        """
        Point d'entrée principal pour traiter une URL
        Gère le cache et la parallélisation avec semaphore

        Returns:
            True si traitement réussi, False sinon
        """
        async with self.semaphore:  # Limite la concurrence
            # Vérifier le cache Redis
            if news_cache.is_cached(url):
                logger.info(f"⚡ Cache hit: {url}")
                news_metrics.increment_cache_hit()
                news_logger.log_processing(url, "cached", metadata={"lang": lang})
                return True

            # Vérifier si existe en base
            exists = await news_db.url_exists(url)
            if exists:
                logger.info(f"⚡ Existe en DB, refresh cache: {url}")
                # Remettre en cache
                news_cache.set_cached(url, {"title": title, "lang": lang})
                news_metrics.increment_cache_hit()
                news_logger.log_processing(url, "cached", metadata={"lang": lang, "source": "db"})
                return True

            # Cache miss: traiter l'URL
            news_metrics.increment_cache_miss()
            success = await self.process_url_with_retry(url, title, lang)

            # Si succès, mettre en cache
            if success:
                news_cache.set_cached(url, {"title": title, "lang": lang})

            return success

    async def process_urls_batch(
        self,
        urls: List[str],
        lang: str = "fr"
    ) -> Dict[str, int]:
        """
        Traite un lot d'URLs en parallèle (avec semaphore)

        Returns:
            {"registered": X, "skipped": Y}
        """
        logger.info(f"🧠 Traitement de {len(urls)} URLs (max_concurrency={self.max_concurrency})")

        # Préparer les tâches
        tasks = []
        for url in urls:
            # Extraire un titre basique depuis l'URL
            title = url.split("/")[-1] or "LinkedIn News"
            tasks.append(self.process_url(url, title, lang))

        # Exécuter en parallèle avec asyncio.gather
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Compter les résultats
        registered = sum(1 for r in results if r is True)
        skipped = sum(1 for r in results if r is False or isinstance(r, Exception))

        logger.info(f"📊 Résultat batch: {registered} enregistrées, {skipped} ignorées/échouées")

        return {"registered": registered, "skipped": skipped}

    async def search_similar_news(
        self,
        query: str,
        lang: str = "fr",
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Recherche les actualités similaires à une requête
        """
        try:
            # Générer l'embedding de la requête
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                logger.error("❌ Impossible de générer l'embedding de la requête")
                return []

            # Recherche vectorielle
            results = await news_db.vector_search(query_embedding, lang, limit)

            logger.info(f"🔍 Recherche pour '{query[:50]}...': {len(results)} résultats")
            return results

        except Exception as e:
            logger.error(f"❌ Erreur recherche similaire: {e}")
            return []


# Instance globale
news_processor = NewsProcessor()
