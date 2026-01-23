/**
 * shared_env.js
 * Point central des variables "build-time" exposées au code de l'extension.
 * Les valeurs sont injectées par scripts/build_frontend.py au moment du build.
 * AUCUNE donnée sensible ne doit être commitée ici.
 */
(function (global) {
  global.ENV = Object.freeze({
    // Adresse du backend (doit être en HTTPS pour LinkedIn)
    BACKEND_URL: (typeof API_CONFIG !== 'undefined' && API_CONFIG) ? API_CONFIG.AI_SERVICE_URL : '__AI_API_URL__'
  });
})(typeof self !== 'undefined' ? self : window);
