"""
Modèles de données pour le module News
Structure de stockage des actualités avec pgvector
"""
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime


class NewsArticle(BaseModel):
    """Modèle d'une actualité LinkedIn"""
    url: str
    title: str
    summary: Optional[str] = None
    lang: str = "fr"
    embedding: Optional[List[float]] = None
    scraped_at: Optional[datetime] = None
    processed: bool = False


class NewsRegisterRequest(BaseModel):
    """Requête pour enregistrer des actualités"""
    urls: List[str]
    lang: str = "fr"


class NewsRegisterResponse(BaseModel):
    """Réponse d'enregistrement d'actualités"""
    registered: int
    skipped: int
    processed_urls: List[str]


class NewsSearchRequest(BaseModel):
    """Requête de recherche vectorielle"""
    query: str
    lang: str = "fr"
    limit: int = 3


class NewsSearchResult(BaseModel):
    """Résultat d'une recherche d'actualité"""
    url: str
    title: str
    summary: str
    similarity: float


class NewsSearchResponse(BaseModel):
    """Réponse de recherche vectorielle"""
    results: List[NewsSearchResult]
