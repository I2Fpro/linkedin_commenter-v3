"""
Fixtures communes pour les tests de l'ai-service.
"""

import os

# Env vars factices requises a l'import de fastapi_backend
os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("USER_SERVICE_URL", "http://test:8444")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def mock_user():
    """Retourne un dict utilisateur factice pour mocker get_current_user."""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "id": "test-user-id-123",
        "role": "FREE",
        "auth_type": "jwt_internal",
    }


@pytest.fixture
def mock_openai_response():
    """Cree un mock de reponse OpenAI avec usage info."""
    mock_choice = MagicMock()
    mock_choice.message.content = "Commentaire genere par l'IA pour le test."

    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 100
    mock_usage.completion_tokens = 50

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage
    mock_response.model = "gpt-4o-mini"

    return mock_response


@pytest.fixture
def client(mock_user):
    """TestClient FastAPI pour l'ai-service avec auth mockee."""
    from fastapi_backend import app, get_current_user

    async def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
