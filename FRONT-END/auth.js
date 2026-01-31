
// Gestion de l'authentification Google pour le plugin - VERSION DYNAMIQUE (pas de Client ID en dur)
class GoogleAuth {
  constructor() {
    // Utilitaire
    this.extensionId = chrome.runtime.id; // dynamique
    this.backendUrl = (typeof API_CONFIG !== 'undefined' && API_CONFIG) ? API_CONFIG.AI_SERVICE_URL : 'http://localhost:8443';
    this.clientId = null; // chargé via backend
    this.userInfo = null;
    this.defaultTimeout = (typeof API_CONFIG !== 'undefined' && API_CONFIG) ? API_CONFIG.REQUEST_TIMEOUT : 15000;

    console.log('GoogleAuth initialized with Extension ID:', this.extensionId);
    this.loadClientId();
  }

  // Charger le Client ID depuis le backend (aucun fallback en dur)
  async loadClientId() {
    try {
      const config = await window.extensionConfig.loadConfig();
      this.clientId = config.google_client_id;
      console.log('✅ Client ID chargé depuis backend:', this.clientId ? 'présent' : 'absent');
    } catch (error) {
      console.error('❌ Erreur chargement Client ID via backend:', error);
      this.clientId = null;
    }
  }

  // S'assurer que le Client ID est chargé avant utilisation
  async ensureClientIdLoaded() {
    if (!this.clientId) {
      await this.loadClientId();
    }
    return this.clientId;
  }

  /** Initialise l'authentification de façon passive (pas de popup). */
  async initialize() {
    console.log('🔐 Initialisation de l\'authentification...');
    try {
      const stored = await chrome.storage.sync.get(['userInfo']);
      if (stored.userInfo) {
        this.userInfo = stored.userInfo;
        console.log('✅ Utilisateur trouvé:', stored.userInfo.email);
        return true;
      }
      const token = await this.getToken(false);
      if (token) {
        const userInfo = await this.fetchUserInfo(token);
        if (userInfo) {
          this.userInfo = userInfo;
          await chrome.storage.sync.set({ userInfo });
          console.log('✅ Utilisateur authentifié:', userInfo.email);
          return true;
        }
      }
      console.log('ℹ️ Aucune authentification active');
      return false;
    } catch (error) {
      console.error('❌ Erreur initialisation:', error);
      return false;
    }
  }

  /** Récupère un token via chrome.identity (Google gère le cache). */
  async getToken(interactive = false) {
    return new Promise((resolve) => {
      try {
        chrome.identity.getAuthToken({ interactive }, (token) => {
          if (chrome.runtime.lastError) {
            console.log(`ℹ️ Pas de token (interactive: ${interactive}):`, chrome.runtime.lastError.message);
            resolve(null);
          } else {
            resolve(token);
          }
        });
      } catch (error) {
        console.error('❌ Erreur getToken:', error);
        resolve(null);
      }
    });
  }

  /** Appelle l'endpoint Google UserInfo pour obtenir email/nom/avatar. */
  async fetchUserInfo(token) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.defaultTimeout);
      const response = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
        headers: { 'Authorization': `Bearer ${token}` },
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error('❌ Erreur récupération user info:', error);
      return null;
    }
  }

  /** Lance un flux d'authentification interactif (popup). */
  async signIn() {
    console.log('🚀 Connexion Google...');
    try {
      await this.clearState();
      await new Promise(resolve => setTimeout(resolve, 300));

      // S'assurer que le Client ID est chargé
      const clientId = await this.ensureClientIdLoaded();
      if (!clientId) {
        throw new Error('Configuration Google OAuth non disponible');
      }

      const token = await this.getToken(true);
      if (!token) {
        const msg = chrome.runtime.lastError?.message || 'Authentification annulée';
        throw new Error(msg);
      }
      const userInfo = await this.fetchUserInfo(token);
      if (!userInfo) {
        chrome.identity.removeCachedAuthToken({ token }, () => {});
        throw new Error('Impossible de récupérer les informations utilisateur');
      }
      this.userInfo = userInfo;
      await chrome.storage.sync.set({ userInfo });

      // Générer userId anonyme (SHA256 de l'email) - Conforme RGPD
      let anonymousUserId = null;
      try {
        if (typeof userIdUtils !== 'undefined') {
          anonymousUserId = await userIdUtils.getOrGenerateUserId(userInfo.email);
          console.log('✅ UserId anonyme généré:', anonymousUserId);
        }
      } catch (e) {
        console.error('❌ Erreur génération userId:', e);
      }

      // Get user data from backend
      let userPlan = 'FREE';
      let userRole = 'FREE';

      try {
        const planResponse = await chrome.runtime.sendMessage({ action: 'getUserQuota' });
        if (planResponse && planResponse.role) {
          userRole = planResponse.role;
          userPlan = planResponse.role;
        }
      } catch (e) {
        console.warn('Could not fetch user plan for tracking:', e);
      }

      // Stocker user_id et user_plan dans le storage (clés officielles)
      await chrome.storage.local.set({
        user_id: anonymousUserId,
        user_plan: userPlan
      });

      // Track user authentication avec PostHog (Plan v3)
      if (typeof posthogClient !== 'undefined' && typeof posthog !== 'undefined' && anonymousUserId) {
        try {

          // Get current UI language
          let currentUiLang = 'fr';
          try {
            const langStorage = await chrome.storage.sync.get(['interfaceLanguage']);
            if (langStorage.interfaceLanguage) {
              currentUiLang = langStorage.interfaceLanguage;
            }
          } catch (e) {
            console.warn('Could not fetch UI language:', e);
          }

          // Wait for PostHog to be ready
          await posthogClient.ready();

          // Get current anonymous ID before aliasing
          const currentAnon = posthog.get_distinct_id();

          // Alias the anonymous session to the user ID
          if (currentAnon && currentAnon !== anonymousUserId) {
            try {
              posthog.alias(currentAnon, anonymousUserId);
              console.log('🔗 PostHog alias created:', currentAnon, '->', anonymousUserId);
            } catch (e) {
              console.warn('PostHog alias failed:', e);
            }
          }

          // Identifier l'utilisateur avec le userId anonyme (PAS d'email)
          posthogClient.identify(anonymousUserId, {
            plan: userPlan,
            role: userRole,
            interface_lang: currentUiLang
          });

          // Set person properties (sans email)
          posthogClient.setPersonProperties({
            plan: userPlan,
            role: userRole,
            interface_lang: currentUiLang
          });

          // Capture user_login event (sans email)
          posthogClient.capture('user_login', {
            user_id: anonymousUserId,
            plan: userPlan,
            auth_method: 'google_oauth2'
          });

          console.log('✅ PostHog user tracking completed (anonyme):', anonymousUserId);
        } catch (e) {
          console.warn('PostHog tracking failed:', e);
        }
      }

      return true;
    } catch (error) {
      console.error('❌ Erreur connexion:', error);
      await this.clearState();
      throw error;
    }
  }

  /** Révoque le token local & distant, nettoie le storage. */
  async signOut() {
    try {
      const token = await this.getToken(false);
      if (token) {
        chrome.identity.removeCachedAuthToken({ token }, () => {});
        try { await fetch(`https://oauth2.googleapis.com/revoke?token=${token}`, { method: 'POST' }); } catch {}
      }

      // Track user logout
      if (typeof posthogClient !== 'undefined') {
        try {
          posthogClient.trackUserLogout();
        } catch (e) {
          console.warn('PostHog tracking failed:', e);
        }
      }

      await this.clearState();
      return true;
    } catch (error) {
      console.error('❌ Erreur déconnexion:', error);
      await this.clearState();
      return false;
    }
  }

  /** Nettoie toute trace d'authentification côté extension. */
  async clearState() {
    this.userInfo = null;
    await chrome.storage.sync.remove(['userInfo']);

    // Nettoyer le userId anonyme
    if (typeof userIdUtils !== 'undefined') {
      await userIdUtils.clearUserId();
    }

    await new Promise(resolve => setTimeout(resolve, 80));
    return new Promise((resolve) => chrome.identity.clearAllCachedAuthTokens(() => resolve()));
  }

  /** Retourne true si un token valide est présent. */
  async isAuthenticated() {
    if (this.userInfo) return true;
    const token = await this.getToken(false);
    return !!token;
  }

  /** Renvoie les informations utilisateur mises en cache. */
  getUserData() { return this.userInfo; }

  /** Renvoie un token d'accès à utiliser sur le backend. */
  async getAuthToken() { return await this.getToken(false); }

  /** Alias pour getAuthToken - utilisé par popup.js */
  async getAccessToken() { return await this.getAuthToken(); }

  // Vérifier la configuration OAuth
  async checkOAuthConfig() {
    const expectedRedirectUri = `https://${this.extensionId}.chromiumapp.org/`;
    return { extensionId: this.extensionId, clientId: this.clientId, redirectUri: expectedRedirectUri };
  }
}

window.googleAuth = new GoogleAuth();
console.log('🔐 GoogleAuth initialisé');
