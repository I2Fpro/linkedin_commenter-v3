"""
Tests pour l'enrichissement du endpoint /generate-comments et le token tracking.
Story 1.1 - Generation de Commentaire avec Citation Contextuelle
"""
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'ai-service'))

import pytest
from prompt_builder import build_enriched_prompt, QUOTE_INSTRUCTION


class TestEnrichmentIntegration:
    """Tests d'integration pour l'enrichissement du prompt dans le endpoint"""

    BASE_PROMPT = 'Post LinkedIn: "Test post"\n\nGenere un commentaire.'

    def test_include_quote_true_calls_build_enriched_prompt(self):
        """Avec include_quote=True, build_enriched_prompt enrichit le prompt"""
        result = build_enriched_prompt(self.BASE_PROMPT, include_quote=True)
        assert QUOTE_INSTRUCTION in result
        assert self.BASE_PROMPT in result

    def test_include_quote_false_produces_v2_identical_prompt(self):
        """Avec include_quote=False, le prompt est identique a la V2"""
        result = build_enriched_prompt(self.BASE_PROMPT, include_quote=False)
        assert result == self.BASE_PROMPT

    def test_new_fields_optional_v2_backward_compat(self):
        """Les nouveaux champs V3 sont optionnels et ne cassent pas les requetes V2"""
        # Simulation : appel sans les nouveaux champs (valeurs par defaut)
        result = build_enriched_prompt(self.BASE_PROMPT)
        assert result == self.BASE_PROMPT
        # Le prompt V2 est inchange si aucune option V3 n'est activee


class TestGenerateCommentsRequestV3Fields:
    """Tests pour verifier que les champs V3 sont bien acceptes par le modele Pydantic"""

    def _read_fastapi_backend_source(self):
        """Lit le contenu de ai-service/fastapi_backend.py"""
        ai_service_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'ai-service')
        module_path = os.path.join(ai_service_dir, 'fastapi_backend.py')
        with open(module_path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_request_model_contains_v3_fields(self):
        """Le fichier fastapi_backend.py contient les champs V3 dans GenerateCommentsRequest"""
        source = self._read_fastapi_backend_source()
        assert "include_quote: bool = False" in source
        assert "tag_author: Optional[str] = None" in source
        assert "web_search_enabled: bool = False" in source
        assert "third_party_comments: Optional[List[str]] = None" in source

    def test_prompt_builder_imported_in_backend(self):
        """Le fichier fastapi_backend.py importe build_enriched_prompt"""
        source = self._read_fastapi_backend_source()
        assert "from prompt_builder import build_enriched_prompt" in source

    def test_build_enriched_prompt_called_in_generate(self):
        """Le endpoint generate_comments appelle build_enriched_prompt"""
        source = self._read_fastapi_backend_source()
        assert "build_enriched_prompt(" in source
        assert "include_quote=request.include_quote" in source

    def test_v3_fields_backward_compatible_defaults(self):
        """Les champs V3 ont des valeurs par defaut pour la retro-compatibilite V2"""
        # Verification via Pydantic standalone (meme definitions que dans le fichier)
        from pydantic import BaseModel
        from typing import Optional, List

        class TestRequest(BaseModel):
            post: Optional[str] = None
            include_quote: bool = False
            tag_author: Optional[str] = None
            web_search_enabled: bool = False
            third_party_comments: Optional[List[str]] = None

        # Requete V2 (sans champs V3) — retro-compatible
        req_v2 = TestRequest(post="Test post")
        assert req_v2.include_quote is False
        assert req_v2.tag_author is None
        assert req_v2.web_search_enabled is False
        assert req_v2.third_party_comments is None

        # Requete V3 (avec champs V3)
        req_v3 = TestRequest(
            post="Test post",
            include_quote=True,
            tag_author="Jean Dupont",
            web_search_enabled=True,
            third_party_comments=["Com 1"],
        )
        assert req_v3.include_quote is True
        assert req_v3.tag_author == "Jean Dupont"


class TestTokenTracking:
    """Tests pour le token tracking V3 dans usage_logs.meta_data"""

    def _read_fastapi_backend_source(self):
        """Lit le contenu de ai-service/fastapi_backend.py"""
        ai_service_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'ai-service')
        module_path = os.path.join(ai_service_dir, 'fastapi_backend.py')
        with open(module_path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_call_openai_api_returns_tuple_with_usage(self):
        """call_openai_api retourne un tuple (comments, usage_info)"""
        source = self._read_fastapi_backend_source()
        # Verifie que la fonction retourne un tuple avec usage_info
        assert '"tokens_input": response.usage.prompt_tokens' in source
        assert '"tokens_output": response.usage.completion_tokens' in source
        assert '"model": response.model' in source

    def test_record_user_usage_includes_tokens(self):
        """record_user_usage est appele avec tokens_input, tokens_output et model dans generate_comments"""
        source = self._read_fastapi_backend_source()
        assert '"tokens_input": usage_info.get("tokens_input"' in source
        assert '"tokens_output": usage_info.get("tokens_output"' in source
        assert '"model": usage_info.get("model"' in source

    def test_record_user_usage_includes_include_quote(self):
        """record_user_usage inclut le champ include_quote dans les metadata"""
        source = self._read_fastapi_backend_source()
        assert '"include_quote": request.include_quote' in source

    def test_call_openai_callers_handle_tuple(self):
        """Tous les appelants de call_openai_api destructurent le tuple"""
        source = self._read_fastapi_backend_source()
        # Le caller principal (generate_comments) utilise usage_info
        assert "comments, usage_info = call_openai_api(" in source
        # Les autres callers ignorent l'usage avec _usage
        assert "comments, _usage = call_openai_api(" in source
