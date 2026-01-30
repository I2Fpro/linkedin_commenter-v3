"""
Module de construction dynamique du prompt V3.
Enrichit le prompt de base avec des instructions contextuelles
(citation, tag auteur, recherche web, commentaires tiers).

Story 1.1 : Citation contextuelle implementee.
Story 1.2 : Tag auteur implemente.
Story 1.3 : Contextualisation via commentaires tiers implementee.
Story 1.4 : Recherche web et fallback gracieux implementee.
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
    Construit l'instruction pour integrer @prenom avec le marqueur {{{SPLIT}}}.
    Le frontend utilisera ce marqueur pour l'insertion en deux temps :
    1. Inserer le debut jusqu'au @prenom
    2. Attendre que l'utilisateur valide la mention LinkedIn
    3. Inserer automatiquement la suite

    Args:
        author_name: Le nom de l'auteur du post a interpeller.

    Returns:
        L'instruction pour le LLM.
    """
    # Extraire le prenom (premier mot)
    first_name = author_name.split()[0] if author_name else "l'auteur"
    return (
        f"IMPORTANT — Tag auteur : Integre @{first_name} naturellement dans ton commentaire. "
        f"JUSTE APRES @{first_name}, ajoute le marqueur {{{{{{SPLIT}}}}}} (exactement comme ecrit). "
        f"Exemple : 'Comme tu le soulignes @{first_name}{{{{{{SPLIT}}}}}}, ton analyse est...' "
        f"Autre exemple : 'Je rejoins ta reflexion @{first_name}{{{{{{SPLIT}}}}}} sur ce point...' "
        f"NE COMMENCE PAS le commentaire par @{first_name}. "
        f"Place @{first_name}{{{{{{SPLIT}}}}}} naturellement au milieu d'une phrase."
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
        web_search_result: Resultat de recherche web (Story 1.4). Si fourni,
                           ajoute une instruction pour integrer la source web
                           de maniere naturelle dans le commentaire.
        third_party_comments: Liste des commentaires tiers existants sur le post.
                              Si fournie, ajoute un contexte pour que le LLM
                              genere un commentaire qui se differencie des existants.

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

    # V3 Story 1.4 — Recherche web
    if web_search_result:
        web_instruction = (
            "CONTEXTE WEB — Source recente trouvee :\n"
            f"{web_search_result}\n\n"
            "INSTRUCTION : Integre cette source de maniere naturelle dans ton commentaire.\n"
            "- Cite la source ou l'information cle de facon pertinente\n"
            "- N'invente PAS de lien ou de source\n"
            "- Si la source inclut une URL, tu peux la mentionner brievement\n"
            "- L'information doit renforcer ton argument, pas le remplacer"
        )
        enriched = f"{enriched}\n\n{web_instruction}"

    # V3 Story 1.3 — Contextualisation via commentaires tiers
    if third_party_comments and len(third_party_comments) > 0:
        # Formater les commentaires existants (max 10, tronques a 300 chars)
        comments_text = "\n".join(
            [f"- {c[:300]}" for c in third_party_comments[:10]]
        )
        context_instruction = (
            "CONTEXTE IMPORTANT - Commentaires existants sur ce post :\n"
            f"{comments_text}\n\n"
            "INSTRUCTION : Ton commentaire doit se differencier des commentaires existants ci-dessus.\n"
            "- Ne repete PAS les memes points de vue\n"
            "- Apporte une perspective nouvelle ou un angle different\n"
            "- Si les autres sont d'accord avec l'auteur, tu peux nuancer ou challenger (avec respect)\n"
            "- Si les autres critiquent, tu peux defendre ou proposer une vision constructive\n"
            "- Evite les formulations deja utilisees par les autres commentateurs"
        )
        enriched = f"{enriched}\n\n{context_instruction}"

    return enriched
