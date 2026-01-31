"""
Tests pour la blacklist - Story 2.1 Epic 2
Gestion de la Blacklist (Ajout et Consultation)
"""
import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

# Ajouter le repertoire user-service au path pour l'import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'user-service'))

from utils.feature_flags import is_feature_enabled, get_feature_value, FEATURES


class TestBlacklistFeatureFlags:
    """Tests pour la feature blacklist dans feature_flags.py"""

    # --- blacklist feature flag ---

    def test_free_blacklist_disabled(self):
        """FREE ne doit pas avoir acces a la blacklist"""
        assert is_feature_enabled("FREE", "blacklist") is False

    def test_medium_blacklist_disabled(self):
        """MEDIUM ne doit pas avoir acces a la blacklist"""
        assert is_feature_enabled("MEDIUM", "blacklist") is False

    def test_premium_blacklist_enabled(self):
        """PREMIUM doit avoir acces a la blacklist"""
        assert is_feature_enabled("PREMIUM", "blacklist") is True

    def test_get_feature_value_free_blacklist(self):
        """get_feature_value pour FREE blacklist retourne False"""
        assert get_feature_value("FREE", "blacklist") is False

    def test_get_feature_value_medium_blacklist(self):
        """get_feature_value pour MEDIUM blacklist retourne False"""
        assert get_feature_value("MEDIUM", "blacklist") is False

    def test_get_feature_value_premium_blacklist(self):
        """get_feature_value pour PREMIUM blacklist retourne True"""
        assert get_feature_value("PREMIUM", "blacklist") is True

    # --- Verification de la structure du dict FEATURES ---

    def test_features_dict_contains_blacklist_key(self):
        """La feature blacklist doit exister dans chaque role"""
        for role in ["FREE", "MEDIUM", "PREMIUM"]:
            assert "blacklist" in FEATURES[role], f"blacklist manquant dans {role}"


class TestBlacklistSchemas:
    """Tests pour les schemas Pydantic de la blacklist"""

    def test_blacklist_entry_create_schema_valid(self):
        """Schema BlacklistEntryCreate avec donnees valides"""
        from schemas.blacklist import BlacklistEntryCreate

        entry = BlacklistEntryCreate(
            blocked_name="Jean Dupont",
            blocked_profile_url="https://linkedin.com/in/jean-dupont"
        )
        assert entry.blocked_name == "Jean Dupont"
        assert entry.blocked_profile_url == "https://linkedin.com/in/jean-dupont"

    def test_blacklist_entry_create_schema_without_url(self):
        """Schema BlacklistEntryCreate sans URL (optionnel)"""
        from schemas.blacklist import BlacklistEntryCreate

        entry = BlacklistEntryCreate(blocked_name="Jean Dupont")
        assert entry.blocked_name == "Jean Dupont"
        assert entry.blocked_profile_url is None

    def test_blacklist_entry_create_schema_name_validation(self):
        """Schema BlacklistEntryCreate rejette les noms vides"""
        from schemas.blacklist import BlacklistEntryCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            BlacklistEntryCreate(blocked_name="")

    def test_blacklist_list_response_schema(self):
        """Schema BlacklistListResponse structure correcte"""
        from schemas.blacklist import BlacklistListResponse, BlacklistEntryResponse

        entries = [
            BlacklistEntryResponse(
                id=uuid4(),
                blocked_name="Jean Dupont",
                blocked_profile_url=None,
                created_at=datetime.now(timezone.utc)
            )
        ]
        response = BlacklistListResponse(entries=entries, count=1)
        assert response.count == 1
        assert len(response.entries) == 1

    def test_blacklist_check_response_schema(self):
        """Schema BlacklistCheckResponse structure correcte"""
        from schemas.blacklist import BlacklistCheckResponse

        response = BlacklistCheckResponse(is_blacklisted=True, blocked_name="Jean Dupont")
        assert response.is_blacklisted is True
        assert response.blocked_name == "Jean Dupont"


class TestBlacklistModel:
    """Tests pour le modele SQLAlchemy BlacklistEntry
    Note: Ces tests sont skip si ENCRYPTION_KEY n'est pas configuree
    car le module models.py depend de utils.encryption qui requiert cette cle.
    """

    @pytest.fixture(autouse=True)
    def skip_if_no_encryption_key(self):
        """Skip les tests si ENCRYPTION_KEY n'est pas definie"""
        if not os.getenv("ENCRYPTION_KEY"):
            pytest.skip("ENCRYPTION_KEY non configuree - skip tests model")

    def test_blacklist_entry_model_exists(self):
        """Le modele BlacklistEntry doit exister"""
        from models import BlacklistEntry
        assert BlacklistEntry is not None

    def test_blacklist_entry_model_tablename(self):
        """Le tablename doit etre blacklist_entries"""
        from models import BlacklistEntry
        assert BlacklistEntry.__tablename__ == "blacklist_entries"

    def test_blacklist_entry_model_has_required_columns(self):
        """Le modele doit avoir toutes les colonnes requises"""
        from models import BlacklistEntry

        columns = [c.name for c in BlacklistEntry.__table__.columns]
        required_columns = ['id', 'user_id', 'blocked_name', 'blocked_profile_url', 'created_at']
        for col in required_columns:
            assert col in columns, f"Colonne {col} manquante"

    def test_blacklist_entry_model_user_fk_cascade(self):
        """La FK user_id doit avoir ondelete CASCADE"""
        from models import BlacklistEntry

        # Verifier que la FK existe avec CASCADE
        fks = list(BlacklistEntry.__table__.foreign_keys)
        assert len(fks) == 1
        fk = fks[0]
        assert fk.column.name == 'id'
        assert fk.column.table.name == 'users'
        assert fk.ondelete == 'CASCADE'

    def test_blacklist_entry_repr(self):
        """Le __repr__ doit retourner le format attendu"""
        from models import BlacklistEntry

        entry = BlacklistEntry(blocked_name="Test User")
        assert "Test User" in repr(entry)


class TestBlacklistRouter:
    """Tests pour les endpoints du router blacklist"""

    @pytest.fixture
    def premium_user_mock(self):
        """Fixture utilisateur Premium"""
        user = Mock()
        user.id = uuid4()
        user.role = Mock()
        user.role.value = "PREMIUM"
        return user

    @pytest.fixture
    def free_user_mock(self):
        """Fixture utilisateur Free"""
        user = Mock()
        user.id = uuid4()
        user.role = Mock()
        user.role.value = "FREE"
        return user

    @pytest.fixture
    def db_session_mock(self):
        """Fixture session DB mockee"""
        return MagicMock()

    def test_is_feature_enabled_premium_blacklist(self):
        """is_feature_enabled retourne True pour PREMIUM + blacklist"""
        assert is_feature_enabled("PREMIUM", "blacklist") is True

    def test_is_feature_enabled_free_blacklist(self):
        """is_feature_enabled retourne False pour FREE + blacklist"""
        assert is_feature_enabled("FREE", "blacklist") is False

    def test_is_feature_enabled_medium_blacklist(self):
        """is_feature_enabled retourne False pour MEDIUM + blacklist"""
        assert is_feature_enabled("MEDIUM", "blacklist") is False


class TestBlacklistMigration:
    """Tests pour la migration Alembic blacklist_entries"""

    def test_migration_file_exists(self):
        """Le fichier de migration doit exister"""
        migration_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..', 'user-service', 'alembic', 'versions',
            '005_add_blacklist_entries_table.py'
        )
        assert os.path.exists(migration_path), "Fichier de migration manquant"

    def test_migration_has_correct_revision(self):
        """La migration doit avoir le bon revision ID"""
        migration_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..', 'user-service', 'alembic', 'versions',
            '005_add_blacklist_entries_table.py'
        )
        with open(migration_path, 'r') as f:
            content = f.read()
            assert "revision = '005_add_blacklist_entries_table'" in content
            assert "down_revision = '004_add_stripe_subscription_fields'" in content
