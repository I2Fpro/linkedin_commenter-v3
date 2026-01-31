// ==================== POPUP NEW - LinkedIn AI Commenter ====================
// Nouveau popup avec design gaming moderne

document.addEventListener('DOMContentLoaded', async function() {
  console.log('🚀 Popup LinkedIn AI Commenter (New Design)');

  // ==================== CONSTANTES ====================
  const LANGUAGES = ['fr', 'en'];
  const TONES = ['professionnel', 'soutenu', 'amical', 'expert', 'informatif', 'negatif'];
  const LENGTHS = [7, 15, 30];
  const GENERATIONS = [1, 2, 3];

  // ==================== STATE ====================
  let currentState = {
    interfaceLanguage: 'fr',
    commentLanguage: 'fr',
    tone: 'professionnel',
    length: 15,
    optionsCount: 2,
    newsEnrichmentMode: 'title-only',
    autoCloseEmotionsPanel: false,
    isAuthenticated: false,
    userData: null,
    planData: null,
    quotaData: null
  };

  // ==================== ÉLÉMENTS DOM ====================

  // Header
  const extensionTitle = document.getElementById('extensionTitle');
  const closeBtn = document.getElementById('closeBtn');
  const versionNumber = document.getElementById('versionNumber');

  // Onglets principaux
  const mainTabs = document.querySelectorAll('.main-tab');
  const tabContents = document.querySelectorAll('.tab-content');

  // Sous-onglets
  const subTabs = document.querySelectorAll('.sub-tab');
  const subContents = document.querySelectorAll('.sub-content');

  // Compte
  const userCardUnauthenticated = document.getElementById('userCardUnauthenticated');
  const userCardAuthenticated = document.getElementById('userCardAuthenticated');
  const googleSignInBtn = document.getElementById('googleSignInBtn');
  const logoutBtn = document.getElementById('logoutBtn');
  const userAvatar = document.getElementById('userAvatar');
  const userName = document.getElementById('userName');
  const userEmail = document.getElementById('userEmail');
  const userPlanBadge = document.getElementById('userPlanBadge');
  const quotaDisplay = document.getElementById('quotaDisplay');
  const quotaValue = document.getElementById('quotaValue');
  const quotaProgress = document.getElementById('quotaProgress');
  const upgradeBtn = document.getElementById('upgradeBtn');
  const manageSubscriptionBtn = document.getElementById('manageSubscriptionBtn');
  const accountBadge = document.getElementById('accountBadge');

  // Toggles authentification
  const authOnBtn = document.getElementById('authOnBtn');
  const authOffBtn = document.getElementById('authOffBtn');

  // Langue
  const interfaceLangPrev = document.getElementById('interfaceLangPrev');
  const interfaceLangNext = document.getElementById('interfaceLangNext');
  const interfaceLangValue = document.getElementById('interfaceLangValue');
  const commentLangPrev = document.getElementById('commentLangPrev');
  const commentLangNext = document.getElementById('commentLangNext');
  const commentLangValue = document.getElementById('commentLangValue');

  // Plus
  const newsOnBtn = document.getElementById('newsOnBtn');
  const newsOffBtn = document.getElementById('newsOffBtn');
  const smartOnBtn = document.getElementById('smartOnBtn');
  const smartOffBtn = document.getElementById('smartOffBtn');
  const newsInfoBox = document.getElementById('newsInfoBox');
  const newsInfoText = document.getElementById('newsInfoText');

  const autoCloseOnBtn = document.getElementById('autoCloseOnBtn');
  const autoCloseOffBtn = document.getElementById('autoCloseOffBtn');

  const tonePrev = document.getElementById('tonePrev');
  const toneNext = document.getElementById('toneNext');
  const toneValue = document.getElementById('toneValue');
  const lengthPrev = document.getElementById('lengthPrev');
  const lengthNext = document.getElementById('lengthNext');
  const lengthValue = document.getElementById('lengthValue');
  const generationsPrev = document.getElementById('generationsPrev');
  const generationsNext = document.getElementById('generationsNext');
  const generationsValue = document.getElementById('generationsValue');

  // ==================== VÉRIFICATION API CONFIG ====================
  if (typeof API_CONFIG === 'undefined') {
    console.warn('⚠️ API_CONFIG non disponible, utilisation de valeurs par défaut');
    window.API_CONFIG = {
      AI_SERVICE_URL: 'http://localhost:8443',
      USER_SERVICE_URL: 'http://localhost:8444',
      REQUEST_TIMEOUT: 15000
    };
  }

  // ==================== ATTENDRE MODULES ====================
  async function waitForModules() {
    for (let i = 0; i < 10; i++) {
      if (window.googleAuth && window.extensionConfig && window.i18n) {
        return true;
      }
      await new Promise(resolve => setTimeout(resolve, 200));
    }
    return false;
  }

  // ==================== INITIALISATION ====================
  async function initialize() {
    // Charger le titre avec version
    const manifest = chrome.runtime.getManifest();
    extensionTitle.textContent = `${manifest.name}`;
    versionNumber.textContent = `${manifest.version}`;

    // Attendre que les modules soient chargés
    const modulesReady = await waitForModules();
    if (!modulesReady) {
      console.error('❌ Modules non chargés');
      return;
    }

    // Initialiser i18n
    await window.i18n.init();

    // Initialiser l'authentification
    await window.googleAuth.initialize();

    // Charger les paramètres
    await loadSettings();

    // Mettre à jour l'UI
    await updateUI();

    // Tester la connectivité backend
    await window.extensionConfig.checkBackendConnectivity();

    // Track settings opened and usage session start
    if (typeof posthogClient !== 'undefined') {
      try {
        posthogClient.trackSettingsOpened();
        posthogClient.trackUsageSessionStart();
        window.sessionStartTime = Date.now();
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }

    console.log('✅ Popup initialisé avec succès');
  }

  // ==================== GESTION ONGLETS PRINCIPAUX ====================
  mainTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetTab = tab.dataset.tab;

      // Désactiver tous les onglets
      mainTabs.forEach(t => t.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));

      // Activer l'onglet cliqué
      tab.classList.add('active');
      document.getElementById(`${targetTab}-content`).classList.add('active');

      // Track tab change
      if (typeof posthogClient !== 'undefined') {
        try {
          posthogClient.trackFeatureUsed('tab_navigation', {
            tab_name: targetTab,
            tab_type: 'main'
          });
        } catch (e) {
          console.warn('PostHog tracking failed:', e);
        }
      }
    });
  });

  // ==================== GESTION SOUS-ONGLETS ====================
  subTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetSubTab = tab.dataset.subtab;

      // Désactiver tous les sous-onglets
      subTabs.forEach(t => t.classList.remove('active'));
      subContents.forEach(c => c.classList.remove('active'));

      // Activer le sous-onglet cliqué
      tab.classList.add('active');
      document.getElementById(`${targetSubTab}-content`).classList.add('active');

      // Track subtab change
      if (typeof posthogClient !== 'undefined') {
        try {
          posthogClient.trackFeatureUsed('tab_navigation', {
            tab_name: targetSubTab,
            tab_type: 'sub'
          });
        } catch (e) {
          console.warn('PostHog tracking failed:', e);
        }
      }
    });
  });

  // ==================== BOUTON FERMER ====================
  closeBtn.addEventListener('click', () => {
    // Track popup closed and usage session end
    if (typeof posthogClient !== 'undefined') {
      try {
        posthogClient.trackFeatureUsed('settings', { action: 'closed' });

        // Track session end with duration
        if (window.sessionStartTime) {
          const sessionDuration = Date.now() - window.sessionStartTime;
          posthogClient.trackUsageSessionEnd(sessionDuration);
        }
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }
    window.close();
  });

  // ==================== AUTHENTIFICATION ====================

  // Connexion Google
  googleSignInBtn.addEventListener('click', async () => {
    try {
      googleSignInBtn.disabled = true;
      googleSignInBtn.innerHTML = '<span>⏳</span> <span data-i18n="generating">Connexion...</span>';

      const success = await window.googleAuth.signIn();
      if (success) {
        await updateUI();
        await loadSettings();

        // Notifier le background script
        chrome.runtime.sendMessage({ action: 'authStateChanged', authenticated: true }, (response) => {
          if (chrome.runtime.lastError) {
            console.warn('⚠️ Erreur lors de la notification au background:', chrome.runtime.lastError.message);
          }
        });

        // Track user authentication (le tracking détaillé est dans auth.js)
        if (typeof posthogClient !== 'undefined') {
          try {
            const userData = window.googleAuth.getUserData();
            if (userData) {
              posthogClient.trackUserAuthenticated(userData.email, {
                name: userData.name,
                plan: currentState.planData?.role || 'FREE'
              });
            }
          } catch (e) {
            console.warn('PostHog tracking failed:', e);
          }
        }

        // Afficher le badge de notification
        accountBadge.style.display = 'block';
        setTimeout(() => {
          accountBadge.style.display = 'none';
        }, 5000);

        // Toast de succès
        window.toastNotification.success(window.i18n.t('signInSuccess') || 'Connexion réussie !');
      }
    } catch (error) {
      console.error('❌ Erreur connexion:', error);
      window.toastNotification.error(window.i18n.t('error') + ': ' + error.message);
    } finally {
      googleSignInBtn.disabled = false;
      googleSignInBtn.innerHTML = '<span>🔐</span> <span data-i18n="signInWithGoogle">Se connecter avec Google</span>';
      window.i18n.updateInterface();
    }
  });

  // Déconnexion
  logoutBtn.addEventListener('click', async () => {
    try {
      logoutBtn.disabled = true;
      logoutBtn.innerHTML = '<span>⏳</span> <span data-i18n="logout">Déconnexion...</span>';

      const success = await window.googleAuth.signOut();
      if (success) {
        await updateUI();

        // Track user logout
        if (typeof posthogClient !== 'undefined') {
          try {
            posthogClient.trackUserLogout();
          } catch (e) {
            console.warn('PostHog tracking failed:', e);
          }
        }

        // Notifier le background script
        chrome.runtime.sendMessage({ action: 'authStateChanged', authenticated: false }, (response) => {
          if (chrome.runtime.lastError) {
            console.warn('⚠️ Erreur lors de la notification au background:', chrome.runtime.lastError.message);
          }
        });
      }
    } catch (error) {
      console.error('❌ Erreur déconnexion:', error);
    } finally {
      logoutBtn.disabled = false;
      logoutBtn.innerHTML = '<span>🚪</span> <span data-i18n="logout">Déconnexion</span>';
      window.i18n.updateInterface();
    }
  });

  // Toggles authentification (affichage uniquement)
  authOnBtn.addEventListener('click', () => {
    if (!currentState.isAuthenticated) {
      googleSignInBtn.click();
    }
  });

  authOffBtn.addEventListener('click', () => {
    if (currentState.isAuthenticated) {
      logoutBtn.click();
    }
  });

  // ==================== LANGUE ====================

  // Interface Language
  interfaceLangPrev.addEventListener('click', () => {
    const oldLanguage = currentState.interfaceLanguage;
    const currentIndex = LANGUAGES.indexOf(currentState.interfaceLanguage);
    const newIndex = (currentIndex - 1 + LANGUAGES.length) % LANGUAGES.length;
    currentState.interfaceLanguage = LANGUAGES[newIndex];
    updateLanguageDisplay();
    saveSettings();
    window.i18n.setLanguage(currentState.interfaceLanguage);
    updateTooltips();

    // Track interface language change
    if (typeof posthogClient !== 'undefined') {
      try {
        posthogClient.trackInterfaceLanguageChanged(currentState.interfaceLanguage, oldLanguage);
        posthogClient.trackInterfaceLanguageSet(currentState.interfaceLanguage);
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }
  });

  interfaceLangNext.addEventListener('click', () => {
    const oldLanguage = currentState.interfaceLanguage;
    const currentIndex = LANGUAGES.indexOf(currentState.interfaceLanguage);
    const newIndex = (currentIndex + 1) % LANGUAGES.length;
    currentState.interfaceLanguage = LANGUAGES[newIndex];
    updateLanguageDisplay();
    saveSettings();
    window.i18n.setLanguage(currentState.interfaceLanguage);
    updateTooltips();

    // Track interface language change
    if (typeof posthogClient !== 'undefined') {
      try {
        posthogClient.trackInterfaceLanguageChanged(currentState.interfaceLanguage, oldLanguage);
        posthogClient.trackInterfaceLanguageSet(currentState.interfaceLanguage);
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }
  });

  // Comment Language
  commentLangPrev.addEventListener('click', () => {
    const oldLanguage = currentState.commentLanguage;
    const currentIndex = LANGUAGES.indexOf(currentState.commentLanguage);
    const newIndex = (currentIndex - 1 + LANGUAGES.length) % LANGUAGES.length;
    currentState.commentLanguage = LANGUAGES[newIndex];
    updateLanguageDisplay();
    saveSettings();

    // Track comment language change
    if (typeof posthogClient !== 'undefined') {
      try {
        posthogClient.trackCommentLanguageChanged(currentState.commentLanguage, oldLanguage);
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }
  });

  commentLangNext.addEventListener('click', () => {
    const oldLanguage = currentState.commentLanguage;
    const currentIndex = LANGUAGES.indexOf(currentState.commentLanguage);
    const newIndex = (currentIndex + 1) % LANGUAGES.length;
    currentState.commentLanguage = LANGUAGES[newIndex];
    updateLanguageDisplay();
    saveSettings();

    // Track comment language change
    if (typeof posthogClient !== 'undefined') {
      try {
        posthogClient.trackCommentLanguageChanged(currentState.commentLanguage, oldLanguage);
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }
  });

  // ==================== ENRICHISSEMENT ====================

  // Toggle News
  newsOnBtn.addEventListener('click', () => {
    // Vérifier le plan utilisateur
    const role = currentState.planData?.role || 'FREE';
    if (role === 'FREE') {
      window.toastNotification.warning(window.i18n.t('newsRequiresMedium') || 'Cette fonctionnalité nécessite un plan MEDIUM ou supérieur');
      return;
    }

    const oldMode = currentState.newsEnrichmentMode;
    if (currentState.newsEnrichmentMode === 'disabled') {
      currentState.newsEnrichmentMode = 'title-only';
      updateNewsDisplay();
      saveSettings();

      // Track news enrichment change
      if (typeof posthogClient !== 'undefined') {
        try {
          posthogClient.trackNewsEnrichmentChanged(currentState.newsEnrichmentMode, oldMode, role);
        } catch (e) {
          console.warn('PostHog tracking failed:', e);
        }
      }
    }
  });

  newsOffBtn.addEventListener('click', () => {
    const oldMode = currentState.newsEnrichmentMode;
    const role = currentState.planData?.role || 'FREE';
    currentState.newsEnrichmentMode = 'disabled';
    updateNewsDisplay();
    saveSettings();

    // Track news enrichment change
    if (typeof posthogClient !== 'undefined') {
      try {
        posthogClient.trackNewsEnrichmentChanged(currentState.newsEnrichmentMode, oldMode, role);
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }
  });

  // Toggle Smart Summary
  smartOnBtn.addEventListener('click', () => {
    // Vérifier le plan utilisateur
    const role = currentState.planData?.role || 'FREE';
    if (role !== 'PREMIUM') {
      window.toastNotification.warning(window.i18n.t('smartRequiresPremium') || 'Cette fonctionnalité nécessite un plan PREMIUM');
      return;
    }

    const oldMode = currentState.newsEnrichmentMode;
    currentState.newsEnrichmentMode = 'smart-summary';
    updateNewsDisplay();
    saveSettings();

    // Track smart summary enabled
    if (typeof posthogClient !== 'undefined') {
      try {
        posthogClient.trackSmartSummaryToggled(true, role);
        posthogClient.trackNewsEnrichmentChanged(currentState.newsEnrichmentMode, oldMode, role);
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }
  });

  smartOffBtn.addEventListener('click', () => {
    const oldMode = currentState.newsEnrichmentMode;
    const role = currentState.planData?.role || 'FREE';
    if (currentState.newsEnrichmentMode === 'smart-summary') {
      currentState.newsEnrichmentMode = 'title-only';
      updateNewsDisplay();
      saveSettings();

      // Track smart summary disabled
      if (typeof posthogClient !== 'undefined') {
        try {
          posthogClient.trackSmartSummaryToggled(false, role);
          posthogClient.trackNewsEnrichmentChanged(currentState.newsEnrichmentMode, oldMode, role);
        } catch (e) {
          console.warn('PostHog tracking failed:', e);
        }
      }
    }
  });

  // ==================== AUTO-CLOSE EMOTIONS PANEL ====================

  autoCloseOnBtn.addEventListener('click', () => {
    currentState.autoCloseEmotionsPanel = true;
    updateAutoCloseDisplay();
    saveSettings();
  });

  autoCloseOffBtn.addEventListener('click', () => {
    currentState.autoCloseEmotionsPanel = false;
    updateAutoCloseDisplay();
    saveSettings();
  });

  // ==================== TON ====================

  tonePrev.addEventListener('click', () => {
    const oldTone = currentState.tone;
    const currentIndex = TONES.indexOf(currentState.tone);
    const newIndex = (currentIndex - 1 + TONES.length) % TONES.length;
    currentState.tone = TONES[newIndex];
    updateToneDisplay();
    saveSettings();

    // Track tone change
    if (typeof posthogClient !== 'undefined') {
      try {
        posthogClient.trackToneChanged(currentState.tone, oldTone);
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }
  });

  toneNext.addEventListener('click', () => {
    const oldTone = currentState.tone;
    const currentIndex = TONES.indexOf(currentState.tone);
    const newIndex = (currentIndex + 1) % TONES.length;
    currentState.tone = TONES[newIndex];
    updateToneDisplay();
    saveSettings();

    // Track tone change
    if (typeof posthogClient !== 'undefined') {
      try {
        posthogClient.trackToneChanged(currentState.tone, oldTone);
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }
  });

  // ==================== LONGUEUR ====================

  lengthPrev.addEventListener('click', () => {
    const oldLength = currentState.length;
    const currentIndex = LENGTHS.indexOf(currentState.length);
    const newIndex = (currentIndex - 1 + LENGTHS.length) % LENGTHS.length;
    currentState.length = LENGTHS[newIndex];
    updateLengthDisplay();
    saveSettings();

    // Track length change
    if (typeof posthogClient !== 'undefined') {
      try {
        posthogClient.trackLengthChanged(currentState.length, oldLength);
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }
  });

  lengthNext.addEventListener('click', () => {
    const oldLength = currentState.length;
    const currentIndex = LENGTHS.indexOf(currentState.length);
    const newIndex = (currentIndex + 1) % LENGTHS.length;
    currentState.length = LENGTHS[newIndex];
    updateLengthDisplay();
    saveSettings();

    // Track length change
    if (typeof posthogClient !== 'undefined') {
      try {
        posthogClient.trackLengthChanged(currentState.length, oldLength);
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }
  });

  // ==================== GÉNÉRATIONS ====================

  generationsPrev.addEventListener('click', () => {
    const oldCount = currentState.optionsCount;
    const currentIndex = GENERATIONS.indexOf(currentState.optionsCount);
    const newIndex = (currentIndex - 1 + GENERATIONS.length) % GENERATIONS.length;
    currentState.optionsCount = GENERATIONS[newIndex];
    updateGenerationsDisplay();
    saveSettings();

    // Track options count change
    if (typeof posthogClient !== 'undefined') {
      try {
        posthogClient.trackOptionsCountChanged(currentState.optionsCount, oldCount);
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }
  });

  generationsNext.addEventListener('click', () => {
    const oldCount = currentState.optionsCount;
    const currentIndex = GENERATIONS.indexOf(currentState.optionsCount);
    const newIndex = (currentIndex + 1) % GENERATIONS.length;
    currentState.optionsCount = GENERATIONS[newIndex];
    updateGenerationsDisplay();
    saveSettings();

    // Track options count change
    if (typeof posthogClient !== 'undefined') {
      try {
        posthogClient.trackOptionsCountChanged(currentState.optionsCount, oldCount);
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }
  });

  // ==================== UPGRADE ====================

  upgradeBtn.addEventListener('click', () => {
    const currentPlan = currentState.planData?.role || 'FREE';
    const targetPlan = currentPlan === 'FREE' ? 'MEDIUM' : 'PREMIUM';

    // Track upgrade button click
    if (typeof posthogClient !== 'undefined') {
      try {
        posthogClient.trackUpgradeButtonClicked(currentPlan, targetPlan);
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }

    // Rediriger vers la page de pricing avec l'ancre #pricing
    chrome.tabs.create({ url: 'http://localhost:80/#pricing' });
  });

  // ==================== MANAGE SUBSCRIPTION ====================

  manageSubscriptionBtn.addEventListener('click', () => {
    // Ouvrir la page de gestion d'abonnement
    chrome.tabs.create({ url: 'http://localhost:80/account/subscription' });
  });

  // ==================== FONCTIONS D'AFFICHAGE ====================

  function updateLanguageDisplay() {
    // Utiliser les traductions i18n pour afficher les noms de langues
    interfaceLangValue.textContent = window.i18n.t(currentState.interfaceLanguage === 'fr' ? 'french' : 'english');
    commentLangValue.textContent = window.i18n.t(currentState.commentLanguage === 'fr' ? 'french' : 'english');
  }

  function updateNewsDisplay() {
    const mode = currentState.newsEnrichmentMode;
    const role = currentState.planData?.role || 'FREE';

    // Mettre à jour les toggles
    newsOnBtn.classList.remove('active');
    newsOffBtn.classList.remove('active');
    smartOnBtn.classList.remove('active');
    smartOffBtn.classList.remove('active');

    if (mode === 'disabled') {
      newsOffBtn.classList.add('active');
      smartOffBtn.classList.add('active');
      // Afficher un message différent pour les utilisateurs FREE
      newsInfoText.innerHTML = role === 'FREE'
        ? window.i18n.t('newsInfoDisabledFree')
        : window.i18n.t('newsInfoDisabled');
    } else if (mode === 'title-only') {
      newsOnBtn.classList.add('active');
      smartOffBtn.classList.add('active');
      // Afficher un message incitatif pour les utilisateurs MEDIUM
      newsInfoText.innerHTML = role === 'MEDIUM'
        ? window.i18n.t('newsInfoTitleOnlyMedium')
        : window.i18n.t('newsInfoTitleOnly');
    } else if (mode === 'smart-summary') {
      newsOnBtn.classList.add('active');
      smartOnBtn.classList.add('active');
      newsInfoText.innerHTML = window.i18n.t('newsInfoSmartSummary');
    }
  }

  function updateToneDisplay() {
    toneValue.textContent = window.i18n.t(getToneTranslationKey(currentState.tone));
  }

  function updateLengthDisplay() {
    lengthValue.textContent = window.i18n.t(getLengthTranslationKey(currentState.length));
  }

  function updateGenerationsDisplay() {
    generationsValue.textContent = currentState.optionsCount;
  }

  function updateAutoCloseDisplay() {
    autoCloseOnBtn.classList.remove('active');
    autoCloseOffBtn.classList.remove('active');

    if (currentState.autoCloseEmotionsPanel) {
      autoCloseOnBtn.classList.add('active');
    } else {
      autoCloseOffBtn.classList.add('active');
    }
  }

  function updateTooltips() {
    const lang = currentState.interfaceLanguage;
    const infoIcons = document.querySelectorAll('.info-icon');
    infoIcons.forEach(icon => {
      const tooltipAttr = lang === 'fr' ? 'data-tooltip-fr' : 'data-tooltip-en';
      const tooltipText = icon.getAttribute(tooltipAttr);
      // On utilise un attribut CSS personnalisé pour le contenu du pseudo-élément
      icon.style.setProperty('--tooltip-content', `"${tooltipText}"`);
    });
  }

  function getToneTranslationKey(tone) {
    const map = {
      'professionnel': 'professional',
      'soutenu': 'formal',
      'amical': 'friendly',
      'expert': 'expert',
      'informatif': 'informative',
      'negatif': 'negative'
    };
    return map[tone] || 'professional';
  }

  function getLengthTranslationKey(length) {
    const map = {
      7: 'words0to10',
      15: 'words10to20',
      30: 'words20to40'
    };
    return map[length] || 'words10to20';
  }

  // ==================== RÉCUPÉRATION DU PLAN ====================

  async function fetchUserPlan() {
    try {
      const userData = window.googleAuth.getUserData();
      if (!userData || !userData.email) {
        console.warn('❌ Pas de données utilisateur pour récupérer le plan');
        return null;
      }

      const googleToken = await window.googleAuth.getAccessToken();
      if (!googleToken) {
        console.warn('❌ Pas de token pour récupérer le plan');
        return null;
      }

      // Vérifier/créer l'utilisateur avec le token Google et obtenir le JWT
      let jwtToken = null;
      try {
        const verifyResponse = await fetch(`${API_CONFIG.USER_SERVICE_URL}/api/users/verify-google`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            google_id: userData.id || userData.sub,
            email: userData.email,
            name: userData.name
          })
        });

        if (verifyResponse.ok) {
          const authResponse = await fetch(`${API_CONFIG.USER_SERVICE_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ google_token: googleToken })
          });

          if (authResponse.ok) {
            const authData = await authResponse.json();
            jwtToken = authData.access_token;
          }
        }
      } catch (error) {
        console.warn('Erreur lors de la vérification Google:', error);
      }

      // Fallback si pas de JWT
      if (!jwtToken) {
        return {
          role: 'FREE',
          email: userData.email,
          name: userData.name,
          daily_limit: 5,
          remaining: 5
        };
      }

      // Récupérer les données utilisateur avec le JWT
      try {
        const profileResponse = await fetch(`${API_CONFIG.USER_SERVICE_URL}/api/users/profile`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${jwtToken}`,
            'Content-Type': 'application/json'
          }
        });

        if (!profileResponse.ok) {
          console.warn(`Erreur récupération profil: ${profileResponse.status}`);
          return {
            role: 'FREE',
            email: userData.email,
            name: userData.name,
            daily_limit: 5,
            remaining: 5
          };
        }

        const planData = await profileResponse.json();

        // Récupérer aussi les permissions
        const permissionsResponse = await fetch(`${API_CONFIG.USER_SERVICE_URL}/api/users/permissions`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${jwtToken}`,
            'Content-Type': 'application/json'
          }
        });

        if (permissionsResponse.ok) {
          const permissions = await permissionsResponse.json();
          planData.daily_limit = permissions.daily_limit;
          planData.remaining = permissions.remaining_quota;
          planData.features = permissions.features;
        }

        return planData;
      } catch (error) {
        console.warn('Erreur User Service, utilisation du fallback:', error);
        return {
          role: 'FREE',
          email: userData.email,
          name: userData.name,
          daily_limit: 5,
          remaining: 5
        };
      }
    } catch (error) {
      console.error('❌ Erreur lors de la récupération du plan:', error);
      return null;
    }
  }

  async function fetchQuotaStatus() {
    try {
      const userData = window.googleAuth.getUserData();
      if (!userData || !userData.email) {
        return null;
      }

      const googleToken = await window.googleAuth.getAccessToken();
      if (!googleToken) {
        return null;
      }

      // Obtenir le JWT token
      let jwtToken = null;
      try {
        const verifyResponse = await fetch(`${API_CONFIG.USER_SERVICE_URL}/api/users/verify-google`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            google_id: userData.id || userData.sub,
            email: userData.email,
            name: userData.name
          })
        });

        if (verifyResponse.ok) {
          const authResponse = await fetch(`${API_CONFIG.USER_SERVICE_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ google_token: googleToken })
          });

          if (authResponse.ok) {
            const authData = await authResponse.json();
            jwtToken = authData.access_token;
          }
        }
      } catch (error) {
        console.warn('Erreur lors de l\'obtention du JWT:', error);
      }

      if (!jwtToken) {
        return {
          daily_limit: 5,
          remaining: 5,
          role: 'FREE'
        };
      }

      // Récupérer le statut du quota
      try {
        const response = await fetch(`${API_CONFIG.USER_SERVICE_URL}/api/users/quota-status`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${jwtToken}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          console.warn(`Erreur récupération quota: ${response.status}`);
          return {
            daily_limit: 5,
            remaining: 5,
            role: 'FREE'
          };
        }

        const quotaData = await response.json();
        return {
          daily_limit: quotaData.daily_limit,
          remaining: quotaData.remaining,
          used_today: quotaData.used_today,
          reset_time: quotaData.reset_time
        };
      } catch (error) {
        console.warn('Erreur quota service, utilisation du fallback:', error);
        return {
          daily_limit: 5,
          remaining: 5,
          role: 'FREE'
        };
      }
    } catch (error) {
      console.error('❌ Erreur lors de la récupération du quota:', error);
      return null;
    }
  }

  // ==================== MISE À JOUR UI ====================

  async function updateUI() {
    const isAuthenticated = await window.googleAuth.isAuthenticated();
    const userData = window.googleAuth.getUserData();

    currentState.isAuthenticated = isAuthenticated;
    currentState.userData = userData;

    if (isAuthenticated && userData) {
      // Utilisateur connecté
      userCardUnauthenticated.style.display = 'none';
      userCardAuthenticated.style.display = 'block';

      // Afficher les infos utilisateur
      userAvatar.src = userData.picture || '';
      userName.textContent = userData.name || 'Utilisateur';
      userEmail.textContent = userData.email || '';

      // Récupérer et afficher le plan utilisateur
      try {
        const [planData, quotaData] = await Promise.all([
          fetchUserPlan(),
          fetchQuotaStatus()
        ]);
        currentState.planData = planData;
        currentState.quotaData = quotaData;
        updatePlanDisplay(planData, quotaData);
      } catch (error) {
        console.error('❌ Erreur lors de la récupération des données utilisateur:', error);
      }

      // Mettre à jour les toggles auth
      authOnBtn.classList.add('active');
      authOffBtn.classList.remove('active');

      console.log('✅ Utilisateur connecté:', userData.email);
    } else {
      // Utilisateur non connecté
      userCardUnauthenticated.style.display = 'block';
      userCardAuthenticated.style.display = 'none';

      // Mettre à jour les toggles auth
      authOnBtn.classList.remove('active');
      authOffBtn.classList.add('active');

      console.log('❌ Utilisateur non connecté');
    }
  }

  function updatePlanDisplay(planData, quotaData) {
    if (!planData) {
      quotaDisplay.style.display = 'none';
      return;
    }

    const role = planData.role || 'FREE';
    const dailyLimit = quotaData?.daily_limit || 5;
    const remaining = quotaData?.remaining || 0;
    const used = dailyLimit === -1 ? 0 : dailyLimit - remaining;

    // Mettre à jour le badge du plan
    userPlanBadge.textContent = role;
    userPlanBadge.className = `plan-badge-inline ${role}`;

    // Mettre à jour les informations de quota
    if (dailyLimit === -1) {
      quotaValue.textContent = '∞';
      quotaProgress.style.width = '100%';
      quotaProgress.className = 'quota-progress';
    } else {
      quotaValue.textContent = `${remaining}/${dailyLimit}`;

      const percentage = dailyLimit > 0 ? (remaining / dailyLimit) * 100 : 0;
      quotaProgress.style.width = `${percentage}%`;

      // Couleur selon le niveau
      if (percentage === 0) {
        quotaProgress.className = 'quota-progress empty';
      } else if (percentage < 25) {
        quotaProgress.className = 'quota-progress low';
      } else {
        quotaProgress.className = 'quota-progress';
      }
    }

    // Afficher le bouton d'upgrade si pas PREMIUM
    if (role !== 'PREMIUM') {
      upgradeBtn.style.display = 'flex';
    } else {
      upgradeBtn.style.display = 'none';
    }

    // Afficher le bouton de gestion d'abonnement si MEDIUM ou PREMIUM
    if (role === 'MEDIUM' || role === 'PREMIUM') {
      manageSubscriptionBtn.style.display = 'flex';
    } else {
      manageSubscriptionBtn.style.display = 'none';
    }

    quotaDisplay.style.display = 'block';

    // Mettre à jour les restrictions de fonctionnalités
    updateFeatureRestrictions(role);
  }

  // Fonction pour gérer les restrictions selon le plan
  function updateFeatureRestrictions(role) {
    // Enrichissement Actualité : disponible pour MEDIUM et PREMIUM uniquement
    const newsEnrichmentRow = document.querySelector('.setting-row:has(#newsOnBtn)');
    const smartSummaryRow = document.querySelector('.setting-row:has(#smartOnBtn)');

    if (role === 'FREE') {
      // Désactiver l'enrichissement actualité pour FREE
      newsOnBtn.style.opacity = '0.5';
      newsOnBtn.style.cursor = 'not-allowed';

      // Si l'enrichissement est activé, le désactiver
      if (currentState.newsEnrichmentMode !== 'disabled') {
        currentState.newsEnrichmentMode = 'disabled';
        updateNewsDisplay();
        saveSettings();
      }
    } else {
      // Activer l'enrichissement actualité pour MEDIUM et PREMIUM
      newsOnBtn.style.opacity = '1';
      newsOnBtn.style.cursor = 'pointer';
    }

    // Smart Summary : disponible uniquement pour PREMIUM
    if (role !== 'PREMIUM') {
      // Désactiver smart summary pour FREE et MEDIUM
      smartOnBtn.style.opacity = '0.5';
      smartOnBtn.style.cursor = 'not-allowed';

      // Si smart summary est activé, le passer en title-only
      if (currentState.newsEnrichmentMode === 'smart-summary') {
        currentState.newsEnrichmentMode = role === 'FREE' ? 'disabled' : 'title-only';
        updateNewsDisplay();
        saveSettings();
      }
    } else {
      // Activer smart summary pour PREMIUM
      smartOnBtn.style.opacity = '1';
      smartOnBtn.style.cursor = 'pointer';
    }
  }

  // ==================== SAUVEGARDE & CHARGEMENT ====================

  async function loadSettings() {
    return new Promise((resolve) => {
      chrome.storage.sync.get([
        'tone',
        'length',
        'optionsCount',
        'commentLanguage',
        'interfaceLanguage',
        'newsEnrichmentMode',
        'autoCloseEmotionsPanel'
      ], function(data) {
        if (data.tone) currentState.tone = data.tone;
        if (data.length) currentState.length = data.length;
        if (data.optionsCount) currentState.optionsCount = data.optionsCount;
        if (data.commentLanguage) currentState.commentLanguage = data.commentLanguage;
        if (data.interfaceLanguage) {
          currentState.interfaceLanguage = data.interfaceLanguage;
          window.i18n.setLanguage(data.interfaceLanguage);
        }
        if (data.newsEnrichmentMode) {
          currentState.newsEnrichmentMode = data.newsEnrichmentMode;
        } else {
          currentState.newsEnrichmentMode = 'title-only';
        }
        if (data.autoCloseEmotionsPanel !== undefined) {
          currentState.autoCloseEmotionsPanel = data.autoCloseEmotionsPanel;
        }

        // Mettre à jour tous les affichages
        updateLanguageDisplay();
        updateNewsDisplay();
        updateToneDisplay();
        updateLengthDisplay();
        updateGenerationsDisplay();
        updateAutoCloseDisplay();
        updateTooltips();

        console.log('✅ Paramètres chargés:', currentState);
        resolve();
      });
    });
  }

  function saveSettings() {
    chrome.storage.sync.set({
      tone: currentState.tone,
      length: currentState.length,
      optionsCount: currentState.optionsCount,
      commentLanguage: currentState.commentLanguage,
      interfaceLanguage: currentState.interfaceLanguage,
      newsEnrichmentMode: currentState.newsEnrichmentMode,
      autoCloseEmotionsPanel: currentState.autoCloseEmotionsPanel
    }, function() {
      console.log('💾 Paramètres sauvegardés:', currentState);

      // Notifier les content scripts du changement
      chrome.tabs.query({ url: "*://*.linkedin.com/*" }, function(tabs) {
        if (chrome.runtime.lastError) {
          console.warn('⚠️ Erreur lors de la recherche des tabs:', chrome.runtime.lastError.message);
          return;
        }
        tabs.forEach(tab => {
          chrome.tabs.sendMessage(tab.id, {
            action: 'settingsUpdated',
            settings: {
              tone: currentState.tone,
              length: currentState.length,
              optionsCount: currentState.optionsCount,
              commentLanguage: currentState.commentLanguage,
              interfaceLanguage: currentState.interfaceLanguage,
              newsEnrichmentMode: currentState.newsEnrichmentMode,
              autoCloseEmotionsPanel: currentState.autoCloseEmotionsPanel
            }
          }, (response) => {
            if (chrome.runtime.lastError) {
              console.warn('⚠️ Erreur lors de l\'envoi au tab:', chrome.runtime.lastError.message);
            }
          });
        });
      });
    });
  }

  // ==================== DÉMARRAGE ====================
  await initialize();
});
