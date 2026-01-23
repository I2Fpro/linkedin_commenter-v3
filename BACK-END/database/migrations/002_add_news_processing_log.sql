-- Migration 002: Ajout de la table news_processing_log
-- Permet de tracker toutes les opérations de traitement des actualités

-- Table de logs de traitement des actualités
CREATE TABLE IF NOT EXISTS news_processing_log (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    status VARCHAR(50) NOT NULL,  -- 'success', 'cached', 'error', 'pending_retry'
    duration_ms FLOAT,            -- Durée du traitement en millisecondes
    error_message TEXT,           -- Message d'erreur si status='error'
    metadata JSONB,               -- Métadonnées additionnelles (title, lang, retry_count, etc.)
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index pour recherche rapide
CREATE INDEX IF NOT EXISTS idx_news_processing_url ON news_processing_log(url);
CREATE INDEX IF NOT EXISTS idx_news_processing_status ON news_processing_log(status);
CREATE INDEX IF NOT EXISTS idx_news_processing_created_at ON news_processing_log(created_at);

-- Commentaire sur la table
COMMENT ON TABLE news_processing_log IS 'Logs de traitement des actualités LinkedIn avec métriques de performance';

-- Ajout d'une colonne processing_time_ms dans la table news pour tracker individuellement
ALTER TABLE news
ADD COLUMN IF NOT EXISTS processing_time_ms FLOAT,
ADD COLUMN IF NOT EXISTS retry_count INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_error TEXT;

-- Index sur les colonnes de retry
CREATE INDEX IF NOT EXISTS idx_news_retry_count ON news(retry_count) WHERE retry_count > 0;

-- Vue pour statistiques rapides
CREATE OR REPLACE VIEW news_stats AS
SELECT
    COUNT(*) as total_news,
    COUNT(*) FILTER (WHERE scraped_at::date = CURRENT_DATE) as processed_today,
    AVG(processing_time_ms) as avg_processing_time_ms,
    COUNT(*) FILTER (WHERE retry_count > 0) as failed_with_retry,
    MAX(scraped_at) as last_update
FROM news;

COMMENT ON VIEW news_stats IS 'Vue agrégée des statistiques de traitement des actualités';
