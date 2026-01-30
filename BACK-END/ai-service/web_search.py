"""
Module de recherche web V3 utilisant Tavily API.
Fournit un contexte factuel enrichi pour les commentaires LinkedIn.

Story 1.4 : Recherche web avec fallback gracieux.

Note: L'implementation utilise Tavily API au lieu d'OpenAI Responses API
pour une meilleure fiabilite et des resultats plus pertinents.
"""
import logging
import asyncio
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Timeout pour la recherche web (10 secondes pour laisser le temps a Tavily)
WEB_SEARCH_TIMEOUT_SECONDS = 10

# Client Tavily (initialise au premier appel)
_tavily_client = None


def _get_tavily_client():
    """
    Retourne le client Tavily, l'initialise si necessaire.
    Retourne None si TAVILY_API_KEY n'est pas configuree.
    """
    global _tavily_client
    if _tavily_client is None:
        try:
            from config_py import TAVILY_API_KEY
            if TAVILY_API_KEY:
                from tavily import TavilyClient
                _tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
                logger.info("Tavily client initialise")
            else:
                logger.warning("TAVILY_API_KEY non configuree - recherche web desactivee")
        except ImportError as e:
            logger.warning(f"Tavily non disponible: {e}")
        except Exception as e:
            logger.warning(f"Erreur initialisation Tavily: {e}")
    return _tavily_client


async def search_web_for_context(
    post_content: str = "",
    **kwargs  # Accepte des kwargs supplementaires pour compatibilite
) -> Tuple[Optional[str], bool]:
    """
    Effectue une recherche web via Tavily API pour enrichir le contexte.

    Args:
        post_content: Contenu du post LinkedIn pour contextualiser la recherche
        **kwargs: Parametres supplementaires ignores (compatibilite avec ancienne API)

    Returns:
        Tuple (resultat_recherche, success)
        - Si succes : (texte enrichi avec sources, True)
        - Si echec/timeout : (None, False)

    Notes:
        - Timeout de 4 secondes pour respecter NFR2 (< 5s total)
        - En cas d'echec, retourne (None, False) pour fallback gracieux
        - Log WARNING en cas d'echec (pas d'erreur user-facing)
    """
    try:
        # Verifier que Tavily est configure
        tavily = _get_tavily_client()
        if tavily is None:
            logger.warning("Web search: Tavily non configure")
            return None, False

        # Construire la requete de recherche a partir du contenu du post
        search_query = _build_search_query(post_content)
        if not search_query:
            logger.warning("Web search: impossible de construire la requete")
            return None, False

        logger.info(f"Web search: recherche Tavily pour '{search_query[:50]}...'")

        # Appel avec timeout via asyncio.to_thread pour le code synchrone
        response = await asyncio.wait_for(
            asyncio.to_thread(
                _execute_tavily_search,
                tavily,
                search_query
            ),
            timeout=WEB_SEARCH_TIMEOUT_SECONDS
        )

        # Verifier si une source a ete trouvee
        if not response:
            logger.warning("Web search: aucune source pertinente trouvee")
            return None, False

        logger.info(f"Web search: source trouvee ({len(response)} chars)")
        return response, True

    except asyncio.TimeoutError:
        logger.warning(f"Web search: timeout apres {WEB_SEARCH_TIMEOUT_SECONDS}s")
        return None, False
    except Exception as e:
        logger.warning(f"Web search: erreur - {type(e).__name__}: {str(e)}")
        return None, False


def _build_search_query(post_content: str) -> Optional[str]:
    """
    Construit une requete de recherche a partir du contenu du post.

    Args:
        post_content: Contenu du post LinkedIn

    Returns:
        Requete de recherche optimisee ou None si echec
    """
    if not post_content or not post_content.strip():
        return None

    # Limiter la longueur et nettoyer
    content = post_content.strip()[:300]

    # Retourner le contenu comme requete (Tavily est assez intelligent pour extraire le sens)
    return content


def _execute_tavily_search(tavily_client, query: str) -> Optional[str]:
    """
    Execute l'appel API Tavily pour la recherche web.

    Args:
        tavily_client: Client Tavily initialise
        query: Requete de recherche

    Returns:
        Texte formate avec la source trouvee ou None
    """
    try:
        # Recherche Tavily avec 1 resultat maximum
        response = tavily_client.search(
            query=query,
            max_results=1,
            search_depth="basic",  # "basic" pour rapidite, "advanced" pour precision
            include_answer=True,   # Inclut une reponse synthetisee par Tavily
            include_raw_content=False,
            exclude_domains=[
                # LinkedIn
                "linkedin.com", "www.linkedin.com",
                # Meta
                "facebook.com", "www.facebook.com",
                "instagram.com", "www.instagram.com",
                "threads.net",
                # X/Twitter
                "twitter.com", "x.com",
                # TikTok
                "tiktok.com", "www.tiktok.com",
                # Reddit
                "reddit.com", "www.reddit.com",
                # YouTube
                "youtube.com", "www.youtube.com",
                # Autres reseaux sociaux
                "pinterest.com", "snapchat.com", "tumblr.com", "quora.com",
            ]
        )

        # Verifier la reponse
        if not response:
            return None

        # Extraire la reponse synthetisee si disponible
        answer = response.get("answer", "")

        # Extraire le premier resultat
        results = response.get("results", [])
        if not results:
            # Si pas de resultat mais une reponse, l'utiliser
            if answer:
                return f"Source: Tavily AI\n{answer}"
            return None

        first_result = results[0]
        title = first_result.get("title", "Source web")
        url = first_result.get("url", "")
        content = first_result.get("content", "")[:300]  # Limiter la longueur

        # Formater le resultat
        result_parts = [f"Source: {title}"]
        if url:
            result_parts.append(f"URL: {url}")
        if content:
            result_parts.append(f"Info: {content}")
        elif answer:
            result_parts.append(f"Info: {answer[:300]}")

        return "\n".join(result_parts)

    except Exception as e:
        logger.warning(f"Tavily search error: {type(e).__name__}: {str(e)}")
        return None
