"""
Tests pour le module prompt_builder.py
Story 1.1 - Generation de Commentaire avec Citation Contextuelle
Story 1.2 - Tag Automatique de l'Auteur du Post
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

    def test_include_quote_true_with_other_params(self):
        """Quote + tag_author sont traites, web_search/third_party ignores (story 1.3/1.4)"""
        result = build_enriched_prompt(
            self.BASE_PROMPT,
            include_quote=True,
            tag_author="Jean Dupont",
            web_search_result="Resultat web",
            third_party_comments=["Commentaire 1", "Commentaire 2"],
        )
        assert QUOTE_INSTRUCTION in result
        assert self.BASE_PROMPT in result
        assert "Jean" in result  # tag_author est maintenant traite

    def test_enriched_prompt_structure(self):
        """Le prompt enrichi a la bonne structure : base + saut de ligne + instruction"""
        result = build_enriched_prompt(self.BASE_PROMPT, include_quote=True)
        expected = f"{self.BASE_PROMPT}\n\n{QUOTE_INSTRUCTION}"
        assert result == expected


class TestTagAuthorFeature:
    """Tests pour la fonctionnalite tag_author (Story 1.2)"""

    BASE_PROMPT = "Genere un commentaire professionnel sur ce post LinkedIn."

    def test_tag_author_adds_instruction(self):
        """Avec tag_author fourni, le prompt contient l'instruction de tag"""
        result = build_enriched_prompt(self.BASE_PROMPT, tag_author="Jean Dupont")
        assert "Jean" in result
        assert "@Jean" in result
        assert self.BASE_PROMPT in result

    def test_tag_author_none_returns_base(self):
        """Avec tag_author=None, le prompt retourne est identique au base_prompt"""
        result = build_enriched_prompt(self.BASE_PROMPT, tag_author=None)
        assert result == self.BASE_PROMPT

    def test_tag_author_instruction_content(self):
        """L'instruction tag_author contient les elements cles"""
        result = build_enriched_prompt(self.BASE_PROMPT, tag_author="Marie Martin")
        assert "@Marie" in result
        assert "{{{SPLIT}}}" in result
        assert "NE COMMENCE PAS" in result

    def test_tag_author_with_quote_both_present(self):
        """Avec include_quote=True et tag_author, les deux instructions sont presentes"""
        result = build_enriched_prompt(
            self.BASE_PROMPT,
            include_quote=True,
            tag_author="Pierre Durand"
        )
        assert QUOTE_INSTRUCTION in result
        assert "@Pierre" in result
        assert "{{{SPLIT}}}" in result

    def test_tag_author_with_special_characters(self):
        """Le tag_author fonctionne avec des noms speciaux"""
        result = build_enriched_prompt(self.BASE_PROMPT, tag_author="Jean-Pierre O'Connor")
        assert "@Jean-Pierre" in result

    def test_tag_author_empty_string_treated_as_falsy(self):
        """Une string vide pour tag_author est traitee comme None"""
        result = build_enriched_prompt(self.BASE_PROMPT, tag_author="")
        # String vide est falsy en Python, donc pas d'instruction ajoutee
        assert result == self.BASE_PROMPT

    def test_tag_author_order_in_prompt(self):
        """L'ordre est : base_prompt, puis quote, puis tag_author"""
        result = build_enriched_prompt(
            self.BASE_PROMPT,
            include_quote=True,
            tag_author="Sophie Lemaire"
        )
        quote_pos = result.find(QUOTE_INSTRUCTION)
        tag_pos = result.find("@Sophie")
        assert quote_pos < tag_pos, "Quote doit apparaitre avant tag_author"
