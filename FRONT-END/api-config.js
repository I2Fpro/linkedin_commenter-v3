// Configuration des URLs des APIs backend pour l'extension LinkedIn AI Commenter
// Utiliser var pour permettre la re-déclaration dans les Service Workers
if (typeof API_CONFIG === 'undefined') {
var API_CONFIG = {
  // URL du service AI (génération de commentaires)
  AI_SERVICE_URL: 'http://localhost:8443',

  // URL du service utilisateur (authentification, quotas, permissions)
  USER_SERVICE_URL: 'http://localhost:8444',

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
}

// Export pour utilisation dans les autres fichiers
if (typeof module !== 'undefined' && module.exports) {
  module.exports = API_CONFIG;
} else if (typeof window !== 'undefined') {
  window.API_CONFIG = API_CONFIG;
}
