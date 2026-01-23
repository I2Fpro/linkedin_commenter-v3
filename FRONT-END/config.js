
// Configuration centralisée pour l'extension LinkedIn AI Commenter - VERSION ENTIÈREMENT DYNAMIQUE
class ExtensionConfig {
  constructor() {
    this.extensionId = chrome.runtime.id; // dynamique
    // URL de base temporaire pour le premier appel - sera remplacée par la config du backend
    this.backendUrl = '__AI_API_URL__';  // Seule valeur en dur, nécessaire pour le bootstrap
    this.USER_SERVICE_URL = null; // Sera chargé depuis le backend
    this.requestTimeout = 15000;
    this.configCache = null;
    this.configLoaded = false;
  }

  // Charger la configuration depuis le backend
  async loadConfig() {
    try {
      if (this.configCache && this.configLoaded) return this.configCache;
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.requestTimeout);
      
      const response = await fetch(`${this.backendUrl}/config/complete`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        mode: 'cors',
        credentials: 'omit',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const config = await response.json();
      
      // Mettre à jour les URLs depuis la configuration du backend
      if (config.urls) {
        this.backendUrl = config.urls.backend || this.backendUrl;
        this.USER_SERVICE_URL = config.urls.user_service;
      }
      
      this.configCache = config;
      this.configLoaded = true;
      
      console.log('✅ Configuration chargée depuis le backend:', config);
      return config;
    } catch (error) {
      console.error('❌ Erreur chargement config:', error);
      // Configuration de fallback minimale
      return { 
        google_client_id: null, 
        backend_version: 'unknown', 
        https_enabled: true,
        urls: {
          backend: this.backendUrl,
          user_service: '__USERS_API_URL__'
        },
        features: {
          google_auth: true,
          user_registration: true
        }
      };
    }
  }

  // Tester la connectivité backend
  async checkBackendConnectivity() {
    try {
      const response = await fetch(`${this.backendUrl}/health`, {
        method: 'GET',
        mode: 'cors',
        credentials: 'omit',
        signal: AbortSignal.timeout(5000)
      });
      return response.ok;
    } catch (error) {
      console.error('❌ Backend non accessible:', error);
      return false;
    }
  }

  // Récupérer l'URL du User Service depuis la config
  getUserServiceUrl() {
    return this.USER_SERVICE_URL || (this.configCache && this.configCache.urls && this.configCache.urls.user_service) || '__USERS_API_URL__';
  }

  // Récupérer le Google Client ID depuis la config
  getGoogleClientId() {
    return this.configCache && this.configCache.google_client_id;
  }

  getExtensionInfo() { 
    return { 
      id: this.extensionId, 
      backendUrl: this.backendUrl,
      userServiceUrl: this.getUserServiceUrl(),
      configLoaded: this.configLoaded
    }; 
  }
}
window.extensionConfig = new ExtensionConfig();
