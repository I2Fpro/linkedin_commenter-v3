"""
Tests pour le module prompt_builder.py
Story 1.1 - Generation de Commentaire avec Citation Contextuelle
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'ai-service'))

from prompt_builder import build_enriched_prompt, QUOTE_INSTRUCTION


class TestBuildEnrichedPrompt:
    """Tests pour build_enriched_prompt()"""

    BASE_PROMPT = "Genere un commentaire professionnel sur ce post LinkedIn."

    def test_include_quote_true_adds_instruction(self):
        """Avec include_quote=True, le prompt enrichi contient l'instruction de citation"""
        result = build_enriched_prompt(self.BASE_PROMPT, include_quote=True)
        assert QUOTE_INSTRUCTION in result
        assert self.BASE_PROMPT in result

    def test_include_quote_false_returns_base(self):
        """Avec include_quote=False, le prompt retourne est identique au base_prompt"""
        result = build_enriched_prompt(self.BASE_PROMPT, include_quote=False)
        assert result == self.BASE_PROMPT

    def test_all_params_none_false_returns_base(self):
        """Avec tous les params a None/False, retour identique au base_prompt"""
        result = build_enriched_prompt(
            self.BASE_PROMPT,
            include_quote=False,
            tag_author=None,
            web_search_result=None,
            third_party_comments=None,
        )
        assert result == self.BASE_PROMPT

    def test_default_params_returns_base(self):
        """Sans arguments optionnels, retour identique au base_prompt"""
        result = build_enriched_prompt(self.BASE_PROMPT)
        assert result == self.BASE_PROMPT

    def test_include_quote_true_with_other_params_ignored(self):
        """Les params tag_author, web_search, third_party sont acceptes mais ignores"""
        result = build_enriched_prompt(
            self.BASE_PROMPT,
            include_quote=True,
            tag_author="Jean Dupont",
            web_search_result="Resultat web",
            third_party_comments=["Commentaire 1", "Commentaire 2"],
        )
        assert QUOTE_INSTRUCTION in result
        assert self.BASE_PROMPT in result

    def test_enriched_prompt_structure(self):
        """Le prompt enrichi a la bonne structure : base + saut de ligne + instruction"""
        result = build_enriched_prompt(self.BASE_PROMPT, include_quote=True)
        expected = f"{self.BASE_PROMPT}\n\n{QUOTE_INSTRUCTION}"
        assert result == expected
