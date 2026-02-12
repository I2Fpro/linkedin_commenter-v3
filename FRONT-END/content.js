// Script principal pour LinkedIn AI Commenter - VERSION MULTILINGUE
(function() {
  'use strict';

  // Éviter la double-injection du script
    console.log('⚠️ Content script déjà chargé, arrêt');
    return;
  }

  console.log('🚀 LinkedIn AI Commenter - Content script chargé');

  // État local
  let isAuthenticated = false;
  let currentInterfaceLanguage = 'fr';
  let currentCommentLanguage = 'fr';

  // Traductions pour le content script
  const translations = {
    fr: {
      generate: 'Générer',
      withPrompt: 'Avec prompt',
      generating: 'Génération...',
      customInstructions: 'Instructions personnalisées',
      addInstructions: 'Ajoutez vos instructions...',
      cancel: 'Annuler',
      refine: '⚡ Affiner',
      refineComment: 'Affiner le commentaire',
      refineInstructions: 'Instructions pour affiner...',
      comment: 'Commentaire',
      generations: 'génération',
      authRequired: 'Connectez-vous via l\'extension pour utiliser cette fonctionnalité',
      error: 'Erreur',
      impossibleExtract: 'Impossible d\'extraire le contenu',
      pleaseSignIn: 'Veuillez vous connecter via l\'extension',
      // Émotions
      admiration: 'Admiration',
      inspiration: 'Inspiration',
      curiosity: 'Curiosité',
      gratitude: 'Gratitude',
      empathy: 'Empathie',
      skepticism: 'Scepticisme\nbienveillant',
      // Intensites (Story 7.13)
      intensityLow: 'Faible',
      intensityMedium: 'Moyen',
      intensityHigh: 'Fort',
      intensity: 'Intensité',
      // Longueurs
      lengthVeryShort: 'Très court',
      lengthShort: 'Court',
      lengthMedium: 'Moyen',
      lengthLong: 'Long',
      lengthVeryLong: 'Très long',
      // Styles de langage
      oral: 'Oral /\nConversationnel',
      professional: 'Professionnel',
      storytelling: 'Storytelling',
      poetic: 'Poétique /\nCréatif',
      humoristic: 'Humoristique',
      impactful: 'Impactant /\nMarketing',
      benevolent: 'Bienveillant /\nPositif',
      // Tons (fusion ex-popup)
      formal: 'Soutenu /\nFormel',
      friendly: 'Amical',
      expert: 'Expert',
      informative: 'Informatif',
      negative: 'Négatif /\nCritique',
      languageStyle: 'Style de langage',
      // V3 Story 2.3 — Warning personne à éviter
      blacklistWarningTitle: 'Attention',
      blacklistWarningMessage: 'Vous avez choisi d\'éviter {name}. Voulez-vous quand même générer un commentaire ?',
      blacklistWarningYes: 'Générer quand même',
      blacklistWarningNo: 'Annuler',
      // Mode Inline - Toggles enrichissement
      quoteToggle: 'Citation',
      quoteToggleActive: 'Citation activée',
      quoteToggleInactive: 'Citation désactivée',
      quoteToggleTooltip: 'Inclut une citation du post',
      quoteUpgradeRequired: 'Passez en Premium pour utiliser les citations contextuelles',
      tagAuthor: 'Tag auteur',
      tagAuthorTooltip: 'Mentionne l\'auteur du post',
      tagAuthorUpgradeRequired: 'Passez en Premium pour taguer l\'auteur',
      tagAuthorSuccess: '{name} sera mentionné dans le commentaire',
      authorNotFound: 'Impossible de trouver l\'auteur du post',
      webSearchToggle: 'Source web',
      webSearchToggleTooltip: 'Recherche des infos sur le web',
      webSearchUpgradeRequired: 'Passez en Premium pour la recherche web',
      contextToggle: 'Contexte comm.',
      contextToggleTooltip: 'Prend en compte les commentaires existants',
      contextUpgradeRequired: 'Passez en Premium pour le contexte',
      generateComment: 'Générer le commentaire',
      randomGenerate: 'Générer aléatoire',
      // Mode Inline - News & Blacklist
      newsToggle: 'News LinkedIn',
      newsToggleTooltip: 'Enrichit avec les actualités LinkedIn',
      newsUpgradeRequired: 'Passez en MEDIUM ou supérieur pour les actualités',
      addToBlacklist: 'Blacklister',
      addToBlacklistTooltip: 'Ajoute l\'auteur à votre blacklist',
      blacklistUpgradeRequired: 'La blacklist est réservée aux abonnés Premium',
      viewBlacklist: 'Ma liste',
      viewBlacklistTooltip: 'Voir ma blacklist',
      blacklistAddSuccess: '{name} a été ajouté à votre blacklist',
      personalisation: 'Style',
      personalisationTooltip: 'Choisir émotion et style de langage',
      // Tooltips & ARIA labels
      generateTooltip: 'Générer un commentaire',
      generateAriaLabel: 'Générer un commentaire pour ce post',
      randomTooltip: 'Génération aléatoire',
      randomAriaLabel: 'Générer avec des paramètres aléatoires',
      promptTooltip: 'Ajouter un prompt personnalisé',
      promptAriaLabel: 'Ouvrir le champ de prompt personnalisé',
      optionsTooltip: 'Options',
      optionsAriaLabel: 'Ouvrir le menu des options',
      quoteToggleAriaLabel: 'Activer ou désactiver la citation',
      contextToggleAriaLabel: 'Activer le contexte des commentaires',
      webSearchToggleAriaLabel: 'Activer ou désactiver la recherche web',
      newsToggleAriaLabel: 'Activer les actualités LinkedIn',
      tagAuthorAriaLabel: 'Activer ou désactiver le tag auteur',
      addToBlacklistAriaLabel: 'Ajouter cet auteur à la blacklist',
      viewBlacklistAriaLabel: 'Voir ma blacklist',
      personalisationAriaLabel: 'Personnaliser le style',
      premiumFeature: 'Fonctionnalité Premium'
    },
    en: {
      generate: 'Generate',
      withPrompt: 'With prompt',
      generating: 'Generating...',
      customInstructions: 'Custom instructions',
      addInstructions: 'Add your instructions...',
      cancel: 'Cancel',
      refine: '⚡ Refine',
      refineComment: 'Refine comment',
      refineInstructions: 'Instructions to refine...',
      comment: 'Comment',
      generations: 'generation',
      authRequired: 'Sign in via the extension to use this feature',
      error: 'Error',
      impossibleExtract: 'Unable to extract content',
      pleaseSignIn: 'Please sign in via the extension',
      // Emotions
      admiration: 'Admiration',
      inspiration: 'Inspiration',
      curiosity: 'Curiosity',
      gratitude: 'Gratitude',
      empathy: 'Empathy',
      skepticism: 'Benevolent\nskepticism',
      // Intensities (Story 7.13)
      intensityLow: 'Low',
      intensityMedium: 'Medium',
      intensityHigh: 'High',
      intensity: 'Intensity',
      // Lengths
      lengthVeryShort: 'Very short',
      lengthShort: 'Short',
      lengthMedium: 'Medium',
      lengthLong: 'Long',
      lengthVeryLong: 'Very long',
      // Styles de langage
      oral: 'Oral /\nConversational',
      professional: 'Professional',
      storytelling: 'Storytelling',
      poetic: 'Poetic /\nCreative',
      humoristic: 'Humoristic',
      impactful: 'Impactful /\nMarketing',
      benevolent: 'Benevolent /\nPositive',
      // Tones (ex-popup fusion)
      formal: 'Formal',
      friendly: 'Friendly',
      expert: 'Expert',
      informative: 'Informative',
      negative: 'Negative /\nCritical',
      languageStyle: 'Language Style',
      // V3 Story 2.3 — Warning person to avoid
      blacklistWarningTitle: 'Warning',
      blacklistWarningMessage: 'You chose to avoid {name}. Do you still want to generate a comment?',
      blacklistWarningYes: 'Generate anyway',
      blacklistWarningNo: 'Cancel',
      // Inline Mode - Enrichment toggles
      quoteToggle: 'Quote',
      quoteToggleActive: 'Quote enabled',
      quoteToggleInactive: 'Quote disabled',
      quoteToggleTooltip: 'Include a quote from the post',
      quoteUpgradeRequired: 'Upgrade to Premium for contextual quotes',
      tagAuthor: 'Tag author',
      tagAuthorTooltip: 'Mention the post author',
      tagAuthorUpgradeRequired: 'Upgrade to Premium to tag author',
      tagAuthorSuccess: '{name} will be mentioned in the comment',
      authorNotFound: 'Could not find the post author',
      webSearchToggle: 'Web source',
      webSearchToggleTooltip: 'Search web for info',
      webSearchUpgradeRequired: 'Upgrade to Premium for web search',
      contextToggle: 'Comment ctx',
      contextToggleTooltip: 'Consider existing comments',
      contextUpgradeRequired: 'Upgrade to Premium for context',
      generateComment: 'Generate comment',
      randomGenerate: 'Random generate',
      // Inline Mode - News & Blacklist
      newsToggle: 'News LinkedIn',
      newsToggleTooltip: 'Enriches with LinkedIn news',
      newsUpgradeRequired: 'Upgrade to MEDIUM or higher for news',
      addToBlacklist: 'Blacklist',
      addToBlacklistTooltip: 'Add author to your blacklist',
      blacklistUpgradeRequired: 'Blacklist is reserved for Premium subscribers',
      viewBlacklist: 'My list',
      viewBlacklistTooltip: 'View my blacklist',
      blacklistAddSuccess: '{name} has been added to your blacklist',
      personalisation: 'Style',
      personalisationTooltip: 'Choose emotion and language style',
      // Tooltips & ARIA labels
      generateTooltip: 'Generate a comment',
      generateAriaLabel: 'Generate a comment for this post',
      randomTooltip: 'Random generation',
      randomAriaLabel: 'Generate with random parameters',
      promptTooltip: 'Add custom prompt',
      promptAriaLabel: 'Open custom prompt field',
      optionsTooltip: 'Options',
      optionsAriaLabel: 'Open options menu',
      quoteToggleAriaLabel: 'Toggle quote on or off',
      contextToggleAriaLabel: 'Toggle comment context',
      webSearchToggleAriaLabel: 'Toggle web search on or off',
      newsToggleAriaLabel: 'Toggle LinkedIn news',
      tagAuthorAriaLabel: 'Toggle author tag on or off',
      addToBlacklistAriaLabel: 'Add this author to blacklist',
      viewBlacklistAriaLabel: 'View my blacklist',
      personalisationAriaLabel: 'Customize style',
      premiumFeature: 'Premium Feature'
    }
  };

  // Fonction de traduction
  function t(key) {
    return translations[currentInterfaceLanguage][key] || translations['fr'][key] || key;
  }

  // Charger les langues depuis le storage
  async function loadLanguageSettings() {
    return new Promise((resolve) => {
      chrome.storage.sync.get(['interfaceLanguage', 'commentLanguage'], function(data) {
        currentInterfaceLanguage = data.interfaceLanguage || 'fr';
        currentCommentLanguage = data.commentLanguage || 'fr';
        console.log('Langues chargées - Interface:', currentInterfaceLanguage, 'Commentaires:', currentCommentLanguage);
        resolve();
      });
    });
  }

  // V3 Story 4.1 — Helper pour afficher un toast d'upgrade Premium avec lien Stripe
  function showPremiumUpgradePrompt(featureMessage) {
    // Utiliser le message i18n global si disponible, sinon fallback local
    const message = featureMessage || (window.i18n ? window.i18n.t('premiumFeatureLockedMessage') : 'Cette fonctionnalité est réservée au plan Premium.');
    const actionText = window.i18n ? window.i18n.t('upgradeNow') : 'Passer au Premium';

    window.toastNotification.warning(message, {
      duration: 6000,
      action: {
        text: actionText,
        callback: () => {
          chrome.runtime.sendMessage({ action: 'openUpgradePage' });
        }
      }
    });
  }

  // Fonction pour extraire les actualités LinkedIn
  function extractLinkedInNews() {
    try {
      const newsModule = document.querySelector('[data-view-name="news-module"]');
      if (!newsModule) {
        console.log('📰 Module d\'actualités non trouvé');
        return [];
      }

      const newsLinks = newsModule.querySelectorAll('a[href*="/news/story/"]');
      const newsItems = [];

      newsLinks.forEach((link, index) => {
        if (index >= 5) return; // Limiter à 5 actualités

        // Extraire le titre (premier élément texte non vide)
        const titleElement = link.querySelector('.news-module-story__title, [class*="headline"], span');
        const title = titleElement ? titleElement.textContent.trim() : link.textContent.trim().split('\n')[0];
        const url = link.href;

        if (title && url && title.length > 5) {
          newsItems.push({ title, url });
        }
      });

      console.log(`📰 ${newsItems.length} actualités LinkedIn extraites:`, newsItems);
      return newsItems;
    } catch (error) {
      console.warn('⚠️ Erreur lors de l\'extraction des actualités:', error);
      return [];
    }
  }

  // Initialiser l'application au démarrage
  (async function boot() {
    await loadLanguageSettings();
    )();

  // ==================== Phase 2: LinkedIn Profile Capture ====================

  async function detectAndCaptureLinkedInProfile() {
    try {
      const currentPath = window.location.pathname;
      const isMyProfile = /\/in\/me\/?(\?.*)?$/.test(currentPath);

      if (!isMyProfile) {
        return;
      }

      console.log('[Phase2] Page /in/me/ detectee, tentative de capture profil');

      const storage = await new Promise(resolve => {
        chrome.storage.local.get(['linkedin_profile_captured', 'user_plan'], resolve);
      });

      if (storage.linkedin_profile_captured) {
        console.log('[Phase2] Profil LinkedIn deja capture, skip');
        return;
      }

      if (!isAuthenticated) {
        console.log('[Phase2] Utilisateur non authentifie, skip capture');
        return;
      }

      let linkedinProfileId = null;

      // Tentative 1 : Attendre que l'URL change (LinkedIn redirect)
      for (let attempt = 0; attempt < 10; attempt++) {
        await new Promise(resolve => setTimeout(resolve, 500));
        const resolvedPath = window.location.pathname;
        const match = resolvedPath.match(/\/in\/([^\/\?]+)\/?/);

        if (match && match[1] !== 'me') {
          linkedinProfileId = match[1].toLowerCase().trim();
          break;
        }
      }

      // Tentative 2 : Extraire depuis un element DOM si l'URL n'a pas change
      if (!linkedinProfileId) {
        const canonicalLink = document.querySelector('link[rel="canonical"]');
        if (canonicalLink) {
          const match = canonicalLink.href.match(/\/in\/([^\/\?]+)\/?/);
          if (match && match[1] !== 'me') {
            linkedinProfileId = match[1].toLowerCase().trim();
          }
        }
      }

      // Tentative 3 : Chercher dans les liens du profil
      if (!linkedinProfileId) {
        const profileLinks = document.querySelectorAll('a[href*="/in/"]');
        for (const link of profileLinks) {
          const match = link.href.match(/\/in\/([^\/\?]+)\/?/);
          if (match && match[1] !== 'me' && match[1].length > 1) {
            linkedinProfileId = match[1].toLowerCase().trim();
            break;
          }
        }
      }

      if (!linkedinProfileId) {
        console.warn('[Phase2] Impossible d\'extraire le linkedin_profile_id reel');
        return;
      }

      if (!/^[a-z0-9\-]+$/.test(linkedinProfileId)) {
        console.warn('[Phase2] linkedin_profile_id invalide:', linkedinProfileId);
        return;
      }

      console.log('[Phase2] linkedin_profile_id extrait:', linkedinProfileId);

      chrome.runtime.sendMessage({
        action: 'captureLinkedInProfile',
        data: {
          linkedin_profile_id: linkedinProfileId
        }
      }, (response) => {
        if (chrome.runtime.lastError) {
          console.warn('[Phase2] Erreur envoi message:', chrome.runtime.lastError);
          return;
        }

        if (response && response.success) {
          console.log('[Phase2] Profil capture avec succes, trial_granted:', response.trial_granted);
          chrome.storage.local.set({ linkedin_profile_captured: true });

          if (response.trial_granted && response.role) {
            chrome.storage.local.set({
              user_plan: response.role,
              trial_ends_at: response.trial_ends_at
            });
          }
        } else if (response) {
          console.log('[Phase2] Capture profil: ', response.reason || 'pas de trial');
          if (response.already_captured) {
            chrome.storage.local.set({ linkedin_profile_captured: true });
          }
        }
      });

    } catch (error) {
      console.error('[Phase2] Erreur capture profil LinkedIn:', error);
    }
  }

  // Vérifier l'authentification
  async function checkAuthentication() {
    try {
      const response = await chrome.runtime.sendMessage({ action: 'checkAuthentication' });
      isAuthenticated = response && response.authenticated;
      console.log('État authentification:', isAuthenticated);
        try {
          // Récupérer les informations utilisateur depuis le storage
          const userInfo = await chrome.storage.local.get(['user_id', 'user_email', 'user_name', 'user_plan']);

          if (userInfo.user_id) {
              email: userInfo.user_email,
              name: userInfo.user_name || null,
              plan: userInfo.user_plan || 'FREE'
            });
          } else if (userInfo.user_email) {
            // Fallback sur email si user_id non disponible
            console.warn('⚠️ user_id non disponible, utilisation de l\'email');
              email: userInfo.user_email,
              name: userInfo.user_name || null,
              plan: userInfo.user_plan || 'FREE'
            });
          }

          // Anti-duplicate session logic (Plan v3)
          if (!window.__PH_BOOTED__) {
            const key = 'ph_session_started';
            if (!sessionStorage.getItem(key)) {
              sessionStorage.setItem(key, '1');
              console.log('📊 Session d\'utilisation démarrée');
            } else {
              console.log('📊 Session déjà démarrée (évite duplication)');
            }

            // Track session end events
            document.addEventListener('visibilitychange', () => {
            });
          }
        } catch (e) {
        }
      }
    } catch (error) {
      console.error('Erreur vérification auth:', error);
      isAuthenticated = false;
    }
  }

  // Mettre à jour tous les boutons
  function updateAllButtons() {
    document.querySelectorAll('.ai-buttons-wrapper').forEach(wrapper => {
      updateButtonsState(wrapper, isAuthenticated);
    });
  }

  // Mettre à jour le texte de tous les boutons
  function updateAllButtonsText() {
    document.querySelectorAll('.ai-button, .ai-generate-button').forEach(button => {
      // Ignorer le bouton de paramètres (settings-button)
      if (button.classList.contains('settings-button')) {
        return; // Ne pas changer le texte du bouton ⚙️
      }

      if (button.classList.contains('with-prompt')) {
        button.querySelector('span').textContent = t('withPrompt');
      } else {
        button.querySelector('span').textContent = t('generate');
      }
    });

    // Mettre à jour les popups existants
    document.querySelectorAll('.ai-popup-title').forEach(title => {
      const count = title.getAttribute('data-count') || '2';
      title.textContent = `${count} ${t('generations')}${count > 1 ? 's' : ''}`;
    });

    document.querySelectorAll('.auth-required-message').forEach(msg => {
      msg.textContent = t('authRequired');
    });
  }

  // ================================================
  // MODAL BEM UTILITIES - Story 7.4
  // Fonctions utilitaires pour creer des modals BEM accessibles
  // ================================================

  // Compteur pour generer des IDs uniques
  let modalIdCounter = 0;

  /**
   * Genere un ID unique pour les attributs aria-labelledby
   * @returns {string} ID unique
   */
  function generateModalId() {
    return `ai-modal-title-${++modalIdCounter}-${Date.now()}`;
  }

  /**
   * Cree une structure de modal BEM complete avec ARIA
   * @param {Object} options - Options de creation du modal
   * @param {string} options.variant - 'generation' | 'warning' | 'confirm'
   * @param {string} options.title - Titre du modal
   * @param {boolean} [options.showCloseButton=true] - Afficher le bouton fermer
   * @param {Function} [options.onClose] - Callback de fermeture
   * @param {Function} [options.onOverlayClick] - Callback clic overlay (null = pas de fermeture)
   * @returns {Object} { modal, overlay, container, header, title, body, footer, close, cleanup }
   */
  function createModalBEM(options) {
    const {
      variant = 'generation',
      title = '',
      showCloseButton = true,
      onClose = null,
      onOverlayClick = null
    } = options;

    const titleId = generateModalId();

    // Element racine du modal
    const modal = document.createElement('div');
    modal.className = `ai-modal ai-modal--${variant}`;
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', titleId);

    // Overlay
    const overlay = document.createElement('div');
    overlay.className = 'ai-modal__overlay';

    // Container principal
    const container = document.createElement('div');
    container.className = 'ai-modal__container';

    // Header
    const header = document.createElement('div');
    header.className = 'ai-modal__header';

    // Titre
    const titleEl = document.createElement('h2');
    titleEl.className = 'ai-modal__title';
    titleEl.id = titleId;
    titleEl.textContent = title;

    // Bouton fermer
    let closeBtn = null;
    if (showCloseButton) {
      closeBtn = document.createElement('button');
      closeBtn.className = 'ai-modal__close';
      closeBtn.setAttribute('aria-label', t('cancel') || 'Fermer');
      closeBtn.innerHTML = '&times;';
    }

    // Body
    const body = document.createElement('div');
    body.className = 'ai-modal__body';

    // Footer
    const footer = document.createElement('div');
    footer.className = 'ai-modal__footer';

    // Assemblage
    header.appendChild(titleEl);
    if (closeBtn) header.appendChild(closeBtn);
    container.appendChild(header);
    container.appendChild(body);
    container.appendChild(footer);
    modal.appendChild(overlay);
    modal.appendChild(container);

    // Gestion du focus trap
    let focusTrapCleanup = null;
    let escapeHandler = null;

    // Fonction de cleanup
    const cleanup = () => {
      if (focusTrapCleanup) focusTrapCleanup();
      if (escapeHandler) document.removeEventListener('keydown', escapeHandler);
      modal.classList.add('ai-modal--closing');
      document.body.classList.remove('ai-modal-active'); // Restaurer les controles
      setTimeout(() => modal.remove(), 200);
    };

    // Handler ESC
    escapeHandler = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        if (onClose) onClose();
        cleanup();
      }
    };

    // Click overlay (sauf confirm)
    if (onOverlayClick !== null) {
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
          if (onOverlayClick) onOverlayClick();
          else if (onClose) onClose();
          cleanup();
        }
      });
    }

    // Click bouton fermer
    if (closeBtn && onClose) {
      closeBtn.addEventListener('click', () => {
        onClose();
        cleanup();
      });
    } else if (closeBtn) {
      closeBtn.addEventListener('click', cleanup);
    }

    return {
      modal,
      overlay,
      container,
      header,
      title: titleEl,
      body,
      footer,
      close: closeBtn,
      cleanup,
      // Methode pour afficher le modal
      show: () => {
        document.body.appendChild(modal);
        modal.classList.add('ai-modal--open');
        document.body.classList.add('ai-modal-active'); // Masquer les controles pendant le modal
        document.addEventListener('keydown', escapeHandler);
        // Setup focus trap apres ajout au DOM
        focusTrapCleanup = setupFocusTrap(modal);
      }
    };
  }

  /**
   * Configure le focus trap dans un modal
   * @param {HTMLElement} modal - Element modal
   * @returns {Function} Fonction de cleanup
   */
  function setupFocusTrap(modal) {
    const focusableSelector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    const focusableElements = modal.querySelectorAll(focusableSelector);

    if (focusableElements.length === 0) return () => {};

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    // Sauvegarder l'element qui avait le focus
    const previouslyFocused = document.activeElement;

    // Focus sur le premier element
    setTimeout(() => firstElement.focus(), 50);

    const trapHandler = (e) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    modal.addEventListener('keydown', trapHandler);

    // Retourner la fonction de cleanup
    return () => {
      modal.removeEventListener('keydown', trapHandler);
      // Restaurer le focus
      if (previouslyFocused && previouslyFocused.focus) {
        previouslyFocused.focus();
      }
    };
  }

  /**
   * Ferme un modal BEM avec animation
   * @param {HTMLElement} modal - Element modal a fermer
   */
  function closeModalBEM(modal) {
    if (!modal) return;
    modal.classList.add('ai-modal--closing');
    modal.classList.remove('ai-modal--open');
    setTimeout(() => modal.remove(), 200);
  }

  // ================================================
  // FIN MODAL BEM UTILITIES
  // ================================================

  // Mettre à jour l'état des boutons
  function updateButtonsState(wrapper, authenticated) {
    // Support both legacy buttons and inline chips
    const buttons = wrapper.querySelectorAll('.ai-button, .ai-generate-button');
    const chips = wrapper.querySelectorAll('.ai-chip');

    // Handle legacy buttons
    buttons.forEach(button => {
      button.disabled = !authenticated;
    });

    // Handle inline chips
    chips.forEach(chip => {
      if (!authenticated) {
        // Disable chip if not already locked (preserve locked state for premium features)
        if (!chip.classList.contains('ai-chip--locked')) {
          chip.setAttribute('data-auth-disabled', 'true');
          chip.style.opacity = '0.5';
          chip.style.pointerEvents = 'none';
        }
      } else {
        // Re-enable chip (unless it's locked for premium)
        chip.removeAttribute('data-auth-disabled');
        if (!chip.classList.contains('ai-chip--locked')) {
          chip.style.opacity = '';
          chip.style.pointerEvents = '';
        }
      }
    });

    // Message d'authentification (only for legacy wrappers and inline controls)
    let authMessage = wrapper.querySelector('.auth-required-message');
    if (!authenticated && !authMessage) {
      authMessage = document.createElement('div');
      authMessage.className = 'auth-required-message';
      authMessage.textContent = t('authRequired');
      wrapper.appendChild(authMessage);
    } else if (authenticated && authMessage) {
      authMessage.remove();
    }
  }

  // Vérifier si les boutons AI existent déjà pour ce commentBox
  function hasAIButtons(commentBox) {
    // 1. Vérifier les marqueurs sur le commentBox lui-même
    if (commentBox.hasAttribute('data-ai-buttons-added') || commentBox.hasAttribute('data-ai-buttons-pending')) {
      return true;
    }

    // 2. Vérifier dans le parent direct
    const parentWrapper = commentBox.parentElement?.querySelector('.ai-buttons-wrapper');
    if (parentWrapper) {
      commentBox.setAttribute('data-ai-buttons-added', 'true');
      return true;
    }

    // 3. Vérifier dans les parents proches (contexte de commentaire)
    const parentContext = commentBox.closest('[data-view-name="comment-box"], .comments-comment-texteditor, .comment-box, .comments-comment-box');
    const contextWrapper = parentContext?.querySelector('.ai-buttons-wrapper');
    if (contextWrapper) {
      commentBox.setAttribute('data-ai-buttons-added', 'true');
      return true;
    }

    // 4. Vérifier dans les siblings (même niveau)
    const siblings = Array.from(commentBox.parentElement?.children || []);
    const siblingsWithWrapper = siblings.filter(sibling => sibling?.classList?.contains('ai-buttons-wrapper'));
    if (siblingsWithWrapper.length > 0) {
      commentBox.setAttribute('data-ai-buttons-added', 'true');
      return true;
    }

    // 5. Vérifier dans un contexte plus large pour les publications privées
    const widerContext = commentBox.closest('[data-view-name="feed-full-update"], [role="listitem"], [data-id], article, .feed-shared-update-v2, [role="article"]');
    if (widerContext) {
      const allCommentBoxes = widerContext.querySelectorAll('[contenteditable="true"], [role="textbox"]');
      let foundNearby = false;
      allCommentBoxes.forEach((box) => {
        const boxHasWrapper = box.parentElement?.querySelector('.ai-buttons-wrapper');
        const boxRect = box.getBoundingClientRect();
        const commentBoxRect = commentBox.getBoundingClientRect();
        const distance = Math.abs(boxRect.top - commentBoxRect.top);

        if (box !== commentBox && boxHasWrapper && distance < 50) {
          commentBox.setAttribute('data-ai-buttons-added', 'true');
          foundNearby = true;
        }
      });

      if (foundNearby) {
        return true;
      }
    }

    return false;
  }

  // ================================================
  // EMOTION WHEEL (Story 7.13)
  // Roue chromatique interactive pour selection emotion/intensite
  // ================================================

  // Configuration des emotions avec leurs couleurs
  const EMOTION_WHEEL_CONFIG = {
    emotions: [
      { key: 'admiration', color: '#FFD700', emoji: '🌟' },
      { key: 'inspiration', color: '#E91E63', emoji: '💡' },
      { key: 'curiosity', color: '#00BCD4', emoji: '🤔' },
      { key: 'gratitude', color: '#4CAF50', emoji: '🙏' },
      { key: 'empathy', color: '#9C27B0', emoji: '❤️' },
      { key: 'skepticism', color: '#FF5722', emoji: '🧐' }
    ],
    intensities: [
      { key: 'low', labelKey: 'intensityLow', opacity: 0.4 },
      { key: 'medium', labelKey: 'intensityMedium', opacity: 0.7 },
      { key: 'high', labelKey: 'intensityHigh', opacity: 1.0 }
    ],
    // Dimensions SVG
    size: 220,
    centerRadius: 30,
    ringWidth: 28
  };

  // ================================================
  // STYLE WHEEL (Story 7.14)
  // Roue chromatique interactive pour selection du style de langage
  // ================================================

  // Configuration des styles de langage avec leurs couleurs
  // Fusion des styles + tons (ex-popup)
  const STYLE_WHEEL_CONFIG = {
    styles: [
      // Styles de langage
      { key: 'oral', color: '#64B5F6', emoji: '🗣️' },
      { key: 'professional', color: '#78909C', emoji: '💼' },
      { key: 'storytelling', color: '#AB47BC', emoji: '📖' },
      { key: 'poetic', color: '#F06292', emoji: '🎨' },
      { key: 'humoristic', color: '#FFD54F', emoji: '😂' },
      { key: 'impactful', color: '#FF7043', emoji: '⚡' },
      { key: 'benevolent', color: '#81C784', emoji: '🤝' },
      // Tons (ex-popup) - ajoutes pour fusion
      { key: 'formal', color: '#7B1FA2', emoji: '👔' },
      { key: 'friendly', color: '#4CAF50', emoji: '😊' },
      { key: 'expert', color: '#1565C0', emoji: '🎓' },
      { key: 'informative', color: '#00ACC1', emoji: '📊' },
      { key: 'negative', color: '#D32F2F', emoji: '😤' }
    ],
    // Dimensions SVG (agrandi pour 12 elements)
    size: 220,
    centerRadius: 30,
    outerRadius: 100
  };

  // Calcul d'un arc SVG (secteur de camembert)
  function describeArc(cx, cy, innerRadius, outerRadius, startAngle, endAngle) {
    const startRad = (startAngle - 90) * Math.PI / 180;
    const endRad = (endAngle - 90) * Math.PI / 180;

    const x1 = cx + outerRadius * Math.cos(startRad);
    const y1 = cy + outerRadius * Math.sin(startRad);
    const x2 = cx + outerRadius * Math.cos(endRad);
    const y2 = cy + outerRadius * Math.sin(endRad);
    const x3 = cx + innerRadius * Math.cos(endRad);
    const y3 = cy + innerRadius * Math.sin(endRad);
    const x4 = cx + innerRadius * Math.cos(startRad);
    const y4 = cy + innerRadius * Math.sin(startRad);

    const largeArc = endAngle - startAngle > 180 ? 1 : 0;

    return [
      'M', x1, y1,
      'A', outerRadius, outerRadius, 0, largeArc, 1, x2, y2,
      'L', x3, y3,
      'A', innerRadius, innerRadius, 0, largeArc, 0, x4, y4,
      'Z'
    ].join(' ');
  }

  // Creation du SVG de la roue
  function createEmotionWheelSVG(commentBox, onSelect, onClose, onReset) {
    const { size, centerRadius, ringWidth, emotions, intensities } = EMOTION_WHEEL_CONFIG;
    const cx = size / 2;
    const cy = size / 2;
    const sectionAngle = 360 / emotions.length; // 60 degres par emotion

    // Creer le conteneur
    const container = document.createElement('div');
    container.className = 'ai-emotion-wheel';
    container.setAttribute('role', 'listbox');
    container.setAttribute('aria-label', t('personalisationAriaLabel') || 'Selectionner emotion et intensite');
    container.setAttribute('tabindex', '0');

    // Creer le SVG
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'ai-emotion-wheel__svg');
    svg.setAttribute('viewBox', `0 0 ${size} ${size}`);
    svg.setAttribute('width', size);
    svg.setAttribute('height', size);

    // Creer le groupe principal
    const mainGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');

    // Creer les zones pour chaque emotion et intensite
    emotions.forEach((emotion, emotionIndex) => {
      const startAngle = emotionIndex * sectionAngle;
      const endAngle = startAngle + sectionAngle;

      // 3 anneaux d'intensite (du centre vers l'exterieur)
      intensities.forEach((intensity, intensityIndex) => {
        const innerR = centerRadius + (intensityIndex * ringWidth);
        const outerR = innerR + ringWidth;

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('class', 'ai-emotion-wheel__zone');
        path.setAttribute('d', describeArc(cx, cy, innerR, outerR, startAngle, endAngle));
        path.setAttribute('data-emotion', emotion.key);
        path.setAttribute('data-intensity', intensity.key);
        path.setAttribute('role', 'option');
        path.setAttribute('aria-label', `${t(emotion.key)} - ${t(intensity.labelKey)}`);
        path.setAttribute('tabindex', '-1');

        // Couleur avec opacite
        path.style.fill = emotion.color;
        path.style.opacity = intensity.opacity;

        // Evenements
        path.addEventListener('click', (e) => {
          e.stopPropagation();
          onSelect(emotion.key, intensity.key);
        });

        path.addEventListener('mouseenter', () => {
          showWheelTooltip(container, emotion, intensity, path);
        });

        path.addEventListener('mouseleave', () => {
          hideWheelTooltip(container);
        });

        mainGroup.appendChild(path);
      });
    });

    // Cercle central (fermeture/annulation)
    const centerGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    centerGroup.setAttribute('class', 'ai-emotion-wheel__center');
    centerGroup.style.cursor = 'pointer';

    const centerCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    centerCircle.setAttribute('class', 'ai-emotion-wheel__center-bg');
    centerCircle.setAttribute('cx', cx);
    centerCircle.setAttribute('cy', cy);
    centerCircle.setAttribute('r', centerRadius - 2);

    const centerText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    centerText.setAttribute('class', 'ai-emotion-wheel__center-icon');
    centerText.setAttribute('x', cx);
    centerText.setAttribute('y', cy);
    centerText.textContent = '✨';

    centerGroup.appendChild(centerCircle);
    centerGroup.appendChild(centerText);
    // Story 7.13 - Clic sur le centre = reset a l'etat neutre (aucune emotion)
    centerGroup.addEventListener('click', (e) => {
      e.stopPropagation();
      if (onReset) {
        onReset();
      } else {
        onClose();
      }
    });

    svg.appendChild(mainGroup);
    svg.appendChild(centerGroup);
    container.appendChild(svg);

    // Creer le tooltip
    const tooltip = document.createElement('div');
    tooltip.className = 'ai-emotion-wheel__tooltip';
    container.appendChild(tooltip);

    return container;
  }

  // Afficher le tooltip de la roue
  function showWheelTooltip(wheelContainer, emotion, intensity, pathElement) {
    const tooltip = wheelContainer.querySelector('.ai-emotion-wheel__tooltip');
    if (!tooltip) return;

    const emotionLabel = t(emotion.key) || emotion.key;
    const intensityLabelText = t(intensity.labelKey) || intensity.key;
    const intensityLabel = `${t('intensity')} ${intensityLabelText.toLowerCase()}`;

    tooltip.textContent = `${emotionLabel} - ${intensityLabel}`;
    tooltip.classList.add('ai-emotion-wheel__tooltip--visible');

    // Story 7.13 - Mettre a jour l'icone centrale avec l'emoji de l'emotion survolee
    const centerIcon = wheelContainer.querySelector('.ai-emotion-wheel__center-icon');
    if (centerIcon) {
      centerIcon.textContent = emotion.emoji;
    }

    // Positionner le tooltip au-dessus de la zone survolee
    const wheelRect = wheelContainer.getBoundingClientRect();
    const pathRect = pathElement.getBoundingClientRect();

    const tooltipX = pathRect.left + pathRect.width / 2 - wheelRect.left;
    const tooltipY = pathRect.top - wheelRect.top - 8;

    tooltip.style.left = `${tooltipX}px`;
    tooltip.style.top = `${tooltipY}px`;
    tooltip.style.transform = 'translate(-50%, -100%)';
  }

  // Masquer le tooltip de la roue
  function hideWheelTooltip(wheelContainer) {
    const tooltip = wheelContainer.querySelector('.ai-emotion-wheel__tooltip');
    if (tooltip) {
      tooltip.classList.remove('ai-emotion-wheel__tooltip--visible');
    }
    // Story 7.13 - Restaurer l'icone centrale par defaut
    const centerIcon = wheelContainer.querySelector('.ai-emotion-wheel__center-icon');
    if (centerIcon) {
      centerIcon.textContent = '✨';
    }
  }

  // Reference globale a la roue ouverte
  let activeEmotionWheel = null;

  // Afficher/masquer la roue d'emotions autour d'un bouton
  function toggleEmotionWheel(triggerButton, commentBox) {
    // Story 7.14 - AC #7: Fermer la roue des styles si ouverte (exclusivite)
    if (activeStyleWheel) {
      closeStyleWheel();
    }

    // Si une roue d'emotions est deja ouverte, la fermer
    if (activeEmotionWheel) {
      closeEmotionWheel();
      return;
    }

    // Callback de selection
    const handleSelect = (emotionKey, intensityKey) => {
      // Stocker dans le commentBox
      commentBox.setAttribute('data-selected-emotion', emotionKey);
      commentBox.setAttribute('data-selected-intensity', intensityKey);

      // Sauvegarder dans chrome.storage
      chrome.storage.sync.set({
        emotion_wheel_selection: { emotion: emotionKey, intensity: intensityKey }
      });

      // Mettre a jour le chip emotion (pas le bouton generer)
      updateEmotionChip(triggerButton, emotionKey, intensityKey);

      // Log
      console.log('Emotion selectionnee:', emotionKey, 'Intensite:', intensityKey);

      // Track
      
      }

      // Fermer la roue
      closeEmotionWheel();
    };

    // Callback de fermeture
    const handleClose = () => {
      closeEmotionWheel();
    };

    // Callback de reset (clic sur le centre = supprime la selection)
    const handleReset = () => {
      // Supprimer les attributs d'emotion du commentBox
      commentBox.removeAttribute('data-selected-emotion');
      commentBox.removeAttribute('data-selected-intensity');

      // Supprimer de chrome.storage
      chrome.storage.sync.remove('emotion_wheel_selection');

      // Remettre le chip emotion a l'etat par defaut
      resetEmotionChipToDefault(triggerButton);

      // Log
      console.log('Emotion supprimee (aucune emotion forcee)');

      // Fermer la roue
      closeEmotionWheel();
    };

    // Creer la roue
    const wheel = createEmotionWheelSVG(commentBox, handleSelect, handleClose, handleReset);
    activeEmotionWheel = wheel;

    // Mettre a jour aria-expanded
    triggerButton.setAttribute('aria-expanded', 'true');
    wheel._triggerButton = triggerButton;

    // Positionner la roue centree sur le bouton
    const buttonRect = triggerButton.getBoundingClientRect();
    const wheelSize = EMOTION_WHEEL_CONFIG.size;

    // Position absolue dans le viewport
    wheel.style.position = 'fixed';
    wheel.style.left = `${buttonRect.left + buttonRect.width / 2 - wheelSize / 2}px`;
    wheel.style.top = `${buttonRect.top + buttonRect.height / 2 - wheelSize / 2}px`;

    // Verifier les debordements viewport
    requestAnimationFrame(() => {
      const wheelRect = wheel.getBoundingClientRect();

      // Ajuster si deborde a droite
      if (wheelRect.right > window.innerWidth - 10) {
        wheel.style.left = `${window.innerWidth - wheelSize - 10}px`;
      }
      // Ajuster si deborde a gauche
      if (wheelRect.left < 10) {
        wheel.style.left = '10px';
      }
      // Ajuster si deborde en bas
      if (wheelRect.bottom > window.innerHeight - 10) {
        wheel.style.top = `${window.innerHeight - wheelSize - 10}px`;
      }
      // Ajuster si deborde en haut
      if (wheelRect.top < 10) {
        wheel.style.top = '10px';
      }
    });

    // Ajouter au document
    document.body.appendChild(wheel);

    // Animer l'ouverture
    requestAnimationFrame(() => {
      wheel.classList.add('ai-emotion-wheel--open');
    });

    // Fermer au clic en dehors
    const closeOnOutsideClick = (e) => {
      if (!wheel.contains(e.target) && e.target !== triggerButton) {
        closeEmotionWheel();
        document.removeEventListener('click', closeOnOutsideClick);
      }
    };
    setTimeout(() => {
      document.addEventListener('click', closeOnOutsideClick);
    }, 10);

    // Story 7.13 - Task 6: Navigation clavier complete
    const { emotions, intensities } = EMOTION_WHEEL_CONFIG;
    let focusedEmotionIndex = 0;
    let focusedIntensityIndex = 1; // Medium par defaut

    // Fonction pour mettre a jour le focus visuel
    const updateFocus = () => {
      // Retirer le focus de toutes les zones
      wheel.querySelectorAll('.ai-emotion-wheel__zone').forEach(zone => {
        zone.classList.remove('ai-emotion-wheel__zone--focused');
      });

      // Ajouter le focus a la zone courante
      const focusedZone = wheel.querySelector(
        `.ai-emotion-wheel__zone[data-emotion="${emotions[focusedEmotionIndex].key}"][data-intensity="${intensities[focusedIntensityIndex].key}"]`
      );
      if (focusedZone) {
        focusedZone.classList.add('ai-emotion-wheel__zone--focused');
        // Afficher le tooltip
        showWheelTooltip(wheel, emotions[focusedEmotionIndex], intensities[focusedIntensityIndex], focusedZone);
      }
    };

    const handleKeydown = (e) => {
      switch (e.key) {
        case 'Escape':
          closeEmotionWheel();
          triggerButton.focus();
          break;

        case 'ArrowLeft':
          e.preventDefault();
          focusedEmotionIndex = (focusedEmotionIndex - 1 + emotions.length) % emotions.length;
          updateFocus();
          break;

        case 'ArrowRight':
          e.preventDefault();
          focusedEmotionIndex = (focusedEmotionIndex + 1) % emotions.length;
          updateFocus();
          break;

        case 'ArrowUp':
          e.preventDefault();
          // Plus d'intensite (vers l'exterieur)
          focusedIntensityIndex = Math.min(focusedIntensityIndex + 1, intensities.length - 1);
          updateFocus();
          break;

        case 'ArrowDown':
          e.preventDefault();
          // Moins d'intensite (vers le centre)
          focusedIntensityIndex = Math.max(focusedIntensityIndex - 1, 0);
          updateFocus();
          break;

        case 'Enter':
        case ' ':
          e.preventDefault();
          handleSelect(emotions[focusedEmotionIndex].key, intensities[focusedIntensityIndex].key);
          triggerButton.focus();
          break;

        default:
          break;
      }
    };
    document.addEventListener('keydown', handleKeydown);

    // Focus initial sur la roue
    wheel.focus();

    // Stocker les handlers pour cleanup
    wheel._closeHandlers = { click: closeOnOutsideClick, keydown: handleKeydown };
  }

  // Fermer la roue d'emotions
  function closeEmotionWheel() {
    if (!activeEmotionWheel) return;

    const wheel = activeEmotionWheel;

    // Cleanup handlers
    if (wheel._closeHandlers) {
      document.removeEventListener('click', wheel._closeHandlers.click);
      document.removeEventListener('keydown', wheel._closeHandlers.keydown);
    }

    // Mettre a jour aria-expanded sur le bouton declencheur
    if (wheel._triggerButton) {
      wheel._triggerButton.setAttribute('aria-expanded', 'false');
    }

    // Animation de fermeture
    wheel.classList.remove('ai-emotion-wheel--open');
    wheel.classList.add('ai-emotion-wheel--closing');

    setTimeout(() => {
      wheel.remove();
    }, 150);

    activeEmotionWheel = null;
  }

  // Remettre le bouton a son etat par defaut (apres generation)
  function resetButtonToDefault(button, commentBox) {
    // Retirer les classes d'emotion
    EMOTION_WHEEL_CONFIG.emotions.forEach(e => {
      button.classList.remove(`ai-button--emotion-${e.key}`);
    });
    button.classList.remove('ai-button--emotion-selected');

    // Remettre le label par defaut
    const labelSpan = button.querySelector('.ai-button__label');
    if (labelSpan) {
      labelSpan.textContent = t('generate');
    }

    // Remettre l'icone par defaut
    const iconSpan = button.querySelector('.ai-button__icon');
    if (iconSpan) {
      iconSpan.textContent = '✨';
    }

    // Retirer les attributs d'emotion du commentBox
    if (commentBox) {
      commentBox.removeAttribute('data-selected-emotion');
      commentBox.removeAttribute('data-selected-intensity');
    }

    console.log('Bouton reset a l\'etat par defaut');
  }

  // Mettre a jour l'apparence du chip emotion avec l'emotion selectionnee
  function updateEmotionChip(chip, emotionKey, intensityKey) {
    // Trouver l'emotion dans la config
    const emotion = EMOTION_WHEEL_CONFIG.emotions.find(e => e.key === emotionKey);
    if (!emotion) return;

    // Retirer les classes d'emotion precedentes
    EMOTION_WHEEL_CONFIG.emotions.forEach(e => {
      chip.classList.remove(`ai-button--emotion-${e.key}`);
    });
    chip.classList.remove('ai-button--emotion-selected');

    // Ajouter les nouvelles classes
    chip.classList.add('ai-button--emotion-selected');
    chip.classList.add(`ai-button--emotion-${emotionKey}`);

    // Mettre a jour le label du chip
    const labelSpan = chip.querySelector('.ai-chip__label');
    if (labelSpan) {
      // Label court pour l'emotion
      const shortLabel = getShortEmotionLabel(emotionKey, intensityKey);
      labelSpan.textContent = shortLabel;
    }

    // Mettre a jour l'icone avec l'emoji de l'emotion
    const iconSpan = chip.querySelector('.ai-chip__icon');
    if (iconSpan) {
      iconSpan.textContent = emotion.emoji;
    }
  }

  // Obtenir un label court pour l'emotion (pour affichage compact)
  function getShortEmotionLabel(emotionKey, intensityKey) {
    const shortLabels = {
      admiration: 'Admire',
      inspiration: 'Inspire',
      curiosity: 'Curieux',
      gratitude: 'Merci',
      empathy: 'Empathie',
      skepticism: 'Sceptique'
    };
    return shortLabels[emotionKey] || emotionKey;
  }

  // Remettre le chip emotion a son etat par defaut
  function resetEmotionChipToDefault(chip) {
    // Retirer les classes d'emotion
    EMOTION_WHEEL_CONFIG.emotions.forEach(e => {
      chip.classList.remove(`ai-button--emotion-${e.key}`);
    });
    chip.classList.remove('ai-button--emotion-selected');

    // Remettre le label par defaut
    const labelSpan = chip.querySelector('.ai-chip__label');
    if (labelSpan) {
      labelSpan.textContent = 'Emotion';
    }

    // Remettre l'icone par defaut
    const iconSpan = chip.querySelector('.ai-chip__icon');
    if (iconSpan) {
      iconSpan.textContent = '✨';
    }
  }

  // ================================================
  // STYLE WHEEL FUNCTIONS (Story 7.14)
  // ================================================

  // Reference globale a la roue de style ouverte
  let activeStyleWheel = null;

  // Story 7.14 Review - Reutilise describeArc() defini plus haut (DRY)

  // Creation du SVG de la roue des styles
  function createStyleWheelSVG(commentBox, onSelect, onClose, onReset) {
    const { size, centerRadius, outerRadius, styles } = STYLE_WHEEL_CONFIG;
    const cx = size / 2;
    const cy = size / 2;
    const sectionAngle = 360 / styles.length; // ~51.4 degres par style (7 sections)

    // Creer le conteneur
    const container = document.createElement('div');
    container.className = 'ai-style-wheel';
    container.setAttribute('role', 'listbox');
    container.setAttribute('aria-label', t('languageStyle') || 'Selectionner le style de langage');
    container.setAttribute('tabindex', '0');

    // Creer le SVG
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'ai-style-wheel__svg');
    svg.setAttribute('viewBox', `0 0 ${size} ${size}`);
    svg.setAttribute('width', size);
    svg.setAttribute('height', size);

    // Creer le groupe principal
    const mainGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');

    // Creer les zones pour chaque style (un seul anneau, pas d'intensites)
    styles.forEach((style, styleIndex) => {
      const startAngle = styleIndex * sectionAngle;
      const endAngle = startAngle + sectionAngle;

      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('class', 'ai-style-wheel__zone');
      path.setAttribute('d', describeArc(cx, cy, centerRadius, outerRadius, startAngle, endAngle));
      path.setAttribute('data-style', style.key);
      path.setAttribute('role', 'option');
      path.setAttribute('aria-label', t(style.key) || style.key);
      path.setAttribute('tabindex', '-1');

      // Couleur du style
      path.style.fill = style.color;

      // Evenements
      path.addEventListener('click', (e) => {
        e.stopPropagation();
        onSelect(style.key);
      });

      path.addEventListener('mouseenter', () => {
        showStyleWheelTooltip(container, style, path);
      });

      path.addEventListener('mouseleave', () => {
        hideStyleWheelTooltip(container);
      });

      mainGroup.appendChild(path);
    });

    // Cercle central (fermeture/reset)
    const centerGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    centerGroup.setAttribute('class', 'ai-style-wheel__center');
    centerGroup.style.cursor = 'pointer';

    const centerCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    centerCircle.setAttribute('class', 'ai-style-wheel__center-bg');
    centerCircle.setAttribute('cx', cx);
    centerCircle.setAttribute('cy', cy);
    centerCircle.setAttribute('r', centerRadius - 2);

    const centerText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    centerText.setAttribute('class', 'ai-style-wheel__center-icon');
    centerText.setAttribute('x', cx);
    centerText.setAttribute('y', cy);
    centerText.textContent = '🎨';

    centerGroup.appendChild(centerCircle);
    centerGroup.appendChild(centerText);
    // Story 7.14 - Clic sur le centre = reset au style par defaut (professional)
    centerGroup.addEventListener('click', (e) => {
      e.stopPropagation();
      if (onReset) {
        onReset();
      } else {
        onClose();
      }
    });

    svg.appendChild(mainGroup);
    svg.appendChild(centerGroup);
    container.appendChild(svg);

    // Creer le tooltip
    const tooltip = document.createElement('div');
    tooltip.className = 'ai-style-wheel__tooltip';
    container.appendChild(tooltip);

    return container;
  }

  // Afficher le tooltip de la roue des styles
  function showStyleWheelTooltip(wheelContainer, style, pathElement) {
    const tooltip = wheelContainer.querySelector('.ai-style-wheel__tooltip');
    if (!tooltip) return;

    const styleLabel = t(style.key) || style.key;
    tooltip.textContent = styleLabel;
    tooltip.classList.add('ai-style-wheel__tooltip--visible');

    // Story 7.14 - Mettre a jour l'icone centrale avec l'emoji du style survole
    const centerIcon = wheelContainer.querySelector('.ai-style-wheel__center-icon');
    if (centerIcon) {
      centerIcon.textContent = style.emoji;
    }

    // Positionner le tooltip au-dessus de la zone survolee
    const wheelRect = wheelContainer.getBoundingClientRect();
    const pathRect = pathElement.getBoundingClientRect();

    const tooltipX = pathRect.left + pathRect.width / 2 - wheelRect.left;
    const tooltipY = pathRect.top - wheelRect.top - 8;

    tooltip.style.left = `${tooltipX}px`;
    tooltip.style.top = `${tooltipY}px`;
    tooltip.style.transform = 'translate(-50%, -100%)';
  }

  // Masquer le tooltip de la roue des styles
  function hideStyleWheelTooltip(wheelContainer) {
    const tooltip = wheelContainer.querySelector('.ai-style-wheel__tooltip');
    if (tooltip) {
      tooltip.classList.remove('ai-style-wheel__tooltip--visible');
    }
    // Story 7.14 - Restaurer l'icone centrale par defaut
    const centerIcon = wheelContainer.querySelector('.ai-style-wheel__center-icon');
    if (centerIcon) {
      centerIcon.textContent = '🎨';
    }
  }

  // Afficher/masquer la roue de styles autour d'un bouton
  function toggleStyleWheel(triggerButton, commentBox) {
    // Story 7.14 - AC #7: Fermer la roue des emotions si ouverte (exclusivite)
    if (activeEmotionWheel) {
      closeEmotionWheel();
    }

    // Si une roue de style est deja ouverte, la fermer
    if (activeStyleWheel) {
      closeStyleWheel();
      return;
    }

    // Callback de selection
    const handleSelect = (styleKey) => {
      // Stocker dans le commentBox
      commentBox.setAttribute('data-selected-style', styleKey);

      // Sauvegarder dans chrome.storage
      chrome.storage.sync.set({
        style_wheel_selection: { style: styleKey }
      });

      // Mettre a jour le bouton
      updateButtonWithStyle(triggerButton, styleKey);

      // Track
      
      }

      // Fermer la roue
      closeStyleWheel();
    };

    // Callback de fermeture
    const handleClose = () => {
      closeStyleWheel();
    };

    // Story 7.14 - Callback de reset (clic sur le centre = supprime la selection)
    const handleReset = () => {
      // Supprimer l'attribut de style du commentBox
      commentBox.removeAttribute('data-selected-style');

      // Supprimer de chrome.storage
      chrome.storage.sync.remove('style_wheel_selection');

      // Remettre le bouton a l'etat par defaut (pas de style)
      resetStyleButtonToDefault(triggerButton);

      // Fermer la roue
      closeStyleWheel();
    };

    // Creer la roue
    const wheel = createStyleWheelSVG(commentBox, handleSelect, handleClose, handleReset);
    activeStyleWheel = wheel;

    // Mettre a jour aria-expanded
    triggerButton.setAttribute('aria-expanded', 'true');
    wheel._triggerButton = triggerButton;

    // Positionner la roue centree sur le bouton
    const buttonRect = triggerButton.getBoundingClientRect();
    const wheelSize = STYLE_WHEEL_CONFIG.size;

    // Position absolue dans le viewport
    wheel.style.position = 'fixed';
    wheel.style.left = `${buttonRect.left + buttonRect.width / 2 - wheelSize / 2}px`;
    wheel.style.top = `${buttonRect.top + buttonRect.height / 2 - wheelSize / 2}px`;

    // Verifier les debordements viewport
    requestAnimationFrame(() => {
      const wheelRect = wheel.getBoundingClientRect();

      // Ajuster si deborde a droite
      if (wheelRect.right > window.innerWidth - 10) {
        wheel.style.left = `${window.innerWidth - wheelSize - 10}px`;
      }
      // Ajuster si deborde a gauche
      if (wheelRect.left < 10) {
        wheel.style.left = '10px';
      }
      // Ajuster si deborde en bas
      if (wheelRect.bottom > window.innerHeight - 10) {
        wheel.style.top = `${window.innerHeight - wheelSize - 10}px`;
      }
      // Ajuster si deborde en haut
      if (wheelRect.top < 10) {
        wheel.style.top = '10px';
      }
    });

    // Ajouter au document
    document.body.appendChild(wheel);

    // Animer l'ouverture
    requestAnimationFrame(() => {
      wheel.classList.add('ai-style-wheel--open');
    });

    // Fermer au clic en dehors
    const closeOnOutsideClick = (e) => {
      if (!wheel.contains(e.target) && e.target !== triggerButton) {
        closeStyleWheel();
        document.removeEventListener('click', closeOnOutsideClick);
      }
    };
    setTimeout(() => {
      document.addEventListener('click', closeOnOutsideClick);
    }, 10);

    // Story 7.14 - Task 8: Navigation clavier
    const { styles } = STYLE_WHEEL_CONFIG;
    let focusedStyleIndex = 0;

    // Fonction pour mettre a jour le focus visuel
    const updateFocus = () => {
      // Retirer le focus de toutes les zones
      wheel.querySelectorAll('.ai-style-wheel__zone').forEach(zone => {
        zone.classList.remove('ai-style-wheel__zone--focused');
      });

      // Ajouter le focus a la zone courante
      const focusedZone = wheel.querySelector(
        `.ai-style-wheel__zone[data-style="${styles[focusedStyleIndex].key}"]`
      );
      if (focusedZone) {
        focusedZone.classList.add('ai-style-wheel__zone--focused');
        // Afficher le tooltip
        showStyleWheelTooltip(wheel, styles[focusedStyleIndex], focusedZone);
      }
    };

    const handleKeydown = (e) => {
      switch (e.key) {
        case 'Escape':
          closeStyleWheel();
          triggerButton.focus();
          break;

        case 'ArrowLeft':
          e.preventDefault();
          focusedStyleIndex = (focusedStyleIndex - 1 + styles.length) % styles.length;
          updateFocus();
          break;

        case 'ArrowRight':
          e.preventDefault();
          focusedStyleIndex = (focusedStyleIndex + 1) % styles.length;
          updateFocus();
          break;

        case 'ArrowUp':
        case 'ArrowDown':
          // Pas de mouvement vertical (pas d'anneaux d'intensite)
          e.preventDefault();
          break;

        case 'Enter':
        case ' ':
          e.preventDefault();
          handleSelect(styles[focusedStyleIndex].key);
          triggerButton.focus();
          break;

        default:
          break;
      }
    };
    document.addEventListener('keydown', handleKeydown);

    // Focus initial sur la roue
    wheel.focus();

    // Stocker les handlers pour cleanup
    wheel._closeHandlers = { click: closeOnOutsideClick, keydown: handleKeydown };
  }

  // Fermer la roue de styles
  function closeStyleWheel() {
    if (!activeStyleWheel) return;

    const wheel = activeStyleWheel;

    // Cleanup handlers
    if (wheel._closeHandlers) {
      document.removeEventListener('click', wheel._closeHandlers.click);
      document.removeEventListener('keydown', wheel._closeHandlers.keydown);
    }

    // Mettre a jour aria-expanded sur le bouton declencheur
    if (wheel._triggerButton) {
      wheel._triggerButton.setAttribute('aria-expanded', 'false');
    }

    // Animation de fermeture
    wheel.classList.remove('ai-style-wheel--open');
    wheel.classList.add('ai-style-wheel--closing');

    setTimeout(() => {
      wheel.remove();
    }, 150);

    activeStyleWheel = null;
  }

  // Mettre a jour l'apparence du bouton avec le style selectionne
  function updateButtonWithStyle(button, styleKey) {
    // Trouver le style dans la config
    const style = STYLE_WHEEL_CONFIG.styles.find(s => s.key === styleKey);
    if (!style) return;

    // Retirer les classes de style precedentes
    STYLE_WHEEL_CONFIG.styles.forEach(s => {
      button.classList.remove(`ai-button--style-${s.key}`);
    });
    button.classList.remove('ai-button--style-selected');

    // Ajouter les nouvelles classes
    button.classList.add('ai-button--style-selected');
    button.classList.add(`ai-button--style-${styleKey}`);

    // Mettre a jour le label du bouton
    const labelSpan = button.querySelector('.ai-chip__label');
    if (labelSpan) {
      // Utiliser un label court (tronque si necessaire)
      const shortLabel = getShortStyleLabel(styleKey);
      labelSpan.textContent = shortLabel;
    }

    // Mettre a jour l'icone avec l'emoji du style
    const iconSpan = button.querySelector('.ai-chip__icon');
    if (iconSpan) {
      iconSpan.textContent = style.emoji;
    }
  }

  // Obtenir un label court pour le style (pour affichage compact)
  function getShortStyleLabel(styleKey) {
    const shortLabels = {
      oral: 'Oral',
      professional: 'Pro',
      storytelling: 'Story',
      poetic: 'Créatif',
      humoristic: 'Humour',
      impactful: 'Impact',
      benevolent: 'Positif'
    };
    return shortLabels[styleKey] || styleKey;
  }

  // Remettre le bouton de style a son etat par defaut
  function resetStyleButtonToDefault(button) {
    // Retirer les classes de style
    STYLE_WHEEL_CONFIG.styles.forEach(s => {
      button.classList.remove(`ai-button--style-${s.key}`);
    });
    button.classList.remove('ai-button--style-selected');

    // Remettre le label par defaut (Story 7.14 Review - coherence avec creation du chip)
    const labelSpan = button.querySelector('.ai-chip__label');
    if (labelSpan) {
      labelSpan.textContent = t('languageStyle') || 'Style';
    }

    // Remettre l'icone par defaut
    const iconSpan = button.querySelector('.ai-chip__icon');
    if (iconSpan) {
      iconSpan.textContent = '🎨';
    }
  }

  // Fonction pour afficher/masquer le panneau d'émotions
  function toggleEmotionsPanel(buttonsWrapper, commentBox) {
    // Vérifier si le panneau existe déjà
    let emotionsPanel = buttonsWrapper.querySelector('.ai-emotions-container');

    if (emotionsPanel) {
      // Si le panneau existe, le supprimer avec animation
      emotionsPanel.style.animation = 'emotionsPanelDisappear 0.2s ease forwards';
      setTimeout(() => emotionsPanel.remove(), 200);
    } else {
      // Créer le panneau d'émotions avec état de chargement
      emotionsPanel = document.createElement('div');
      emotionsPanel.className = 'ai-emotions-container loading';

      // Ajouter le spinner de chargement
      const loadingSpinner = document.createElement('div');
      loadingSpinner.className = 'ai-emotions-loading-spinner';
      const loadingText = document.createElement('div');
      loadingText.className = 'ai-emotions-loading-text';
      loadingText.textContent = 'Chargement...';
      loadingSpinner.appendChild(loadingText);
      emotionsPanel.appendChild(loadingSpinner);

      // Insérer le panneau immédiatement pour avoir la position correcte
      buttonsWrapper.appendChild(emotionsPanel);

      // Forcer un reflow pour calculer la position
      void emotionsPanel.offsetHeight;

      // Vérifier si le panneau déborde de l'écran
      requestAnimationFrame(() => {
        const panelRect = emotionsPanel.getBoundingClientRect();
        const viewportWidth = window.innerWidth;

        // Si déborde à droite, aligner à droite
        if (panelRect.right > viewportWidth - 20) {
          emotionsPanel.style.left = 'auto';
          emotionsPanel.style.right = '0';
        }

        // Si déborde en bas, afficher au-dessus
        const viewportHeight = window.innerHeight;
        if (panelRect.bottom > viewportHeight - 20) {
          emotionsPanel.style.top = 'auto';
          emotionsPanel.style.bottom = '100%';
          emotionsPanel.style.marginTop = '0';
          emotionsPanel.style.marginBottom = '8px';
        }

        // Construire le contenu après un court délai (effet de chargement)
        setTimeout(() => {
          buildEmotionsContent(emotionsPanel, commentBox);
        }, 150);
      });
    }
  }

  // Fonction pour construire le contenu du panneau d'émotions
  function buildEmotionsContent(emotionsPanel, commentBox) {
    // Retirer le spinner de chargement
    emotionsPanel.innerHTML = '';
    emotionsPanel.classList.remove('loading');
    emotionsPanel.classList.add('visible');

    // Définir les émotions avec leurs emojis pour chaque intensité
    const emotions = [
      {
        emoji: '🌟',
        key: 'admiration',
        label: t('admiration'),
        intensities: {
          low: '😊',
          medium: '👏',
          high: '🤩'
        }
      },
      {
        emoji: '💡',
        key: 'inspiration',
        label: t('inspiration'),
        intensities: {
          low: '💡',
          medium: '✨',
          high: '🔥'
        }
      },
      {
        emoji: '🤔',
        key: 'curiosity',
        label: t('curiosity'),
        intensities: {
          low: '🤔',
          medium: '🧐',
          high: '😲'
        }
      },
      {
        emoji: '🙏',
        key: 'gratitude',
        label: t('gratitude'),
        intensities: {
          low: '🙂',
          medium: '🙏',
          high: '🥰'
        }
      },
      {
        emoji: '❤️',
        key: 'empathy',
        label: t('empathy'),
        intensities: {
          low: '🤝',
          medium: '💬',
          high: '❤️'
        }
      },
      {
        emoji: '🧐',
        key: 'skepticism',
        label: t('skepticism'),
        intensities: {
          low: '😐',
          medium: '🤨',
          high: '😅'
        }
      }
    ];

    // Créer l'en-tête de la matrice
    const header = document.createElement('div');
    header.className = 'ai-emotion-matrix-header';

    const emptyCell = document.createElement('div');
    emptyCell.className = 'ai-emotion-matrix-cell header-cell empty';
    header.appendChild(emptyCell);

    const intensityLevels = [
      { key: 'low', emoji: '🟢', label: 'Faible' },
      { key: 'medium', emoji: '🟡', label: 'Moyen' },
      { key: 'high', emoji: '🔴', label: 'Fort' }
    ];

    intensityLevels.forEach(level => {
      const headerCell = document.createElement('div');
      headerCell.className = 'ai-emotion-matrix-cell header-cell';
      headerCell.textContent = level.emoji;
      headerCell.title = level.label;
      header.appendChild(headerCell);
    });

    emotionsPanel.appendChild(header);

    // Créer une ligne pour chaque émotion
    emotions.forEach(emotion => {
      const row = document.createElement('div');
      row.className = 'ai-emotion-matrix-row';

      // Cellule de label (première colonne)
      const labelCell = document.createElement('div');
      labelCell.className = 'ai-emotion-matrix-cell label-cell';
      labelCell.innerHTML = `<span class="emotion-icon">${emotion.emoji}</span><span class="emotion-label">${emotion.label}</span>`;
      row.appendChild(labelCell);

      // Cellules d'intensité
      intensityLevels.forEach(level => {
        const intensityCell = document.createElement('div');
        intensityCell.className = `ai-emotion-matrix-cell intensity-cell intensity-${level.key}`;
        intensityCell.setAttribute('data-emotion', emotion.key);
        intensityCell.setAttribute('data-intensity', level.key);
        intensityCell.textContent = emotion.intensities[level.key];

        // Gérer le clic sur l'émotion avec intensité
        intensityCell.onclick = () => handleEmotionClick(intensityCell, emotion, commentBox, level.key);

        row.appendChild(intensityCell);
      });

      emotionsPanel.appendChild(row);
    });

    // Ajouter le séparateur et le titre pour les styles de langage
    const stylesSeparator = document.createElement('div');
    stylesSeparator.className = 'ai-styles-separator';
    emotionsPanel.appendChild(stylesSeparator);

    const stylesTitle = document.createElement('div');
    stylesTitle.className = 'ai-styles-title';
    stylesTitle.textContent = t('languageStyle');
    emotionsPanel.appendChild(stylesTitle);

    // Définir les styles de langage
    const styles = [
      { emoji: '🗣️', key: 'oral', label: t('oral') },
      { emoji: '💼', key: 'professional', label: t('professional') },
      { emoji: '📖', key: 'storytelling', label: t('storytelling') },
      { emoji: '🎨', key: 'poetic', label: t('poetic') },
      { emoji: '😂', key: 'humoristic', label: t('humoristic') },
      { emoji: '⚡', key: 'impactful', label: t('impactful') },
      { emoji: '🤝', key: 'benevolent', label: t('benevolent') }
    ];

    // Créer le conteneur de styles
    const stylesContainer = document.createElement('div');
    stylesContainer.className = 'ai-styles-container';

    styles.forEach(style => {
      const styleButton = document.createElement('button');
      styleButton.className = 'ai-style-button';
      styleButton.setAttribute('data-style', style.key);
      styleButton.innerHTML = `<span class="style-emoji">${style.emoji}</span><span class="style-label">${style.label}</span>`;

      // Gérer le clic sur le style
      styleButton.onclick = () => handleStyleClick(styleButton, style, commentBox);

      stylesContainer.appendChild(styleButton);
    });

    emotionsPanel.appendChild(stylesContainer);
  }

  // Fonction pour gérer le clic sur un style
  function handleStyleClick(styleButton, style, commentBox) {
    // Retirer la sélection des autres styles
    const stylesContainer = styleButton.closest('.ai-styles-container');
    stylesContainer.querySelectorAll('.ai-style-button').forEach(btn => {
      btn.classList.remove('selected');
    });

    // Sélectionner le style cliqué
    styleButton.classList.add('selected');

    // Stocker le style sélectionné dans un attribut du commentBox
    commentBox.setAttribute('data-selected-style', style.key);

    console.log('Style sélectionné:', style.key);

    // Track style selection
    
    }
  }

  // Fonction pour gérer le clic sur une émotion
  function handleEmotionClick(emotionButton, emotion, commentBox, intensity) {
    // Retirer la sélection des autres émotions
    const emotionsContainer = emotionButton.closest('.ai-emotions-container');
    emotionsContainer.querySelectorAll('.intensity-cell').forEach(cell => {
      cell.classList.remove('selected');
    });

    // Sélectionner l'émotion cliquée
    emotionButton.classList.add('selected');

    // Stocker l'émotion et l'intensité sélectionnées dans des attributs du commentBox
    commentBox.setAttribute('data-selected-emotion', emotion.key);
    commentBox.setAttribute('data-selected-intensity', intensity);

    console.log('Émotion sélectionnée:', emotion.key, 'Intensité:', intensity);

    // Track emotion selection
    
    }
  }

  // ================================================
  // Create Inline Mode Controls
  // Creates the chip-based UI for regular users
  // Chips: horizontal layout with labels courts
  // ================================================
  function createInlineModeControls(commentBox, userPlan, isNegative, isReplyToComment) {
    const isPremium = userPlan === 'PREMIUM';
    const isMediumPlus = userPlan === 'MEDIUM' || userPlan === 'PREMIUM';

    // Container principal
    const container = document.createElement('div');
    container.className = 'ai-controls ai-controls--inline';
    container.setAttribute('data-viewport', 'normal');
    container.setAttribute('role', 'region');
    container.setAttribute('aria-label', 'AI Comment Generator');

    // Helper pour creer un chip d'action
    const createActionChip = (icon, labelKey, onClick, variant = 'secondary') => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = `ai-chip ai-chip--${variant}`;
      if (isNegative) chip.classList.add('negative');
      if (isReplyToComment) chip.classList.add('reply-mode');
      chip.innerHTML = `<span class="ai-chip__icon">${icon}</span><span class="ai-chip__label">${t(labelKey)}</span>`;
      chip.setAttribute('aria-label', t(labelKey));
      chip.onclick = onClick;
      return chip;
    };

    // Helper pour creer un chip toggle
    const createToggleChip = (icon, labelKey, dataAttr, ariaLabelKey, lockedMessageKey, requiredPlan = 'PREMIUM') => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.setAttribute('aria-pressed', 'false');

      // Determiner si l'utilisateur a acces
      const hasAccess = requiredPlan === 'MEDIUM' ? isMediumPlus : isPremium;

      if (!hasAccess) {
        chip.className = 'ai-chip ai-chip--locked';
        chip.setAttribute('aria-disabled', 'true');
        chip.setAttribute('aria-label', t(ariaLabelKey) + ' (Premium)');
        chip.setAttribute('tabindex', '-1'); // Story 7.10 - Retirer du flux de tabulation
        chip.innerHTML = `<span class="ai-chip__icon">${icon}</span><span class="ai-chip__label">${t(labelKey)}</span><span class="ai-chip__lock">🔒</span>`;
      } else {
        chip.className = 'ai-chip ai-chip--inactive';
        chip.setAttribute('aria-label', t(ariaLabelKey));
        chip.innerHTML = `<span class="ai-chip__icon">${icon}</span><span class="ai-chip__label">${t(labelKey)}</span>`;
      }

      if (isNegative) chip.classList.add('negative');
      if (isReplyToComment) chip.classList.add('reply-mode');

      chip.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();

        if (!hasAccess) {
          showPremiumUpgradePrompt(t(lockedMessageKey));
          return;
        }

        const isActive = commentBox.getAttribute(dataAttr) === 'true';
        if (isActive) {
          commentBox.removeAttribute(dataAttr);
          chip.classList.remove('ai-chip--active');
          chip.classList.add('ai-chip--inactive');
          chip.setAttribute('aria-pressed', 'false');
          chip.innerHTML = `<span class="ai-chip__icon">${icon}</span><span class="ai-chip__label">${t(labelKey)}</span>`;
        } else {
          commentBox.setAttribute(dataAttr, 'true');
          chip.classList.remove('ai-chip--inactive');
          chip.classList.add('ai-chip--active');
          chip.setAttribute('aria-pressed', 'true');
          chip.innerHTML = `<span class="ai-chip__icon">${icon}</span><span class="ai-chip__label">${t(labelKey)}</span><span class="ai-chip__check">✓</span>`;
        }

        const storageKey = `toggle_${dataAttr.replace('data-', '')}`;
        chrome.storage.local.set({ [storageKey]: !isActive });
      };

      return chip;
    };

    // Helper pour creer un chip d'action avec gestion premium
    const createPremiumActionChip = (icon, labelKey, ariaLabelKey, onClick, variant = 'secondary', lockedMessageKey = 'premiumRequired') => {
      const chip = document.createElement('button');
      chip.type = 'button';

      if (!isPremium) {
        chip.className = `ai-chip ai-chip--${variant} ai-chip--locked`;
        chip.setAttribute('aria-disabled', 'true');
        chip.setAttribute('aria-label', t(ariaLabelKey) + ' (Premium)');
        chip.setAttribute('tabindex', '-1'); // Story 7.10 - Retirer du flux de tabulation
        chip.innerHTML = `<span class="ai-chip__icon">${icon}</span><span class="ai-chip__label">${t(labelKey)}</span><span class="ai-chip__lock">🔒</span>`;
      } else {
        chip.className = `ai-chip ai-chip--${variant}`;
        chip.setAttribute('aria-label', t(ariaLabelKey));
        chip.innerHTML = `<span class="ai-chip__icon">${icon}</span><span class="ai-chip__label">${t(labelKey)}</span>`;
      }

      if (isNegative) chip.classList.add('negative');
      if (isReplyToComment) chip.classList.add('reply-mode');

      chip.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!isPremium) {
          showPremiumUpgradePrompt(t(lockedMessageKey));
          return;
        }
        onClick(e);
      };

      return chip;
    };

    // === CHIPS D'ACTION ===
    // Story 7.13 - Le bouton generate ouvre la roue si aucune emotion selectionnee,
    // sinon lance la generation
    const generateChip = document.createElement('button');
    generateChip.type = 'button';
    generateChip.className = 'ai-button ai-button--primary';
    if (isNegative) generateChip.classList.add('ai-button--negative');
    if (isReplyToComment) generateChip.classList.add('ai-button--reply-mode');
    generateChip.innerHTML = `<span class="ai-button__icon">✨</span><span class="ai-button__label">${t('generate')}</span>`;
    generateChip.setAttribute('aria-label', t('generateAriaLabel') || t('generate'));
    generateChip.setAttribute('aria-expanded', 'false');

    // Story 7.14 - Le bouton generate lance toujours la generation
    // L'emotion n'est envoyee QUE si l'utilisateur l'a selectionnee via le chip Emotion
    generateChip.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      handleGenerateClick(e, commentBox, isReplyToComment);
    };

    // Chip Prompt : reserve aux plans MEDIUM et PREMIUM
    const promptChip = document.createElement('button');
    promptChip.type = 'button';
    if (!isMediumPlus) {
      // User FREE : afficher cadenas
      promptChip.className = 'ai-chip ai-chip--secondary ai-chip--locked';
      promptChip.setAttribute('aria-disabled', 'true');
      promptChip.setAttribute('aria-label', t('withPrompt') + ' (Premium)');
      promptChip.setAttribute('tabindex', '-1');
      promptChip.innerHTML = `<span class="ai-chip__icon">💭</span><span class="ai-chip__label">${t('withPrompt')}</span><span class="ai-chip__lock">🔒</span>`;
    } else {
      promptChip.className = 'ai-chip ai-chip--secondary';
      promptChip.setAttribute('aria-label', t('withPrompt'));
      promptChip.innerHTML = `<span class="ai-chip__icon">💭</span><span class="ai-chip__label">${t('withPrompt')}</span>`;
    }
    if (isNegative) promptChip.classList.add('negative');
    if (isReplyToComment) promptChip.classList.add('reply-mode');
    promptChip.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (!isMediumPlus) {
        showPremiumUpgradePrompt(t('promptRequiresPremium') || 'Le prompt personnalise necessite un plan MEDIUM ou PREMIUM');
        return;
      }
      handlePromptClick(e, commentBox, isReplyToComment);
    };

    const randomChip = createActionChip('🎲', 'randomGenerate', (e) => {
      e.preventDefault();
      e.stopPropagation();
      handleRandomGenerate(e, commentBox, isReplyToComment);
    }, 'secondary');

    // Chip Emotion : ouvre la roue des emotions (modifie pour fonctionner comme Style)
    const emotionChip = document.createElement('button');
    emotionChip.type = 'button';
    emotionChip.className = 'ai-chip ai-chip--secondary';
    emotionChip.setAttribute('data-chip-type', 'emotion');
    emotionChip.setAttribute('aria-label', 'Emotion');
    emotionChip.setAttribute('aria-haspopup', 'true');
    emotionChip.setAttribute('aria-expanded', 'false');
    emotionChip.innerHTML = `<span class="ai-chip__icon">✨</span><span class="ai-chip__label">Emotion</span>`;
    emotionChip.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      // Ouvrir la roue chromatique des emotions centree sur le chip emotion
      toggleEmotionWheel(emotionChip, commentBox);
    });

    // Story 7.14 - Pas de chargement automatique de l'emotion depuis storage
    // L'utilisateur doit explicitement cliquer sur le chip Emotion pour selectionner une emotion
    // Le chip reste a l'etat par defaut "Emotion" jusqu'a selection explicite

    // Story 7.14 - Chip Style : ouvre la roue des styles de langage
    const styleChip = document.createElement('button');
    styleChip.type = 'button';
    styleChip.className = 'ai-chip ai-chip--secondary';
    styleChip.setAttribute('data-chip-type', 'style');
    styleChip.setAttribute('aria-label', t('languageStyle') || 'Style de langage');
    styleChip.setAttribute('aria-haspopup', 'true');
    styleChip.setAttribute('aria-expanded', 'false');
    styleChip.innerHTML = `<span class="ai-chip__icon">🎨</span><span class="ai-chip__label">${t('languageStyle') || 'Style'}</span>`;
    styleChip.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      // Story 7.14 - Ouvrir la roue chromatique des styles
      toggleStyleWheel(styleChip, commentBox);
    });

    // Story 7.14 - Charger la selection de style sauvegardee
    // Story 7.14 Review - Task 6.3: valeur par defaut 'professional' si jamais selectionnee
    chrome.storage.sync.get(['style_wheel_selection'], (data) => {
      if (data.style_wheel_selection && data.style_wheel_selection.style) {
        const savedStyle = data.style_wheel_selection.style;
        commentBox.setAttribute('data-selected-style', savedStyle);
        updateButtonWithStyle(styleChip, savedStyle);
      } else if (data.style_wheel_selection === undefined) {
        // Premiere utilisation : definir 'professional' comme defaut
        commentBox.setAttribute('data-selected-style', 'professional');
        // Bouton reste en etat neutre (pas de bordure coloree) pour inciter a explorer
      }
      // Si style_wheel_selection existe mais vide (reset explicite) : pas de style force
    });

    // === CHIP LONGUEUR CYCLIQUE ===
    // XS(7) -> S(14) -> M(21) -> L(28) -> XL(35) -> XS...
    // Longueurs en nombre de mots : XS=court, XL=x2
    const LENGTH_OPTIONS = [
      { key: 'XS', value: 7, labelKey: 'lengthVeryShort' },
      { key: 'S', value: 20, labelKey: 'lengthShort' },
      { key: 'M', value: 35, labelKey: 'lengthMedium' },
      { key: 'L', value: 50, labelKey: 'lengthLong' },
      { key: 'XL', value: 70, labelKey: 'lengthVeryLong' }
    ];

    const lengthChip = document.createElement('button');
    lengthChip.type = 'button';
    lengthChip.className = 'ai-chip ai-chip--secondary ai-chip--cycle';
    if (isNegative) lengthChip.classList.add('negative');
    if (isReplyToComment) lengthChip.classList.add('reply-mode');
    lengthChip.setAttribute('aria-label', t('length') || 'Longueur');
    lengthChip.setAttribute('data-chip-type', 'length');

    // Charger la longueur sauvegardee et initialiser l'affichage
    let currentLengthIndex = 2; // Default: M (21 mots)
    chrome.storage.sync.get(['length'], (data) => {
      if (data.length) {
        const savedIndex = LENGTH_OPTIONS.findIndex(opt => opt.value === data.length);
        if (savedIndex !== -1) {
          currentLengthIndex = savedIndex;
        }
      }
      const currentLength = LENGTH_OPTIONS[currentLengthIndex];
      lengthChip.innerHTML = `<span class="ai-chip__icon">📏</span><span class="ai-chip__label">${t(currentLength.labelKey)}</span>`;
      commentBox.setAttribute('data-length', currentLength.value);
      commentBox.setAttribute('data-length-key', currentLength.labelKey);
    });

    lengthChip.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      // Cycler vers la prochaine longueur
      currentLengthIndex = (currentLengthIndex + 1) % LENGTH_OPTIONS.length;
      const newLength = LENGTH_OPTIONS[currentLengthIndex];
      lengthChip.innerHTML = `<span class="ai-chip__icon">📏</span><span class="ai-chip__label">${t(newLength.labelKey)}</span>`;
      commentBox.setAttribute('data-length', newLength.value);
      commentBox.setAttribute('data-length-key', newLength.labelKey);
      // Sauvegarder
      chrome.storage.sync.set({ length: newLength.value });
    };

    // === CHIPS TOGGLE (Enrichissement) ===
    const quoteChip = createToggleChip('💬', 'quoteToggle', 'data-include-quote', 'quoteToggleTooltip', 'quoteUpgradeRequired');
    const contextChip = createToggleChip('💭', 'contextToggle', 'data-include-context', 'contextToggleTooltip', 'contextUpgradeRequired');
    const webChip = createToggleChip('🔍', 'webSearchToggle', 'data-web-search', 'webSearchToggleTooltip', 'webSearchUpgradeRequired');
    const newsChip = createToggleChip('📰', 'newsToggle', 'data-news-enrichment', 'newsToggleTooltip', 'newsUpgradeRequired', 'MEDIUM');

    // Chip Tag auteur - N'utilise pas createToggleChip car :
    // 1. Logique async pour detecter l'auteur du post
    // 2. Stocke une valeur string (nom d'auteur) et non un boolean
    // 3. Pas de sauvegarde automatique dans chrome.storage
    const tagChip = document.createElement('button');
    tagChip.type = 'button';
    tagChip.setAttribute('aria-pressed', 'false');

    if (!isPremium) {
      tagChip.className = 'ai-chip ai-chip--locked';
      tagChip.setAttribute('aria-disabled', 'true');
      tagChip.setAttribute('aria-label', t('tagAuthorTooltip') + ' (Premium)');
      tagChip.setAttribute('tabindex', '-1'); // Story 7.10 - Retirer du flux de tabulation
      tagChip.innerHTML = `<span class="ai-chip__icon">👤</span><span class="ai-chip__label">${t('tagAuthor')}</span><span class="ai-chip__lock">🔒</span>`;
    } else {
      tagChip.className = 'ai-chip ai-chip--inactive';
      tagChip.setAttribute('aria-label', t('tagAuthorTooltip'));
      tagChip.innerHTML = `<span class="ai-chip__icon">👤</span><span class="ai-chip__label">${t('tagAuthor')}</span>`;
    }

    if (isNegative) tagChip.classList.add('negative');
    if (isReplyToComment) tagChip.classList.add('reply-mode');

    tagChip.onclick = async (e) => {
      e.preventDefault();
      e.stopPropagation();

      if (!isPremium) {
        showPremiumUpgradePrompt(t('tagAuthorUpgradeRequired'));
        return;
      }

      const currentAuthor = commentBox.getAttribute('data-tag-author');
      if (currentAuthor) {
        commentBox.removeAttribute('data-tag-author');
        tagChip.classList.remove('ai-chip--active');
        tagChip.classList.add('ai-chip--inactive');
        tagChip.setAttribute('aria-pressed', 'false');
        tagChip.innerHTML = `<span class="ai-chip__icon">👤</span><span class="ai-chip__label">${t('tagAuthor')}</span>`;
        return;
      }

      // LinkedIn 2026 SDUI: remonter jusqu'au conteneur du POST (pas du commentaire)
      // On cherche d'abord [role="listitem"] qui englobe tout le post
      let postContainer = commentBox.closest('[role="listitem"]');

      // Si pas trouve, essayer les autres selecteurs en remontant le plus haut possible
      if (!postContainer) {
        // Remonter via parentElement jusqu'a trouver un conteneur avec data-view-name="feed-full-update"
        // mais au niveau du POST (pas du commentaire)
        let current = commentBox;
        let lastFeedUpdate = null;
        while (current && current !== document.body) {
          if (current.getAttribute('data-view-name') === 'feed-full-update') {
            lastFeedUpdate = current;
          }
          // Arreter si on trouve un listitem
          if (current.getAttribute('role') === 'listitem') {
            postContainer = current;
            break;
          }
          current = current.parentElement;
        }
        // Utiliser le feed-full-update le plus haut trouve
        if (!postContainer && lastFeedUpdate) {
          postContainer = lastFeedUpdate.parentElement || lastFeedUpdate;
        }
      }

      // Fallback sur les anciens selecteurs
      if (!postContainer) {
        postContainer = commentBox.closest('[data-id], article, .feed-shared-update-v2, [data-urn]');
      }

      const authorInfo = extractPostAuthorInfo(postContainer);
      if (authorInfo && authorInfo.name) {
        commentBox.setAttribute('data-tag-author', authorInfo.name);
        tagChip.classList.remove('ai-chip--inactive');
        tagChip.classList.add('ai-chip--active');
        tagChip.setAttribute('aria-pressed', 'true');
        tagChip.innerHTML = `<span class="ai-chip__icon">👤</span><span class="ai-chip__label">${t('tagAuthor')}</span><span class="ai-chip__check">✓</span>`;
        window.toastNotification.success(t('tagAuthorSuccess').replace('{name}', authorInfo.name));
      } else {
        window.toastNotification.warning(t('authorNotFound'));
      }
    };

    // === CHIPS BLACKLIST ===
    const addBlacklistChip = createPremiumActionChip(
      '🚫',
      'addToBlacklist',
      'addToBlacklistTooltip',
      async () => {
        // LinkedIn 2026 SDUI: remonter jusqu'au conteneur du POST
        let postContainer = commentBox.closest('[role="listitem"]');
        if (!postContainer) {
          let current = commentBox;
          let lastFeedUpdate = null;
          while (current && current !== document.body) {
            if (current.getAttribute('data-view-name') === 'feed-full-update') {
              lastFeedUpdate = current;
            }
            if (current.getAttribute('role') === 'listitem') {
              postContainer = current;
              break;
            }
            current = current.parentElement;
          }
          if (!postContainer && lastFeedUpdate) {
            postContainer = lastFeedUpdate.parentElement || lastFeedUpdate;
          }
        }
        if (!postContainer) {
          postContainer = commentBox.closest('[data-id], article, .feed-shared-update-v2, [data-urn]');
        }

        const authorInfo = extractPostAuthorInfo(postContainer);
        if (!authorInfo || !authorInfo.name) {
          window.toastNotification.warning(t('authorNotFound'));
          return;
        }

        chrome.runtime.sendMessage({
          action: 'addToBlacklist',
          blockedName: authorInfo.name,
          blockedProfileUrl: authorInfo.url || null
        }, (response) => {
          if (response && response.success) {
            window.toastNotification.success(t('blacklistAddSuccess').replace('{name}', authorInfo.name));
          } else {
            window.toastNotification.error(t('error'));
          }
        });
      },
      'danger',
      'blacklistUpgradeRequired'
    );

    const viewBlacklistChip = createPremiumActionChip(
      '📋',
      'viewBlacklist',
      'viewBlacklistTooltip',
      () => showBlacklistModal(),
      'secondary',
      'blacklistUpgradeRequired'
    );

    // === ASSEMBLER LES CHIPS ===
    // Actions principales
    container.appendChild(generateChip);
    container.appendChild(promptChip);
    container.appendChild(randomChip);
    container.appendChild(emotionChip);
    container.appendChild(styleChip);  // Story 7.14 - Nouveau chip style de langage
    container.appendChild(lengthChip); // Chip longueur cyclique XS/S/M/L/XL
    // Toggles enrichissement
    container.appendChild(quoteChip);
    container.appendChild(tagChip);
    container.appendChild(contextChip);
    container.appendChild(webChip);
    container.appendChild(newsChip);
    // Blacklist
    container.appendChild(addBlacklistChip);
    container.appendChild(viewBlacklistChip);

    // Stocker les references aux elements
    container._elements = {
      generateChip,
      promptChip,
      randomChip,
      emotionChip,
      styleChip,  // Story 7.14 - Nouveau chip style de langage
      lengthChip, // Chip longueur cyclique
      quoteChip,
      tagChip,
      contextChip,
      webChip,
      newsChip,
      addBlacklistChip,
      viewBlacklistChip
    };

    // Fix Code Review: Restaurer les etats des toggles sauvegardes
    chrome.storage.local.get([
      'toggle_include-quote',
      'toggle_include-context',
      'toggle_web-search',
      'toggle_news-enrichment'
    ], (savedStates) => {
      const toggleConfigs = [
        { chip: quoteChip, key: 'toggle_include-quote', dataAttr: 'data-include-quote', icon: '💬', labelKey: 'quoteToggle', hasAccess: isPremium },
        { chip: contextChip, key: 'toggle_include-context', dataAttr: 'data-include-context', icon: '💭', labelKey: 'contextToggle', hasAccess: isPremium },
        { chip: webChip, key: 'toggle_web-search', dataAttr: 'data-web-search', icon: '🔍', labelKey: 'webSearchToggle', hasAccess: isPremium },
        { chip: newsChip, key: 'toggle_news-enrichment', dataAttr: 'data-news-enrichment', icon: '📰', labelKey: 'newsToggle', hasAccess: isMediumPlus }
      ];

      toggleConfigs.forEach(({ chip, key, dataAttr, icon, labelKey, hasAccess }) => {
        if (savedStates[key] === true && hasAccess && !chip.classList.contains('ai-chip--locked')) {
          commentBox.setAttribute(dataAttr, 'true');
          chip.classList.remove('ai-chip--inactive');
          chip.classList.add('ai-chip--active');
          chip.setAttribute('aria-pressed', 'true');
          chip.innerHTML = `<span class="ai-chip__icon">${icon}</span><span class="ai-chip__label">${t(labelKey)}</span><span class="ai-chip__check">✓</span>`;
        }
      });
    });

    return container;
  }

  // ================================================
  // Handle Random Generate
  // Randomizes toggle states before generating
  // ================================================
  function handleRandomGenerate(e, commentBox, isReplyToComment) {
    // Randomiser les toggles premium
    const randomBool = () => Math.random() > 0.5;

    chrome.storage.local.get(['user_plan'], (result) => {
      const userPlan = result.user_plan || 'FREE';
      if (userPlan === 'PREMIUM') {
        // Randomiser les etats des toggles
        if (randomBool()) {
          commentBox.setAttribute('data-include-quote', 'true');
        } else {
          commentBox.removeAttribute('data-include-quote');
        }
        if (randomBool()) {
          commentBox.setAttribute('data-include-context', 'true');
        } else {
          commentBox.removeAttribute('data-include-context');
        }
        if (randomBool()) {
          commentBox.setAttribute('data-web-search', 'true');
        } else {
          commentBox.removeAttribute('data-web-search');
        }
        // Tag auteur: on ne randomise pas car necessite extraction
      }

      // Lancer la generation
      handleGenerateClick(e, commentBox, isReplyToComment);
    });
  }

  // Ajouter les boutons
  async function addButtonsToCommentBox(commentBox) {
    // Triple vérification stricte avec verrouillage immédiat
    if (hasAIButtons(commentBox)) {
      return;
    }

    // VERROUILLAGE IMMÉDIAT : marquer AVANT toute autre opération
    // Cela empêche les race conditions entre événements concurrents
    commentBox.setAttribute('data-ai-buttons-pending', 'true');

    // S'assurer que le parent a un positionnement relatif
    const parent = commentBox.parentElement;
    if (parent && getComputedStyle(parent).position === 'static') {
      parent.style.position = 'relative';
    }

    // Charger le plan utilisateur
    const userPlanResult = await new Promise(resolve => {
      chrome.storage.local.get(['user_plan'], resolve);
    });
    const userPlan = userPlanResult.user_plan || 'FREE';

    chrome.storage.sync.get(['tone'], function(data) {
      const isNegative = data.tone === 'negatif';
      const isReplyToComment = commentBox.closest('[data-view-name="comment-container"]') !== null ||
                                commentBox.closest('.comments-comment-entity') !== null;

      // Mode Inline (unique mode V3.1)
      const inlineControls = createInlineModeControls(commentBox, userPlan, isNegative, isReplyToComment);

      parent.appendChild(inlineControls);

      // Retirer le marqueur "en cours" et marquer comme "ajouté"
      commentBox.removeAttribute('data-ai-buttons-pending');
      commentBox.setAttribute('data-ai-buttons-added', 'true');
      commentBox.setAttribute('data-ai-ui-mode', 'inline');

      updateButtonsState(inlineControls, isAuthenticated);

      // Legacy mode supprimé - tout le code ci-dessous est maintenu pour référence
      // mais n'est plus exécuté
      return;

      // Mode Legacy (référence historique) — code existant
      const buttonsWrapper = document.createElement('div');
      buttonsWrapper.className = 'ai-buttons-wrapper';

      // Bouton Générer
      const generateButton = document.createElement('button');
      generateButton.className = 'ai-button ai-button--primary';
      generateButton.type = 'button'; // IMPORTANT: empêche la soumission du formulaire
      if (isNegative) generateButton.classList.add('negative');
      if (isReplyToComment) generateButton.classList.add('reply-mode');
      generateButton.innerHTML = `<span>${t('generate')}</span>`;
      generateButton.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        handleGenerateClick(e, commentBox, isReplyToComment);
      };

      // Bouton Avec prompt
      const promptButton = document.createElement('button');
      promptButton.className = 'ai-button ai-button--primary';
      promptButton.type = 'button'; // IMPORTANT: empêche la soumission du formulaire
      if (isNegative) promptButton.classList.add('negative');
      if (isReplyToComment) promptButton.classList.add('reply-mode');
      promptButton.innerHTML = `<span>${t('withPrompt')}</span>`;
      promptButton.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        handlePromptClick(e, commentBox, isReplyToComment);
      };

      // Bouton Paramètres (engrenage)
      const personalisationButton = document.createElement('button');
      personalisationButton.className = 'ai-button ai-button--secondary settings-button';
      personalisationButton.type = 'button'; // IMPORTANT: empêche la soumission du formulaire
      if (isNegative) personalisationButton.classList.add('negative');
      if (isReplyToComment) personalisationButton.classList.add('reply-mode');
      personalisationButton.innerHTML = `<span>⚙️</span>`;
      personalisationButton.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleEmotionsPanel(buttonsWrapper, commentBox);
      };

      // V3 Story 7.3 — Toggle Citation BEM (PREMIUM uniquement)
      const quoteToggle = document.createElement('button');
      quoteToggle.className = 'ai-toggle ai-toggle--inactive ai-quote-toggle';
      quoteToggle.type = 'button';
      quoteToggle.setAttribute('aria-pressed', 'false');
      quoteToggle.setAttribute('aria-label', t('quoteToggleInactive'));
      if (isNegative) quoteToggle.classList.add('negative');
      if (isReplyToComment) quoteToggle.classList.add('reply-mode');
      quoteToggle.innerHTML = `<span class="ai-toggle__icon">💬</span><span class="ai-toggle__label">${t('quoteToggle')}</span>`;
      quoteToggle.title = t('quoteToggleInactive');

      // Verifier le plan utilisateur pour le gating
      chrome.storage.local.get(['user_plan'], (result) => {
        const userPlan = result.user_plan || 'FREE';
        if (userPlan !== 'PREMIUM') {
          quoteToggle.classList.remove('ai-toggle--inactive');
          quoteToggle.classList.add('ai-toggle--locked');
          quoteToggle.setAttribute('aria-disabled', 'true');
          quoteToggle.setAttribute('tabindex', '-1'); // Story 7.10 - Retirer du flux de tabulation
          quoteToggle.innerHTML = `<span class="ai-toggle__icon">💬</span><span class="ai-toggle__label">${t('quoteToggle')}</span><span class="ai-toggle__lock">🔒</span>`;
        }
      });

      quoteToggle.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        chrome.storage.local.get(['user_plan'], (result) => {
          const userPlan = result.user_plan || 'FREE';
          if (userPlan !== 'PREMIUM') {
            // V3 Story 4.1 — Toast avec lien Stripe
            showPremiumUpgradePrompt(t('quoteUpgradeRequired'));
            return;
          }
          // Toggle l'etat actif/inactif
          const isActive = commentBox.getAttribute('data-include-quote') === 'true';
          if (isActive) {
            commentBox.removeAttribute('data-include-quote');
            quoteToggle.classList.remove('ai-toggle--active');
            quoteToggle.classList.add('ai-toggle--inactive');
            quoteToggle.setAttribute('aria-pressed', 'false');
            quoteToggle.innerHTML = `<span class="ai-toggle__icon">💬</span><span class="ai-toggle__label">${t('quoteToggle')}</span>`;
            quoteToggle.title = t('quoteToggleInactive');
          } else {
            commentBox.setAttribute('data-include-quote', 'true');
            quoteToggle.classList.remove('ai-toggle--inactive');
            quoteToggle.classList.add('ai-toggle--active');
            quoteToggle.setAttribute('aria-pressed', 'true');
            quoteToggle.innerHTML = `<span class="ai-toggle__icon">💬</span><span class="ai-toggle__label">${t('quoteToggle')}</span><span class="ai-toggle__check">✓</span>`;
            quoteToggle.title = t('quoteToggleActive');
          }
        });
      };

      // V3 Story 7.3 — Toggle Tag Auteur BEM (PREMIUM uniquement)
      const tagAuthorToggle = document.createElement('button');
      tagAuthorToggle.className = 'ai-toggle ai-toggle--inactive ai-tag-author-toggle';
      tagAuthorToggle.type = 'button';
      tagAuthorToggle.setAttribute('aria-pressed', 'false');
      tagAuthorToggle.setAttribute('aria-label', t('tagAuthorTooltip'));
      if (isNegative) tagAuthorToggle.classList.add('negative');
      if (isReplyToComment) tagAuthorToggle.classList.add('reply-mode');
      tagAuthorToggle.innerHTML = `<span class="ai-toggle__icon">👤</span><span class="ai-toggle__label">${t('tagAuthor')}</span>`;
      tagAuthorToggle.title = t('tagAuthorTooltip');

      // Verifier le plan utilisateur pour le gating
      chrome.storage.local.get(['user_plan'], (result) => {
        const userPlan = result.user_plan || 'FREE';
        if (userPlan !== 'PREMIUM') {
          tagAuthorToggle.classList.remove('ai-toggle--inactive');
          tagAuthorToggle.classList.add('ai-toggle--locked');
          tagAuthorToggle.setAttribute('aria-disabled', 'true');
          tagAuthorToggle.setAttribute('tabindex', '-1'); // Story 7.10 - Retirer du flux de tabulation
          tagAuthorToggle.innerHTML = `<span class="ai-toggle__icon">👤</span><span class="ai-toggle__label">${t('tagAuthor')}</span><span class="ai-toggle__lock">🔒</span>`;
        }
      });

      tagAuthorToggle.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        chrome.storage.local.get(['user_plan'], (result) => {
          const userPlan = result.user_plan || 'FREE';
          if (userPlan !== 'PREMIUM') {
            // V3 Story 4.1 — Toast avec lien Stripe
            showPremiumUpgradePrompt(t('tagAuthorUpgradeRequired'));
            return;
          }

          // Verifier si deja actif — toggle off
          const currentAuthor = commentBox.getAttribute('data-tag-author');
          if (currentAuthor) {
            commentBox.removeAttribute('data-tag-author');
            tagAuthorToggle.classList.remove('ai-toggle--active');
            tagAuthorToggle.classList.add('ai-toggle--inactive');
            tagAuthorToggle.setAttribute('aria-pressed', 'false');
            tagAuthorToggle.innerHTML = `<span class="ai-toggle__icon">👤</span><span class="ai-toggle__label">${t('tagAuthor')}</span>`;
            tagAuthorToggle.title = t('tagAuthorTooltip');
            return;
          }

          // Tenter d'extraire le nom de l'auteur
          // LinkedIn 2026 SDUI: remonter jusqu'au conteneur du POST (pas du commentaire)
          // On cherche d'abord [role="listitem"] qui englobe tout le post
          let postContainer = commentBox.closest('[role="listitem"]');

          // Si pas trouve, essayer les autres selecteurs en remontant le plus haut possible
          if (!postContainer) {
            // Remonter via parentElement jusqu'a trouver un conteneur avec data-view-name="feed-full-update"
            // mais au niveau du POST (pas du commentaire)
            let current = commentBox;
            let lastFeedUpdate = null;
            while (current && current !== document.body) {
              if (current.getAttribute('data-view-name') === 'feed-full-update') {
                lastFeedUpdate = current;
              }
              // Arreter si on trouve un listitem
              if (current.getAttribute('role') === 'listitem') {
                postContainer = current;
                break;
              }
              current = current.parentElement;
            }
            // Utiliser le feed-full-update le plus haut trouve
            if (!postContainer && lastFeedUpdate) {
              postContainer = lastFeedUpdate.parentElement || lastFeedUpdate;
            }
          }

          // Fallback sur les anciens selecteurs
          if (!postContainer) {
            postContainer = commentBox.closest('[data-id], article, .feed-shared-update-v2, [data-urn]');
          }

          const authorName = extractPostAuthorName(postContainer);

          if (authorName) {
            // Activation reussie
            commentBox.setAttribute('data-tag-author', authorName);
            tagAuthorToggle.classList.remove('ai-toggle--inactive');
            tagAuthorToggle.classList.add('ai-toggle--active');
            tagAuthorToggle.setAttribute('aria-pressed', 'true');
            tagAuthorToggle.innerHTML = `<span class="ai-toggle__icon">👤</span><span class="ai-toggle__label">${t('tagAuthor')}</span><span class="ai-toggle__check">✓</span>`;
            tagAuthorToggle.title = `${t('tagAuthorActive')}: ${authorName}`;
          } else {
            // Extraction echouee
            window.toastNotification.warning(t('authorNotFound'));
          }
        });
      };

      // V3 Story 7.3 — Toggle Contexte BEM (commentaires tiers) (PREMIUM uniquement)
      const contextToggle = document.createElement('button');
      contextToggle.className = 'ai-toggle ai-toggle--inactive ai-context-toggle';
      contextToggle.type = 'button';
      contextToggle.setAttribute('aria-pressed', 'false');
      contextToggle.setAttribute('aria-label', t('contextToggleTooltip'));
      if (isNegative) contextToggle.classList.add('negative');
      if (isReplyToComment) contextToggle.classList.add('reply-mode');
      contextToggle.innerHTML = `<span class="ai-toggle__icon">💭</span><span class="ai-toggle__label">${t('contextToggle')}</span>`;
      contextToggle.title = t('contextToggleTooltip');

      // Verifier le plan utilisateur pour le gating
      chrome.storage.local.get(['user_plan'], (result) => {
        const userPlan = result.user_plan || 'FREE';
        if (userPlan !== 'PREMIUM') {
          contextToggle.classList.remove('ai-toggle--inactive');
          contextToggle.classList.add('ai-toggle--locked');
          contextToggle.setAttribute('aria-disabled', 'true');
          contextToggle.setAttribute('tabindex', '-1'); // Story 7.10 - Retirer du flux de tabulation
          contextToggle.innerHTML = `<span class="ai-toggle__icon">💭</span><span class="ai-toggle__label">${t('contextToggle')}</span><span class="ai-toggle__lock">🔒</span>`;
        }
      });

      contextToggle.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        chrome.storage.local.get(['user_plan'], (result) => {
          const userPlan = result.user_plan || 'FREE';
          if (userPlan !== 'PREMIUM') {
            // V3 Story 4.1 — Toast avec lien Stripe
            showPremiumUpgradePrompt(t('contextUpgradeRequired'));
            return;
          }
          // Toggle l'etat actif/inactif
          const isActive = commentBox.getAttribute('data-include-context') === 'true';
          if (isActive) {
            commentBox.removeAttribute('data-include-context');
            contextToggle.classList.remove('ai-toggle--active');
            contextToggle.classList.add('ai-toggle--inactive');
            contextToggle.setAttribute('aria-pressed', 'false');
            contextToggle.innerHTML = `<span class="ai-toggle__icon">💭</span><span class="ai-toggle__label">${t('contextToggle')}</span>`;
            contextToggle.title = t('contextToggleInactive');
          } else {
            commentBox.setAttribute('data-include-context', 'true');
            contextToggle.classList.remove('ai-toggle--inactive');
            contextToggle.classList.add('ai-toggle--active');
            contextToggle.setAttribute('aria-pressed', 'true');
            contextToggle.innerHTML = `<span class="ai-toggle__icon">💭</span><span class="ai-toggle__label">${t('contextToggle')}</span><span class="ai-toggle__check">✓</span>`;
            contextToggle.title = t('contextToggleActive');
          }
        });
      };

      // V3 Story 7.3 — Toggle Recherche Web BEM (PREMIUM uniquement)
      const webSearchToggle = document.createElement('button');
      webSearchToggle.className = 'ai-toggle ai-toggle--inactive ai-web-search-toggle';
      webSearchToggle.type = 'button';
      webSearchToggle.setAttribute('aria-pressed', 'false');
      webSearchToggle.setAttribute('aria-label', t('webSearchToggleTooltip'));
      if (isNegative) webSearchToggle.classList.add('negative');
      if (isReplyToComment) webSearchToggle.classList.add('reply-mode');
      webSearchToggle.innerHTML = `<span class="ai-toggle__icon">🔍</span><span class="ai-toggle__label">${t('webSearchToggle')}</span>`;
      webSearchToggle.title = t('webSearchToggleTooltip');

      // Verifier le plan utilisateur pour le gating
      chrome.storage.local.get(['user_plan'], (result) => {
        const userPlan = result.user_plan || 'FREE';
        if (userPlan !== 'PREMIUM') {
          webSearchToggle.classList.remove('ai-toggle--inactive');
          webSearchToggle.classList.add('ai-toggle--locked');
          webSearchToggle.setAttribute('aria-disabled', 'true');
          webSearchToggle.setAttribute('tabindex', '-1'); // Story 7.10 - Retirer du flux de tabulation
          webSearchToggle.innerHTML = `<span class="ai-toggle__icon">🔍</span><span class="ai-toggle__label">${t('webSearchToggle')}</span><span class="ai-toggle__lock">🔒</span>`;
        }
      });

      webSearchToggle.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        chrome.storage.local.get(['user_plan'], (result) => {
          const userPlan = result.user_plan || 'FREE';
          if (userPlan !== 'PREMIUM') {
            // V3 Story 4.1 — Toast avec lien Stripe
            showPremiumUpgradePrompt(t('webSearchUpgradeRequired'));
            return;
          }
          // Toggle l'etat actif/inactif
          const isActive = commentBox.getAttribute('data-web-search') === 'true';
          if (isActive) {
            commentBox.removeAttribute('data-web-search');
            webSearchToggle.classList.remove('ai-toggle--active');
            webSearchToggle.classList.add('ai-toggle--inactive');
            webSearchToggle.setAttribute('aria-pressed', 'false');
            webSearchToggle.innerHTML = `<span class="ai-toggle__icon">🔍</span><span class="ai-toggle__label">${t('webSearchToggle')}</span>`;
            webSearchToggle.title = t('webSearchToggleInactive');
          } else {
            commentBox.setAttribute('data-web-search', 'true');
            webSearchToggle.classList.remove('ai-toggle--inactive');
            webSearchToggle.classList.add('ai-toggle--active');
            webSearchToggle.setAttribute('aria-pressed', 'true');
            webSearchToggle.innerHTML = `<span class="ai-toggle__icon">🔍</span><span class="ai-toggle__label">${t('webSearchToggle')}</span><span class="ai-toggle__check">✓</span>`;
            webSearchToggle.title = t('webSearchToggleActive');
          }
        });
      };

      // V3 Story 5.4 — Bouton toggle News LinkedIn (MEDIUM+ uniquement)
      // V3 Story 7.3 — Toggle News LinkedIn BEM (MEDIUM+ uniquement)
      const newsToggle = document.createElement('button');
      newsToggle.className = 'ai-toggle ai-toggle--inactive ai-news-toggle';
      newsToggle.type = 'button';
      newsToggle.setAttribute('aria-pressed', 'false');
      newsToggle.setAttribute('aria-label', t('newsToggleTooltip'));
      if (isNegative) newsToggle.classList.add('negative');
      if (isReplyToComment) newsToggle.classList.add('reply-mode');
      newsToggle.innerHTML = `<span class="ai-toggle__icon">📰</span><span class="ai-toggle__label">${t('newsToggle')}</span>`;
      newsToggle.title = t('newsToggleTooltip');

      // Verifier le plan utilisateur pour le gating (MEDIUM+ requis)
      chrome.storage.local.get(['user_plan'], (result) => {
        const userPlan = result.user_plan || 'FREE';
        if (userPlan === 'FREE') {
          newsToggle.classList.remove('ai-toggle--inactive');
          newsToggle.classList.add('ai-toggle--locked');
          newsToggle.setAttribute('aria-disabled', 'true');
          newsToggle.setAttribute('tabindex', '-1'); // Story 7.10 - Retirer du flux de tabulation
          newsToggle.innerHTML = `<span class="ai-toggle__icon">📰</span><span class="ai-toggle__label">${t('newsToggle')}</span><span class="ai-toggle__lock">🔒</span>`;
        }
      });

      newsToggle.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        chrome.storage.local.get(['user_plan'], (result) => {
          const userPlan = result.user_plan || 'FREE';
          if (userPlan === 'FREE') {
            // V3 Story 5.4 — Toast avec lien Stripe (MEDIUM+ requis)
            showPremiumUpgradePrompt(t('newsUpgradeRequired'));
            return;
          }
          // V3 Story 5.4 — MEDIUM et PREMIUM utilisent le meme mode smart-summary
          const newsMode = 'smart-summary';
          // Toggle l'etat actif/inactif
          const currentMode = commentBox.getAttribute('data-news-enrichment');
          if (currentMode) {
            commentBox.removeAttribute('data-news-enrichment');
            newsToggle.classList.remove('ai-toggle--active');
            newsToggle.classList.add('ai-toggle--inactive');
            newsToggle.setAttribute('aria-pressed', 'false');
            newsToggle.innerHTML = `<span class="ai-toggle__icon">📰</span><span class="ai-toggle__label">${t('newsToggle')}</span>`;
            newsToggle.title = t('newsToggleInactive');
          } else {
            commentBox.setAttribute('data-news-enrichment', newsMode);
            newsToggle.classList.remove('ai-toggle--inactive');
            newsToggle.classList.add('ai-toggle--active');
            newsToggle.setAttribute('aria-pressed', 'true');
            newsToggle.innerHTML = `<span class="ai-toggle__icon">📰</span><span class="ai-toggle__label">${t('newsToggle')}</span><span class="ai-toggle__check">✓</span>`;
            newsToggle.title = t('newsToggleActive');
          }
        });
      };

      // V3 Story 2.1 — Bouton Blacklist (PREMIUM uniquement)
      const blacklistBtn = document.createElement('button');
      blacklistBtn.className = 'ai-button ai-button--danger ai-blacklist-btn';
      blacklistBtn.type = 'button';
      if (isNegative) blacklistBtn.classList.add('negative');
      if (isReplyToComment) blacklistBtn.classList.add('reply-mode');
      blacklistBtn.innerHTML = `<span>🚫 ${t('addToBlacklist')}</span>`;
      blacklistBtn.title = t('addToBlacklistTooltip');

      // Verifier le plan utilisateur pour le gating
      chrome.storage.local.get(['user_plan'], (result) => {
        const userPlan = result.user_plan || 'FREE';
        if (userPlan !== 'PREMIUM') {
          blacklistBtn.classList.add('locked');
          blacklistBtn.innerHTML = `<span>🔒 ${t('addToBlacklist')}</span>`;
        }
      });

      blacklistBtn.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        chrome.storage.local.get(['user_plan'], (result) => {
          const userPlan = result.user_plan || 'FREE';
          if (userPlan !== 'PREMIUM') {
            // V3 Story 4.1 — Toast avec lien Stripe
            showPremiumUpgradePrompt(t('blacklistUpgradeRequired'));
            return;
          }

          // Extraire le nom et URL de l'auteur du post
          let postContainer = commentBox.closest('[role="listitem"]');
          if (!postContainer) {
            let current = commentBox;
            let lastFeedUpdate = null;
            while (current && current !== document.body) {
              if (current.getAttribute('data-view-name') === 'feed-full-update') {
                lastFeedUpdate = current;
              }
              if (current.getAttribute('role') === 'listitem') {
                postContainer = current;
                break;
              }
              current = current.parentElement;
            }
            if (!postContainer && lastFeedUpdate) {
              postContainer = lastFeedUpdate.parentElement || lastFeedUpdate;
            }
          }
          if (!postContainer) {
            postContainer = commentBox.closest('[data-id], article, .feed-shared-update-v2, [data-urn]');
          }

          const authorInfo = extractPostAuthorInfo(postContainer);
          if (!authorInfo || !authorInfo.name) {
            window.toastNotification.warning(t('authorNotFound'));
            return;
          }

          // Ajouter a la blacklist via background.js
          chrome.runtime.sendMessage({
            action: 'addToBlacklist',
            blockedName: authorInfo.name,
            blockedProfileUrl: authorInfo.url || null
          }, (response) => {
            if (response && response.success) {
              window.toastNotification.success(t('blacklistAddSuccess').replace('{name}', authorInfo.name));
            } else if (response && response.errorCode === 'ALREADY_EXISTS') {
              window.toastNotification.warning(t('blacklistAlreadyExists').replace('{name}', authorInfo.name));
            } else {
              window.toastNotification.error(t('blacklistAddError'));
            }
          });
        });
      };

      // V3 Story 2.1 — Bouton Voir ma blacklist (PREMIUM uniquement)
      const viewBlacklistBtn = document.createElement('button');
      viewBlacklistBtn.className = 'ai-button ai-button--secondary ai-view-blacklist-btn';
      viewBlacklistBtn.type = 'button';
      if (isNegative) viewBlacklistBtn.classList.add('negative');
      if (isReplyToComment) viewBlacklistBtn.classList.add('reply-mode');
      viewBlacklistBtn.innerHTML = `<span>📋 ${t('viewBlacklist')}</span>`;
      viewBlacklistBtn.title = t('viewBlacklistTooltip');

      chrome.storage.local.get(['user_plan'], (result) => {
        const userPlan = result.user_plan || 'FREE';
        if (userPlan !== 'PREMIUM') {
          viewBlacklistBtn.classList.add('locked');
          viewBlacklistBtn.innerHTML = `<span>🔒 ${t('viewBlacklist')}</span>`;
        }
      });

      viewBlacklistBtn.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        chrome.storage.local.get(['user_plan'], (result) => {
          const userPlan = result.user_plan || 'FREE';
          if (userPlan !== 'PREMIUM') {
            // V3 Story 4.1 — Toast avec lien Stripe
            showPremiumUpgradePrompt(t('blacklistUpgradeRequired'));
            return;
          }
          showBlacklistModal();
        });
      };

      buttonsWrapper.appendChild(generateButton);
      buttonsWrapper.appendChild(promptButton);
      buttonsWrapper.appendChild(personalisationButton);
      buttonsWrapper.appendChild(quoteToggle);
      buttonsWrapper.appendChild(tagAuthorToggle);
      buttonsWrapper.appendChild(contextToggle);
      buttonsWrapper.appendChild(webSearchToggle);
      buttonsWrapper.appendChild(newsToggle);  // V3 Story 5.4 — News LinkedIn toggle
      buttonsWrapper.appendChild(blacklistBtn);
      buttonsWrapper.appendChild(viewBlacklistBtn);
      commentBox.parentElement.appendChild(buttonsWrapper);

      // Retirer le marqueur "en cours" et marquer comme "ajouté"
      commentBox.removeAttribute('data-ai-buttons-pending');
      commentBox.setAttribute('data-ai-buttons-added', 'true');

      updateButtonsState(buttonsWrapper, isAuthenticated);
    });
  }

  // Détecter les clics dans les zones de commentaire
  document.addEventListener('click', function(event) {
    // Ignorer les clics sur les boutons AI et leurs enfants
    if (event.target.closest('.ai-button') ||
        event.target.closest('.ai-generate-button') ||
        event.target.closest('.ai-buttons-wrapper') ||
        event.target.closest('.ai-prompt-popup') ||
        event.target.closest('.ai-options-popup') ||
        event.target.closest('.ai-refine-popup')) {
      return;
    }

    // Sélecteurs multiples pour une meilleure compatibilité
    const commentBox = event.target.closest('[contenteditable="true"]') ||
                       event.target.closest('[role="textbox"]') ||
                       event.target.closest('.ql-editor');

    if (commentBox) {
      // FILTRE CRITIQUE : Ignorer les éléments ql-clipboard (Quill editor clipboard)
      if (commentBox.classList.contains('ql-clipboard')) {
        return;
      }

      // Vérifier plusieurs attributs pour le placeholder
      const placeholder = commentBox.getAttribute('data-placeholder') ||
                         commentBox.getAttribute('aria-label') ||
                         commentBox.getAttribute('aria-placeholder') ||
                         commentBox.getAttribute('placeholder') ||
                         commentBox.closest('[data-placeholder]')?.getAttribute('data-placeholder') ||
                         '';

      // Vérifier le parent pour le placeholder
      const parentPlaceholder = commentBox.parentElement?.getAttribute('data-placeholder') ||
                               commentBox.parentElement?.getAttribute('aria-label') || '';

      // Contextes de commentaire étendus
      const isInCommentContext = commentBox.closest('.comments-comment-texteditor, .comment-box, .comments-comment-box, .ql-editor, [data-test-id*="comment"], [class*="comment-input"], [class*="reply-input"], .tiptap, .ProseMirror');

      // Classes du commentBox
      const commentBoxClasses = commentBox.className || '';

      const hasCommentKeywords = placeholder.toLowerCase().includes('comment') ||
                                 placeholder.toLowerCase().includes('ajouter') ||
                                 placeholder.toLowerCase().includes('add') ||
                                 placeholder.toLowerCase().includes('reply') ||
                                 parentPlaceholder.toLowerCase().includes('comment') ||
                                 parentPlaceholder.toLowerCase().includes('ajouter') ||
                                 parentPlaceholder.toLowerCase().includes('add') ||
                                 parentPlaceholder.toLowerCase().includes('reply');

      // Validation améliorée : accepter aussi si c'est un TipTap/ProseMirror editor
      const isTipTapEditor = commentBoxClasses.includes('tiptap') || commentBoxClasses.includes('ProseMirror');

      if (hasCommentKeywords || isInCommentContext || isTipTapEditor) {
        // Vérifier via la fonction hasAIButtons avant d'ajouter
        // IMPORTANT : ne PAS marquer comme pending ici car addButtonsToCommentBox le fait déjà
        if (!hasAIButtons(commentBox)) {
          setTimeout(() => {
            // Triple vérification au moment de l'exécution du setTimeout
            // (car entre-temps, un autre événement pourrait avoir ajouté les boutons)
            if (!hasAIButtons(commentBox)) {
              addButtonsToCommentBox(commentBox);
            }
          }, 100);
        }
      }
    }
  }, { capture: true }); // Utiliser capture pour attraper l'événement plus tôt

  // Vérifier le quota avant génération
  async function checkQuotaBeforeGenerate() {
    try {
      const response = await chrome.runtime.sendMessage({
        action: 'checkQuota'
      });

      return response;
    } catch (error) {
      console.error('Erreur vérification quota:', error);
      return { hasQuota: true }; // Autoriser en cas d'erreur pour éviter de bloquer
    }
  }

  // Envoyer les actualités au backend pour vectorisation (mode smart-summary uniquement)
  async function sendNewsToBackend(newsEnrichmentMode, commentLanguage) {
    // Vérifier si le mode smart-summary est activé
    if (newsEnrichmentMode !== 'smart-summary') {
      console.log(`📰 Mode enrichissement: ${newsEnrichmentMode} - Pas d'envoi au backend`);
      return extractLinkedInNews(); // Retourner les news pour le contexte seulement
    }

    // Extraire les actualités LinkedIn
    const newsItems = extractLinkedInNews();

    if (newsItems.length === 0) {
      console.log('⚠️ Aucune actualité LinkedIn détectée pour smart-summary');
      return [];
    }

    console.log('🧠 Envoi des actualités LinkedIn au backend (mode smart-summary)...');
    console.log('🧠 URLs envoyées:', newsItems.map(n => n.url));

    try {
      // Extraire uniquement les URLs (le backend attend un tableau de strings)
      const urlsOnly = newsItems.map(item => item.url);

      // Créer une promesse avec timeout de 5 secondes
      const registerPromise = new Promise((resolve, reject) => {
        chrome.runtime.sendMessage({
          action: 'registerNews',
          data: {
            urls: urlsOnly,
            lang: commentLanguage || 'fr'
          }
        }, response => {
          if (chrome.runtime.lastError) {
            reject(new Error(chrome.runtime.lastError.message));
          } else if (response && response.error) {
            reject(new Error(response.error));
          } else {
            resolve(response);
          }
        });
      });

      // Timeout de 5 secondes
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Timeout')), 5000);
      });

      // Attendre la réponse ou le timeout
      const response = await Promise.race([registerPromise, timeoutPromise]);

      console.log('✅ News envoyées au backend:', response);
      return newsItems;

    } catch (error) {
      console.warn('⚠️ registerNews failed:', error.message);
      // Mode dégradé : continuer avec les news non vectorisées
      return newsItems;
    }
  }

  // Afficher une popup d'upgrade
  function showUpgradePrompt(quotaInfo) {
    const message = quotaInfo.message || 'Limite quotidienne atteinte';
    const role = quotaInfo.role || 'FREE';
    const upgradePlan = role === 'FREE' ? 'MEDIUM' : 'PREMIUM';
    
    const upgradeMessage = `${message}\n\nPour continuer à utiliser le service, vous pouvez passer au plan ${upgradePlan}.\n\nSouhaitez-vous ouvrir les paramètres de l'extension ?`;
    
    if (confirm(upgradeMessage)) {
      chrome.runtime.openOptionsPage();
    }
  }

  // Gestionnaire de clic sur Générer
  async function handleGenerateClick(event, commentBox, isReplyToComment) {
    if (!isAuthenticated) {
      window.toastNotification.warning(t('pleaseSignIn'));
      return;
    }

    // Fermer le panneau d'émotions si l'option est activée
    chrome.storage.sync.get(['autoCloseEmotionsPanel'], function(data) {
      if (data.autoCloseEmotionsPanel) {
        const buttonsWrapper = commentBox.closest('.ai-buttons-wrapper') || commentBox.parentElement?.querySelector('.ai-buttons-wrapper');
        if (buttonsWrapper) {
          const emotionsPanel = buttonsWrapper.querySelector('.ai-emotions-container');
          if (emotionsPanel) {
            emotionsPanel.style.animation = 'emotionsPanelDisappear 0.2s ease forwards';
            setTimeout(() => emotionsPanel.remove(), 200);
          }
        }
      }
    });

    // Vérifier le quota avant de procéder
    const quotaCheck = await checkQuotaBeforeGenerate();
    if (!quotaCheck.hasQuota) {
      showUpgradePrompt(quotaCheck);
      return;
    }

    // V3 Story 2.3 — Verifier si l'auteur est dans la blacklist (PREMIUM uniquement)
    const userPlanData = await chrome.storage.local.get(['user_plan']);
    const userPlan = userPlanData.user_plan || 'FREE';
    if (userPlan === 'PREMIUM') {
      const postContainer = findPostContainer(commentBox);
      const authorInfo = extractPostAuthorInfo(postContainer);
      if (authorInfo && authorInfo.name) {
        const isBlacklisted = await isAuthorBlacklisted(authorInfo.name);
        if (isBlacklisted) {
          const shouldProceed = await showBlacklistWarningPopup(authorInfo.name);
          if (!shouldProceed) {
            // Utilisateur a clique "Non" — annuler la generation
            return;
          }
          // Utilisateur a clique "Oui" — continuer normalement
        }
      }
    }

    const button = event.target.closest('.ai-button') || event.target.closest('.ai-generate-button') || event.target.closest('.ai-card') || event.target.closest('.ai-chip');
    const isCard = button && button.classList.contains('ai-card');
    const isChip = button && button.classList.contains('ai-chip');

    // Trouver l'element texte selon le type de bouton
    let labelElement = null;
    const isAiButton = button && button.classList.contains('ai-button');
    if (isCard) {
      labelElement = button.querySelector('.ai-card__label');
    } else if (isChip) {
      labelElement = button.querySelector('.ai-chip__label');
    } else if (isAiButton) {
      // Story 7.13 - Fix: chercher .ai-button__label, pas le premier span
      labelElement = button.querySelector('.ai-button__label');
    } else {
      labelElement = button.querySelector('span');
    }
    const originalContent = labelElement?.textContent || '';

    // Vider le champ de commentaire AVANT l'extraction pour éviter toute confusion
    commentBox.textContent = '';
    commentBox.innerHTML = '';

    button.disabled = true;
    button.classList.add('loading');
    if (labelElement) {
      labelElement.textContent = t('generating');
    }

    // Track generation started
    const generationStartTime = Date.now();
    const selectedEmotion = commentBox.getAttribute('data-selected-emotion');
    const selectedIntensity = commentBox.getAttribute('data-selected-intensity');
    const selectedStyle = commentBox.getAttribute('data-selected-style');

     catch (e) {
      }
    }

    try {
      const postContainer = findPostContainer(commentBox);
      const postContent = extractContent(postContainer, isReplyToComment);

      // Pour "Générer", le contenu est maintenant optionnel comme pour "Avec Prompt"
      console.log('📝 Post content:', postContent ? postContent.substring(0, 50) + '...' : 'None');

      // Récupérer les paramètres contextuels (émotions/styles)
      const selectedEmotion = commentBox.getAttribute('data-selected-emotion');
      const selectedIntensity = commentBox.getAttribute('data-selected-intensity');
      const selectedStyle = commentBox.getAttribute('data-selected-style');

      console.log('🎭 Paramètres contextuels:', {
        emotion: selectedEmotion,
        intensity: selectedIntensity,
        style: selectedStyle
      });

      // V3 Story 5.4 — Priorite au toggle du panneau, sinon fallback vers preference popup
      const toggleNewsMode = commentBox.getAttribute('data-news-enrichment');
      let newsEnrichmentMode = 'disabled';

      if (toggleNewsMode && toggleNewsMode !== 'disabled') {
        // Toggle actif dans le panneau → utiliser ce mode
        newsEnrichmentMode = toggleNewsMode;
      } else {
        // Fallback vers la preference popup existante
        const settings = await chrome.storage.sync.get(['newsEnrichmentMode']);
        newsEnrichmentMode = settings.newsEnrichmentMode || 'title-only';
      }

      // Extraire et envoyer les actualités LinkedIn au backend (si mode smart-summary)
      let newsContext = [];
      if (newsEnrichmentMode !== 'disabled') {
        // sendNewsToBackend gère l'envoi au backend uniquement si mode = 'smart-summary'
        // Sinon, elle retourne simplement les news extraites pour le contexte
        newsContext = await sendNewsToBackend(newsEnrichmentMode, currentCommentLanguage);
        console.log(`📰 Mode enrichissement: ${newsEnrichmentMode}${toggleNewsMode ? ' (toggle panneau)' : ' (preference popup)'}, ${newsContext.length} actualités traitées`);
      } else {
        console.log('📰 Mode enrichissement désactivé');
      }

      // V3 — Lire l'etat du toggle Citation
      const includeQuote = commentBox.getAttribute('data-include-quote') === 'true';
      // V3 — Lire l'etat du toggle Tag Auteur
      const tagAuthor = commentBox.getAttribute('data-tag-author') || null;
      // V3 Story 1.3 — Lire l'etat du toggle Contexte et extraire si actif
      const includeContext = commentBox.getAttribute('data-include-context') === 'true';
      const thirdPartyComments = includeContext ? extractThirdPartyComments(postContainer) : [];
      // V3 Story 1.4 — Lire l'etat du toggle Recherche Web
      const webSearchEnabled = commentBox.getAttribute('data-web-search') === 'true';
      // Lire la longueur selectionnee depuis le chip (ou defaut 21 = M)
      const selectedLength = parseInt(commentBox.getAttribute('data-length')) || 21;

      const requestData = {
        post: postContent || null,
        isComment: isReplyToComment,
        commentLanguage: currentCommentLanguage,
        // Longueur cible (nombre de mots)
        length: selectedLength,
        // Paramètres contextuels (prioritaires sur les paramètres globaux du popup)
        emotion: selectedEmotion,
        intensity: selectedIntensity,
        style: selectedStyle,
        // Contexte des actualités LinkedIn
        newsContext: newsContext,
        newsEnrichmentMode: newsEnrichmentMode,
        // V3 — Citation contextuelle
        include_quote: includeQuote,
        // V3 — Tag auteur
        tag_author: tagAuthor,
        // V3 Story 1.3 — Commentaires tiers pour contextualisation
        third_party_comments: thirdPartyComments.length > 0 ? thirdPartyComments : null,
        // V3 Story 1.4 — Recherche web
        web_search_enabled: webSearchEnabled
      };

      if (isReplyToComment && postContent) {
        const parentPostContent = extractPostContent(postContainer);
        if (parentPostContent && parentPostContent !== postContent) {
          requestData.postParent = parentPostContent;
          requestData.includePostParent = true;
        }
      }

      chrome.runtime.sendMessage({
        action: 'generateThreeComments',
        data: requestData
      }, response => {
        const generationDuration = Date.now() - generationStartTime;

        if (response && response.error) {
          window.toastNotification.error(t('error') + ': ' + response.error);

          // Track generation error
           catch (e) {
            }
          }
        } else if (response && response.comments) {
          // V3 Story 5.5 — Passer l'URL source et le flag fallback au popup
          // Fix: passer webSearchEnabled pour n'afficher le bouton source que si la recherche etait activee
          showOptionsPopup(commentBox, response.comments, postContent || '', null, isReplyToComment, response.web_search_source_url, response.web_search_fallback, webSearchEnabled);

          // V3 Story 1.4 — Notification de fallback si recherche web echouee
          if (response.web_search_fallback) {
            window.toastNotification.warning(t('webSearchFallbackMessage'));
          }

          // Track successful generation
           catch (e) {
            }
          }

          // Story 7.14 — L'emotion et le style persistent apres generation
          // (pas de reset - l'utilisateur garde ses derniers parametres)
        }

        button.disabled = false;
        button.classList.remove('loading');
        // Ne restaurer le texte original QUE si pas un ai-button (qui a ete reset)
        if (!button.classList.contains('ai-button')) {
          if (isIconBtn) {
            button.textContent = originalContent;
          } else if (labelElement) {
            labelElement.textContent = originalContent;
          }
        }
      });

    } catch (error) {
      const generationDuration = Date.now() - generationStartTime;
      window.toastNotification.error(t('error') + ': ' + error.message);

      // Track generation exception
       catch (e) {
        }
      }

      button.disabled = false;
      button.classList.remove('loading');
      if (isIconBtn) {
        button.textContent = originalContent;
      } else if (labelElement) {
        labelElement.textContent = originalContent;
      }
    }
  }

  // Gestionnaire de clic sur Avec prompt
  async function handlePromptClick(event, commentBox, isReplyToComment) {
    if (!isAuthenticated) {
      window.toastNotification.warning(t('pleaseSignIn'));
      return;
    }

    // V3 Story 2.3 — Verifier si l'auteur est dans la blacklist (PREMIUM uniquement)
    const userPlanData = await chrome.storage.local.get(['user_plan']);
    const userPlan = userPlanData.user_plan || 'FREE';

    // Bloquer les utilisateurs FREE — prompt personnalise reserve aux plans payants
    if (userPlan === 'FREE') {
      window.toastNotification.warning(t('promptRequiresPremium') || 'Le prompt personnalise necessite un plan MEDIUM ou PREMIUM');
      return;
    }

    if (userPlan === 'PREMIUM') {
      const postContainer = findPostContainer(commentBox);
      const authorInfo = extractPostAuthorInfo(postContainer);
      if (authorInfo && authorInfo.name) {
        const isBlacklisted = await isAuthorBlacklisted(authorInfo.name);
        if (isBlacklisted) {
          const shouldProceed = await showBlacklistWarningPopup(authorInfo.name);
          if (!shouldProceed) {
            // Utilisateur a clique "Non" — annuler la generation
            return;
          }
          // Utilisateur a clique "Oui" — continuer normalement
        }
      }
    }

    showPromptPopup(commentBox, isReplyToComment);
  }

  // Afficher le popup de prompt
  // V3 Story 7.4 — Migration vers BEM avec ARIA et focus trap
  function showPromptPopup(commentBox, isReplyToComment) {
    // Nettoyer les popups et overlays existants (anciens + nouveaux)
    document.querySelectorAll('.ai-prompt-popup, .ai-options-popup, .ai-popup-overlay, .ai-modal--generation').forEach(p => p.remove());

    chrome.storage.sync.get(['tone'], function(data) {
      const isNegative = data.tone === 'negatif';

      // V3 Story 7.4 — Creer le modal BEM avec ARIA
      const modalParts = createModalBEM({
        variant: 'generation',
        title: t('customInstructions'),
        showCloseButton: true,
        onClose: null,
        onOverlayClick: () => {}
      });

      // Ajouter ancienne classe pour compatibilite CSS
      modalParts.modal.classList.add('ai-prompt-popup');
      modalParts.title.classList.add('ai-popup-title');

      // Reduire la taille du container (350px au lieu de 600px)
      modalParts.container.style.minWidth = '350px';
      modalParts.container.style.maxWidth = '400px';

      // Textarea dans le body
      const textArea = document.createElement('textarea');
      textArea.className = 'ai-prompt-textarea';
      textArea.placeholder = t('addInstructions');
      modalParts.body.appendChild(textArea);

      // Boutons dans le footer
      const cancelButton = document.createElement('button');
      cancelButton.className = 'ai-button ai-button--secondary ai-prompt-cancel';
      cancelButton.textContent = t('cancel');
      cancelButton.onclick = () => modalParts.cleanup();

      const submitButton = document.createElement('button');
      submitButton.className = 'ai-button ai-button--primary ai-prompt-submit';
      if (isNegative) submitButton.classList.add('negative');
      if (isReplyToComment) submitButton.classList.add('reply-mode');
      submitButton.textContent = t('generate');
      submitButton.onclick = () => {
        const userPrompt = textArea.value.trim();
        if (userPrompt) {
          // Track prompt usage (Plan v3)
           catch (e) {
            }
          }

          // Désactiver le bouton et afficher l'indicateur de chargement
          submitButton.disabled = true;
          submitButton.textContent = t('generating');

          // Masquer le popup après un court délai
          setTimeout(() => modalParts.cleanup(), 100);

          handleGenerateWithPrompt(commentBox, userPrompt, isReplyToComment);
        }
      };

      modalParts.footer.appendChild(cancelButton);
      modalParts.footer.appendChild(submitButton);

      // Afficher le modal et focus sur le textarea
      modalParts.show();
      setTimeout(() => textArea.focus(), 100);
    });
  }

  // Générer avec prompt
  async function handleGenerateWithPrompt(commentBox, userPrompt, isReplyToComment) {
    // Trouver le bouton "Avec prompt" et le désactiver pendant le traitement
    const buttonsWrapper = commentBox.parentElement.querySelector('.ai-buttons-wrapper');
    const promptButton = buttonsWrapper ? buttonsWrapper.querySelector('.with-prompt') : null;
    const originalButtonText = promptButton ? promptButton.querySelector('span').textContent : '';

    // Fermer le panneau d'émotions si l'option est activée
    chrome.storage.sync.get(['autoCloseEmotionsPanel'], function(data) {
      if (data.autoCloseEmotionsPanel && buttonsWrapper) {
        const emotionsPanel = buttonsWrapper.querySelector('.ai-emotions-container');
        if (emotionsPanel) {
          emotionsPanel.style.animation = 'emotionsPanelDisappear 0.2s ease forwards';
          setTimeout(() => emotionsPanel.remove(), 200);
        }
      }
    });

    // Vider le champ de commentaire AVANT l'extraction pour éviter toute confusion
    commentBox.textContent = '';
    commentBox.innerHTML = '';

    if (promptButton) {
      promptButton.disabled = true;
      promptButton.classList.add('loading');
      promptButton.querySelector('span').textContent = t('generating');
    }

    // Vérifier le quota avant de procéder
    const quotaCheck = await checkQuotaBeforeGenerate();
    if (!quotaCheck.hasQuota) {
      // Restaurer le bouton en cas d'erreur de quota
      if (promptButton) {
        promptButton.disabled = false;
        promptButton.classList.remove('loading');
        promptButton.querySelector('span').textContent = originalButtonText;
      }
      showUpgradePrompt(quotaCheck);
      return;
    }

    // Track generation started
    const generationStartTime = Date.now();
    const selectedEmotion = commentBox.getAttribute('data-selected-emotion');
    const selectedIntensity = commentBox.getAttribute('data-selected-intensity');
    const selectedStyle = commentBox.getAttribute('data-selected-style');

     catch (e) {
      }
    }

    try {
      const postContainer = findPostContainer(commentBox);
      const postContent = extractContent(postContainer, isReplyToComment);

      // Pour "Avec Prompt", le contenu du post est optionnel
      // L'utilisateur peut générer du contenu uniquement à partir du prompt
      console.log('📝 Post content:', postContent ? postContent.substring(0, 50) + '...' : 'None (prompt only)');

      // Récupérer les paramètres contextuels (émotions/styles)
      const selectedEmotion = commentBox.getAttribute('data-selected-emotion');
      const selectedIntensity = commentBox.getAttribute('data-selected-intensity');
      const selectedStyle = commentBox.getAttribute('data-selected-style');

      console.log('🎭 Paramètres contextuels:', {
        emotion: selectedEmotion,
        intensity: selectedIntensity,
        style: selectedStyle
      });

      // V3 Story 5.4 — Priorite au toggle du panneau, sinon fallback vers preference popup
      const toggleNewsMode = commentBox.getAttribute('data-news-enrichment');
      let newsEnrichmentMode = 'disabled';

      if (toggleNewsMode && toggleNewsMode !== 'disabled') {
        // Toggle actif dans le panneau → utiliser ce mode
        newsEnrichmentMode = toggleNewsMode;
      } else {
        // Fallback vers la preference popup existante
        const settings = await chrome.storage.sync.get(['newsEnrichmentMode']);
        newsEnrichmentMode = settings.newsEnrichmentMode || 'title-only';
      }

      // Extraire et envoyer les actualités LinkedIn au backend (si mode smart-summary)
      let newsContext = [];
      if (newsEnrichmentMode !== 'disabled') {
        // sendNewsToBackend gère l'envoi au backend uniquement si mode = 'smart-summary'
        // Sinon, elle retourne simplement les news extraites pour le contexte
        newsContext = await sendNewsToBackend(newsEnrichmentMode, currentCommentLanguage);
        console.log(`📰 Mode enrichissement (avec prompt): ${newsEnrichmentMode}${toggleNewsMode ? ' (toggle panneau)' : ' (preference popup)'}, ${newsContext.length} actualités traitées`);
      } else {
        console.log('📰 Mode enrichissement désactivé (avec prompt)');
      }

      // V3 — Lire l'etat des toggles
      const includeQuote = commentBox.getAttribute('data-include-quote') === 'true';
      const tagAuthor = commentBox.getAttribute('data-tag-author') || null;
      const includeContext = commentBox.getAttribute('data-include-context') === 'true';
      const thirdPartyComments = includeContext ? extractThirdPartyComments(postContainer) : [];
      const webSearchEnabled = commentBox.getAttribute('data-web-search') === 'true';
      // Lire la longueur selectionnee depuis le chip (ou defaut 21 = M)
      const selectedLength = parseInt(commentBox.getAttribute('data-length')) || 21;

      const requestData = {
        post: postContent || null,
        userPrompt: userPrompt,
        isComment: isReplyToComment,
        commentLanguage: currentCommentLanguage,
        // Longueur cible (nombre de mots)
        length: selectedLength,
        // Paramètres contextuels (prioritaires sur les paramètres globaux du popup)
        emotion: selectedEmotion,
        intensity: selectedIntensity,
        style: selectedStyle,
        // Contexte des actualités LinkedIn
        newsContext: newsContext,
        newsEnrichmentMode: newsEnrichmentMode,
        // V3 — Citation contextuelle
        include_quote: includeQuote,
        // V3 — Tag auteur
        tag_author: tagAuthor,
        // V3 Story 1.3 — Commentaires tiers pour contextualisation
        third_party_comments: thirdPartyComments.length > 0 ? thirdPartyComments : null,
        // V3 Story 1.4 — Recherche web
        web_search_enabled: webSearchEnabled
      };

      if (isReplyToComment && postContent) {
        const parentPostContent = extractPostContent(postContainer);
        if (parentPostContent && parentPostContent !== postContent) {
          requestData.postParent = parentPostContent;
          requestData.includePostParent = true;
        }
      }

      chrome.runtime.sendMessage({
        action: 'generateThreeCommentsWithPrompt',
        data: requestData
      }, response => {
        const generationDuration = Date.now() - generationStartTime;

        // Restaurer le bouton "Avec prompt"
        if (promptButton) {
          promptButton.disabled = false;
          promptButton.classList.remove('loading');
          promptButton.querySelector('span').textContent = originalButtonText;
        }

        if (response && response.error) {
          window.toastNotification.error(t('error') + ': ' + response.error);

          // Track generation error
           catch (e) {
            }
          }
        } else if (response && response.comments) {
          // V3 Story 5.5 — Passer l'URL source et le flag fallback au popup
          // Fix: passer webSearchEnabled pour n'afficher le bouton source que si la recherche etait activee
          showOptionsPopup(commentBox, response.comments, postContent || '', userPrompt, isReplyToComment, response.web_search_source_url, response.web_search_fallback, webSearchEnabled);

          // V3 Story 1.4 — Notification de fallback si recherche web echouee
          if (response.web_search_fallback) {
            window.toastNotification.warning(t('webSearchFallbackMessage'));
          }

          // Track successful generation
           catch (e) {
            }
          }
        }
      });

    } catch (error) {
      const generationDuration = Date.now() - generationStartTime;

      // Restaurer le bouton en cas d'erreur
      if (promptButton) {
        promptButton.disabled = false;
        promptButton.classList.remove('loading');
        promptButton.querySelector('span').textContent = originalButtonText;
      }
      window.toastNotification.error(t('error') + ': ' + error.message);

      // Track generation exception
       catch (e) {
        }
      }
    }
  }

  // Afficher le popup avec les options
  // V3 Story 5.5 — Ajout des parametres webSearchSourceUrl (6eme) et webSearchFallback (7eme)
  // V3 Story 7.4 — Migration vers BEM avec ARIA et focus trap
  // Fix: Ajout de webSearchEnabled (8eme) pour conditionner l'affichage du bouton source
  function showOptionsPopup(commentBox, comments, postContent, userPrompt, isReplyToComment, webSearchSourceUrl, webSearchFallback, webSearchEnabled) {
    // Nettoyer les popups et overlays existants (anciens + nouveaux)
    document.querySelectorAll('.ai-options-popup, .ai-prompt-popup, .ai-popup-overlay, .ai-modal--generation').forEach(p => p.remove());

    chrome.storage.sync.get(['tone'], function(data) {
      const isNegative = data.tone === 'negatif';

      // Récupérer le plan utilisateur
      chrome.runtime.sendMessage({ action: 'getQuotaInfo' }, (quotaResponse) => {
        console.log('🔍 Quota response:', quotaResponse);
        const userPlan = quotaResponse?.role || 'FREE';
        console.log('🎫 User plan detected:', userPlan);

        // Récupérer les paramètres contextuels pour les métadonnées
        const selectedEmotion = commentBox.getAttribute('data-selected-emotion');
        const selectedIntensity = commentBox.getAttribute('data-selected-intensity');
        const selectedStyle = commentBox.getAttribute('data-selected-style');
        const selectedLengthKey = commentBox.getAttribute('data-length-key') || 'lengthMedium';
        // Options d'enrichissement activées
        const hasQuote = commentBox.getAttribute('data-include-quote') === 'true';
        const hasTagAuthor = !!commentBox.getAttribute('data-tag-author');
        const hasContext = commentBox.getAttribute('data-include-context') === 'true';
        const hasNews = commentBox.getAttribute('data-news-enrichment') && commentBox.getAttribute('data-news-enrichment') !== 'disabled';

        // V3 Story 7.4 — Creer le modal BEM avec ARIA (sans header pour ce modal)
        const titleText = `${comments.length} ${t('generations')}${comments.length > 1 ? 's' : ''}`;
        const modalParts = createModalBEM({
          variant: 'generation',
          title: titleText,
          showCloseButton: true,
          onClose: null, // Cleanup gere automatiquement
          onOverlayClick: () => {} // Ferme au clic overlay
        });

        // Reference au modal pour createCommentOption (compatibilite)
        // createCommentOption utilise popup.remove() - on garde la reference
        const popup = modalParts.modal;
        popup.classList.add('ai-options-popup'); // Compatibilite ancienne classe

        // Supprimer header et footer (design minimaliste pour ce modal)
        modalParts.header.remove();
        modalParts.footer.remove();

        // Ajouter bouton fermer flottant (top-right du container)
        const floatingClose = document.createElement('button');
        floatingClose.className = 'ai-modal__close ai-modal__close--floating';
        floatingClose.setAttribute('aria-label', 'Fermer');
        floatingClose.innerHTML = '×';
        // IMPORTANT: Utiliser modalParts.cleanup() pour proper cleanup (focus trap, ESC handler, focus restoration)
        floatingClose.addEventListener('click', () => modalParts.cleanup());
        modalParts.container.appendChild(floatingClose);

        // Ajouter les options de commentaires dans le body
        comments.forEach((comment, index) => {
          const metadata = {
            language: currentCommentLanguage,
            length: selectedLengthKey, // Utiliser la taille sélectionnée (XS/S/M/L/XL)
            emotion: selectedEmotion,
            intensity: selectedIntensity,
            style: selectedStyle,
            // Options d'enrichissement
            hasQuote,
            hasTagAuthor,
            hasContext,
            hasWebSearch: webSearchEnabled,
            hasNews
          };
          // V3 Story 5.5 — Passer webSearchSourceUrl (11eme), webSearchFallback (12eme), webSearchEnabled (13eme)
          // Note: popup passe pour compatibilite avec createCommentOption, cleanup pour fermer proprement le modal
          const option = createCommentOption(comment, index, commentBox, popup, postContent, userPrompt, isReplyToComment, isNegative, userPlan, metadata, webSearchSourceUrl, webSearchFallback, webSearchEnabled, modalParts.cleanup);
          modalParts.body.appendChild(option);
        });

        // Afficher le modal
        modalParts.show();
      });
    });
  }

  // Créer un séparateur de métadonnées
  function createMetaSeparator() {
    const separator = document.createElement('span');
    separator.className = 'ai-meta-separator';
    separator.textContent = '•';
    return separator;
  }

  // Mapper les émotions vers leurs labels
  function getEmotionLabel(emotionKey) {
    const emotionLabels = {
      admiration: 'Admiration',
      inspiration: 'Inspiration',
      curiosity: 'Curiosité',
      gratitude: 'Gratitude',
      empathy: 'Empathie',
      skepticism: 'Scepticisme'
    };
    return emotionLabels[emotionKey] || emotionKey;
  }

  // Story 7.13 - Recuperer l'emoji d'une emotion depuis EMOTION_WHEEL_CONFIG
  function getEmotionEmoji(emotionKey) {
    const emotion = EMOTION_WHEEL_CONFIG.emotions.find(e => e.key === emotionKey);
    return emotion ? emotion.emoji : '😊';
  }

  // Mapper les styles vers leurs labels
  function getStyleLabel(styleKey) {
    const styleLabels = {
      // Styles de langage
      oral: 'Conversationnel',
      professional: 'Professionnel',
      storytelling: 'Storytelling',
      poetic: 'Créatif',
      humoristic: 'Humoristique',
      impactful: 'Impactant',
      benevolent: 'Bienveillant',
      // Tons (fusion ex-popup)
      formal: 'Soutenu',
      friendly: 'Amical',
      expert: 'Expert',
      informative: 'Informatif',
      negative: 'Négatif'
    };
    return styleLabels[styleKey] || styleKey;
  }

  // Mapper l'intensité vers un label
  function getIntensityLabel(intensityKey) {
    const intensityLabels = {
      low: 'Légère',
      medium: 'Modérée',
      high: 'Forte'
    };
    return intensityLabels[intensityKey] || intensityKey;
  }

  // Créer une option de commentaire
  // V3 Story 5.5 — Ajout des parametres webSearchSourceUrl (11eme), webSearchFallback (12eme), webSearchEnabled (13eme)
  function createCommentOption(comment, index, commentBox, popup, postContent, userPrompt, isReplyToComment, isNegative, userPlan, metadata, webSearchSourceUrl, webSearchFallback, webSearchEnabled, modalCleanup) {
    const option = document.createElement('div');
    option.className = 'ai-option';
    if (isNegative) option.classList.add('negative');

    // V3 Story 5.5 — Variable pour suivre le commentaire (peut etre modifie si source ajoutee)
    let currentComment = comment;

    // Vérifier si cette option est verrouillée pour les utilisateurs FREE
    const isLocked = userPlan === 'FREE' && index > 0; // Options 2 et 3 verrouillées (index 1 et 2)

    if (isLocked) {
      option.classList.add('locked');
    }

    const optionNumber = document.createElement('div');
    optionNumber.className = 'ai-option-number';
    if (isNegative) optionNumber.classList.add('negative');
    optionNumber.textContent = `${index + 1}`;

    option.appendChild(optionNumber);

    // Ajouter les métadonnées (Option 3)
    if (metadata) {
      const metaContainer = document.createElement('div');
      metaContainer.className = 'ai-generation-meta';

      // Langue
      const langMeta = document.createElement('span');
      langMeta.className = 'ai-meta-item meta-language';
      langMeta.title = 'Langue du commentaire';
      langMeta.innerHTML = `🌐 ${metadata.language.toUpperCase()}`;
      metaContainer.appendChild(langMeta);

      metaContainer.appendChild(createMetaSeparator());

      // Longueur (metadata.length contient la clé de traduction comme 'lengthVeryShort')
      const lengthMeta = document.createElement('span');
      lengthMeta.className = 'ai-meta-item meta-length';
      lengthMeta.title = 'Longueur du commentaire';
      lengthMeta.innerHTML = `📝 ${t(metadata.length)}`;
      metaContainer.appendChild(lengthMeta);

      // Émotion + Intensité (combinés dans un seul tag)
      if (metadata.emotion) {
        metaContainer.appendChild(createMetaSeparator());
        const emotionMeta = document.createElement('span');
        emotionMeta.className = 'ai-meta-item meta-emotion';
        // Story 7.14 - Inclure l'intensite entre parentheses si definie
        const intensityText = metadata.intensity ? ` (${getIntensityLabel(metadata.intensity)})` : '';
        emotionMeta.title = metadata.intensity ? `Émotion: ${getEmotionLabel(metadata.emotion)}, Intensité: ${getIntensityLabel(metadata.intensity)}` : 'Émotion';
        emotionMeta.innerHTML = `${getEmotionEmoji(metadata.emotion)} ${getEmotionLabel(metadata.emotion)}${intensityText}`;
        metaContainer.appendChild(emotionMeta);
      }

      // Style (si défini)
      if (metadata.style) {
        metaContainer.appendChild(createMetaSeparator());
        const styleMeta = document.createElement('span');
        styleMeta.className = 'ai-meta-item meta-style';
        styleMeta.title = 'Style de langage';
        styleMeta.innerHTML = `💼 ${getStyleLabel(metadata.style)}`;
        metaContainer.appendChild(styleMeta);
      }

      // Options d'enrichissement activées (labels verts)
      const enrichmentOptions = [];
      if (metadata.hasQuote) enrichmentOptions.push({ icon: '💬', label: t('quoteToggle') });
      if (metadata.hasTagAuthor) enrichmentOptions.push({ icon: '👤', label: t('tagAuthor') });
      if (metadata.hasContext) enrichmentOptions.push({ icon: '💭', label: t('contextToggle') });
      if (metadata.hasWebSearch) enrichmentOptions.push({ icon: '🔍', label: t('webSearchToggle') });
      if (metadata.hasNews) enrichmentOptions.push({ icon: '📰', label: t('newsToggle') });

      if (enrichmentOptions.length > 0) {
        metaContainer.appendChild(createMetaSeparator());
        enrichmentOptions.forEach((opt, idx) => {
          const enrichMeta = document.createElement('span');
          enrichMeta.className = 'ai-meta-item meta-enrichment';
          enrichMeta.innerHTML = `${opt.icon} ${opt.label}`;
          metaContainer.appendChild(enrichMeta);
          if (idx < enrichmentOptions.length - 1) {
            metaContainer.appendChild(createMetaSeparator());
          }
        });
      }

      option.appendChild(metaContainer);
    }

    const optionText = document.createElement('div');
    optionText.className = 'ai-option-text';
    optionText.textContent = comment;

    option.appendChild(optionText);

    // V3 Story 5.5 — Bouton "Afficher la source" ou "Aucune source trouvée"
    // Fix: Le bouton s'affiche SEULEMENT si webSearchEnabled est true (l'utilisateur a demande une source)
    if (webSearchEnabled && webSearchSourceUrl) {
      // Cas 1: Source disponible — bouton actif
      const showSourceBtn = document.createElement('button');
      showSourceBtn.className = 'ai-button ai-button--ghost ai-button--sm ai-show-source-btn';
      if (isNegative) showSourceBtn.classList.add('negative');
      showSourceBtn.innerHTML = `🔗 ${t('showSourceBtn')}`;
      showSourceBtn.onclick = (e) => {
        e.stopPropagation(); // Empecher le clic de selectionner l'option
        // Ajouter la source au commentaire
        currentComment = comment + `\n\nSource: ${webSearchSourceUrl}`;
        optionText.textContent = currentComment;
        // Mettre a jour le bouton
        showSourceBtn.innerHTML = `✓ ${t('showSourceAdded')}`;
        showSourceBtn.classList.add('added');
        showSourceBtn.disabled = true;
      };
      option.appendChild(showSourceBtn);
    } else if (webSearchEnabled && !webSearchSourceUrl) {
      // Cas 2: Recherche web activee mais aucune source trouvee — bouton grise informatif
      // Fix: on verifie webSearchEnabled pour n'afficher que si l'utilisateur a demande une source
      const showSourceBtn = document.createElement('button');
      showSourceBtn.className = 'ai-button ai-button--ghost ai-button--sm ai-button--disabled ai-show-source-btn';
      if (isNegative) showSourceBtn.classList.add('negative');
      showSourceBtn.innerHTML = `🔗 ${t('noSourceAvailable')}`;
      showSourceBtn.onclick = (e) => {
        e.stopPropagation();
        window.toastNotification.info(t('noSourceAvailable'));
      };
      option.appendChild(showSourceBtn);
    }
    // Cas 3: Recherche web non activee (webSearchFallback === undefined) — pas de bouton

    // Ajouter l'icône de verrouillage si l'option est verrouillée
    if (isLocked) {
      const lockIcon = document.createElement('div');
      lockIcon.className = 'ai-lock-icon';
      lockIcon.innerHTML = '🔒';
      lockIcon.title = t('upgradeToPremium') || 'Passez à MEDIUM ou PREMIUM pour débloquer';
      option.appendChild(lockIcon);
    }

    option.addEventListener('click', (event) => {
      if (event.target.closest('button')) return;

      // Empêcher la sélection si l'option est verrouillée
      if (isLocked) {
        showPremiumUpgradePrompt(t('lockedCommentUpgradeRequired'));
        return;
      }

      // V3 Story 1.2 v2 — Insertion en deux temps pour les mentions LinkedIn
      // V3 Story 5.5 — Utiliser currentComment qui peut inclure la source
      const tagAuthorName = commentBox.getAttribute('data-tag-author');
      const { beforeMention, afterMention, hasSplit } = splitCommentForMention(currentComment);

      if (tagAuthorName && hasSplit && afterMention) {
        // Mode deux temps : inserer seulement le debut (jusqu'au @Prenom inclus)
        commentBox.textContent = beforeMention;

        // Extraire le prenom pour la detection
        const firstName = tagAuthorName.split(' ')[0];

        // Lancer l'observer pour detecter la mention
        // Passer un callback pour supprimer ai-modal-active une fois la mention completee
        observeMentionCreation(commentBox, afterMention, firstName, () => {
          document.body.classList.remove('ai-modal-active');
        });

        // Fermer le modal visuellement mais GARDER ai-modal-active pour masquer les boutons
        // L'utilisateur doit pouvoir cliquer sur la suggestion LinkedIn sans interference
        popup.remove();
        document.querySelectorAll('.ai-popup-overlay').forEach(o => o.remove());

        // Toast pour guider l'utilisateur
        if (window.toastNotification) {
          window.toastNotification.info(t('clickMentionSuggestion') || 'Cliquez sur la suggestion LinkedIn');
        }
      } else {
        // Mode normal : inserer tout le commentaire (nettoyer le delimiteur si present)
        commentBox.textContent = currentComment.replace('{{{SPLIT}}}', '');

        // Fermer proprement le modal (supprime aussi ai-modal-active du body)
        if (modalCleanup) {
          modalCleanup();
        } else {
          popup.remove();
          document.querySelectorAll('.ai-popup-overlay').forEach(o => o.remove());
          document.body.classList.remove('ai-modal-active');
        }
      }
      commentBox.focus();

      // Positionner le curseur a la fin du texte (necessaire pour que LinkedIn detecte le @)
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(commentBox);
      range.collapse(false); // false = collapse to end
      selection.removeAllRanges();
      selection.addRange(range);

      const inputEvent = new Event('input', { bubbles: true });
      commentBox.dispatchEvent(inputEvent);

      // Track comment insertion
      // V3 Story 5.5 — Utiliser currentComment.length (peut inclure la source)
       catch (e) {
        }
      }
    });

    // Ajouter les boutons d'action
    const buttonsContainer = document.createElement('div');
    buttonsContainer.className = 'ai-action-buttons-container';

    // V3 Story 5.1 Review - Variable unique pour verrouillage boutons FREE
    const isButtonsLocked = userPlan === 'FREE';

    const refineButton = document.createElement('button');
    refineButton.className = 'ai-button ai-button--ghost ai-refine-button';
    if (isNegative) refineButton.classList.add('negative');
    if (isButtonsLocked) {
      refineButton.classList.add('locked');
      refineButton.setAttribute('aria-disabled', 'true');
      refineButton.innerHTML = `<span>🔒 ${t('refine')}</span>`;
    } else {
      refineButton.innerHTML = `<span>${t('refine')}</span>`;
    }
    refineButton.onclick = () => {
      if (isButtonsLocked) {
        showPremiumUpgradePrompt(t('lockedRefineResizeUpgradeRequired'));
        return;
      }
      showRefinePopup(commentBox, comment, postContent, userPrompt, index, popup, isReplyToComment);
    };

    const minusButton = document.createElement('button');
    minusButton.className = 'ai-button ai-button--ghost ai-minus-button';
    if (isNegative) minusButton.classList.add('negative');
    if (isButtonsLocked) {
      minusButton.classList.add('locked');
      minusButton.setAttribute('aria-disabled', 'true');
      minusButton.textContent = '🔒';
    } else {
      minusButton.textContent = '➖';
    }
    minusButton.onclick = (e) => {
      if (isButtonsLocked) {
        showPremiumUpgradePrompt(t('lockedRefineResizeUpgradeRequired'));
        return;
      }
      handleResizeComment(e, commentBox, comment, postContent, '-', index, popup, isReplyToComment);
    };

    const plusButton = document.createElement('button');
    plusButton.className = 'ai-button ai-button--ghost ai-plus-button';
    if (isNegative) plusButton.classList.add('negative');
    if (isButtonsLocked) {
      plusButton.classList.add('locked');
      plusButton.setAttribute('aria-disabled', 'true');
      plusButton.textContent = '🔒';
    } else {
      plusButton.textContent = '➕';
    }
    plusButton.onclick = (e) => {
      if (isButtonsLocked) {
        showPremiumUpgradePrompt(t('lockedRefineResizeUpgradeRequired'));
        return;
      }
      handleResizeComment(e, commentBox, comment, postContent, '+', index, popup, isReplyToComment);
    };

    buttonsContainer.appendChild(minusButton);
    buttonsContainer.appendChild(refineButton);
    buttonsContainer.appendChild(plusButton);
    option.appendChild(buttonsContainer);

    return option;
  }

  // Redimensionner un commentaire
  function handleResizeComment(event, commentBox, originalComment, postContent, direction, optionIndex, optionsPopup, isReplyToComment) {
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = '⏳';
    button.disabled = true;

    const resizeStartTime = Date.now();

    // Track resize started
    );
      } catch (e) {
      }
    }

    chrome.runtime.sendMessage({
      action: 'resizeComment',
      data: {
        post: postContent,
        originalComment: originalComment,
        resizeDirection: direction,
        currentWordCount: originalComment.split(' ').length,
        commentLanguage: currentCommentLanguage
      }
    }, response => {
      const resizeDuration = Date.now() - resizeStartTime;

      if (response.error) {
        window.toastNotification.error(t('error') + ': ' + response.error);

        // Track resize error
         catch (e) {
          }
        }
      } else if (response.resizedComment) {
        // Mettre à jour le texte
        const option = optionsPopup.querySelectorAll('.ai-option')[optionIndex];
        if (option) {
          const textElement = option.querySelector('.ai-option-text');
          textElement.textContent = response.resizedComment;
        }

        // Track successful resize
         catch (e) {
          }
        }
      }

      button.textContent = originalText;
      button.disabled = false;
    });
  }

  // Affiner un commentaire
  // V3 Story 7.4 — Migration vers BEM avec ARIA et focus trap
  function showRefinePopup(commentBox, originalComment, postContent, userPrompt, optionIndex, optionsPopup, isReplyToComment) {
    document.querySelectorAll('.ai-refine-popup').forEach(p => p.remove());

    chrome.storage.sync.get(['tone'], function(data) {
      const isNegative = data.tone === 'negatif';

      // V3 Story 7.4 — Creer le modal BEM avec ARIA
      // Note: z-index eleve car ce modal s'affiche AU-DESSUS du modal options
      const modalParts = createModalBEM({
        variant: 'generation',
        title: t('refineComment'),
        showCloseButton: true,
        onClose: null,
        onOverlayClick: () => {}
      });

      // Z-index eleve pour etre au-dessus du modal options
      modalParts.modal.style.zIndex = '10004';
      modalParts.overlay.style.zIndex = '10004';
      modalParts.container.style.zIndex = '10005';

      // Ajouter ancienne classe pour compatibilite CSS
      modalParts.modal.classList.add('ai-refine-popup');
      modalParts.title.classList.add('ai-popup-title');

      // Reduire la taille du container
      modalParts.container.style.minWidth = '350px';
      modalParts.container.style.maxWidth = '400px';

      // Contexte du commentaire original dans le body
      const context = document.createElement('div');
      context.className = 'ai-refine-context';
      context.textContent = `${t('comment')}: "${originalComment}"`;
      modalParts.body.appendChild(context);

      // Textarea pour les instructions
      const textArea = document.createElement('textarea');
      textArea.className = 'ai-refine-textarea';
      textArea.placeholder = t('refineInstructions');
      modalParts.body.appendChild(textArea);

      // Boutons dans le footer
      const cancelButton = document.createElement('button');
      cancelButton.className = 'ai-button ai-button--secondary ai-refine-cancel';
      cancelButton.textContent = t('cancel');
      cancelButton.onclick = () => modalParts.cleanup();

      const submitButton = document.createElement('button');
      submitButton.className = 'ai-button ai-button--primary ai-refine-submit';
      if (isNegative) submitButton.classList.add('negative');
      if (isReplyToComment) submitButton.classList.add('reply-mode');
      submitButton.textContent = t('refine');
      submitButton.onclick = () => {
        const refineInstructions = textArea.value.trim();
        if (refineInstructions) {
          modalParts.cleanup();
          handleRefineComment(commentBox, originalComment, postContent, userPrompt, refineInstructions, optionIndex, optionsPopup, isReplyToComment);
        }
      };

      modalParts.footer.appendChild(cancelButton);
      modalParts.footer.appendChild(submitButton);

      // Afficher le modal et focus sur le textarea
      modalParts.show();
      setTimeout(() => textArea.focus(), 100);
    });
  }
  
  function handleRefineComment(commentBox, originalComment, postContent, userPrompt, refineInstructions, optionIndex, optionsPopup, isReplyToComment) {
    const refineStartTime = Date.now();

    // Track refine started
     catch (e) {
      }
    }

    chrome.runtime.sendMessage({
      action: 'refineComment',
      data: {
        post: postContent,
        userPrompt: userPrompt,
        originalComment: originalComment,
        refineInstructions: refineInstructions,
        commentLanguage: currentCommentLanguage
      }
    }, response => {
      const refineDuration = Date.now() - refineStartTime;

      if (response.error) {
        window.toastNotification.error(t('error') + ': ' + response.error);

        // Track refine error
         catch (e) {
          }
        }
      } else if (response.refinedComment) {
        // Mettre à jour le texte
        const option = optionsPopup.querySelectorAll('.ai-option')[optionIndex];
        if (option) {
          const textElement = option.querySelector('.ai-option-text');
          textElement.textContent = response.refinedComment;
        }

        // Track successful refine
         catch (e) {
          }
        }
      }
    });
  }

  // Fonctions utilitaires
  function findPostContainer(commentBox) {
    console.log('🔍 Recherche du container depuis commentBox:', commentBox);
    const container = commentBox.closest('[data-view-name="feed-full-update"]') ||
                      commentBox.closest('[role="listitem"]') ||
                      commentBox.closest('[data-id]') ||
                      commentBox.closest('article') ||
                      commentBox.closest('.feed-shared-update-v2') ||
                      commentBox.closest('[role="article"]');
    console.log('📦 Container trouvé:', container);
    return container;
  }
  
  function extractContent(container, isComment) {
    if (!container) return null;
    return isComment ? extractCommentContent(container) : extractPostContent(container);
  }
  
  function extractCommentContent(container) {
    if (!container) {
      console.warn('⚠️ extractCommentContent: Container est null');
      return null;
    }

    console.log('🔍 extractCommentContent: Début extraction depuis container:', container.className);

    // D'abord, essayer de trouver le commentaire parent le plus proche
    const commentEntity = container.closest('[data-view-name="comment-container"]') ||
                          container.closest('.comments-comment-entity, .comments-comment-item, [data-id*="comment"]');
    console.log('🔍 extractCommentContent: commentEntity trouvé:', !!commentEntity, commentEntity?.className);

    if (commentEntity) {
      const selectors = [
        // Sélecteurs LinkedIn 2025+ SDUI
        '[data-view-name="comment-commentary"] [data-testid="expandable-text-box"]',
        '[data-view-name="comment-commentary"]',
        // Sélecteurs legacy
        '.comments-comment-item__main-content',
        '.feed-shared-main-content--comment',
        '.update-components-text',
        '.break-words',
        '.comments-comment-item-content-body',
        '.attributed-text-segment-list__content',
        '[data-test-id="comment-text"]',
        '.feed-shared-text__text-view'
      ];

      for (const selector of selectors) {
        const element = commentEntity.querySelector(selector);
        if (element) {
          const content = element.textContent.trim();
          console.log(`🔍 extractCommentContent: Sélecteur ${selector} trouvé, contenu:`, content ? content.substring(0, 50) + '...' : 'vide');
          if (content && content.length > 0) {
            console.log('✅ Contenu du commentaire extrait via:', selector);
            return content;
          }
        }
      }

      // Fallback 1 : prendre tout le texte du commentaire parent
      const allText = commentEntity.textContent.trim();
      console.log('🔍 extractCommentContent: Fallback 1 (commentEntity), contenu:', allText ? allText.substring(0, 50) + '...' : 'vide');
      if (allText && allText.length > 0) {
        console.log('✅ Contenu du commentaire extrait via fallback 1 (commentEntity)');
        return allText;
      }
    }

    // Fallback 2 : utiliser directement le container
    const containerText = container.textContent.trim();
    console.log('🔍 extractCommentContent: Fallback 2 (container direct), contenu:', containerText ? containerText.substring(0, 50) + '...' : 'vide');
    if (containerText && containerText.length > 0) {
      console.log('✅ Contenu du commentaire extrait via fallback 2 (container direct)');
      return containerText;
    }

    console.warn('⚠️ extractCommentContent: Impossible de trouver le contenu du commentaire');
    console.warn('⚠️ extractCommentContent: Container HTML:', container.innerHTML.substring(0, 200));
    return null;
  }

  // V3 Story 1.2 — Extraction du nom de l'auteur du post
  function extractPostAuthorName(postElement) {
    if (!postElement) {
      return null;
    }

    // Selecteurs tries dans l'ordre de fiabilite (LinkedIn 2026 SDUI)
    const selectors = [
      // LinkedIn 2026 SDUI - Bouton Suivre avec aria-label contenant le nom
      'button[aria-label^="Suivre "]',
      'button[aria-label^="Follow "]',
      // LinkedIn 2026 SDUI - Nom dans feed-actor-sub-description
      '[data-view-name="feed-actor-sub-description"] strong',
      '[data-view-name="feed-actor-sub-description"] a',
      // LinkedIn 2025+ legacy - Classes BEM (fallback si SDUI pas actif)
      '.update-components-actor__name .visually-hidden',
      '.update-components-actor__name span[aria-hidden="true"]',
      '.feed-shared-actor__name .visually-hidden',
      '.feed-shared-actor__name span[aria-hidden="true"]',
      // Fallback generique
      '[data-view-name="feed-actor-name"]',
      '.feed-shared-actor__title',
      '.update-components-actor__title'
    ];

    for (const selector of selectors) {
      const element = postElement.querySelector(selector);
      if (element) {
        let rawName = '';

        // Pour les boutons Suivre, extraire le nom depuis aria-label
        if (selector.startsWith('button[aria-label')) {
          rawName = element.getAttribute('aria-label') || '';
          // Retirer le prefixe "Suivre " ou "Follow "
          rawName = rawName.replace(/^Suivre\s+/i, '').replace(/^Follow\s+/i, '');
        } else {
          rawName = element.textContent || '';
        }

        // Nettoyer : retirer emojis, titres, espaces multiples
        const cleaned = rawName
          .replace(/[\u{1F300}-\u{1F9FF}]/gu, '')
          .replace(/\s*\|.*$/, '')
          .replace(/\s+/g, ' ')
          .trim();

        if (cleaned && cleaned.length >= 2 && cleaned.length <= 60) {
          return cleaned;
        }
      }
    }

    // Fallback : chercher des liens <a> avec le pattern LinkedIn "Nom • Titre"
    const allLinks = postElement.querySelectorAll('a');
    for (const link of allLinks) {
      const text = link.textContent || '';
      // Pattern LinkedIn: "Prénom Nom • 1er/2e/3e" ou "Prénom Nom • Titre"
      if (text.includes('•') || text.includes('·')) {
        const parts = text.split(/[•·]/);
        if (parts.length >= 2) {
          const potentialName = parts[0].trim();
          // Verifier que ca ressemble a un nom (2-60 chars, pas que des chiffres)
          if (potentialName.length >= 2 && potentialName.length <= 60 && !/^\d+$/.test(potentialName)) {
            // Nettoyer : retirer emojis
            const cleaned = potentialName
              .replace(/[\u{1F300}-\u{1F9FF}]/gu, '')
              .replace(/\s+/g, ' ')
              .trim();
            if (cleaned.length >= 2) {
              return cleaned;
            }
          }
        }
      }
    }

    return null;
  }

  // V3 Story 2.1 — Extraction du nom ET de l'URL du profil de l'auteur
  function extractPostAuthorInfo(postElement) {
    if (!postElement) {
      return { name: null, url: null };
    }

    // D'abord extraire le nom via la fonction existante
    const name = extractPostAuthorName(postElement);

    // Ensuite essayer d'extraire l'URL du profil
    let url = null;

    // Selecteurs pour le lien du profil (ordre de fiabilite)
    const profileLinkSelectors = [
      // LinkedIn 2026 SDUI - Lien profil dans l'en-tete
      'a[href*="/in/"][data-tracking-control-name]',
      'a[href*="/in/"]',
      // Fallback - lien vers company pages
      'a[href*="/company/"]'
    ];

    for (const selector of profileLinkSelectors) {
      const element = postElement.querySelector(selector);
      if (element && element.href) {
        // Verifier que c'est bien un lien LinkedIn profil
        if (element.href.includes('/in/') || element.href.includes('/company/')) {
          url = element.href;
          break;
        }
      }
    }

    return { name, url };
  }

  // V3 Story 2.3 — Verifier si l'auteur est dans la blacklist (cache local)
  async function isAuthorBlacklisted(authorName) {
    if (!authorName) return false;

    try {
      const cached = await chrome.storage.local.get('blacklist_cache');
      const entries = cached.blacklist_cache?.entries || [];

      // Comparaison insensible a la casse et aux espaces
      const normalizedName = authorName.toLowerCase().trim();
      return entries.some(entry =>
        entry.blocked_name.toLowerCase().trim() === normalizedName
      );
    } catch (error) {
      console.error('isAuthorBlacklisted error:', error);
      return false; // Fallback gracieux
    }
  }

  // V3 Story 2.3 — Popup de confirmation blacklist
  // V3 Story 7.4 — Migration vers BEM avec ARIA et focus trap
  function showBlacklistWarningPopup(authorName) {
    return new Promise((resolve) => {
      let resolved = false;

      // V3 Story 7.4 — Creer le modal BEM avec variant warning
      const modalParts = createModalBEM({
        variant: 'warning',
        title: t('blacklistWarningTitle'),
        showCloseButton: false, // Pas de bouton X pour ce modal
        onClose: null,
        onOverlayClick: () => {
          if (!resolved) {
            resolved = true;
            resolve(false);
          }
        }
      });

      // Ajouter anciennes classes pour compatibilite CSS
      modalParts.modal.classList.add('ai-blacklist-warning-popup');
      modalParts.modal.id = 'ai-blacklist-warning-popup';

      // Icone warning dans le body
      const icon = document.createElement('div');
      icon.className = 'ai-warning-icon';
      icon.textContent = '\u26A0\uFE0F';
      icon.setAttribute('aria-hidden', 'true');
      modalParts.body.appendChild(icon);

      // Message d'avertissement
      const message = document.createElement('p');
      message.className = 'ai-warning-message';
      message.textContent = t('blacklistWarningMessage').replace('{name}', authorName);
      modalParts.body.appendChild(message);

      // Boutons dans le footer
      const cancelBtn = document.createElement('button');
      cancelBtn.className = 'ai-button ai-button--secondary';
      cancelBtn.textContent = t('blacklistWarningNo');
      cancelBtn.addEventListener('click', () => {
        if (!resolved) {
          resolved = true;
          modalParts.cleanup();
          resolve(false);
        }
      });

      const confirmBtn = document.createElement('button');
      confirmBtn.className = 'ai-button ai-button--primary';
      confirmBtn.textContent = t('blacklistWarningYes');
      confirmBtn.addEventListener('click', () => {
        if (!resolved) {
          resolved = true;
          modalParts.cleanup();
          resolve(true);
        }
      });

      modalParts.footer.appendChild(cancelBtn);
      modalParts.footer.appendChild(confirmBtn);

      // Override le handler ESC pour resoudre la Promise
      const originalShow = modalParts.show;
      modalParts.show = () => {
        originalShow();
        // Handler ESC personnalise
        const customEscHandler = (e) => {
          if (e.key === 'Escape' && !resolved) {
            resolved = true;
            document.removeEventListener('keydown', customEscHandler);
            modalParts.cleanup();
            resolve(false);
          }
        };
        // Remplacer le handler ESC par defaut
        document.addEventListener('keydown', customEscHandler);
        // Focus sur le bouton Annuler (securite)
        setTimeout(() => cancelBtn.focus(), 100);
      };

      modalParts.show();
    });
  }

  // V3 Story 2.1 — Afficher le modal de la blacklist
  function showBlacklistModal() {
    chrome.runtime.sendMessage({ action: 'getBlacklist' }, (response) => {
      if (!response || !response.success) {
        window.toastNotification.error(t('blacklistLoadError'));
        return;
      }
      createBlacklistModal(response.entries || []);
    });
  }

  // V3 Story 2.1 — Creer le modal de la blacklist
  // V3 Story 7.4 — Migration vers BEM avec ARIA et focus trap
  function createBlacklistModal(entries) {
    // Supprimer un modal existant
    const existingModal = document.getElementById('ai-blacklist-modal');
    if (existingModal) {
      existingModal.remove();
    }

    // V3 Story 7.4 — Creer le modal BEM avec variant generation
    const modalParts = createModalBEM({
      variant: 'generation',
      title: t('blacklistTitle'),
      showCloseButton: true,
      onClose: null,
      onOverlayClick: () => {}
    });

    // Ajouter ID pour compatibilite
    modalParts.modal.id = 'ai-blacklist-modal';
    // Reduire la largeur du modal
    modalParts.container.style.minWidth = '400px';
    modalParts.container.style.maxWidth = '450px';

    // Supprimer le footer (pas utilise)
    modalParts.footer.remove();

    // Contenu du body
    if (entries.length === 0) {
      const emptyMsg = document.createElement('p');
      emptyMsg.className = 'ai-empty-message';
      emptyMsg.textContent = t('blacklistEmpty');
      modalParts.body.appendChild(emptyMsg);
    } else {
      const list = document.createElement('ul');
      list.className = 'ai-blacklist-list';
      entries.forEach(entry => {
        const item = document.createElement('li');
        item.className = 'ai-blacklist-item';
        item.setAttribute('data-entry-id', entry.id);
        const dateStr = new Date(entry.created_at).toLocaleDateString();

        // V3 Security fix: Use textContent to prevent XSS
        const nameSpan = document.createElement('span');
        nameSpan.className = 'ai-blacklist-name';
        nameSpan.textContent = entry.blocked_name;

        const dateSpan = document.createElement('span');
        dateSpan.className = 'ai-blacklist-date';
        dateSpan.textContent = dateStr;

        // V3 Story 2.2 — Bouton "Retirer"
        const removeBtn = document.createElement('button');
        removeBtn.className = 'ai-button ai-button--danger ai-button--sm ai-blacklist-remove-btn';
        removeBtn.textContent = t('removeFromBlacklist');
        removeBtn.addEventListener('click', (e) => {
          e.preventDefault();
          handleRemoveFromBlacklist(entry.id, entry.blocked_name, item);
        });

        item.appendChild(nameSpan);
        item.appendChild(dateSpan);
        item.appendChild(removeBtn);
        list.appendChild(item);
      });
      modalParts.body.appendChild(list);
    }

    // Afficher le modal
    modalParts.show();
  }

  // V3 Story 2.2 — Handler pour retirer de la blacklist
  function handleRemoveFromBlacklist(entryId, blockedName, itemElement) {
    // Confirmation utilisateur
    if (!confirm(t('blacklistRemoveConfirm', { name: blockedName }))) {
      return;
    }

    // V3 Story 2.2 Fix: Desactiver le bouton pour eviter les double-clics (race condition)
    const removeBtn = itemElement.querySelector('.ai-blacklist-remove-btn');
    if (removeBtn) {
      removeBtn.disabled = true;
      removeBtn.style.opacity = '0.5';
      removeBtn.style.cursor = 'wait';
    }

    chrome.runtime.sendMessage({
      action: 'removeFromBlacklist',
      entryId: entryId
    }, (response) => {
      if (response.success) {
        // Supprimer l'element du DOM
        itemElement.remove();
        window.toastNotification.success(t('blacklistRemoveSuccess', { name: blockedName }));

        // Verifier si la liste est maintenant vide
        const list = document.querySelector('.ai-blacklist-list');
        if (list && list.children.length === 0) {
          const content = document.querySelector('.ai-modal-content');
          if (content) {
            const emptyMsg = document.createElement('p');
            emptyMsg.className = 'ai-empty-message';
            emptyMsg.textContent = t('blacklistEmpty');
            // V3 Story 2.2 Fix: Utiliser removeChild au lieu de innerHTML pour coherence XSS
            while (content.firstChild) {
              content.removeChild(content.firstChild);
            }
            content.appendChild(emptyMsg);
          }
        }
      } else if (response.error === 'not_found') {
        window.toastNotification.warning(t('blacklistNotFound'));
        itemElement.remove();
      } else {
        // Reactiver le bouton en cas d'erreur
        if (removeBtn) {
          removeBtn.disabled = false;
          removeBtn.style.opacity = '';
          removeBtn.style.cursor = '';
        }
        window.toastNotification.error(t('blacklistRemoveError'));
        console.error('removeFromBlacklist error:', response.error);
      }
    });
  }

  // V3 Story 1.3 — Extraction des commentaires tiers depuis le DOM LinkedIn
  /**
   * Extrait les commentaires tiers visibles depuis le DOM LinkedIn.
   * Utilise une strategie multi-selecteurs resiliente aux changements de DOM.
   *
   * Selecteurs LinkedIn 2026 (SDUI architecture):
   * 1. data-urn sur les containers de commentaires
   * 2. Classes semantiques .comments-comment-item
   * 3. Role="article" pour les commentaires
   * 4. Fallback classes generiques feed-shared-*
   *
   * @param {HTMLElement} postElement - L'element du post LinkedIn
   * @returns {string[]} - Tableau des textes de commentaires (max 10)
   */
  function extractThirdPartyComments(postElement) {
    if (!postElement) {
      return [];
    }

    // Selecteurs pour les containers de commentaires (ordre de fiabilite)
    const commentContainerSelectors = [
      // LinkedIn 2026 SDUI - Containers avec componentkey (plus fiable)
      '[componentkey*="replaceableComment_urn:li:comment"]',
      // LinkedIn 2026 SDUI - Containers de commentaires avec data-urn
      '[data-urn*="comment"]',
      // LinkedIn 2025+ - Classes semantiques
      '.comments-comment-item',
      '.comments-comment-entity',
      // LinkedIn 2024 - Fallback
      '.feed-shared-update-v2__comments-container article',
      '.comments-comments-list article',
      // Fallback generique
      '[data-view-name="comments-comment"]'
    ];

    // Selecteurs pour le texte du commentaire (a tester sur chaque container)
    const commentTextSelectors = [
      // LinkedIn 2026 SDUI - data-testid expandable-text-box (plus fiable)
      '[data-testid="expandable-text-box"]',
      // LinkedIn 2026 SDUI - Contenu du commentaire
      '.update-components-text',
      '.comments-comment-item__main-content',
      // LinkedIn 2025+ - Texte du commentaire
      '.comments-comment-item-content-body',
      '.comments-comment-texteditor',
      // Fallback
      'span.break-words',
      'p[dir="ltr"]'
    ];

    // Helper pour extraire les commentaires d'un scope donne
    function extractFromScope(scope) {
      const comments = [];
      for (const containerSelector of commentContainerSelectors) {
        const containers = scope.querySelectorAll(containerSelector);
        if (containers.length === 0) continue;

        for (const container of containers) {
          for (const textSelector of commentTextSelectors) {
            const textElement = container.querySelector(textSelector);
            if (textElement) {
              let text = textElement.textContent || textElement.innerText || '';
              text = text
                .trim()
                .replace(/See more\s*$/i, '')
                .replace(/Voir plus\s*$/i, '')
                .replace(/Show less\s*$/i, '')
                .replace(/Voir moins\s*$/i, '')
                .replace(/\s+/g, ' ')
                .trim();

              if (text.length >= 10 && text.length <= 500) {
                if (!comments.includes(text)) {
                  comments.push(text);
                }
              }
              break;
            }
          }
          if (comments.length >= 10) break;
        }
        if (comments.length > 0) break;
      }
      return comments;
    }

    // 1. D'abord chercher dans le postElement
    let comments = extractFromScope(postElement);

    // 2. Si aucun commentaire trouve, chercher dans la section commentList adjacente
    // LinkedIn 2026 SDUI: les commentaires sont dans [data-testid*="commentList"]
    // qui peut etre adjacent au post plutot qu'a l'interieur
    if (comments.length === 0) {
      // Remonter au parent le plus haut possible (listitem ou main container)
      let searchScope = postElement.closest('[role="listitem"]') ||
                        postElement.closest('[data-view-name="feed-full-update"]') ||
                        postElement.closest('[data-id]') ||
                        postElement.parentElement;

      if (searchScope && searchScope !== postElement) {
        // Chercher la section de commentaires dans ce scope elargi
        const commentListSection = searchScope.querySelector('[data-testid*="commentList"]');
        if (commentListSection) {
          comments = extractFromScope(commentListSection);
        } else {
          // Dernier recours: chercher dans tout le scope
          comments = extractFromScope(searchScope);
        }
      }
    }

    // AC#3 : Fallback gracieux - warning si extraction echoue (utile pour debug)
    if (comments.length === 0) {
      console.warn('[AI] Could not extract third-party comments');
    }

    return comments.slice(0, 10);
  }

  // V3 Story 1.2 v2 — Separation du commentaire pour insertion en deux temps
  function splitCommentForMention(comment) {
    const delimiter = '{{{SPLIT}}}';
    const parts = comment.split(delimiter);
    if (parts.length === 2) {
      return {
        beforeMention: parts[0],  // "Comme tu le soulignes @Jean"
        afterMention: parts[1],   // ", ton analyse est pertinente..."
        hasSplit: true
      };
    }
    // Pas de delimiteur trouve — fallback
    return { beforeMention: comment, afterMention: '', hasSplit: false };
  }

  // V3 Story 1.2 v2 — Observer pour detecter quand LinkedIn cree une mention
  function observeMentionCreation(commentBox, afterMentionText, firstName, onComplete) {
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        // Chercher les nouveaux elements ajoutes
        for (const node of mutation.addedNodes) {
          if (node.nodeType === 1) { // Element node
            // LinkedIn cree un element pour la mention (plusieurs patterns possibles)
            const isMention =
              node.hasAttribute('data-mention-id') ||
              node.getAttribute('href')?.includes('linkedin.com/in/') ||
              node.getAttribute('href')?.includes('linkedin.com/company/') ||
              node.classList?.contains('mention') ||
              node.getAttribute('contenteditable') === 'false';

            // Verifier que c'est bien notre mention (contient le prenom)
            if (isMention && node.textContent?.toLowerCase().includes(firstName.toLowerCase())) {
              observer.disconnect();
              clearTimeout(timeoutId);
              // Petit delai pour laisser LinkedIn finir son traitement
              setTimeout(() => {
                insertAfterMention(commentBox, afterMentionText);
                // Callback pour restaurer les boutons
                if (onComplete) onComplete();
              }, 50);
              return;
            }
          }
        }
      }
    });

    observer.observe(commentBox, {
      childList: true,
      subtree: true
    });

    // Timeout de securite : si pas de mention detectee apres 30s, abandonner et restaurer les boutons
    const timeoutId = setTimeout(() => {
      observer.disconnect();
      // Restaurer les boutons meme en cas de timeout
      if (onComplete) onComplete();
    }, 30000);

    // Stocker le timeout pour pouvoir l'annuler si besoin
    observer._timeoutId = timeoutId;

    return observer;
  }

  // V3 Story 1.2 v2 — Inserer la suite du commentaire apres la mention
  function insertAfterMention(commentBox, afterText) {
    // Positionner le curseur a la fin
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(commentBox);
    range.collapse(false); // false = collapse to end
    selection.removeAllRanges();
    selection.addRange(range);

    // Inserer la suite du texte via execCommand (meilleure compatibilite avec contentEditable)
    document.execCommand('insertText', false, afterText);

    // Declencher l'evenement input pour que LinkedIn detecte le changement
    commentBox.dispatchEvent(new Event('input', { bubbles: true }));

    // Toast de confirmation
    if (window.toastNotification) {
      window.toastNotification.success(t('mentionCompleted') || 'Mention ajoutée !');
    }
  }

  function extractPostContent(container) {
    if (!container) {
      console.warn('⚠️ extractPostContent: Container est null');
      return null;
    }

    console.log('🔍 extractPostContent: Début extraction depuis container:', container.className);

    // Sélecteurs prioritaires (LinkedIn 2025+ SDUI)
    const selectors = [
      '[data-view-name="feed-commentary"] [data-testid="expandable-text-box"]',
      '[data-view-name="feed-commentary"]',
      '[data-testid="expandable-text-box"]',
      // Sélecteurs legacy (LinkedIn classique)
      '.feed-shared-update-v2__description',
      '.update-components-text',
      '.feed-shared-inline-show-more-text',
      '.feed-shared-text',
      '.break-words',
      '[data-test-id="main-feed-activity-card__commentary"]',
      '.feed-shared-text__text-view',
      '.attributed-text-segment-list__content'
    ];

    for (const selector of selectors) {
      const element = container.querySelector(selector);
      if (element) {
        const content = element.textContent.trim();
        console.log(`🔍 extractPostContent: Sélecteur ${selector} trouvé, contenu:`, content ? content.substring(0, 50) + '...' : 'vide');
        if (content && content.length > 0) {
          console.log('✅ Contenu du post extrait via:', selector);
          return content;
        }
      }
    }

    // Fallback 1 : chercher dans le container global
    const postContainer = container.querySelector('[data-view-name="feed-full-update"], [data-id], article, .feed-shared-update-v2');
    console.log('🔍 extractPostContent: postContainer trouvé:', !!postContainer);
    if (postContainer) {
      const allText = postContainer.textContent.trim();
      console.log('🔍 extractPostContent: Fallback 1 (postContainer), contenu:', allText ? allText.substring(0, 50) + '...' : 'vide');
      if (allText && allText.length > 0) {
        console.log('✅ Contenu du post extrait via fallback 1');
        // Limiter la taille si trop long (éviter d'inclure les commentaires)
        return allText.substring(0, 2000);
      }
    }

    // Fallback 2 : utiliser directement le container
    const containerText = container.textContent.trim();
    console.log('🔍 extractPostContent: Fallback 2 (container direct), contenu:', containerText ? containerText.substring(0, 50) + '...' : 'vide');
    if (containerText && containerText.length > 0) {
      console.log('✅ Contenu du post extrait via fallback 2 (container direct)');
      // Limiter la taille si trop long
      return containerText.substring(0, 2000);
    }

    console.warn('⚠️ extractPostContent: Impossible de trouver le contenu du post');
    console.warn('⚠️ extractPostContent: Container HTML:', container.innerHTML.substring(0, 200));
    return null;
  }

  // Écouter les changements d'état et de langue
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'authStateChanged') {
      isAuthenticated = message.authenticated;
      updateAllButtons();

      if (isAuthenticated) {
        // Phase 2: Tenter capture du profil LinkedIn quand l'utilisateur se connecte
        detectAndCaptureLinkedInProfile();

         catch (e) {
              }
            }
          });
        }

        const allCommentBoxes = document.querySelectorAll('[contenteditable="true"], [role="textbox"], .ql-editor, .tiptap, .ProseMirror');

        allCommentBoxes.forEach((commentBox) => {
          // FILTRE CRITIQUE : Ignorer les éléments ql-clipboard (Quill editor clipboard)
          if (commentBox.classList.contains('ql-clipboard')) {
            return;
          }

          const placeholder = commentBox.getAttribute('data-placeholder') ||
                             commentBox.getAttribute('aria-label') ||
                             commentBox.getAttribute('aria-placeholder') ||
                             commentBox.getAttribute('placeholder') ||
                             commentBox.closest('[data-placeholder]')?.getAttribute('data-placeholder') ||
                             '';

          const parentPlaceholder = commentBox.parentElement?.getAttribute('data-placeholder') ||
                                   commentBox.parentElement?.getAttribute('aria-label') || '';

          const isInCommentContext = commentBox.closest('.comments-comment-texteditor, .comment-box, .comments-comment-box, .ql-editor, [data-test-id*="comment"], [class*="comment-input"], [class*="reply-input"], .tiptap, .ProseMirror');

          const commentBoxClasses = commentBox.className || '';
          const isTipTapEditor = commentBoxClasses.includes('tiptap') || commentBoxClasses.includes('ProseMirror');

          const hasCommentKeywords = placeholder.toLowerCase().includes('comment') ||
                                     placeholder.toLowerCase().includes('ajouter') ||
                                     placeholder.toLowerCase().includes('add') ||
                                     placeholder.toLowerCase().includes('reply') ||
                                     parentPlaceholder.toLowerCase().includes('comment') ||
                                     parentPlaceholder.toLowerCase().includes('ajouter') ||
                                     parentPlaceholder.toLowerCase().includes('add') ||
                                     parentPlaceholder.toLowerCase().includes('reply');

          if (hasCommentKeywords || isInCommentContext || isTipTapEditor) {
            // Triple vérification via hasAIButtons avant d'ajouter
            // pour éviter les doublons lors de l'authentification
            if (!hasAIButtons(commentBox)) {
              addButtonsToCommentBox(commentBox);
            }
          }
        });
      } else {
        if (phClient && phClient.reset) {
          try {
          } catch (e) {
          }
        }
      }
    } else if (message.action === 'languageChanged') {
      currentInterfaceLanguage = message.interfaceLanguage;
      updateAllButtonsText();
    } else if (message.action === 'settingsUpdated') {
      if (message.settings.interfaceLanguage) {
        currentInterfaceLanguage = message.settings.interfaceLanguage;
      }
      if (message.settings.commentLanguage) {
        currentCommentLanguage = message.settings.commentLanguage;
      }
      updateAllButtonsText();
    } else if (message.action === 'uiModeChanged') {
      // Réinitialiser l'UI quand le mode change (legacy - plus utilisé)
      console.log('🎨 Mode UI changé depuis popup:', message.uiMode);

      // Supprimer tous les contrôles existants (nouveaux ET legacy)
      document.querySelectorAll('.ai-controls, .ai-buttons-wrapper, .ai-button-container').forEach(el => el.remove());

      // Réinitialiser les marqueurs sur toutes les zones de commentaire
      document.querySelectorAll('[data-ai-buttons-added], [data-ai-buttons-pending], [data-ai-ui-mode]').forEach(el => {
        el.removeAttribute('data-ai-buttons-added');
        el.removeAttribute('data-ai-buttons-pending');
        el.removeAttribute('data-ai-ui-mode');
      });

      // Réinjecter les boutons sur les zones de commentaire actives
      setTimeout(() => {
        document.querySelectorAll('[contenteditable="true"], [role="textbox"], .ql-editor').forEach(commentBox => {
          if (!commentBox.classList.contains('ql-clipboard') && commentBox.offsetParent !== null) {
            addButtonsToCommentBox(commentBox);
          }
        });
      }, 100);
    } else if (message.action === 'trialStatusChanged') {
      // Phase 2: Mise a jour du plan utilisateur apres capture profil
      console.log('[Phase2] Trial status changed:', message.role);
      chrome.storage.local.get(['user_plan'], (storage) => {
        if (storage.user_plan !== message.role) {
          chrome.storage.local.set({
            user_plan: message.role,
            trial_ends_at: message.trial_ends_at
          });
          console.log('[Phase2] Plan utilisateur mis a jour:', message.role);
        }
      });
    }
  });

  // Vérification périodique de l'authentification
  setInterval(checkAuthentication, 60000); // 1 minute

  // Observer pour détecter les nouvelles zones de commentaire
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === 1) { // Element node
          // Chercher les zones de commentaire dans les nouveaux éléments
          const commentBoxes = node.querySelectorAll('[contenteditable="true"], [role="textbox"], .ql-editor, .tiptap, .ProseMirror');

          commentBoxes.forEach((commentBox) => {
            // FILTRE CRITIQUE : Ignorer les éléments ql-clipboard (Quill editor clipboard)
            if (commentBox.classList.contains('ql-clipboard')) {
              return;
            }

            const placeholder = commentBox.getAttribute('data-placeholder') ||
                               commentBox.getAttribute('aria-label') ||
                               commentBox.getAttribute('aria-placeholder') ||
                               commentBox.getAttribute('placeholder') ||
                               commentBox.closest('[data-placeholder]')?.getAttribute('data-placeholder') ||
                               '';

            const parentPlaceholder = commentBox.parentElement?.getAttribute('data-placeholder') ||
                                     commentBox.parentElement?.getAttribute('aria-label') || '';

            const isInCommentContext = commentBox.closest('.comments-comment-texteditor, .comment-box, .comments-comment-box, .ql-editor, [data-test-id*="comment"], [class*="comment-input"], [class*="reply-input"], .tiptap, .ProseMirror');

            const commentBoxClasses = commentBox.className || '';

            const hasCommentKeywords = placeholder.toLowerCase().includes('comment') ||
                                       placeholder.toLowerCase().includes('ajouter') ||
                                       placeholder.toLowerCase().includes('add') ||
                                       placeholder.toLowerCase().includes('reply') ||
                                       parentPlaceholder.toLowerCase().includes('comment') ||
                                       parentPlaceholder.toLowerCase().includes('ajouter') ||
                                       parentPlaceholder.toLowerCase().includes('add') ||
                                       parentPlaceholder.toLowerCase().includes('reply');

            const isTipTapEditor = commentBoxClasses.includes('tiptap') || commentBoxClasses.includes('ProseMirror');

            if (hasCommentKeywords || isInCommentContext || isTipTapEditor) {
              // Triple vérification via hasAIButtons avant d'ajouter
              // pour éviter les doublons lors de mutations DOM
              if (!hasAIButtons(commentBox)) {
                addButtonsToCommentBox(commentBox);
              }
            }
          });
        }
      });
    });
  });

  // Démarrer l'observation
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });

  console.log('✅ LinkedIn AI Commenter actif');
  console.log('✅ MutationObserver actif pour détecter les nouvelles zones de commentaire');

  // ===== 🧠 ENRICHISSEMENT AUTOMATIQUE DES ACTUALITÉS =====

  /**
   * Gère l'envoi automatique des actualités LinkedIn au backend
   * Uniquement en mode "smart-summary"
   */
  async function handleLinkedInNewsEnrichment() {
    try {
      // Récupérer les paramètres d'enrichissement
      const settings = await chrome.storage.sync.get(['newsEnrichmentMode', 'commentLanguage']);
      const mode = settings.newsEnrichmentMode || 'title-only';
      const lang = settings.commentLanguage || 'fr';

      console.log(`📰 Mode d'enrichissement détecté: ${mode}`);

      // N'envoyer au backend que si mode smart-summary
      if (mode !== 'smart-summary') {
        console.log(`⚡ Mode "${mode}" → pas d'envoi automatique au backend`);
        return;
      }

      console.log('🧠 Mode smart-summary activé → extraction des actualités LinkedIn...');

      // Extraire les actualités de la page
      const newsItems = extractLinkedInNews();

      if (newsItems.length === 0) {
        console.warn('⚠️ Aucune actualité LinkedIn trouvée sur cette page');
        return;
      }

      // Préparer les URLs pour l'envoi
      const urls = newsItems.map(item => item.url);

      console.log(`📡 Envoi de ${urls.length} actualités au backend pour enrichissement...`);
      console.log('📋 URLs:', urls);

      // Envoyer au background pour traitement backend
      chrome.runtime.sendMessage({
        action: 'registerNews',
        data: { urls, lang }
      }, (response) => {
        if (chrome.runtime.lastError) {
          console.error('❌ Erreur lors de l\'envoi des actualités:', chrome.runtime.lastError);
          return;
        }

        if (response && response.success) {
          console.log(`✅ ${response.registered || 0} actualités enregistrées, ${response.skipped || 0} ignorées (déjà en base)`);
        } else if (response && response.error) {
          console.error('❌ Erreur backend:', response.error);
        }
      });

    } catch (error) {
      console.error('❌ Erreur handleLinkedInNewsEnrichment:', error);
    }
  }

  // Appeler l'enrichissement automatique après chargement de la page
  // Délai de 4 secondes pour laisser le module actualités se charger
  window.addEventListener('load', () => {
    console.log('📄 Page LinkedIn chargée, attente avant extraction des actualités...');
    setTimeout(() => {
      handleLinkedInNewsEnrichment();
    }, 4000);
  });

  // Réessayer si le module d'actualités apparaît plus tard (via MutationObserver)
  let newsEnrichmentAttempts = 0;
  const MAX_ENRICHMENT_ATTEMPTS = 3;

  const newsObserver = new MutationObserver(() => {
    const newsModule = document.querySelector('[data-view-name="news-module"]');

    if (newsModule && newsEnrichmentAttempts < MAX_ENRICHMENT_ATTEMPTS) {
      newsEnrichmentAttempts++;
      console.log(`📰 Module d'actualités détecté (tentative ${newsEnrichmentAttempts}/${MAX_ENRICHMENT_ATTEMPTS})`);
      handleLinkedInNewsEnrichment();

      if (newsEnrichmentAttempts >= MAX_ENRICHMENT_ATTEMPTS) {
        newsObserver.disconnect();
        console.log('🛑 Arrêt de la détection automatique des actualités');
      }
    }
  });

  // Observer l'apparition du module d'actualités
  newsObserver.observe(document.body, {
    childList: true,
    subtree: true
  });

  // Phase 2: Detecter et capturer le profil LinkedIn si sur /in/me/
  window.addEventListener('load', () => {
    setTimeout(() => {
      detectAndCaptureLinkedInProfile();
    }, 2000);
  });

  // Phase 2: Observer les changements d'URL (LinkedIn SPA)
  let lastUrl = window.location.href;
  const urlObserver = new MutationObserver(() => {
    if (window.location.href !== lastUrl) {
      lastUrl = window.location.href;
      detectAndCaptureLinkedInProfile();
    }
  });
  urlObserver.observe(document.body, { childList: true, subtree: true });

})();