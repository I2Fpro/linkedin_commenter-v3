"""
Tests automatises pour l'endpoint GET /api/admin/token-usage (Story 3.2)

Pour executer:
    cd GIT/BACK-END/user-service
    pytest test_admin_token_usage.py -v

Couvre les Acceptance Criteria:
- AC #1: Admin autorise recoit les donnees de tokens
- AC #2: Tri par consommation decroissante
- AC #3: Liste vide si pas de donnees (pas d'erreur)
- AC #4: Non-admin recoit 403 Forbidden
- AC #5: Sans JWT recoit 401 Unauthorized
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone
from fastapi.testclient import TestClient


# Mock des modules avant import
@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock les dependances externes avant l'import de l'app."""
    with patch.dict('os.environ', {
        'DATABASE_URL': 'postgresql://test:test@localhost/test',
        'JWT_SECRET': 'test-secret-key',
        'ENCRYPTION_KEY': 'dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcyE=',
        'ADMIN_EMAILS': 'admin@test.com,admin2@test.com',
        'POSTHOG_API_KEY': 'test-key',
    }):
        yield


@pytest.fixture
def mock_db_session():
    """Mock de la session SQLAlchemy."""
    session = MagicMock()
    return session


@pytest.fixture
def admin_user():
    """Cree un utilisateur admin mock."""
    user = Mock()
    user.id = uuid4()
    user.email = "admin@test.com"
    user.name = "Admin Test"
    user.role = "PREMIUM"
    user.is_active = True
    return user


@pytest.fixture
def non_admin_user():
    """Cree un utilisateur non-admin mock."""
    user = Mock()
    user.id = uuid4()
    user.email = "user@test.com"
    user.name = "Regular User"
    user.role = "FREE"
    user.is_active = True
    return user


@pytest.fixture
def sample_usage_logs():
    """Cree des logs d'usage mock avec tokens."""
    user1_id = uuid4()
    user2_id = uuid4()

    logs = [
        # User 1: 3 generations, 1500 tokens total
        Mock(
            user_id=user1_id,
            meta_data={"tokens_input": 200, "tokens_output": 100, "model": "gpt-4o-mini"},
            timestamp=datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)
        ),
        Mock(
            user_id=user1_id,
            meta_data={"tokens_input": 300, "tokens_output": 150, "model": "gpt-4o-mini"},
            timestamp=datetime(2026, 1, 16, 10, 0, tzinfo=timezone.utc)
        ),
        Mock(
            user_id=user1_id,
            meta_data={"tokens_input": 500, "tokens_output": 250, "model": "gpt-4o"},
            timestamp=datetime(2026, 1, 17, 10, 0, tzinfo=timezone.utc)
        ),
        # User 2: 2 generations, 600 tokens total
        Mock(
            user_id=user2_id,
            meta_data={"tokens_input": 150, "tokens_output": 50, "model": "gpt-4o-mini"},
            timestamp=datetime(2026, 1, 14, 10, 0, tzinfo=timezone.utc)
        ),
        Mock(
            user_id=user2_id,
            meta_data={"tokens_input": 250, "tokens_output": 150, "model": "gpt-4o-mini"},
            timestamp=datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)
        ),
    ]
    return logs, user1_id, user2_id


class TestTokenUsageEndpoint:
    """Tests pour GET /api/admin/token-usage"""

    def test_ac1_admin_receives_token_data(self, admin_user, mock_db_session, sample_usage_logs):
        """
        AC #1: Given admin authentifie, When GET /api/admin/token-usage,
        Then recoit la liste des utilisateurs avec leurs tokens.
        """
        logs, user1_id, user2_id = sample_usage_logs

        # Setup mock query
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = logs
        mock_db_session.query.return_value = mock_query

        with patch('routers.admin.get_db', return_value=mock_db_session):
            with patch('routers.admin.require_admin', return_value=admin_user):
                from routers.admin import get_token_usage
                import asyncio

                result = asyncio.run(get_token_usage(admin_user, mock_db_session))

                # Verifications AC #1
                assert result.total_users == 2
                assert result.total_tokens_all == 2100  # 1500 + 600
                assert len(result.users) == 2

                # Verifier structure des donnees
                for user_detail in result.users:
                    assert user_detail.user_id is not None
                    assert user_detail.total_tokens == user_detail.total_tokens_input + user_detail.total_tokens_output
                    assert user_detail.generation_count > 0
                    assert len(user_detail.models_used) > 0

    def test_ac2_sorted_by_consumption_descending(self, admin_user, mock_db_session, sample_usage_logs):
        """
        AC #2: Given admin, When consulte les tokens,
        Then utilisateurs tries par consommation decroissante.
        """
        logs, user1_id, user2_id = sample_usage_logs

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = logs
        mock_db_session.query.return_value = mock_query

        with patch('routers.admin.get_db', return_value=mock_db_session):
            with patch('routers.admin.require_admin', return_value=admin_user):
                from routers.admin import get_token_usage
                import asyncio

                result = asyncio.run(get_token_usage(admin_user, mock_db_session))

                # Verifier tri decroissant
                tokens_list = [u.total_tokens for u in result.users]
                assert tokens_list == sorted(tokens_list, reverse=True)

                # User1 (1500 tokens) doit etre premier
                assert result.users[0].total_tokens == 1500
                assert result.users[1].total_tokens == 600

    def test_ac3_empty_list_when_no_data(self, admin_user, mock_db_session):
        """
        AC #3: Given aucune donnee token, When GET /api/admin/token-usage,
        Then recoit liste vide (pas d'erreur).
        """
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []  # Pas de logs
        mock_db_session.query.return_value = mock_query

        with patch('routers.admin.get_db', return_value=mock_db_session):
            with patch('routers.admin.require_admin', return_value=admin_user):
                from routers.admin import get_token_usage
                import asyncio

                result = asyncio.run(get_token_usage(admin_user, mock_db_session))

                # Pas d'erreur, liste vide
                assert result.users == []
                assert result.total_users == 0
                assert result.total_tokens_all == 0

    def test_ac4_non_admin_receives_403(self, non_admin_user):
        """
        AC #4: Given utilisateur non-admin, When GET /api/admin/token-usage,
        Then recoit 403 Forbidden.
        """
        from fastapi import HTTPException
        from utils.admin_auth import require_admin
        import asyncio

        with patch('utils.admin_auth.get_current_user', return_value=non_admin_user):
            with patch.dict('os.environ', {'ADMIN_EMAILS': 'admin@test.com'}):
                with pytest.raises(HTTPException) as exc_info:
                    asyncio.run(require_admin(non_admin_user))

                assert exc_info.value.status_code == 403
                assert "administrateur" in exc_info.value.detail.lower()

    def test_ac5_no_jwt_receives_401(self):
        """
        AC #5: Given pas de JWT, When GET /api/admin/token-usage,
        Then recoit 401 Unauthorized.
        """
        # Ce test verifie que get_current_user leve 401 sans token
        # La logique est dans auth.py, testee indirectement via require_admin
        from fastapi import HTTPException
        from auth import get_current_user
        import asyncio

        mock_db = MagicMock()

        # Simuler un appel sans credentials
        with pytest.raises(HTTPException) as exc_info:
            # get_current_user attend un HTTPAuthorizationCredentials
            # Sans token, il devrait lever 401
            asyncio.run(get_current_user(credentials=None, db=mock_db))

        assert exc_info.value.status_code == 401

    def test_models_used_sorted_deterministic(self, admin_user, mock_db_session):
        """
        Fix M1: Verifier que models_used est trie pour des reponses deterministes.
        """
        user_id = uuid4()
        # Ordre volontairement non-alphabetique dans les logs
        logs = [
            Mock(
                user_id=user_id,
                meta_data={"tokens_input": 100, "tokens_output": 50, "model": "gpt-4o"},
                timestamp=datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)
            ),
            Mock(
                user_id=user_id,
                meta_data={"tokens_input": 100, "tokens_output": 50, "model": "gpt-3.5-turbo"},
                timestamp=datetime(2026, 1, 16, 10, 0, tzinfo=timezone.utc)
            ),
            Mock(
                user_id=user_id,
                meta_data={"tokens_input": 100, "tokens_output": 50, "model": "gpt-4o-mini"},
                timestamp=datetime(2026, 1, 17, 10, 0, tzinfo=timezone.utc)
            ),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = logs
        mock_db_session.query.return_value = mock_query

        with patch('routers.admin.get_db', return_value=mock_db_session):
            with patch('routers.admin.require_admin', return_value=admin_user):
                from routers.admin import get_token_usage
                import asyncio

                result = asyncio.run(get_token_usage(admin_user, mock_db_session))

                # models_used doit etre trie alphabetiquement
                assert result.users[0].models_used == ["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"]

    def test_handles_none_timestamp_gracefully(self, admin_user, mock_db_session):
        """
        Fix M2: Verifier que les logs avec timestamp None ne crashent pas.
        """
        user_id = uuid4()
        logs = [
            Mock(
                user_id=user_id,
                meta_data={"tokens_input": 100, "tokens_output": 50, "model": "gpt-4o-mini"},
                timestamp=None  # Legacy V2 data
            ),
            Mock(
                user_id=user_id,
                meta_data={"tokens_input": 200, "tokens_output": 100, "model": "gpt-4o-mini"},
                timestamp=datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)
            ),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = logs
        mock_db_session.query.return_value = mock_query

        with patch('routers.admin.get_db', return_value=mock_db_session):
            with patch('routers.admin.require_admin', return_value=admin_user):
                from routers.admin import get_token_usage
                import asyncio

                # Ne doit pas lever d'exception
                result = asyncio.run(get_token_usage(admin_user, mock_db_session))

                assert result.total_users == 1
                assert result.users[0].generation_count == 2
                # last_generation doit etre la date non-None
                assert result.users[0].last_generation == datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)

    def test_handles_missing_meta_data_fields(self, admin_user, mock_db_session):
        """
        Verifier que les logs avec champs manquants dans meta_data sont geres.
        """
        user_id = uuid4()
        logs = [
            Mock(
                user_id=user_id,
                meta_data={"tokens_input": 100},  # Manque tokens_output et model
                timestamp=datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)
            ),
            Mock(
                user_id=user_id,
                meta_data={},  # Totalement vide
                timestamp=datetime(2026, 1, 16, 10, 0, tzinfo=timezone.utc)
            ),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = logs
        mock_db_session.query.return_value = mock_query

        with patch('routers.admin.get_db', return_value=mock_db_session):
            with patch('routers.admin.require_admin', return_value=admin_user):
                from routers.admin import get_token_usage
                import asyncio

                # Ne doit pas lever d'exception
                result = asyncio.run(get_token_usage(admin_user, mock_db_session))

                assert result.total_users == 1
                assert result.users[0].total_tokens_input == 100
                assert result.users[0].total_tokens_output == 0  # Default
                assert result.users[0].models_used == []  # Pas de modele


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
