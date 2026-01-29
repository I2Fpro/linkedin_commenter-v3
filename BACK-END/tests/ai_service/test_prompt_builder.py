"""
Tests pour le module prompt_builder.py
Story 1.1 - Generation de Commentaire avec Citation Contextuelle
Story 1.2 - Tag Automatique de l'Auteur du Post
Story 1.3 - Contextualisation via les Commentaires Tiers
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
        """Quote + tag_author + third_party sont traites, web_search ignore (story 1.4)"""
        result = build_enriched_prompt(
            self.BASE_PROMPT,
            include_quote=True,
            tag_author="Jean Dupont",
            web_search_result="Resultat web",
            third_party_comments=["Commentaire 1", "Commentaire 2"],
        )
        assert QUOTE_INSTRUCTION in result
        assert self.BASE_PROMPT in result
        assert "Jean" in result  # tag_author est traite
        assert "Commentaire 1" in result  # third_party_comments est traite

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


class TestThirdPartyCommentsFeature:
    """Tests pour la fonctionnalite third_party_comments (Story 1.3)"""

    BASE_PROMPT = "Genere un commentaire professionnel sur ce post LinkedIn."

    def test_third_party_comments_adds_context_instruction(self):
        """Avec third_party_comments fournis, le prompt contient l'instruction de contexte"""
        comments = ["Super article !", "Je suis d'accord avec toi"]
        result = build_enriched_prompt(self.BASE_PROMPT, third_party_comments=comments)
        assert "Commentaires existants" in result
        assert "Super article" in result
        # Verifier que l'instruction de differenciation est presente
        assert "differencier" in result.lower() or "perspective nouvelle" in result.lower()

    def test_third_party_comments_empty_list_returns_base(self):
        """Avec third_party_comments=[], le prompt retourne est identique au base_prompt"""
        result = build_enriched_prompt(self.BASE_PROMPT, third_party_comments=[])
        assert result == self.BASE_PROMPT

    def test_third_party_comments_none_returns_base(self):
        """Avec third_party_comments=None, le prompt retourne est identique au base_prompt"""
        result = build_enriched_prompt(self.BASE_PROMPT, third_party_comments=None)
        assert result == self.BASE_PROMPT

    def test_third_party_comments_limits_to_ten(self):
        """Les commentaires tiers sont limites a 10 maximum"""
        comments = [f"Commentaire {i}" for i in range(15)]
        result = build_enriched_prompt(self.BASE_PROMPT, third_party_comments=comments)
        # Verifier que seuls les 10 premiers commentaires sont inclus
        assert "Commentaire 9" in result
        assert "Commentaire 10" not in result

    def test_third_party_comments_truncates_long_comments(self):
        """Les commentaires longs sont tronques a 300 caracteres"""
        long_comment = "A" * 500
        result = build_enriched_prompt(self.BASE_PROMPT, third_party_comments=[long_comment])
        # Verifier que le commentaire est tronque a 300 caracteres
        assert "A" * 300 in result
        assert "A" * 301 not in result

    def test_third_party_comments_with_other_options(self):
        """Les commentaires tiers fonctionnent avec les autres options V3"""
        comments = ["Excellent point !"]
        result = build_enriched_prompt(
            self.BASE_PROMPT,
            include_quote=True,
            tag_author="Marie Martin",
            third_party_comments=comments
        )
        # Verifier que toutes les instructions sont presentes
        assert QUOTE_INSTRUCTION in result
        assert "@Marie" in result
        assert "Excellent point" in result

    def test_third_party_comments_order_in_prompt(self):
        """L'ordre est : base_prompt, quote, tag_author, third_party_comments"""
        result = build_enriched_prompt(
            self.BASE_PROMPT,
            include_quote=True,
            tag_author="Sophie Lemaire",
            third_party_comments=["Commentaire test"]
        )
        quote_pos = result.find(QUOTE_INSTRUCTION)
        tag_pos = result.find("@Sophie")
        comments_pos = result.find("Commentaire test")
        assert quote_pos < tag_pos < comments_pos, "Ordre: quote < tag < comments"

    def test_third_party_comments_instruction_content(self):
        """L'instruction third_party_comments contient les consignes de differenciation"""
        comments = ["Point de vue interessant"]
        result = build_enriched_prompt(self.BASE_PROMPT, third_party_comments=comments)
        # Verifier les consignes cles
        assert "Ne repete PAS" in result
        assert "perspective nouvelle" in result or "angle different" in result
        assert "nuancer" in result or "challenger" in result

    def test_third_party_comments_multiple_comments_formatted(self):
        """Plusieurs commentaires sont formates avec des tirets"""
        comments = ["Premier commentaire", "Deuxieme commentaire", "Troisieme commentaire"]
        result = build_enriched_prompt(self.BASE_PROMPT, third_party_comments=comments)
        assert "- Premier commentaire" in result
        assert "- Deuxieme commentaire" in result
        assert "- Troisieme commentaire" in result
