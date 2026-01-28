"""
Module de construction dynamique du prompt V3.
Enrichit le prompt de base avec des instructions contextuelles
(citation, tag auteur, recherche web, commentaires tiers).

Story 1.1 : Seule la logique citation est implementee.
Les params tag_author, web_search_result, third_party_comments sont
acceptes mais non traites (preparation stories 1.2, 1.3, 1.4).
"""
from typing import List, Optional


QUOTE_INSTRUCTION = (
    "IMPORTANT — Citation contextuelle : Integre naturellement UNE citation, "
    "un adage ou un proverbe qui est DIRECTEMENT lie au theme principal du post. "
    "La citation doit faire echo a un point precis aborde par l'auteur du post, "
    "pas etre une citation generique sur le succes ou la motivation. "
    "Cite l'auteur de la citation entre guillemets. "
    "La citation doit renforcer ton argument et montrer que tu as compris le fond du sujet."
)


def build_enriched_prompt(
    base_prompt: str,
    include_quote: bool = False,
    tag_author: Optional[str] = None,
    web_search_result: Optional[str] = None,
    third_party_comments: Optional[List[str]] = None,
) -> str:
    """
    Construit un prompt enrichi a partir du prompt de base et des options V3.

    Args:
        base_prompt: Le prompt de base genere par le systeme existant.
        include_quote: Si True, ajoute une instruction pour inclure une citation.
        tag_author: Nom de l'auteur a tagger (non traite dans story 1.1).
        web_search_result: Resultat de recherche web (non traite dans story 1.1).
        third_party_comments: Commentaires tiers (non traite dans story 1.1).

    Returns:
        Le prompt enrichi ou le prompt de base inchange.
    """
    if not include_quote:
        return base_prompt

    return f"{base_prompt}\n\n{QUOTE_INSTRUCTION}"
