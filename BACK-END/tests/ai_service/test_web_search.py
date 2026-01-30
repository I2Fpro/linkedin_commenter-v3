"""
Tests pour le module web_search.py (Story 1.4)
Recherche web avec fallback gracieux via Tavily API.
"""
import sys
import os
import asyncio
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'ai-service'))

from web_search import (
    search_web_for_context,
    _build_search_query,
    _execute_tavily_search,
    WEB_SEARCH_TIMEOUT_SECONDS
)


class TestSearchWebForContext:
    """Tests pour la fonction search_web_for_context()"""

    def test_search_web_success_returns_result_and_true(self):
        """Test: recherche reussie retourne (resultat, True)"""
        mock_tavily = Mock()
        mock_tavily.search.return_value = {
            "results": [{
                "title": "Article X",
                "url": "https://example.com",
                "content": "Info pertinente sur le sujet"
            }],
            "answer": "Resume de l'article"
        }

        async def run_test():
            with patch('web_search._get_tavily_client', return_value=mock_tavily):
                return await search_web_for_context(
                    post_content="Test post about AI"
                )

        result, success = asyncio.run(run_test())

        assert success is True
        assert result is not None
        assert "Article X" in result
        assert "example.com" in result

    def test_search_web_no_source_returns_none_and_false(self):
        """Test: aucune source pertinente retourne (None, False)"""
        mock_tavily = Mock()
        mock_tavily.search.return_value = {
            "results": [],
            "answer": ""
        }

        async def run_test():
            with patch('web_search._get_tavily_client', return_value=mock_tavily):
                return await search_web_for_context(
                    post_content="Test post obscur"
                )

        result, success = asyncio.run(run_test())

        assert success is False
        assert result is None

    def test_search_web_tavily_not_configured_returns_none_and_false(self):
        """Test: Tavily non configure retourne (None, False)"""
        async def run_test():
            with patch('web_search._get_tavily_client', return_value=None):
                return await search_web_for_context(
                    post_content="Test post"
                )

        result, success = asyncio.run(run_test())

        assert success is False
        assert result is None

    def test_search_web_timeout_returns_none_and_false(self):
        """Test: timeout retourne (None, False) - fallback gracieux"""
        async def run_test():
            with patch('web_search.asyncio.wait_for', side_effect=asyncio.TimeoutError()):
                with patch('web_search._get_tavily_client', return_value=Mock()):
                    return await search_web_for_context(
                        post_content="Test post"
                    )

        result, success = asyncio.run(run_test())

        assert success is False
        assert result is None

    def test_search_web_exception_returns_none_and_false(self):
        """Test: exception retourne (None, False) - pas de crash"""
        mock_tavily = Mock()
        mock_tavily.search.side_effect = Exception("API Error")

        async def run_test():
            with patch('web_search._get_tavily_client', return_value=mock_tavily):
                return await search_web_for_context(
                    post_content="Test post"
                )

        result, success = asyncio.run(run_test())

        assert success is False
        assert result is None

    def test_search_web_empty_post_returns_none_and_false(self):
        """Test: post vide retourne (None, False)"""
        async def run_test():
            with patch('web_search._get_tavily_client', return_value=Mock()):
                return await search_web_for_context(
                    post_content=""
                )

        result, success = asyncio.run(run_test())

        assert success is False
        assert result is None

    def test_search_web_whitespace_only_returns_none_and_false(self):
        """Test: post avec espaces seulement retourne (None, False)"""
        async def run_test():
            with patch('web_search._get_tavily_client', return_value=Mock()):
                return await search_web_for_context(
                    post_content="   \n\t   "
                )

        result, success = asyncio.run(run_test())

        assert success is False
        assert result is None


class TestBuildSearchQuery:
    """Tests pour la fonction _build_search_query()"""

    def test_build_query_from_normal_content(self):
        """Test: contenu normal retourne le contenu nettoye"""
        result = _build_search_query("Ceci est un post LinkedIn interessant")
        assert result == "Ceci est un post LinkedIn interessant"

    def test_build_query_truncates_long_content(self):
        """Test: contenu long est tronque a 300 caracteres"""
        long_content = "A" * 500
        result = _build_search_query(long_content)
        assert len(result) == 300
        assert result == "A" * 300

    def test_build_query_strips_whitespace(self):
        """Test: espaces en debut/fin sont supprimes"""
        result = _build_search_query("   contenu avec espaces   ")
        assert result == "contenu avec espaces"

    def test_build_query_empty_returns_none(self):
        """Test: contenu vide retourne None"""
        result = _build_search_query("")
        assert result is None

    def test_build_query_none_returns_none(self):
        """Test: None retourne None"""
        result = _build_search_query(None)
        assert result is None

    def test_build_query_whitespace_only_returns_none(self):
        """Test: espaces seulement retourne None"""
        result = _build_search_query("   \t\n   ")
        assert result is None


class TestExecuteTavilySearch:
    """Tests pour la fonction _execute_tavily_search()"""

    def test_execute_formats_result_with_all_fields(self):
        """Test: formate correctement le resultat avec tous les champs"""
        mock_client = Mock()
        mock_client.search.return_value = {
            "results": [{
                "title": "Article Test",
                "url": "https://test.com/article",
                "content": "Contenu de l'article"
            }],
            "answer": "Resume"
        }

        result = _execute_tavily_search(mock_client, "test query")

        assert "Source: Article Test" in result
        assert "URL: https://test.com/article" in result
        assert "Info: Contenu de l'article" in result

    def test_execute_uses_answer_when_no_content(self):
        """Test: utilise answer si content est vide"""
        mock_client = Mock()
        mock_client.search.return_value = {
            "results": [{
                "title": "Article",
                "url": "https://test.com",
                "content": ""
            }],
            "answer": "Reponse synthetisee par Tavily"
        }

        result = _execute_tavily_search(mock_client, "test query")

        assert "Info: Reponse synthetisee" in result

    def test_execute_returns_none_when_no_results(self):
        """Test: retourne None si pas de resultats"""
        mock_client = Mock()
        mock_client.search.return_value = {
            "results": [],
            "answer": ""
        }

        result = _execute_tavily_search(mock_client, "test query")

        assert result is None

    def test_execute_uses_answer_only_when_no_results_but_answer(self):
        """Test: utilise answer seul si pas de resultats mais answer presente"""
        mock_client = Mock()
        mock_client.search.return_value = {
            "results": [],
            "answer": "Reponse Tavily AI"
        }

        result = _execute_tavily_search(mock_client, "test query")

        assert result is not None
        assert "Source: Tavily AI" in result
        assert "Reponse Tavily AI" in result

    def test_execute_truncates_long_content(self):
        """Test: tronque le contenu a 300 caracteres"""
        mock_client = Mock()
        long_content = "B" * 500
        mock_client.search.return_value = {
            "results": [{
                "title": "Article",
                "url": "https://test.com",
                "content": long_content
            }],
            "answer": ""
        }

        result = _execute_tavily_search(mock_client, "test query")

        assert "B" * 300 in result
        assert "B" * 301 not in result

    def test_execute_handles_exception_gracefully(self):
        """Test: gere les exceptions sans crash"""
        mock_client = Mock()
        mock_client.search.side_effect = Exception("API Error")

        result = _execute_tavily_search(mock_client, "test query")

        assert result is None

    def test_execute_handles_none_response(self):
        """Test: gere une reponse None"""
        mock_client = Mock()
        mock_client.search.return_value = None

        result = _execute_tavily_search(mock_client, "test query")

        assert result is None


class TestWebSearchTimeout:
    """Tests pour verifier le timeout de la recherche web"""

    def test_timeout_value_is_10_seconds(self):
        """Test: le timeout est bien de 10 secondes (ajuste pour Tavily)"""
        assert WEB_SEARCH_TIMEOUT_SECONDS == 10

    def test_timeout_is_reasonable(self):
        """Test: le timeout est raisonnable (entre 5 et 15 secondes)"""
        assert 5 <= WEB_SEARCH_TIMEOUT_SECONDS <= 15
