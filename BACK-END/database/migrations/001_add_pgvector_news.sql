-- Migration pour ajouter le support des actualités LinkedIn avec pgvector
-- Date: 2025-01-24
-- Description: Ajoute l'extension pgvector et la table news pour l'enrichissement contextuel

-- Créer l'extension pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Table des actualités LinkedIn
CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    lang VARCHAR(10) NOT NULL DEFAULT 'fr',
    embedding vector(1536),  -- OpenAI text-embedding-3-small génère des vecteurs de 1536 dimensions
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour les recherches par URL
CREATE INDEX IF NOT EXISTS idx_news_url ON news(url);

-- Index pour les recherches par langue
CREATE INDEX IF NOT EXISTS idx_news_lang ON news(lang);

-- Index pour les recherches par date
CREATE INDEX IF NOT EXISTS idx_news_created_at ON news(created_at DESC);

-- Index vectoriel pour la recherche sémantique (IVFFlat)
-- IVFFlat est plus rapide que la recherche exacte pour les grandes bases
-- lists = 100 est un bon compromis pour jusqu'à 100k enregistrements
CREATE INDEX IF NOT EXISTS news_embedding_idx
ON news USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Vue pour les actualités récentes par langue
CREATE OR REPLACE VIEW recent_news AS
SELECT
    id,
    url,
    title,
    summary,
    lang,
    scraped_at,
    processed,
    created_at
FROM news
WHERE processed = TRUE
AND scraped_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;

-- Vue pour les statistiques des actualités
CREATE OR REPLACE VIEW news_stats AS
SELECT
    lang,
    COUNT(*) as total_articles,
    COUNT(*) FILTER (WHERE processed = TRUE) as processed_articles,
    COUNT(*) FILTER (WHERE embedding IS NOT NULL) as articles_with_embedding,
    MIN(created_at) as oldest_article,
    MAX(created_at) as newest_article
FROM news
GROUP BY lang;

-- Fonction pour rechercher les actualités similaires
-- Cette fonction peut être appelée directement depuis SQL si nécessaire
CREATE OR REPLACE FUNCTION search_similar_news(
    query_embedding vector(1536),
    target_lang VARCHAR(10),
    result_limit INTEGER DEFAULT 3
)
RETURNS TABLE(
    url TEXT,
    title TEXT,
    summary TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.url,
        n.title,
        n.summary,
        1 - (n.embedding <=> query_embedding) as similarity
    FROM news n
    WHERE n.lang = target_lang
    AND n.embedding IS NOT NULL
    ORDER BY n.embedding <=> query_embedding
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour nettoyer les anciennes actualités
-- Garde les actualités des 30 derniers jours
CREATE OR REPLACE FUNCTION cleanup_old_news(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM news
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_to_keep;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Commentaires pour la documentation
COMMENT ON TABLE news IS 'Table des actualités LinkedIn scrapées pour l''enrichissement contextuel des commentaires';
COMMENT ON COLUMN news.url IS 'URL unique de l''actualité LinkedIn';
COMMENT ON COLUMN news.title IS 'Titre de l''actualité';
COMMENT ON COLUMN news.summary IS 'Résumé généré par GPT (2-3 phrases)';
COMMENT ON COLUMN news.lang IS 'Langue de l''actualité (fr, en, etc.)';
COMMENT ON COLUMN news.embedding IS 'Vecteur d''embedding de 1536 dimensions (OpenAI text-embedding-3-small)';
COMMENT ON COLUMN news.scraped_at IS 'Date et heure du scraping de l''actualité';
COMMENT ON COLUMN news.processed IS 'Indique si l''actualité a été entièrement traitée (scraping + résumé + embedding)';

COMMENT ON INDEX news_embedding_idx IS 'Index vectoriel IVFFlat pour la recherche sémantique par similarité cosinus';
COMMENT ON FUNCTION search_similar_news IS 'Recherche les actualités les plus similaires à un vecteur d''embedding donné';
COMMENT ON FUNCTION cleanup_old_news IS 'Supprime les actualités plus anciennes que le nombre de jours spécifié';

-- Fin de la migration
SELECT 'Migration 001_add_pgvector_news completed successfully!' as message;
