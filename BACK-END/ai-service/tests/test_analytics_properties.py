"""
Tests de validation des 6 proprietes enrichies dans les events analytics.

Ces tests verifient que les 4 endpoints (/generate-comments, /generate-comments-with-prompt,
/refine-comment, /resize-comment) emettent correctement les 6 proprietes enrichies :
- news_enrichment_mode
- web_search_enabled
- web_search_success
- web_search_source_url
- include_quote_enabled
- custom_prompt_used

Les tests mockent les appels OpenAI, les appels au user-service et la fonction track_analytics_event
pour capturer les proprietes envoyees.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestGenerateCommentsEndpoint:
    """Tests pour l'endpoint /generate-comments"""

    @patch("fastapi_backend.track_analytics_event", new_callable=AsyncMock)
    @patch("fastapi_backend.record_user_usage", new_callable=AsyncMock)
    @patch("fastapi_backend.check_user_permissions", new_callable=AsyncMock)
    @patch("fastapi_backend.client")
    def test_generate_comments_default_properties(
        self, mock_openai_client, mock_permissions, mock_record_usage, mock_track_analytics, client, mock_openai_response
    ):
        """Test que /generate-comments envoie les 6 proprietes avec les valeurs par defaut."""
        # Setup mocks
        mock_openai_client.chat.completions.create.return_value = mock_openai_response
        mock_permissions.return_value = {"allowed": True}

        # Requete sans enrichissement
        response = client.post(
            "/generate-comments",
            json={
                "post": "Un post LinkedIn interessant",
                "tone": "professionnel",
                "length": 40,
                "optionsCount": 2,
                "commentLanguage": "fr",
                "newsEnrichmentMode": "disabled",
                "web_search_enabled": False,
                "include_quote": False,
            },
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200

        # Verifier que track_analytics_event a ete appele
        assert mock_track_analytics.called
        call_args = mock_track_analytics.call_args_list

        # Trouver l'appel avec event_type = "comment_generated"
        event_call = None
        for call in call_args:
            if len(call[0]) > 1 and call[0][1] == "comment_generated":
                event_call = call
                break

        assert event_call is not None, "Aucun event 'comment_generated' trouve"

        # Extraire les proprietes
        properties = event_call[0][2]

        # Verifier les 6 proprietes enrichies
        assert "news_enrichment_mode" in properties
        assert properties["news_enrichment_mode"] == "disabled"

        assert "web_search_enabled" in properties
        assert properties["web_search_enabled"] is False

        assert "web_search_success" in properties
        assert properties["web_search_success"] is False

        assert "web_search_source_url" in properties
        assert properties["web_search_source_url"] is None

        assert "include_quote_enabled" in properties
        assert properties["include_quote_enabled"] is False

        assert "custom_prompt_used" in properties
        assert properties["custom_prompt_used"] is False

    @patch("fastapi_backend.track_analytics_event", new_callable=AsyncMock)
    @patch("fastapi_backend.record_user_usage", new_callable=AsyncMock)
    @patch("fastapi_backend.check_user_permissions", new_callable=AsyncMock)
    @patch("fastapi_backend.search_web_for_context", new_callable=AsyncMock)
    @patch("fastapi_backend.client")
    def test_generate_comments_with_enrichment(
        self,
        mock_openai_client,
        mock_web_search,
        mock_permissions,
        mock_record_usage,
        mock_track_analytics,
        client,
        mock_openai_response,
    ):
        """Test que /generate-comments envoie les bonnes valeurs quand enrichissement est active."""
        # Setup mocks
        mock_openai_client.chat.completions.create.return_value = mock_openai_response
        mock_permissions.return_value = {"allowed": True}
        mock_web_search.return_value = (
            "Contexte web simule",
            True,
            "https://example.com/source-article",
        )

        # Requete avec enrichissement
        response = client.post(
            "/generate-comments",
            json={
                "post": "Un post LinkedIn interessant",
                "tone": "professionnel",
                "length": 40,
                "optionsCount": 2,
                "commentLanguage": "fr",
                "newsEnrichmentMode": "smart-summary",
                "web_search_enabled": True,
                "include_quote": True,
            },
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200

        # Verifier que track_analytics_event a ete appele
        assert mock_track_analytics.called
        call_args = mock_track_analytics.call_args_list

        # Trouver l'appel avec event_type = "comment_generated"
        event_call = None
        for call in call_args:
            if len(call[0]) > 1 and call[0][1] == "comment_generated":
                event_call = call
                break

        assert event_call is not None, "Aucun event 'comment_generated' trouve"

        # Extraire les proprietes
        properties = event_call[0][2]

        # Verifier les 6 proprietes enrichies
        assert properties["news_enrichment_mode"] == "smart-summary"
        assert properties["web_search_enabled"] is True
        assert properties["web_search_success"] is True
        assert properties["web_search_source_url"] == "https://example.com/source-article"
        assert properties["include_quote_enabled"] is True
        assert properties["custom_prompt_used"] is False


class TestGenerateCommentsWithPromptEndpoint:
    """Tests pour l'endpoint /generate-comments-with-prompt"""

    @patch("fastapi_backend.track_analytics_event", new_callable=AsyncMock)
    @patch("fastapi_backend.record_user_usage", new_callable=AsyncMock)
    @patch("fastapi_backend.check_user_permissions", new_callable=AsyncMock)
    @patch("fastapi_backend.client")
    def test_custom_prompt_sets_flag_to_true(
        self, mock_openai_client, mock_permissions, mock_record_usage, mock_track_analytics, client, mock_openai_response
    ):
        """Test que /generate-comments-with-prompt met custom_prompt_used a True."""
        # Setup mocks
        mock_openai_client.chat.completions.create.return_value = mock_openai_response
        mock_permissions.return_value = {"allowed": True}

        # Requete avec custom prompt
        response = client.post(
            "/generate-comments-with-prompt",
            json={
                "post": "Un post LinkedIn interessant",
                "userPrompt": "Genere un commentaire enthousiaste",
                "tone": "professionnel",
                "length": 40,
                "optionsCount": 2,
                "commentLanguage": "fr",
                "newsEnrichmentMode": "disabled",
                "web_search_enabled": False,
                "include_quote": False,
            },
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200

        # Verifier que track_analytics_event a ete appele
        assert mock_track_analytics.called
        call_args = mock_track_analytics.call_args_list

        # Trouver l'appel avec event_type = "comment_generated"
        event_call = None
        for call in call_args:
            if len(call[0]) > 1 and call[0][1] == "comment_generated":
                event_call = call
                break

        assert event_call is not None, "Aucun event 'comment_generated' trouve"

        # Extraire les proprietes
        properties = event_call[0][2]

        # Verifier custom_prompt_used = True
        assert "custom_prompt_used" in properties
        assert properties["custom_prompt_used"] is True

        # Verifier les autres proprietes par defaut
        assert properties["news_enrichment_mode"] == "disabled"
        assert properties["web_search_enabled"] is False
        assert properties["web_search_success"] is False
        assert properties["web_search_source_url"] is None
        assert properties["include_quote_enabled"] is False


class TestRefineCommentEndpoint:
    """Tests pour l'endpoint /refine-comment"""

    @patch("fastapi_backend.track_analytics_event", new_callable=AsyncMock)
    @patch("fastapi_backend.record_user_usage", new_callable=AsyncMock)
    @patch("fastapi_backend.check_user_permissions", new_callable=AsyncMock)
    @patch("fastapi_backend.client")
    def test_refine_comment_defaults(
        self, mock_openai_client, mock_permissions, mock_record_usage, mock_track_analytics, client, mock_openai_response
    ):
        """Test que /refine-comment envoie les defaults corrects (disabled, False, False, None, False, False)."""
        # Setup mocks
        mock_openai_client.chat.completions.create.return_value = mock_openai_response
        mock_permissions.return_value = {"allowed": True}

        # Requete refine
        response = client.post(
            "/refine-comment",
            json={
                "post": "Un post LinkedIn interessant",
                "originalComment": "Commentaire original",
                "refineInstructions": "Rend le plus formel",
                "tone": "professionnel",
                "length": 40,
                "commentLanguage": "fr",
            },
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200

        # Verifier que track_analytics_event a ete appele
        assert mock_track_analytics.called
        call_args = mock_track_analytics.call_args_list

        # Trouver l'appel avec event_type = "comment_generated"
        event_call = None
        for call in call_args:
            if len(call[0]) > 1 and call[0][1] == "comment_generated":
                event_call = call
                break

        assert event_call is not None, "Aucun event 'comment_generated' trouve"

        # Extraire les proprietes
        properties = event_call[0][2]

        # Verifier les 6 proprietes enrichies avec les defaults corrects
        assert properties["news_enrichment_mode"] == "disabled"
        assert properties["web_search_enabled"] is False
        assert properties["web_search_success"] is False
        assert properties["web_search_source_url"] is None
        assert properties["include_quote_enabled"] is False
        assert properties["custom_prompt_used"] is False


class TestResizeCommentEndpoint:
    """Tests pour l'endpoint /resize-comment"""

    @patch("fastapi_backend.track_analytics_event", new_callable=AsyncMock)
    @patch("fastapi_backend.record_user_usage", new_callable=AsyncMock)
    @patch("fastapi_backend.check_user_permissions", new_callable=AsyncMock)
    @patch("fastapi_backend.client")
    def test_resize_comment_defaults(
        self, mock_openai_client, mock_permissions, mock_record_usage, mock_track_analytics, client, mock_openai_response
    ):
        """Test que /resize-comment envoie les defaults corrects (disabled, False, False, None, False, False)."""
        # Setup mocks
        mock_openai_client.chat.completions.create.return_value = mock_openai_response
        mock_permissions.return_value = {"allowed": True}

        # Requete resize
        response = client.post(
            "/resize-comment",
            json={
                "post": "Un post LinkedIn interessant",
                "originalComment": "Commentaire original",
                "resizeDirection": "+",
                "currentWordCount": 30,
                "tone": "professionnel",
                "commentLanguage": "fr",
            },
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200

        # Verifier que track_analytics_event a ete appele
        assert mock_track_analytics.called
        call_args = mock_track_analytics.call_args_list

        # Trouver l'appel avec event_type = "comment_generated"
        event_call = None
        for call in call_args:
            if len(call[0]) > 1 and call[0][1] == "comment_generated":
                event_call = call
                break

        assert event_call is not None, "Aucun event 'comment_generated' trouve"

        # Extraire les proprietes
        properties = event_call[0][2]

        # Verifier les 6 proprietes enrichies avec les defaults corrects
        assert properties["news_enrichment_mode"] == "disabled"
        assert properties["web_search_enabled"] is False
        assert properties["web_search_success"] is False
        assert properties["web_search_source_url"] is None
        assert properties["include_quote_enabled"] is False
        assert properties["custom_prompt_used"] is False


class TestPropertiesCompleteness:
    """Tests globaux pour verifier que toutes les proprietes legacy sont preservees."""

    @patch("fastapi_backend.track_analytics_event", new_callable=AsyncMock)
    @patch("fastapi_backend.record_user_usage", new_callable=AsyncMock)
    @patch("fastapi_backend.check_user_permissions", new_callable=AsyncMock)
    @patch("fastapi_backend.client")
    def test_all_legacy_properties_present(
        self, mock_openai_client, mock_permissions, mock_record_usage, mock_track_analytics, client, mock_openai_response
    ):
        """Test que les proprietes legacy sont toutes presentes en plus des 6 nouvelles."""
        # Setup mocks
        mock_openai_client.chat.completions.create.return_value = mock_openai_response
        mock_permissions.return_value = {"allowed": True}

        # Requete simple
        response = client.post(
            "/generate-comments",
            json={
                "post": "Un post LinkedIn interessant",
                "tone": "professionnel",
                "length": 40,
                "optionsCount": 2,
                "commentLanguage": "fr",
                "newsEnrichmentMode": "disabled",
                "web_search_enabled": False,
                "include_quote": False,
            },
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200

        # Verifier que track_analytics_event a ete appele
        assert mock_track_analytics.called
        call_args = mock_track_analytics.call_args_list

        # Trouver l'appel avec event_type = "comment_generated"
        event_call = None
        for call in call_args:
            if len(call[0]) > 1 and call[0][1] == "comment_generated":
                event_call = call
                break

        assert event_call is not None, "Aucun event 'comment_generated' trouve"

        # Extraire les proprietes
        properties = event_call[0][2]

        # Proprietes legacy attendues
        legacy_properties = [
            "mode",
            "language",
            "role",
            "tone",
            "emotion",
            "style",
            "post_type",
            "options_count",
            "tokens_input",
            "tokens_output",
            "model",
            "duration_ms",
            "success",
        ]

        for prop in legacy_properties:
            assert prop in properties, f"Propriete legacy '{prop}' manquante"

        # Les 6 nouvelles proprietes
        new_properties = [
            "news_enrichment_mode",
            "web_search_enabled",
            "web_search_success",
            "web_search_source_url",
            "include_quote_enabled",
            "custom_prompt_used",
        ]

        for prop in new_properties:
            assert prop in properties, f"Nouvelle propriete '{prop}' manquante"
