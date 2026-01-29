"""
Module de construction dynamique du prompt V3.
Enrichit le prompt de base avec des instructions contextuelles
(citation, tag auteur, recherche web, commentaires tiers).

Story 1.1 : Citation contextuelle implementee.
Story 1.2 : Tag auteur implemente.
Les params web_search_result, third_party_comments sont
acceptes mais non traites (preparation stories 1.3, 1.4).
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


def _build_tag_author_instruction(author_name: str) -> str:
    """
    Construit l'instruction pour integrer le nom de l'auteur naturellement.

    Args:
        author_name: Le nom de l'auteur du post a interpeller.

    Returns:
        L'instruction pour le LLM.
    """
    return (
        f"IMPORTANT — Tag auteur : Integre naturellement le nom de l'auteur du post "
        f"({author_name}) dans ton commentaire pour l'interpeller directement. "
        f"NE COMMENCE PAS le commentaire par le nom ou par '@{author_name}'. "
        f"Integre-le de maniere fluide dans une phrase, par exemple : "
        f"'Comme tu le soulignes, {author_name}, ...' ou "
        f"'Ton point de vue, {author_name}, ...' ou "
        f"'Je rejoins ta reflexion {author_name} sur...' "
        f"Evite les formulations trop formelles comme 'Cher {author_name}' ou 'Monsieur/Madame'."
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
        tag_author: Nom de l'auteur a tagger. Si fourni, ajoute une instruction
                    pour integrer le nom naturellement dans le commentaire.
        web_search_result: Resultat de recherche web (non traite dans stories 1.1-1.2).
        third_party_comments: Commentaires tiers (non traite dans stories 1.1-1.2).

    Returns:
        Le prompt enrichi ou le prompt de base inchange.
    """
    enriched = base_prompt

    # V3 Story 1.1 — Citation contextuelle
    if include_quote:
        enriched = f"{enriched}\n\n{QUOTE_INSTRUCTION}"

    # V3 Story 1.2 — Tag auteur
    if tag_author:
        tag_instruction = _build_tag_author_instruction(tag_author)
        enriched = f"{enriched}\n\n{tag_instruction}"

    return enriched
