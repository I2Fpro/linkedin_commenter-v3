"""
Tests pour la validation du feature gating V3 cote User Service.
Story 1.1 - Generation de Commentaire avec Citation Contextuelle
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'user-service'))

from utils.feature_flags import FEATURES, is_feature_enabled


class TestPermissionsV3FeatureGating:
    """Tests pour verifier que include_quote est correctement gere dans le feature gating"""

    def test_include_quote_in_features_dict_all_roles(self):
        """include_quote doit exister dans tous les roles"""
        for role in ["FREE", "MEDIUM", "PREMIUM"]:
            assert "include_quote" in FEATURES[role], f"include_quote manquant dans {role}"

    def test_free_include_quote_false(self):
        """FREE n'a pas acces a include_quote"""
        assert FEATURES["FREE"]["include_quote"] is False

    def test_medium_include_quote_false(self):
        """MEDIUM n'a pas acces a include_quote"""
        assert FEATURES["MEDIUM"]["include_quote"] is False

    def test_premium_include_quote_true(self):
        """PREMIUM a acces a include_quote"""
        assert FEATURES["PREMIUM"]["include_quote"] is True

    def test_is_feature_enabled_coherent(self):
        """is_feature_enabled retourne les bonnes valeurs pour include_quote"""
        assert is_feature_enabled("FREE", "include_quote") is False
        assert is_feature_enabled("MEDIUM", "include_quote") is False
        assert is_feature_enabled("PREMIUM", "include_quote") is True

    def test_validate_action_recognizes_include_quote(self):
        """Le router permissions reconnait include_quote comme feature valide"""
        permissions_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'user-service', 'routers', 'permissions.py'
        )
        with open(permissions_path, 'r', encoding='utf-8') as f:
            source = f.read()
        # include_quote doit etre dans la liste des features booleennes reconnues
        assert '"include_quote"' in source
        # Verifie que c'est dans le bloc elif (pas dans le else qui retourne 400)
        assert 'request.feature in [' in source
        # Verifie la presence dans la liste
        lines = source.split('\n')
        for line in lines:
            if 'request.feature in [' in line and 'include_quote' in line:
                assert True
                return
        assert False, "include_quote n'est pas dans la liste request.feature in [...]"
