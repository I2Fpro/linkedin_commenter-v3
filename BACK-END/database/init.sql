-- Création de la base de données LinkedIn AI Commenter
-- Script d'initialisation PostgreSQL

-- Création des types ENUM
CREATE TYPE role_type AS ENUM ('FREE', 'MEDIUM', 'PREMIUM');
CREATE TYPE subscription_status AS ENUM ('ACTIVE', 'EXPIRED', 'CANCELLED');

-- Extension pour les UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    google_id VARCHAR(255) UNIQUE,
    role role_type DEFAULT 'FREE' NOT NULL,
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    subscription_status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Table des rôles (pour la configuration future)
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    daily_limit INTEGER DEFAULT 5,
    features JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des abonnements
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan role_type NOT NULL,
    status subscription_status DEFAULT 'ACTIVE',
    start_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des logs d'utilisation
CREATE TABLE IF NOT EXISTS usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Index pour les performances
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_users_stripe_subscription_id ON users(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_timestamp ON usage_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_timestamp ON usage_logs(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_usage_logs_feature ON usage_logs(feature);

-- Fonction pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger pour mettre à jour updated_at sur la table users
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insertion des données initiales pour les rôles
INSERT INTO roles (name, description, daily_limit, features) VALUES 
(
    'FREE',
    'Plan gratuit avec fonctionnalités de base',
    5,
    '{
        "daily_generations": 5,
        "custom_prompt": false,
        "languages": ["fr"],
        "history_days": 0,
        "refine_enabled": false,
        "resize_enabled": false,
        "priority_support": false,
        "advanced_analytics": false,
        "bulk_operations": false,
        "api_access": false,
        "export_formats": ["txt"],
        "max_prompt_length": 200,
        "concurrent_requests": 1
    }'::jsonb
),
(
    'MEDIUM',
    'Plan intermédiaire avec fonctionnalités avancées',
    50,
    '{
        "daily_generations": 50,
        "custom_prompt": true,
        "languages": ["fr", "en"],
        "history_days": 7,
        "refine_enabled": true,
        "resize_enabled": true,
        "priority_support": false,
        "advanced_analytics": true,
        "bulk_operations": false,
        "api_access": false,
        "export_formats": ["txt", "csv"],
        "max_prompt_length": 500,
        "concurrent_requests": 2
    }'::jsonb
),
(
    'PREMIUM',
    'Plan premium avec toutes les fonctionnalités',
    -1,
    '{
        "daily_generations": -1,
        "custom_prompt": true,
        "languages": ["fr", "en", "es", "de", "it"],
        "history_days": -1,
        "refine_enabled": true,
        "resize_enabled": true,
        "priority_support": true,
        "advanced_analytics": true,
        "bulk_operations": true,
        "api_access": true,
        "export_formats": ["txt", "csv", "json", "xlsx"],
        "max_prompt_length": 1000,
        "concurrent_requests": 5
    }'::jsonb
)
ON CONFLICT (name) DO NOTHING;

-- Création d'un utilisateur de test (optionnel, à supprimer en production)
-- INSERT INTO users (email, name, google_id, role) VALUES 
-- ('test@example.com', 'Test User', 'google_test_123', 'FREE')
-- ON CONFLICT (email) DO NOTHING;

-- Vues utiles pour les requêtes fréquentes

-- Vue pour les statistiques d'utilisation quotidienne
CREATE OR REPLACE VIEW daily_usage_stats AS
SELECT 
    u.id as user_id,
    u.email,
    u.role,
    DATE(ul.timestamp) as usage_date,
    COUNT(*) as daily_count,
    ul.feature
FROM users u
LEFT JOIN usage_logs ul ON u.id = ul.user_id
WHERE ul.timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY u.id, u.email, u.role, DATE(ul.timestamp), ul.feature
ORDER BY usage_date DESC;

-- Vue pour les abonnements actifs
CREATE OR REPLACE VIEW active_subscriptions AS
SELECT 
    s.*,
    u.email,
    u.name
FROM subscriptions s
JOIN users u ON s.user_id = u.id
WHERE s.status = 'ACTIVE'
AND (s.end_date IS NULL OR s.end_date > CURRENT_TIMESTAMP);

-- Fonction pour nettoyer les anciens logs (à appeler périodiquement)
CREATE OR REPLACE FUNCTION cleanup_old_logs(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM usage_logs 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour obtenir les statistiques d'un utilisateur
CREATE OR REPLACE FUNCTION get_user_stats(user_uuid UUID, days_back INTEGER DEFAULT 30)
RETURNS TABLE(
    total_usage BIGINT,
    daily_average NUMERIC,
    most_used_feature TEXT,
    last_activity TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_usage,
        ROUND(COUNT(*)::NUMERIC / GREATEST(days_back, 1), 2) as daily_average,
        (
            SELECT feature 
            FROM usage_logs 
            WHERE user_id = user_uuid 
            AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 day' * days_back
            GROUP BY feature 
            ORDER BY COUNT(*) DESC 
            LIMIT 1
        ) as most_used_feature,
        MAX(timestamp) as last_activity
    FROM usage_logs
    WHERE user_id = user_uuid
    AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 day' * days_back;
END;
$$ LANGUAGE plpgsql;

-- Contraintes supplémentaires pour l'intégrité des données
ALTER TABLE subscriptions ADD CONSTRAINT check_end_date_after_start
CHECK (end_date IS NULL OR end_date > start_date);

-- Note: La contrainte check_email_format a été supprimée car les emails sont chiffrés
-- avec EncryptedString (Fernet AES-128) et ne peuvent pas être validés par une regex classique

-- Commentaires pour la documentation
COMMENT ON TABLE users IS 'Table des utilisateurs de l''application LinkedIn AI Commenter';
COMMENT ON TABLE subscriptions IS 'Table des abonnements et plans des utilisateurs';
COMMENT ON TABLE usage_logs IS 'Logs d''utilisation des fonctionnalités par les utilisateurs';
COMMENT ON TABLE roles IS 'Configuration des rôles et leurs fonctionnalités';

COMMENT ON COLUMN users.role IS 'Rôle actuel de l''utilisateur (FREE, MEDIUM, PREMIUM)';
COMMENT ON COLUMN usage_logs.metadata IS 'Données additionnelles sur l''utilisation (format JSON)';
COMMENT ON COLUMN roles.features IS 'Configuration des fonctionnalités pour chaque rôle (format JSON)';

-- Fin du script d'initialisation
SELECT 'Database initialization completed successfully!' as message;