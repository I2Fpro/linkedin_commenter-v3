// Configuration des URLs des APIs backend pour l'extension LinkedIn AI Commenter
const API_CONFIG = {
  // URL du service AI (génération de commentaires)
  AI_SERVICE_URL: '__AI_API_URL__',

  // URL du service utilisateur (authentification, quotas, permissions)
  USER_SERVICE_URL: '__USERS_API_URL__',

  // URL de la base de données PostgreSQL (pour référence, non utilisée directement par le frontend)
  DATABASE_URL: 'postgres://database-host:5432',

  // Timeout par défaut pour les requêtes API (en millisecondes)
  REQUEST_TIMEOUT: 15000,

  // Configuration PostHog
  posthog: {
    apiKey: 'phc_Igj1h8n3Ap7uuJNxZ5cVgsoqpx8kC9hALpPMyYWO0TQ',
    apiHost: 'https://eu.i.posthog.com',
    enabled: true
  }
};

// Export pour utilisation dans les autres fichiers
if (typeof module !== 'undefined' && module.exports) {
  module.exports = API_CONFIG;
} else if (typeof window !== 'undefined') {
  window.API_CONFIG = API_CONFIG;
}
