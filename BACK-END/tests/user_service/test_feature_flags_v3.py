"""
Tests des feature flags V3 Premium (include_quote, tag_author, web_search_enabled)
Story 1.1 - Generation de Commentaire avec Citation Contextuelle
"""
import sys
import os

# Ajouter le repertoire user-service au path pour l'import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'user-service'))

from utils.feature_flags import is_feature_enabled, get_feature_value, FEATURES


class TestFeatureFlagsV3:
    """Tests pour les features V3 ajoutees dans feature_flags.py"""

    # --- include_quote ---

    def test_free_include_quote_disabled(self):
        """FREE ne doit pas avoir acces a include_quote"""
        assert is_feature_enabled("FREE", "include_quote") is False

    def test_medium_include_quote_disabled(self):
        """MEDIUM ne doit pas avoir acces a include_quote"""
        assert is_feature_enabled("MEDIUM", "include_quote") is False

    def test_premium_include_quote_enabled(self):
        """PREMIUM doit avoir acces a include_quote"""
        assert is_feature_enabled("PREMIUM", "include_quote") is True

    def test_get_feature_value_free_include_quote(self):
        """get_feature_value pour FREE include_quote retourne False"""
        assert get_feature_value("FREE", "include_quote") is False

    def test_get_feature_value_medium_include_quote(self):
        """get_feature_value pour MEDIUM include_quote retourne False"""
        assert get_feature_value("MEDIUM", "include_quote") is False

    def test_get_feature_value_premium_include_quote(self):
        """get_feature_value pour PREMIUM include_quote retourne True"""
        assert get_feature_value("PREMIUM", "include_quote") is True

    # --- tag_author ---

    def test_free_tag_author_disabled(self):
        """FREE ne doit pas avoir acces a tag_author"""
        assert is_feature_enabled("FREE", "tag_author") is False

    def test_medium_tag_author_disabled(self):
        """MEDIUM ne doit pas avoir acces a tag_author"""
        assert is_feature_enabled("MEDIUM", "tag_author") is False

    def test_premium_tag_author_enabled(self):
        """PREMIUM doit avoir acces a tag_author"""
        assert is_feature_enabled("PREMIUM", "tag_author") is True

    # --- web_search_enabled ---

    def test_free_web_search_disabled(self):
        """FREE ne doit pas avoir acces a web_search_enabled"""
        assert is_feature_enabled("FREE", "web_search_enabled") is False

    def test_medium_web_search_disabled(self):
        """MEDIUM ne doit pas avoir acces a web_search_enabled"""
        assert is_feature_enabled("MEDIUM", "web_search_enabled") is False

    def test_premium_web_search_enabled(self):
        """PREMIUM doit avoir acces a web_search_enabled"""
        assert is_feature_enabled("PREMIUM", "web_search_enabled") is True

    # --- Verification de la structure du dict FEATURES ---

    def test_features_dict_contains_v3_keys(self):
        """Les 3 features V3 doivent exister dans chaque role"""
        v3_features = ["include_quote", "tag_author", "web_search_enabled"]
        for role in ["FREE", "MEDIUM", "PREMIUM"]:
            for feature in v3_features:
                assert feature in FEATURES[role], f"{feature} manquant dans {role}"
