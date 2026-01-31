// Charger les scripts nécessaires
try {
  self.importScripts('api-config.js');
  console.log('API_CONFIG loaded:', !!API_CONFIG);
} catch (err) {
  console.warn('Failed to load API_CONFIG:', err);
  // Configuration par défaut si échec
  var API_CONFIG = {
    AI_SERVICE_URL: '__AI_API_URL__',
    USER_SERVICE_URL: '__USERS_API_URL__',
    REQUEST_TIMEOUT: 15000
  };
}

// Import PostHog - Charger posthog.min.js puis initialiser
let posthogClient = null;

// Charger posthog.min.js via importScripts (Manifest V3 compatible)
try {
  self.importScripts('posthog.min.js');
  console.log('PostHog.js loaded:', typeof posthog !== 'undefined');

  // Initialiser PostHog avec la configuration
  if (typeof posthog !== 'undefined') {
    posthog.init('phc_Igj1h8n3Ap7uuJNxZ5cVgsoqpx8kC9hALpPMyYWO0TQ', {
      api_host: 'https://eu.i.posthog.com',
      person_profiles: 'always',
      persistence: 'localStorage',
      autocapture: false,
      disable_session_recording: true,

      // Empêche le chargement de scripts externes (CSP)
      disable_external_dependency_loading: true,

      // Évite les activations via /decide qui pourraient relancer des deps externes
      advanced_disable_decide: true,

      loaded: (ph) => {
        console.log('📊 PostHog initialisé dans background.js', {
          distinctId: ph.get_distinct_id(),
          apiHost: 'https://eu.i.posthog.com'
        });
      }
    });

    // Créer un wrapper simple pour la compatibilité
    posthogClient = {
      initialized: true,
      capture: (event, properties = {}) => {
        try {
          console.log('📊 PostHog capture (background):', event, properties);
          posthog.capture(event, properties);
        } catch (error) {
          console.error('❌ Erreur capture PostHog:', error);
        }
      },
      identify: (userId, properties = {}) => {
        try {
          console.log('👤 PostHog identify (background):', userId, properties);
          posthog.identify(userId, properties);
        } catch (error) {
          console.error('❌ Erreur identify PostHog:', error);
        }
      },
      reset: () => {
        try {
          console.log('🔄 PostHog reset (background)');
          posthog.reset();
        } catch (error) {
          console.error('❌ Erreur reset PostHog:', error);
        }
      },
      trackCommentGenerationStarted: (options) => {
        posthogClient.capture('generation_started', {
          generation_type: options.generationType || 'automatic',
          has_custom_prompt: options.hasCustomPrompt || false,
          tone: options.tone || null,
          language: options.language || 'fr',
          emotion: options.emotion || null,
          emotionIntensity: options.emotionIntensity || null,
          style: options.style || null,
          newsEnrichment: options.newsEnrichment || 'disabled',
          length: options.length,
          optionsCount: options.optionsCount,
          timestamp: new Date().toISOString()
        });
      },
      trackCommentGenerated: (options) => {
        posthogClient.capture('comment_generated', {
          generation_type: options.generationType || 'automatic',
          has_custom_prompt: options.hasCustomPrompt || false,
          success: options.success !== false,
          duration_ms: options.durationMs || 0,
          options_count: options.optionsCount || 0,
          tone: options.tone || null,
          language: options.language || 'fr',
          emotion: options.emotion || null,
          emotionIntensity: options.emotionIntensity || null,
          style: options.style || null,
          error: options.error || null,
          timestamp: new Date().toISOString()
        });
      }
    };
    self.posthogClient = posthogClient;
    console.log('✅ PostHog client wrapper créé dans background');
  }
} catch (err) {
  console.warn('Failed to load PostHog:', err);
}

// Valeurs par défaut (seront mises à jour après import)
let BACKEND_URL = API_CONFIG.AI_SERVICE_URL;
let USER_SERVICE_URL = API_CONFIG.USER_SERVICE_URL;
const REQUEST_TIMEOUT = 15000;
const RETRY_COUNT = 2;
const EXTENSION_ID = chrome.runtime.id; // DYNAMIQUE

// Charger la configuration depuis le backend
async function loadBackendConfig() {
  try {
    const response = await fetch(`${BACKEND_URL}/config/complete`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
      credentials: 'omit'
    });

    if (response.ok) {
      const config = await response.json();
      if (config.urls) {
        // Ignorer les placeholders (commençant par __)
        const isPlaceholder = (url) => url && url.startsWith('__');

        if (config.urls.backend && !isPlaceholder(config.urls.backend)) {
          BACKEND_URL = config.urls.backend;
        }
        if (config.urls.user_service && !isPlaceholder(config.urls.user_service)) {
          USER_SERVICE_URL = config.urls.user_service;
        }
        console.log('✅ Configuration backend chargée (URLs effectives):', { BACKEND_URL, USER_SERVICE_URL });
      }
      return config;
    }
  } catch (error) {
    console.warn('⚠️ Impossible de charger la configuration backend:', error);
  }
  return null;
}

// État global
let isAuthenticated = false;

// Vérifier l'authentification
async function checkAuthentication() {
  try {
    // Obtenir un token sans interaction
    const token = await new Promise((resolve) => {
      chrome.identity.getAuthToken({ interactive: false }, (token) => {
        if (chrome.runtime.lastError) {
          resolve(null);
        } else {
          resolve(token);
        }
      });
    });

    isAuthenticated = !!token;

    // Si authentifié, récupérer et stocker le profil utilisateur
    if (isAuthenticated && token) {
      await fetchAndStoreUserProfile(token);
    }

    return isAuthenticated;
  } catch (error) {
    console.error('❌ Erreur vérification auth:', error);
    isAuthenticated = false;
    return false;
  }
}

// Récupérer le profil utilisateur Google et le stocker
async function fetchAndStoreUserProfile(token) {
  try {
    // Récupérer le profil Google
    const response = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.ok) {
      const userData = await response.json();
      console.log('📊 Profil utilisateur Google récupéré:', userData.email);

      // Récupérer le plan utilisateur depuis le user-service
      let userPlan = 'FREE';
      try {
        // D'abord, vérifier/créer l'utilisateur et obtenir le JWT
        console.log('🔐 Vérification utilisateur Google...');
        const verifyResponse = await fetch(`${USER_SERVICE_URL}/api/users/verify-google`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            google_id: userData.id || userData.sub,
            email: userData.email,
            name: userData.name
          })
        });

        if (!verifyResponse.ok) {
          console.warn('⚠️ Erreur verify-google:', verifyResponse.status);
          throw new Error('Erreur verification Google');
        }

        // Ensuite, se connecter pour obtenir le JWT
        console.log('🔑 Récupération du JWT...');
        const authResponse = await fetch(`${USER_SERVICE_URL}/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ google_token: token })
        });

        if (!authResponse.ok) {
          console.warn('⚠️ Erreur auth/login:', authResponse.status);
          throw new Error('Erreur authentification backend');
        }

        const authData = await authResponse.json();
        const jwtToken = authData.access_token;
        console.log('✅ JWT obtenu');

        // Maintenant, récupérer le quota avec le JWT
        const quotaResponse = await fetch(`${USER_SERVICE_URL}/api/users/quota-status`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${jwtToken}`,
            'Content-Type': 'application/json'
          },
          mode: 'cors'
        });

        if (quotaResponse.ok) {
          const quotaData = await quotaResponse.json();
          userPlan = quotaData.role || 'FREE';
          console.log('✅ Plan utilisateur récupéré:', userPlan);

          // Stocker l'user_id pour PostHog
          if (quotaData.user_id) {
            await chrome.storage.local.set({
              user_id: quotaData.user_id
            });
          }
        } else {
          console.warn('⚠️ Erreur quota-status:', quotaResponse.status);
        }
      } catch (e) {
        console.warn('⚠️ Impossible de récupérer le plan utilisateur:', e);
      }

      // Stocker dans chrome.storage.local (sans email pour PostHog)
      await chrome.storage.local.set({
        user_name: userData.name || null,
        user_plan: userPlan,
        user_picture: userData.picture || null
      });

      // V3 Story 2.1 — Synchroniser le cache blacklist au login (Premium uniquement)
      if (userPlan === 'PREMIUM') {
        try {
          await syncBlacklistCache(null);
          console.log('✅ Blacklist cache synchronise au login');
        } catch (e) {
          console.warn('⚠️ Erreur sync blacklist au login:', e);
        }
      }

      // Identifier l'utilisateur dans PostHog avec userId anonyme (SHA256)
      if (posthogClient && typeof posthog !== 'undefined') {
        try {
          // Récupérer le userId anonyme depuis le storage
          const storageLocal = await chrome.storage.local.get(['user_id', 'userId']);
          const storageSync = await chrome.storage.sync.get(['interfaceLanguage']);
          // Lire user_id en priorité, fallback sur userId
          const userId = storageLocal.user_id || storageLocal.userId;
          const interfaceLang = storageSync.interfaceLanguage || 'fr';

          if (userId) {
            // Get current anonymous ID before aliasing
            const currentAnon = posthog.get_distinct_id();

            // Alias the anonymous session to the user ID
            if (currentAnon && currentAnon !== userId) {
              try {
                posthog.alias(currentAnon, userId);
                console.log('🔗 PostHog alias created (background):', currentAnon, '->', userId);
              } catch (e) {
                console.warn('PostHog alias failed:', e);
              }
            }

            // Utiliser userId anonyme comme distinct_id (SANS email)
            posthogClient.identify(userId, {
              plan: userPlan,
              interface_lang: interfaceLang
            });

            // Set person properties
            posthogClient.setPersonProperties({
              plan: userPlan,
              interface_lang: interfaceLang
            });

            console.log('📊 PostHog - Utilisateur identifié avec userId anonyme:', userId);
          } else {
            console.warn('⚠️ userId anonyme non disponible');
          }
        } catch (e) {
          console.warn('PostHog identification failed:', e);
        }
      }
    }
  } catch (error) {
    console.error('❌ Erreur récupération profil utilisateur:', error);
  }
}

// Faire une requête au backend avec retry
async function makeBackendRequest(endpoint, data, token) {
  for (let attempt = 1; attempt <= RETRY_COUNT; attempt++) {
    try {
      console.log(`🔄 Tentative ${attempt}/${RETRY_COUNT} vers ${endpoint}`);

      // Récupérer le userId anonyme et le plan depuis le storage
      let userId = null;
      let userPlan = 'FREE';
      try {
        const storage = await chrome.storage.local.get(['user_id', 'userId', 'user_plan']);
        // Lire user_id en priorité, fallback sur userId
        userId = storage.user_id || storage.userId || null;
        userPlan = storage.user_plan || 'FREE';
      } catch (e) {
        console.warn('⚠️ Impossible de récupérer userId/plan:', e);
      }

      // Ajouter userId et plan aux données
      const requestData = {
        ...data,
        user_id: userId,
        plan: userPlan
      };

      // Timeout adapté : 45s pour le scraping des news, 15s pour le reste
      const timeout = endpoint === '/news/register' ? 45000 : REQUEST_TIMEOUT;

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'Origin': `chrome-extension://${chrome.runtime.id}`
        },
        body: JSON.stringify(requestData),
        mode: 'cors',
        credentials: 'omit',
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      
      if (!response.ok) {
        if (response.status === 401) {
          // Token invalide, nettoyer et retourner erreur
          chrome.identity.removeCachedAuthToken({ token }, () => {
            console.log('🧹 Token invalide nettoyé');
          });
          throw new Error('Authentification requise. Veuillez vous reconnecter.');
        }
        if (response.status === 404) {
          throw new Error(`Endpoint non trouvé: ${endpoint}`);
        }
        if (response.status === 500) {
          const errorText = await response.text().catch(() => 'Erreur serveur interne');
          throw new Error(`Erreur serveur (${response.status}): ${errorText}`);
        }
        throw new Error(`HTTP ${response.status}`);
      }
      
      return await response.json();
      
    } catch (error) {
      console.error(`❌ Erreur tentative ${attempt}:`, error);
      
      if (attempt === RETRY_COUNT) {
        throw error;
      }
      
      // Attendre avant de réessayer
      await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
    }
  }
}

// Gestionnaire de messages universel (MV3)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('📨 Message reçu:', request.action);

  // Gestion d'erreur pour toutes les actions
  try {
    switch (request.action) {
      case 'checkAuthentication':
        checkAuthentication()
          .then(authenticated => sendResponse({ ok: true, authenticated }))
          .catch(error => sendResponse({ ok: false, authenticated: false }));
        return true;
      
    case 'generateThreeComments':
      handleGenerateComments(request.data, sendResponse);
      return true;
      
    case 'generateThreeCommentsWithPrompt':
      handleGenerateCommentsWithPrompt(request.data, sendResponse);
      return true;
      
    case 'resizeComment':
      handleResizeComment(request.data, sendResponse);
      return true;
      
    case 'refineComment':
      handleRefineComment(request.data, sendResponse);
      return true;
      
    case 'checkQuota':
      handleCheckQuota(request.data, sendResponse);
      return true;

    case 'getQuotaInfo':
      handleGetQuotaInfo(sendResponse);
      return true;

    case 'registerNews':
      handleRegisterNews(request.data, sendResponse);
      return true;

    // V3 Story 2.1 — Actions Blacklist
    case 'addToBlacklist':
      handleAddToBlacklist(request.blockedName, request.blockedProfileUrl, sendResponse);
      return true;

    case 'getBlacklist':
      handleGetBlacklist(sendResponse);
      return true;

    case 'syncBlacklistCache':
      syncBlacklistCache(sendResponse);
      return true;

	case 'authStateChanged':
	  // Gérer le changement d'état d'authentification
	  if (request.authenticated) {
	    // Connexion : récupérer et stocker le profil utilisateur
	    getAuthToken().then(token => {
	      if (token) {
	        fetchAndStoreUserProfile(token);
	      }
	    });
	  } else {
	    // Déconnexion : nettoyer les données utilisateur
	    chrome.storage.local.remove(['user_id', 'user_email', 'user_name', 'user_plan', 'user_picture'], () => {
	      console.log('🧹 Données utilisateur nettoyées');
	    });

	    // Reset PostHog
	    if (posthogClient && posthogClient.reset) {
	      try {
	        posthogClient.reset();
	        console.log('📊 PostHog reset (déconnexion)');
	      } catch (e) {
	        console.warn('PostHog reset failed:', e);
	      }
	    }
	  }

	  // Relayer vers tous les content scripts
	  chrome.tabs.query({ url: "*://*.linkedin.com/*" }, function(tabs) {
        for (const tab of tabs) {
          chrome.tabs.sendMessage(tab.id, request);
        }
	  });
	break;

      default:
        // Réponse par défaut pour les actions inconnues
        sendResponse({ ok: true, message: 'Action non reconnue: ' + request.action });
        return false;
    }
  } catch (error) {
    console.error('❌ Erreur dans le gestionnaire de messages:', error);
    sendResponse({ error: error.message, ok: false });
    return false;
  }
});

// Gestionnaires spécifiques
async function handleGenerateComments(data, sendResponse) {
  const startTime = Date.now();
  try {
    // Vérifier l'authentification
    const token = await getAuthToken();
    if (!token) {
      sendResponse({ error: 'Authentification requise' });
      return;
    }

    // Ajouter les paramètres depuis le storage
    const settings = await chrome.storage.sync.get(['tone', 'length', 'optionsCount', 'commentLanguage']);

    // Fusion des paramètres : contextuels (data) + globaux (settings)
    // Les paramètres contextuels (emotion, intensity, style) sont prioritaires
    const requestData = {
      ...data,  // Contient: post, isComment, commentLanguage, emotion, intensity, style, newsContext
      // Paramètres globaux du popup (utilisés comme fallback)
      tone: settings.tone || 'professionnel',
      length: settings.length || 15,
      optionsCount: settings.optionsCount || 2,
      commentLanguage: data.commentLanguage || settings.commentLanguage || 'fr'
    };

    console.log('📦 Requête backend (paramètres fusionnés):', {
      emotion: requestData.emotion,
      intensity: requestData.intensity,
      style: requestData.style,
      tone: requestData.tone,
      length: requestData.length,
      newsCount: requestData.newsContext ? requestData.newsContext.length : 0
    });

    // Track comment generation started
    if (posthogClient) {
      try {
        posthogClient.trackCommentGenerationStarted({
          generationType: 'automatic',
          tone: requestData.tone,
          language: requestData.commentLanguage,
          isComment: requestData.isComment || false,
          hasCustomPrompt: false,
          emotion: requestData.emotion || null,
          emotionIntensity: requestData.intensity || null,
          style: requestData.style || null,
          newsEnrichment: requestData.newsContext ? 'enabled' : 'disabled',
          length: requestData.length,
          optionsCount: requestData.optionsCount
        });
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }

    // Faire la requête
    const result = await makeBackendRequest('/generate-comments', requestData, token);

    const durationMs = Date.now() - startTime;

    // Track comment generation success
    if (posthogClient) {
      try {
        posthogClient.trackCommentGenerated({
          generationType: 'automatic',
          success: true,
          durationMs: durationMs,
          optionsCount: requestData.optionsCount,
          tone: requestData.tone,
          language: requestData.commentLanguage,
          emotion: requestData.emotion || null,
          emotionIntensity: requestData.intensity || null,
          style: requestData.style || null
        });
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }

    sendResponse({ comments: result.comments });

  } catch (error) {
    console.error('❌ Erreur génération:', error);

    const durationMs = Date.now() - startTime;

    // Track comment generation error
    if (posthogClient) {
      try {
        posthogClient.trackCommentGenerated({
          generationType: 'automatic',
          success: false,
          durationMs: durationMs,
          error: error.message
        });
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }

    sendResponse({ error: error.message });
  }
}

async function handleGenerateCommentsWithPrompt(data, sendResponse) {
  const startTime = Date.now();
  try {
    const token = await getAuthToken();
    if (!token) {
      sendResponse({ error: 'Authentification requise' });
      return;
    }

    const settings = await chrome.storage.sync.get(['tone', 'length', 'optionsCount', 'commentLanguage']);

    // Fusion des paramètres : contextuels (data) + globaux (settings)
    // Les paramètres contextuels (emotion, intensity, style) sont prioritaires
    const requestData = {
      ...data,  // Contient: post, userPrompt, isComment, commentLanguage, emotion, intensity, style, newsContext
      // Paramètres globaux du popup (utilisés comme fallback)
      tone: settings.tone || 'professionnel',
      length: settings.length || 15,
      optionsCount: settings.optionsCount || 2,
      commentLanguage: data.commentLanguage || settings.commentLanguage || 'fr'
    };

    console.log('📦 Requête backend avec prompt (paramètres fusionnés):', {
      emotion: requestData.emotion,
      intensity: requestData.intensity,
      style: requestData.style,
      tone: requestData.tone,
      length: requestData.length,
      hasPrompt: !!requestData.userPrompt,
      newsCount: requestData.newsContext ? requestData.newsContext.length : 0
    });

    // Track comment generation started with prompt
    if (posthogClient) {
      try {
        posthogClient.trackCommentGenerationStarted({
          generationType: 'with_prompt',
          tone: requestData.tone,
          language: requestData.commentLanguage,
          isComment: requestData.isComment || false,
          hasCustomPrompt: true,
          emotion: requestData.emotion || null,
          emotionIntensity: requestData.intensity || null,
          style: requestData.style || null,
          newsEnrichment: requestData.newsContext ? 'enabled' : 'disabled',
          length: requestData.length,
          optionsCount: requestData.optionsCount
        });
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }

    const result = await makeBackendRequest('/generate-comments-with-prompt', requestData, token);

    const durationMs = Date.now() - startTime;

    // Track comment generation success
    if (posthogClient) {
      try {
        posthogClient.trackCommentGenerated({
          generationType: 'with_prompt',
          success: true,
          durationMs: durationMs,
          optionsCount: requestData.optionsCount,
          tone: requestData.tone,
          language: requestData.commentLanguage,
          emotion: requestData.emotion || null,
          emotionIntensity: requestData.intensity || null,
          style: requestData.style || null
        });
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }

    sendResponse({ comments: result.comments });

  } catch (error) {
    console.error('❌ Erreur génération avec prompt:', error);

    const durationMs = Date.now() - startTime;

    // Track comment generation error
    if (posthogClient) {
      try {
        posthogClient.trackCommentGenerated({
          generationType: 'with_prompt',
          success: false,
          durationMs: durationMs,
          error: error.message
        });
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }

    sendResponse({ error: error.message });
  }
}

async function handleResizeComment(data, sendResponse) {
  try {
    const token = await getAuthToken();
    if (!token) {
      sendResponse({ error: 'Authentification requise' });
      return;
    }
    
    const settings = await chrome.storage.sync.get(['tone', 'commentLanguage']);
    const requestData = {
      ...data,
      tone: settings.tone || 'professionnel',
      commentLanguage: data.commentLanguage || settings.commentLanguage || 'fr'
    };
    
    const result = await makeBackendRequest('/resize-comment', requestData, token);
    sendResponse({ resizedComment: result.comment });
    
  } catch (error) {
    console.error('❌ Erreur redimensionnement:', error);
    sendResponse({ error: error.message });
  }
}

async function handleRefineComment(data, sendResponse) {
  try {
    const token = await getAuthToken();
    if (!token) {
      sendResponse({ error: 'Authentification requise' });
      return;
    }
    
    const settings = await chrome.storage.sync.get(['tone', 'length', 'commentLanguage']);
    const requestData = {
      ...data,
      tone: settings.tone || 'professionnel',
      length: settings.length || 15,
      commentLanguage: data.commentLanguage || settings.commentLanguage || 'fr'
    };
    
    const result = await makeBackendRequest('/refine-comment', requestData, token);
    sendResponse({ refinedComment: result.comment });
    
  } catch (error) {
    console.error('❌ Erreur affinement:', error);
    sendResponse({ error: error.message });
  }
}

async function handleCheckQuota(data, sendResponse) {
  try {
    const token = await getAuthToken();
    if (!token) {
      sendResponse({ hasQuota: false, message: 'Authentification requise' });
      return;
    }

    // Appel à l'endpoint quota du user-service
    try {
      const response = await fetch(`${USER_SERVICE_URL}/api/users/quota-status`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        mode: 'cors'
      });

      if (response.ok) {
        const quotaData = await response.json();
        sendResponse({
          hasQuota: quotaData.remaining > 0,
          remaining: quotaData.remaining,
          limit: quotaData.daily_limit,
          role: quotaData.role || 'FREE',
          message: quotaData.remaining === 0 ? 'Limite quotidienne atteinte' : null
        });
      } else {
        // Fallback en cas d'erreur API
        sendResponse({
          hasQuota: true,
          remaining: 5,
          limit: 5,
          role: 'FREE'
        });
      }
    } catch (apiError) {
      console.warn('⚠️ User-service non disponible, utilisation des données par défaut');
      sendResponse({
        hasQuota: true,
        remaining: 5,
        limit: 5,
        role: 'FREE'
      });
    }


  } catch (error) {
    console.error('❌ Erreur vérification quota:', error);
    // En cas d'erreur, on autorise pour ne pas bloquer l'utilisateur
    sendResponse({
      hasQuota: true,
      remaining: 5,
      limit: 5,
      role: 'FREE',
      message: error.message
    });
  }
}

async function handleGetQuotaInfo(sendResponse) {
  try {
    const token = await getAuthToken();
    if (!token) {
      console.log('❌ handleGetQuotaInfo: No token');
      sendResponse({ error: 'Not authenticated' });
      return;
    }

    // Récupérer les informations utilisateur depuis le storage local
    const userInfo = await chrome.storage.local.get(['user_email', 'user_name', 'user_plan', 'user_picture']);
    console.log('📦 handleGetQuotaInfo: Storage data:', userInfo);

    // Obtenir un JWT pour accéder au backend
    let jwtToken = token; // Par défaut, utiliser le token Google (au cas où)
    try {
      // Récupérer les infos utilisateur Google
      const googleResponse = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (googleResponse.ok) {
        await googleResponse.json(); // Consommer la réponse

        // Authentifier avec le backend pour obtenir le JWT
        const authResponse = await fetch(`${USER_SERVICE_URL}/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ google_token: token })
        });

        if (authResponse.ok) {
          const authData = await authResponse.json();
          jwtToken = authData.access_token;
          console.log('✅ handleGetQuotaInfo: JWT obtenu');
        } else {
          console.warn('⚠️ handleGetQuotaInfo: Impossible d\'obtenir le JWT, utilisation du token Google');
        }
      }
    } catch (jwtError) {
      console.warn('⚠️ handleGetQuotaInfo: Erreur JWT:', jwtError);
    }

    // Récupérer le quota depuis le user-service
    try {
      const response = await fetch(`${USER_SERVICE_URL}/api/users/quota-status`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${jwtToken}`,
          'Content-Type': 'application/json'
        },
        mode: 'cors'
      });

      if (response.ok) {
        const quotaData = await response.json();
        console.log('✅ handleGetQuotaInfo: Backend quota data:', quotaData);
        const finalRole = quotaData.role || userInfo.user_plan || 'FREE';
        console.log('🎫 handleGetQuotaInfo: Final role:', finalRole);
        sendResponse({
          email: userInfo.user_email || null,
          name: userInfo.user_name || null,
          picture: userInfo.user_picture || null,
          role: finalRole,
          remaining: quotaData.remaining || 0,
          limit: quotaData.daily_limit || 5
        });
      } else {
        console.warn('⚠️ handleGetQuotaInfo: Backend error', response.status);
        // Fallback avec les données du storage
        sendResponse({
          email: userInfo.user_email || null,
          name: userInfo.user_name || null,
          picture: userInfo.user_picture || null,
          role: userInfo.user_plan || 'FREE',
          remaining: 5,
          limit: 5
        });
      }
    } catch (apiError) {
      console.warn('⚠️ User-service non disponible, utilisation des données du storage');
      sendResponse({
        email: userInfo.user_email || null,
        name: userInfo.user_name || null,
        picture: userInfo.user_picture || null,
        role: userInfo.user_plan || 'FREE',
        remaining: 5,
        limit: 5
      });
    }
  } catch (error) {
    console.error('❌ Erreur récupération info utilisateur:', error);
    sendResponse({ error: error.message });
  }
}

async function handleRegisterNews(data, sendResponse) {
  try {
    // Vérifier l'authentification
    const token = await getAuthToken();
    if (!token) {
      console.error('❌ Authentification requise pour enregistrer les actualités');
      sendResponse({
        success: false,
        error: 'Authentification requise'
      });
      return;
    }

    // Valider les données
    if (!data.urls || !Array.isArray(data.urls) || data.urls.length === 0) {
      console.error('❌ Aucune URL fournie');
      sendResponse({
        success: false,
        error: 'Aucune URL fournie'
      });
      return;
    }

    // Préparer la requête
    // Le backend attend un tableau de strings (URLs uniquement)
    // Si data.urls contient des objets {title, url}, extraire uniquement les URLs
    const urls = Array.isArray(data.urls)
      ? data.urls.map(item => typeof item === 'string' ? item : item.url)
      : [];

    const requestData = {
      urls: urls,
      lang: data.lang || 'fr'
    };

    console.log(`📰 Enregistrement de ${urls.length} actualité(s) LinkedIn...`);
    console.log('🌍 Langue:', requestData.lang);
    console.log('📋 URLs:', urls);

    // Faire la requête vers le backend
    const result = await makeBackendRequest('/news/register', requestData, token);

    // Log des résultats
    const registered = result.registered || 0;
    const skipped = result.skipped || 0;
    const total = registered + skipped;

    if (registered > 0 && skipped > 0) {
      console.log(`✅ ${registered} actualité(s) enregistrée(s), ${skipped} ignorée(s) (déjà existante(s))`);
    } else if (registered > 0) {
      console.log(`✅ ${registered} actualité(s) enregistrée(s) avec succès`);
    } else if (skipped > 0) {
      console.log(`⚠️ ${skipped} actualité(s) ignorée(s) (déjà existante(s))`);
    }

    // Retourner le résultat au content script
    sendResponse({
      success: true,
      registered: result.registered,
      skipped: result.skipped,
      results: result.results
    });

  } catch (error) {
    console.error('❌ Erreur lors de l\'enregistrement des actualités:', error);

    // Gérer les erreurs spécifiques
    let errorMessage = error.message;
    if (error.message.includes('timeout') || error.message.includes('aborted')) {
      errorMessage = 'Timeout: Le scraping des actualités a pris trop de temps (>15s)';
    } else if (error.message.includes('Authentification requise')) {
      errorMessage = 'Session expirée. Veuillez vous reconnecter.';
    } else if (error.message.includes('Endpoint non trouvé')) {
      errorMessage = 'Module actualités non disponible sur le backend';
    }

    sendResponse({
      success: false,
      error: errorMessage
    });
  }
}

// V3 Story 2.1 — Ajouter a la blacklist
async function handleAddToBlacklist(blockedName, blockedProfileUrl, sendResponse) {
  try {
    const token = await getAuthToken();
    if (!token) {
      sendResponse({ success: false, error: 'not_authenticated' });
      return;
    }

    // Obtenir le JWT
    const authResponse = await fetch(`${USER_SERVICE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ google_token: token })
    });

    if (!authResponse.ok) {
      sendResponse({ success: false, error: 'auth_failed' });
      return;
    }

    const authData = await authResponse.json();
    const jwtToken = authData.access_token;

    const response = await fetch(`${USER_SERVICE_URL}/api/blacklist`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${jwtToken}`
      },
      body: JSON.stringify({
        blocked_name: blockedName,
        blocked_profile_url: blockedProfileUrl || null
      })
    });

    if (!response.ok) {
      const error = await response.json();
      // Support structured error response: {code, message} or plain string
      const errorDetail = error.detail;
      const errorCode = typeof errorDetail === 'object' ? errorDetail.code : null;
      const errorMessage = typeof errorDetail === 'object' ? errorDetail.message : errorDetail;
      sendResponse({ success: false, error: errorMessage || 'unknown_error', errorCode: errorCode });
      return;
    }

    const entry = await response.json();

    // Mettre a jour le cache local
    await updateBlacklistCache(entry, 'add');

    console.log('✅ Blacklist: ajout de', blockedName);
    sendResponse({ success: true, entry });
  } catch (error) {
    console.error('❌ addToBlacklist error:', error);
    sendResponse({ success: false, error: error.message });
  }
}

// V3 Story 2.1 — Recuperer la blacklist (depuis cache local)
async function handleGetBlacklist(sendResponse) {
  try {
    const cached = await chrome.storage.local.get('blacklist_cache');
    if (cached.blacklist_cache && cached.blacklist_cache.entries) {
      sendResponse({ success: true, entries: cached.blacklist_cache.entries, fromCache: true });
      return;
    }

    // Si pas de cache, sync depuis le backend
    syncBlacklistCache((result) => {
      if (result.success) {
        sendResponse({ success: true, entries: result.entries, fromCache: false });
      } else {
        sendResponse({ success: false, error: result.error, entries: [] });
      }
    });
  } catch (error) {
    console.error('❌ getBlacklist error:', error);
    sendResponse({ success: false, error: error.message, entries: [] });
  }
}

// V3 Story 2.1 — Synchroniser le cache blacklist depuis le backend
async function syncBlacklistCache(sendResponse) {
  try {
    const token = await getAuthToken();
    if (!token) {
      if (sendResponse) sendResponse({ success: false, error: 'not_authenticated' });
      return;
    }

    // Obtenir le JWT
    const authResponse = await fetch(`${USER_SERVICE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ google_token: token })
    });

    if (!authResponse.ok) {
      if (sendResponse) sendResponse({ success: false, error: 'auth_failed' });
      return;
    }

    const authData = await authResponse.json();
    const jwtToken = authData.access_token;

    const response = await fetch(`${USER_SERVICE_URL}/api/blacklist`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${jwtToken}`
      }
    });

    if (!response.ok) {
      // 403 = pas Premium, retourner liste vide sans erreur
      if (response.status === 403) {
        await chrome.storage.local.set({
          blacklist_cache: {
            entries: [],
            count: 0,
            synced_at: Date.now()
          }
        });
        if (sendResponse) sendResponse({ success: true, entries: [] });
        return;
      }
      const error = await response.json();
      if (sendResponse) sendResponse({ success: false, error: error.detail || 'unknown_error' });
      return;
    }

    const data = await response.json();

    // Sauvegarder dans le cache local
    await chrome.storage.local.set({
      blacklist_cache: {
        entries: data.entries,
        count: data.count,
        synced_at: Date.now()
      }
    });

    console.log('✅ Blacklist cache synchronise:', data.count, 'entrees');
    if (sendResponse) sendResponse({ success: true, entries: data.entries });
  } catch (error) {
    console.error('❌ syncBlacklistCache error:', error);
    if (sendResponse) sendResponse({ success: false, error: error.message });
  }
}

// V3 Story 2.1 — Mettre a jour le cache local
async function updateBlacklistCache(entry, action) {
  try {
    const cached = await chrome.storage.local.get('blacklist_cache');
    let entries = cached.blacklist_cache?.entries || [];

    if (action === 'add') {
      entries.unshift(entry); // Ajouter au debut
    } else if (action === 'remove') {
      entries = entries.filter(e => e.id !== entry.id);
    }

    await chrome.storage.local.set({
      blacklist_cache: {
        entries,
        count: entries.length,
        synced_at: Date.now()
      }
    });
  } catch (error) {
    console.error('❌ updateBlacklistCache error:', error);
  }
}

// Obtenir un token d'authentification
async function getAuthToken() {
  return new Promise((resolve) => {
    chrome.identity.getAuthToken({ interactive: false }, (token) => {
      if (chrome.runtime.lastError) {
        console.log('❌ Pas de token disponible');
        resolve(null);
      } else {
        resolve(token);
      }
    });
  });
}

// Fonction d'initialisation commune
async function initializeExtension() {
  console.log('🚀 Extension initialisée');
  console.log('Extension ID:', chrome.runtime.id);
  console.log('Extension ID configuré:', EXTENSION_ID);
  
  // Mettre à jour les URLs depuis API_CONFIG
  BACKEND_URL = API_CONFIG.AI_SERVICE_URL;
  USER_SERVICE_URL = API_CONFIG.USER_SERVICE_URL;
  
  // Charger la configuration au démarrage
  await loadBackendConfig();
  
  if (chrome.runtime.id !== EXTENSION_ID) {
    console.warn('⚠️ ATTENTION: Extension ID différent du configuré!');
  }
  
  await checkAuthentication();
}

// Vérification initiale
chrome.runtime.onStartup.addListener(async () => {
  await initializeExtension();
  console.log('État authentification:', isAuthenticated);
});

chrome.runtime.onInstalled.addListener(async () => {
  await initializeExtension();
  console.log('État authentification:', isAuthenticated);
});

console.log('🚀 LinkedIn AI Commenter Background Script chargé');
console.log('Backend URL:', BACKEND_URL);
console.log('Extension ID:', chrome.runtime.id);