// Script principal pour LinkedIn AI Commenter - VERSION MULTILINGUE
(function() {
  'use strict';

  // Éviter la double-injection du script
  if (window.__PH_BOOTED__) {
    console.log('⚠️ Content script déjà chargé, arrêt');
    return;
  }
  window.__PH_BOOTED__ = true;

  console.log('🚀 LinkedIn AI Commenter - Content script chargé');

  // Initialiser PostHog et attendre qu'il soit prêt
  const phClient = window.posthogClient;
  if (phClient) {
    phClient.init();
  }

  // État local
  let isAuthenticated = false;
  let currentInterfaceLanguage = 'fr';
  let currentCommentLanguage = 'fr';

  // Traductions pour le content script
  const translations = {
    fr: {
      generate: '✨ Générer',
      withPrompt: '💭 Avec prompt',
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
      // Styles de langage
      oral: 'Oral /\nConversationnel',
      professional: 'Professionnel',
      storytelling: 'Storytelling',
      poetic: 'Poétique /\nCréatif',
      humoristic: 'Humoristique',
      impactful: 'Impactant /\nMarketing',
      benevolent: 'Bienveillant /\nPositif',
      languageStyle: 'Style de langage'
    },
    en: {
      generate: '✨ Generate',
      withPrompt: '💭 With prompt',
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
      // Styles de langage
      oral: 'Oral /\nConversational',
      professional: 'Professional',
      storytelling: 'Storytelling',
      poetic: 'Poetic /\nCreative',
      humoristic: 'Humoristic',
      impactful: 'Impactful /\nMarketing',
      benevolent: 'Benevolent /\nPositive',
      languageStyle: 'Language Style'
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

    // Attendre que PostHog soit prêt avant de continuer
    if (phClient) {
      await phClient.ready();
      console.log('✅ PostHog prêt');
    }

    // Vérifier l'authentification après l'init
    await checkAuthentication();
  })();

  // Vérifier l'authentification
  async function checkAuthentication() {
    try {
      const response = await chrome.runtime.sendMessage({ action: 'checkAuthentication' });
      isAuthenticated = response && response.authenticated;
      console.log('État authentification:', isAuthenticated);

      // Identifier l'utilisateur dans PostHog si authentifié
      if (isAuthenticated && phClient && typeof posthog !== 'undefined') {
        try {
          // Récupérer les informations utilisateur depuis le storage
          const userInfo = await chrome.storage.local.get(['user_id', 'user_email', 'user_name', 'user_plan']);

          if (userInfo.user_id) {
            console.log('📊 Identification PostHog avec user_id:', userInfo.user_id);
            phClient.identify(userInfo.user_id, {
              email: userInfo.user_email,
              name: userInfo.user_name || null,
              plan: userInfo.user_plan || 'FREE'
            });
          } else if (userInfo.user_email) {
            // Fallback sur email si user_id non disponible
            console.warn('⚠️ user_id non disponible, utilisation de l\'email');
            phClient.identify(userInfo.user_email, {
              email: userInfo.user_email,
              name: userInfo.user_name || null,
              plan: userInfo.user_plan || 'FREE'
            });
          }

          // Anti-duplicate session logic (Plan v3)
          if (!window.__PH_BOOTED__) {
            window.__PH_BOOTED__ = true;
            const key = 'ph_session_started';
            if (!sessionStorage.getItem(key)) {
              posthog.capture('usage_session_start');
              sessionStorage.setItem(key, '1');
              console.log('📊 Session d\'utilisation démarrée');
            } else {
              console.log('📊 Session déjà démarrée (évite duplication)');
            }

            // Track session end events
            window.addEventListener('beforeunload', () => posthog.capture('usage_session_end'));
            document.addEventListener('visibilitychange', () => {
              if (document.visibilityState === 'hidden') posthog.capture('usage_session_end');
            });
          }
        } catch (e) {
          console.warn('PostHog identification failed:', e);
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
    document.querySelectorAll('.ai-generate-button').forEach(button => {
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

  // Mettre à jour l'état des boutons
  function updateButtonsState(wrapper, authenticated) {
    const buttons = wrapper.querySelectorAll('.ai-generate-button');
    buttons.forEach(button => {
      button.disabled = !authenticated;

      // Message d'authentification
      let authMessage = wrapper.querySelector('.auth-required-message');
      if (!authenticated && !authMessage) {
        authMessage = document.createElement('div');
        authMessage.className = 'auth-required-message';
        authMessage.textContent = t('authRequired');
        wrapper.appendChild(authMessage);
      } else if (authenticated && authMessage) {
        authMessage.remove();
      }
    });
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
    if (phClient) {
      try {
        phClient.trackStyleSelected(style.key);
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
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
    if (phClient) {
      try {
        phClient.trackEmotionSelected(emotion.key, intensity);
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
      }
    }
  }

  // Ajouter les boutons
  function addButtonsToCommentBox(commentBox) {
    // Triple vérification stricte avec verrouillage immédiat
    if (hasAIButtons(commentBox)) {
      return;
    }

    // VERROUILLAGE IMMÉDIAT : marquer AVANT toute autre opération
    // Cela empêche les race conditions entre événements concurrents
    commentBox.setAttribute('data-ai-buttons-pending', 'true');

    const buttonsWrapper = document.createElement('div');
    buttonsWrapper.className = 'ai-buttons-wrapper';

    // S'assurer que le parent a un positionnement relatif
    const parent = commentBox.parentElement;
    if (parent && getComputedStyle(parent).position === 'static') {
      parent.style.position = 'relative';
    }

    chrome.storage.sync.get(['tone'], function(data) {
      const isNegative = data.tone === 'negatif';
      const isReplyToComment = commentBox.closest('[data-view-name="comment-container"]') !== null ||
                                commentBox.closest('.comments-comment-entity') !== null;

      // Bouton Générer
      const generateButton = document.createElement('button');
      generateButton.className = 'ai-generate-button';
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
      promptButton.className = 'ai-generate-button with-prompt';
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
      personalisationButton.className = 'ai-generate-button settings-button';
      personalisationButton.type = 'button'; // IMPORTANT: empêche la soumission du formulaire
      if (isNegative) personalisationButton.classList.add('negative');
      if (isReplyToComment) personalisationButton.classList.add('reply-mode');
      personalisationButton.innerHTML = `<span>⚙️</span>`;
      personalisationButton.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleEmotionsPanel(buttonsWrapper, commentBox);
      };

      // V3 — Bouton toggle Citation (PREMIUM uniquement)
      const quoteToggle = document.createElement('button');
      quoteToggle.className = 'ai-generate-button ai-quote-toggle';
      quoteToggle.type = 'button';
      if (isNegative) quoteToggle.classList.add('negative');
      if (isReplyToComment) quoteToggle.classList.add('reply-mode');
      quoteToggle.innerHTML = `<span>💬 ${t('quoteToggle')}</span>`;
      quoteToggle.title = t('quoteToggleInactive');

      // Verifier le plan utilisateur pour le gating
      chrome.storage.local.get(['user_plan'], (result) => {
        const userPlan = result.user_plan || 'FREE';
        if (userPlan !== 'PREMIUM') {
          quoteToggle.classList.add('locked');
          quoteToggle.innerHTML = `<span>🔒 ${t('quoteToggle')}</span>`;
        }
      });

      quoteToggle.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        chrome.storage.local.get(['user_plan'], (result) => {
          const userPlan = result.user_plan || 'FREE';
          if (userPlan !== 'PREMIUM') {
            window.toastNotification.warning(t('quoteUpgradeRequired'));
            return;
          }
          // Toggle l'etat actif/inactif
          const isActive = commentBox.getAttribute('data-include-quote') === 'true';
          if (isActive) {
            commentBox.removeAttribute('data-include-quote');
            quoteToggle.classList.remove('active');
            quoteToggle.innerHTML = `<span>💬 ${t('quoteToggle')}</span>`;
            quoteToggle.title = t('quoteToggleInactive');
          } else {
            commentBox.setAttribute('data-include-quote', 'true');
            quoteToggle.classList.add('active');
            quoteToggle.innerHTML = `<span>✨ ${t('quoteToggle')}</span>`;
            quoteToggle.title = t('quoteToggleActive');
          }
        });
      };

      // V3 — Bouton toggle Tag Auteur (PREMIUM uniquement)
      const tagAuthorToggle = document.createElement('button');
      tagAuthorToggle.className = 'ai-generate-button ai-tag-author-toggle';
      tagAuthorToggle.type = 'button';
      if (isNegative) tagAuthorToggle.classList.add('negative');
      if (isReplyToComment) tagAuthorToggle.classList.add('reply-mode');
      tagAuthorToggle.innerHTML = `<span>👤 ${t('tagAuthor')}</span>`;
      tagAuthorToggle.title = t('tagAuthorTooltip');

      // Verifier le plan utilisateur pour le gating
      chrome.storage.local.get(['user_plan'], (result) => {
        const userPlan = result.user_plan || 'FREE';
        if (userPlan !== 'PREMIUM') {
          tagAuthorToggle.classList.add('locked');
          tagAuthorToggle.innerHTML = `<span>🔒 ${t('tagAuthor')}</span>`;
        }
      });

      tagAuthorToggle.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        chrome.storage.local.get(['user_plan'], (result) => {
          const userPlan = result.user_plan || 'FREE';
          if (userPlan !== 'PREMIUM') {
            window.toastNotification.warning(t('tagAuthorUpgradeRequired'));
            return;
          }

          // Verifier si deja actif — toggle off
          const currentAuthor = commentBox.getAttribute('data-tag-author');
          if (currentAuthor) {
            commentBox.removeAttribute('data-tag-author');
            tagAuthorToggle.classList.remove('active');
            tagAuthorToggle.innerHTML = `<span>👤 ${t('tagAuthor')}</span>`;
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
            tagAuthorToggle.classList.add('active');
            tagAuthorToggle.innerHTML = `<span>✨ ${t('tagAuthor')}</span>`;
            tagAuthorToggle.title = `${t('tagAuthorActive')}: ${authorName}`;
          } else {
            // Extraction echouee
            window.toastNotification.warning(t('authorNotFound'));
          }
        });
      };

      // V3 Story 1.3 — Bouton toggle Contexte (commentaires tiers) (PREMIUM uniquement)
      const contextToggle = document.createElement('button');
      contextToggle.className = 'ai-generate-button ai-context-toggle';
      contextToggle.type = 'button';
      if (isNegative) contextToggle.classList.add('negative');
      if (isReplyToComment) contextToggle.classList.add('reply-mode');
      contextToggle.innerHTML = `<span>💬 ${t('contextToggle')}</span>`;
      contextToggle.title = t('contextToggleTooltip');

      // Verifier le plan utilisateur pour le gating
      chrome.storage.local.get(['user_plan'], (result) => {
        const userPlan = result.user_plan || 'FREE';
        if (userPlan !== 'PREMIUM') {
          contextToggle.classList.add('locked');
          contextToggle.innerHTML = `<span>🔒 ${t('contextToggle')}</span>`;
        }
      });

      contextToggle.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        chrome.storage.local.get(['user_plan'], (result) => {
          const userPlan = result.user_plan || 'FREE';
          if (userPlan !== 'PREMIUM') {
            window.toastNotification.warning(t('contextUpgradeRequired'));
            return;
          }
          // Toggle l'etat actif/inactif
          const isActive = commentBox.getAttribute('data-include-context') === 'true';
          if (isActive) {
            commentBox.removeAttribute('data-include-context');
            contextToggle.classList.remove('active');
            contextToggle.innerHTML = `<span>💬 ${t('contextToggle')}</span>`;
            contextToggle.title = t('contextToggleInactive');
          } else {
            commentBox.setAttribute('data-include-context', 'true');
            contextToggle.classList.add('active');
            contextToggle.innerHTML = `<span>✨ ${t('contextToggle')}</span>`;
            contextToggle.title = t('contextToggleActive');
          }
        });
      };

      buttonsWrapper.appendChild(generateButton);
      buttonsWrapper.appendChild(promptButton);
      buttonsWrapper.appendChild(personalisationButton);
      buttonsWrapper.appendChild(quoteToggle);
      buttonsWrapper.appendChild(tagAuthorToggle);
      buttonsWrapper.appendChild(contextToggle);
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
    if (event.target.closest('.ai-generate-button') ||
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

    const button = event.target.closest('.ai-generate-button');
    const originalText = button.querySelector('span').textContent;

    // Vider le champ de commentaire AVANT l'extraction pour éviter toute confusion
    commentBox.textContent = '';
    commentBox.innerHTML = '';

    button.disabled = true;
    button.classList.add('loading');
    button.querySelector('span').textContent = t('generating');

    // Track generation started
    const generationStartTime = Date.now();
    const selectedEmotion = commentBox.getAttribute('data-selected-emotion');
    const selectedIntensity = commentBox.getAttribute('data-selected-intensity');
    const selectedStyle = commentBox.getAttribute('data-selected-style');

    if (phClient) {
      try {
        phClient.trackGenerationStarted({
          generationType: 'automatic',
          hasCustomPrompt: false,
          language: currentCommentLanguage,
          emotion: selectedEmotion,
          intensity: selectedIntensity,
          style: selectedStyle,
          isReply: isReplyToComment
        });
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
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

      // Récupérer le mode d'enrichissement des actualités
      const settings = await chrome.storage.sync.get(['newsEnrichmentMode']);
      const newsEnrichmentMode = settings.newsEnrichmentMode || 'title-only';

      // Extraire et envoyer les actualités LinkedIn au backend (si mode smart-summary)
      let newsContext = [];
      if (newsEnrichmentMode !== 'disabled') {
        // sendNewsToBackend gère l'envoi au backend uniquement si mode = 'smart-summary'
        // Sinon, elle retourne simplement les news extraites pour le contexte
        newsContext = await sendNewsToBackend(newsEnrichmentMode, currentCommentLanguage);
        console.log(`📰 Mode enrichissement: ${newsEnrichmentMode}, ${newsContext.length} actualités traitées`);
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

      const requestData = {
        post: postContent || null,
        isComment: isReplyToComment,
        commentLanguage: currentCommentLanguage,
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
        third_party_comments: thirdPartyComments.length > 0 ? thirdPartyComments : null
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
          if (phClient) {
            try {
              phClient.trackCommentGeneration({
                generationType: 'automatic',
                hasCustomPrompt: false,
                language: currentCommentLanguage,
                emotion: selectedEmotion,
                intensity: selectedIntensity,
                style: selectedStyle,
                isReply: isReplyToComment,
                success: false,
                error: response.error,
                durationMs: generationDuration
              });
            } catch (e) {
              console.warn('PostHog tracking failed:', e);
            }
          }
        } else if (response && response.comments) {
          showOptionsPopup(commentBox, response.comments, postContent || '', null, isReplyToComment);

          // Track successful generation
          if (phClient) {
            try {
              phClient.trackCommentGeneration({
                generationType: 'automatic',
                hasCustomPrompt: false,
                language: currentCommentLanguage,
                emotion: selectedEmotion,
                intensity: selectedIntensity,
                style: selectedStyle,
                optionsCount: response.comments.length,
                isReply: isReplyToComment,
                success: true,
                durationMs: generationDuration
              });
            } catch (e) {
              console.warn('PostHog tracking failed:', e);
            }
          }
        }

        button.disabled = false;
        button.classList.remove('loading');
        button.querySelector('span').textContent = originalText;
      });

    } catch (error) {
      const generationDuration = Date.now() - generationStartTime;
      window.toastNotification.error(t('error') + ': ' + error.message);

      // Track generation exception
      if (phClient) {
        try {
          phClient.trackCommentGeneration({
            generationType: 'automatic',
            hasCustomPrompt: false,
            language: currentCommentLanguage,
            emotion: selectedEmotion,
            intensity: selectedIntensity,
            style: selectedStyle,
            isReply: isReplyToComment,
            success: false,
            error: error.message,
            durationMs: generationDuration
          });
        } catch (e) {
          console.warn('PostHog tracking failed:', e);
        }
      }

      button.disabled = false;
      button.classList.remove('loading');
      button.querySelector('span').textContent = originalText;
    }
  }

  // Gestionnaire de clic sur Avec prompt
  function handlePromptClick(event, commentBox, isReplyToComment) {
    if (!isAuthenticated) {
      window.toastNotification.warning(t('pleaseSignIn'));
      return;
    }

    showPromptPopup(commentBox, isReplyToComment);
  }

  // Afficher le popup de prompt
  function showPromptPopup(commentBox, isReplyToComment) {
    // Nettoyer les popups et overlays existants
    document.querySelectorAll('.ai-prompt-popup, .ai-options-popup, .ai-popup-overlay').forEach(p => p.remove());

    chrome.storage.sync.get(['tone'], function(data) {
      const isNegative = data.tone === 'negatif';

      // Créer l'overlay
      const overlay = document.createElement('div');
      overlay.className = 'ai-popup-overlay';
      overlay.onclick = () => {
        popup.remove();
        overlay.remove();
      };

      const popup = document.createElement('div');
      popup.className = 'ai-prompt-popup';

      const title = document.createElement('div');
      title.className = 'ai-popup-title';
      title.textContent = t('customInstructions');
      popup.appendChild(title);

      const textArea = document.createElement('textarea');
      textArea.className = 'ai-prompt-textarea';
      textArea.placeholder = t('addInstructions');
      popup.appendChild(textArea);

      const actionButtons = document.createElement('div');
      actionButtons.className = 'ai-prompt-actions';

      const cancelButton = document.createElement('button');
      cancelButton.className = 'ai-prompt-cancel';
      cancelButton.textContent = t('cancel');
      cancelButton.onclick = () => {
        popup.remove();
        overlay.remove();
      };

      const submitButton = document.createElement('button');
      submitButton.className = 'ai-prompt-submit';
      if (isNegative) submitButton.classList.add('negative');
      if (isReplyToComment) submitButton.classList.add('reply-mode');
      submitButton.textContent = t('generate');
      submitButton.onclick = () => {
        const userPrompt = textArea.value.trim();
        if (userPrompt) {
          // Track prompt usage (Plan v3)
          if (phClient) {
            try {
              const selectedEmotion = commentBox.getAttribute('data-selected-emotion');
              const selectedIntensity = commentBox.getAttribute('data-selected-intensity');
              const selectedStyle = commentBox.getAttribute('data-selected-style');

              phClient.capture('prompt_used', {
                custom: true,
                length: userPrompt.length,
                tone: selectedIntensity || null,
                emotion: selectedEmotion || null,
                style: selectedStyle || null
              });
            } catch (e) {
              console.warn('PostHog tracking failed:', e);
            }
          }

          // Désactiver le bouton et afficher l'indicateur de chargement
          submitButton.disabled = true;
          submitButton.textContent = t('generating');

          // Masquer le popup après un court délai
          setTimeout(() => {
            popup.remove();
            overlay.remove();
          }, 100);

          handleGenerateWithPrompt(commentBox, userPrompt, isReplyToComment);
        }
      };

      actionButtons.appendChild(cancelButton);
      actionButtons.appendChild(submitButton);
      popup.appendChild(actionButtons);

      const closeButton = document.createElement('button');
      closeButton.className = 'ai-close-button';
      closeButton.textContent = '×';
      closeButton.onclick = () => {
        popup.remove();
        overlay.remove();
      };
      popup.appendChild(closeButton);

      // Ajouter l'overlay puis le popup au body
      document.body.appendChild(overlay);
      document.body.appendChild(popup);
      textArea.focus();
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

    if (phClient) {
      try {
        phClient.trackGenerationStarted({
          generationType: 'with_prompt',
          hasCustomPrompt: true,
          language: currentCommentLanguage,
          emotion: selectedEmotion,
          intensity: selectedIntensity,
          style: selectedStyle,
          isReply: isReplyToComment
        });
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
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

      // Récupérer le mode d'enrichissement des actualités
      const settings = await chrome.storage.sync.get(['newsEnrichmentMode']);
      const newsEnrichmentMode = settings.newsEnrichmentMode || 'title-only';

      // Extraire et envoyer les actualités LinkedIn au backend (si mode smart-summary)
      let newsContext = [];
      if (newsEnrichmentMode !== 'disabled') {
        // sendNewsToBackend gère l'envoi au backend uniquement si mode = 'smart-summary'
        // Sinon, elle retourne simplement les news extraites pour le contexte
        newsContext = await sendNewsToBackend(newsEnrichmentMode, currentCommentLanguage);
        console.log(`📰 Mode enrichissement (avec prompt): ${newsEnrichmentMode}, ${newsContext.length} actualités traitées`);
      } else {
        console.log('📰 Mode enrichissement désactivé (avec prompt)');
      }

      const requestData = {
        post: postContent || null,
        userPrompt: userPrompt,
        isComment: isReplyToComment,
        commentLanguage: currentCommentLanguage,
        // Paramètres contextuels (prioritaires sur les paramètres globaux du popup)
        emotion: selectedEmotion,
        intensity: selectedIntensity,
        style: selectedStyle,
        // Contexte des actualités LinkedIn
        newsContext: newsContext,
        newsEnrichmentMode: newsEnrichmentMode
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
          if (phClient) {
            try {
              phClient.trackCommentGeneration({
                generationType: 'with_prompt',
                hasCustomPrompt: true,
                language: currentCommentLanguage,
                emotion: selectedEmotion,
                intensity: selectedIntensity,
                style: selectedStyle,
                isReply: isReplyToComment,
                success: false,
                error: response.error,
                durationMs: generationDuration
              });
            } catch (e) {
              console.warn('PostHog tracking failed:', e);
            }
          }
        } else if (response && response.comments) {
          showOptionsPopup(commentBox, response.comments, postContent || '', userPrompt, isReplyToComment);

          // Track successful generation
          if (phClient) {
            try {
              phClient.trackCommentGeneration({
                generationType: 'with_prompt',
                hasCustomPrompt: true,
                language: currentCommentLanguage,
                emotion: selectedEmotion,
                intensity: selectedIntensity,
                style: selectedStyle,
                optionsCount: response.comments.length,
                isReply: isReplyToComment,
                success: true,
                durationMs: generationDuration
              });
            } catch (e) {
              console.warn('PostHog tracking failed:', e);
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
      if (phClient) {
        try {
          phClient.trackCommentGeneration({
            generationType: 'with_prompt',
            hasCustomPrompt: true,
            language: currentCommentLanguage,
            emotion: selectedEmotion,
            intensity: selectedIntensity,
            style: selectedStyle,
            isReply: isReplyToComment,
            success: false,
            error: error.message,
            durationMs: generationDuration
          });
        } catch (e) {
          console.warn('PostHog tracking failed:', e);
        }
      }
    }
  }

  // Afficher le popup avec les options
  function showOptionsPopup(commentBox, comments, postContent, userPrompt, isReplyToComment) {
    // Nettoyer les popups et overlays existants
    document.querySelectorAll('.ai-options-popup, .ai-prompt-popup, .ai-popup-overlay').forEach(p => p.remove());

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

        // Créer l'overlay
        const overlay = document.createElement('div');
        overlay.className = 'ai-popup-overlay';
        overlay.onclick = () => {
          popup.remove();
          overlay.remove();
        };

        const popup = document.createElement('div');
        popup.className = 'ai-options-popup';

        const title = document.createElement('div');
        title.className = 'ai-popup-title';
        title.setAttribute('data-count', comments.length);
        title.textContent = `${comments.length} ${t('generations')}${comments.length > 1 ? 's' : ''}`;
        popup.appendChild(title);

        comments.forEach((comment, index) => {
          const metadata = {
            language: currentCommentLanguage,
            length: calculateCommentLength(comment),
            emotion: selectedEmotion,
            intensity: selectedIntensity,
            style: selectedStyle
          };
          const option = createCommentOption(comment, index, commentBox, popup, postContent, userPrompt, isReplyToComment, isNegative, userPlan, metadata);
          popup.appendChild(option);
        });

        const closeButton = document.createElement('button');
        closeButton.className = 'ai-close-button';
        closeButton.textContent = '×';
        closeButton.onclick = () => {
          popup.remove();
          overlay.remove();
        };
        popup.appendChild(closeButton);

        // Ajouter l'overlay puis le popup au body
        document.body.appendChild(overlay);
        document.body.appendChild(popup);
      });
    });
  }

  // Fonction pour calculer la longueur du commentaire
  function calculateCommentLength(comment) {
    const lines = comment.split('\n').filter(line => line.trim().length > 0).length;
    if (lines <= 2) return 'Court';
    if (lines <= 4) return 'Moyen';
    return 'Long';
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

  // Mapper les styles vers leurs labels
  function getStyleLabel(styleKey) {
    const styleLabels = {
      oral: 'Conversationnel',
      professional: 'Professionnel',
      storytelling: 'Storytelling',
      poetic: 'Créatif',
      humoristic: 'Humoristique',
      impactful: 'Impactant',
      benevolent: 'Bienveillant'
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
  function createCommentOption(comment, index, commentBox, popup, postContent, userPrompt, isReplyToComment, isNegative, userPlan, metadata) {
    const option = document.createElement('div');
    option.className = 'ai-option';
    if (isNegative) option.classList.add('negative');

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

      // Longueur
      const lengthMeta = document.createElement('span');
      lengthMeta.className = 'ai-meta-item meta-length';
      lengthMeta.title = 'Longueur du commentaire';
      lengthMeta.innerHTML = `📝 ${metadata.length}`;
      metaContainer.appendChild(lengthMeta);

      // Émotion (si définie)
      if (metadata.emotion) {
        metaContainer.appendChild(createMetaSeparator());
        const emotionMeta = document.createElement('span');
        emotionMeta.className = 'ai-meta-item meta-emotion';
        emotionMeta.title = 'Émotion';
        emotionMeta.innerHTML = `😊 ${getEmotionLabel(metadata.emotion)}`;
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

      // Intensité (si définie)
      if (metadata.intensity) {
        metaContainer.appendChild(createMetaSeparator());
        const intensityMeta = document.createElement('span');
        intensityMeta.className = 'ai-meta-item meta-intensity';
        intensityMeta.title = 'Intensité de l\'émotion';
        intensityMeta.innerHTML = `🔥 ${getIntensityLabel(metadata.intensity)}`;
        metaContainer.appendChild(intensityMeta);
      }

      option.appendChild(metaContainer);
    }

    const optionText = document.createElement('div');
    optionText.className = 'ai-option-text';
    optionText.textContent = comment;

    option.appendChild(optionText);

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
        window.toastNotification.warning(t('upgradeRequired') || 'Veuillez passer à un plan supérieur pour accéder à cette option.');
        return;
      }

      // V3 Story 1.2 v2 — Insertion en deux temps pour les mentions LinkedIn
      const tagAuthorName = commentBox.getAttribute('data-tag-author');
      const { beforeMention, afterMention, hasSplit } = splitCommentForMention(comment);

      if (tagAuthorName && hasSplit && afterMention) {
        // Mode deux temps : inserer seulement le debut (jusqu'au @Prenom inclus)
        commentBox.textContent = beforeMention;

        // Extraire le prenom pour la detection
        const firstName = tagAuthorName.split(' ')[0];

        // Lancer l'observer pour detecter la mention
        observeMentionCreation(commentBox, afterMention, firstName);

        // Toast pour guider l'utilisateur
        if (window.toastNotification) {
          window.toastNotification.info(t('clickMentionSuggestion') || 'Cliquez sur la suggestion LinkedIn');
        }
      } else {
        // Mode normal : inserer tout le commentaire (nettoyer le delimiteur si present)
        commentBox.textContent = comment.replace('{{{SPLIT}}}', '');
      }

      popup.remove();
      // Supprimer aussi l'overlay
      document.querySelectorAll('.ai-popup-overlay').forEach(o => o.remove());
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
      if (phClient) {
        try {
          phClient.trackCommentInserted({
            commentIndex: index,
            commentLength: comment.length,
            hasCustomPrompt: !!userPrompt,
            language: metadata?.language || currentCommentLanguage,
            emotion: metadata?.emotion,
            intensity: metadata?.intensity,
            style: metadata?.style,
            isReply: isReplyToComment
          });
        } catch (e) {
          console.warn('PostHog tracking failed:', e);
        }
      }
    });

    // Ajouter les boutons d'action
    const buttonsContainer = document.createElement('div');
    buttonsContainer.className = 'ai-action-buttons-container';

    const refineButton = document.createElement('button');
    refineButton.className = 'ai-refine-button';
    if (isNegative) refineButton.classList.add('negative');
    refineButton.innerHTML = `<span>${t('refine')}</span>`;
    refineButton.onclick = () => {
      if (isLocked) {
        window.toastNotification.warning(t('upgradeRequired') || 'Veuillez passer à un plan supérieur pour accéder à cette option.');
        return;
      }
      showRefinePopup(commentBox, comment, postContent, userPrompt, index, popup, isReplyToComment);
    };
    if (isLocked) refineButton.disabled = true;

    const minusButton = document.createElement('button');
    minusButton.className = 'ai-minus-button';
    if (isNegative) minusButton.classList.add('negative');
    minusButton.textContent = '-';
    minusButton.onclick = (e) => {
      if (isLocked) {
        window.toastNotification.warning(t('upgradeRequired') || 'Veuillez passer à un plan supérieur pour accéder à cette option.');
        return;
      }
      handleResizeComment(e, commentBox, comment, postContent, '-', index, popup, isReplyToComment);
    };
    if (isLocked) minusButton.disabled = true;

    const plusButton = document.createElement('button');
    plusButton.className = 'ai-plus-button';
    if (isNegative) plusButton.classList.add('negative');
    plusButton.textContent = '+';
    plusButton.onclick = (e) => {
      if (isLocked) {
        window.toastNotification.warning(t('upgradeRequired') || 'Veuillez passer à un plan supérieur pour accéder à cette option.');
        return;
      }
      handleResizeComment(e, commentBox, comment, postContent, '+', index, popup, isReplyToComment);
    };
    if (isLocked) plusButton.disabled = true;

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
    if (phClient) {
      try {
        phClient.trackFeatureUsed('comment_resize', {
          direction: direction,
          language: currentCommentLanguage,
          is_reply: isReplyToComment,
          comment_index: optionIndex,
          current_word_count: originalComment.split(' ').length
        });

        // Track UI resized event
        phClient.trackUIResized({
          target: 'comment',
          deltaW: direction === '+' ? 1 : -1,
          deltaH: null,
          width: originalComment.split(' ').length,
          height: null
        });
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
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
        if (phClient) {
          try {
            phClient.capture('comment_resize_failed', {
              direction: direction,
              error: response.error,
              duration_ms: resizeDuration,
              language: currentCommentLanguage
            });
          } catch (e) {
            console.warn('PostHog tracking failed:', e);
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
        if (phClient) {
          try {
            phClient.capture('comment_resize_success', {
              direction: direction,
              duration_ms: resizeDuration,
              language: currentCommentLanguage,
              new_word_count: response.resizedComment.split(' ').length,
              comment_index: optionIndex
            });
          } catch (e) {
            console.warn('PostHog tracking failed:', e);
          }
        }
      }

      button.textContent = originalText;
      button.disabled = false;
    });
  }

  // Affiner un commentaire
  function showRefinePopup(commentBox, originalComment, postContent, userPrompt, optionIndex, optionsPopup, isReplyToComment) {
    document.querySelectorAll('.ai-refine-popup').forEach(p => p.remove());

    chrome.storage.sync.get(['tone'], function(data) {
      const isNegative = data.tone === 'negatif';

      // Créer un overlay secondaire (au-dessus de l'overlay principal)
      const refineOverlay = document.createElement('div');
      refineOverlay.className = 'ai-popup-overlay';
      refineOverlay.style.zIndex = '2147483648'; // Au-dessus de l'overlay principal
      refineOverlay.onclick = () => {
        popup.remove();
        refineOverlay.remove();
      };

      const popup = document.createElement('div');
      popup.className = 'ai-refine-popup';
      popup.style.zIndex = '2147483649'; // Au-dessus de l'overlay de raffinement

      const title = document.createElement('div');
      title.className = 'ai-popup-title';
      title.textContent = t('refineComment');
      popup.appendChild(title);

      const context = document.createElement('div');
      context.className = 'ai-refine-context';
      context.textContent = `${t('comment')}: "${originalComment}"`;
      popup.appendChild(context);

      const textArea = document.createElement('textarea');
      textArea.className = 'ai-refine-textarea';
      textArea.placeholder = t('refineInstructions');
      popup.appendChild(textArea);

      const actionButtons = document.createElement('div');
      actionButtons.className = 'ai-refine-actions';

      const cancelButton = document.createElement('button');
      cancelButton.className = 'ai-refine-cancel';
      cancelButton.textContent = t('cancel');
      cancelButton.onclick = () => {
        popup.remove();
        refineOverlay.remove();
      };

      const submitButton = document.createElement('button');
      submitButton.className = 'ai-refine-submit';
      if (isNegative) submitButton.classList.add('negative');
      if (isReplyToComment) submitButton.classList.add('reply-mode');
      submitButton.textContent = t('refine');
      submitButton.onclick = () => {
        const refineInstructions = textArea.value.trim();
        if (refineInstructions) {
          popup.remove();
          refineOverlay.remove();
          handleRefineComment(commentBox, originalComment, postContent, userPrompt, refineInstructions, optionIndex, optionsPopup, isReplyToComment);
        }
      };

      actionButtons.appendChild(cancelButton);
      actionButtons.appendChild(submitButton);
      popup.appendChild(actionButtons);

      const closeButton = document.createElement('button');
      closeButton.className = 'ai-close-button';
      closeButton.textContent = '×';
      closeButton.onclick = () => {
        popup.remove();
        refineOverlay.remove();
      };
      popup.appendChild(closeButton);

      // Ajouter l'overlay de raffinement puis le popup au body
      document.body.appendChild(refineOverlay);
      document.body.appendChild(popup);
      textArea.focus();
    });
  }
  
  function handleRefineComment(commentBox, originalComment, postContent, userPrompt, refineInstructions, optionIndex, optionsPopup, isReplyToComment) {
    const refineStartTime = Date.now();

    // Track refine started
    if (phClient) {
      try {
        phClient.trackFeatureUsed('comment_refine', {
          has_custom_prompt: !!userPrompt,
          language: currentCommentLanguage,
          is_reply: isReplyToComment,
          comment_index: optionIndex
        });
      } catch (e) {
        console.warn('PostHog tracking failed:', e);
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
        if (phClient) {
          try {
            phClient.capture('comment_refine_failed', {
              error: response.error,
              duration_ms: refineDuration,
              language: currentCommentLanguage
            });
          } catch (e) {
            console.warn('PostHog tracking failed:', e);
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
        if (phClient) {
          try {
            phClient.capture('comment_refine_success', {
              duration_ms: refineDuration,
              language: currentCommentLanguage,
              comment_index: optionIndex
            });
          } catch (e) {
            console.warn('PostHog tracking failed:', e);
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
  function observeMentionCreation(commentBox, afterMentionText, firstName) {
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
              // Petit delai pour laisser LinkedIn finir son traitement
              setTimeout(() => {
                insertAfterMention(commentBox, afterMentionText);
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

    // Timeout de securite : si pas de mention detectee apres 30s, abandonner
    const timeoutId = setTimeout(() => {
      observer.disconnect();
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
        // Identifier l'utilisateur dans PostHog lors de la connexion
        if (phClient) {
          chrome.storage.local.get(['user_email', 'user_name', 'user_plan'], (userInfo) => {
            if (userInfo.user_email) {
              console.log('📊 PostHog - Identification utilisateur:', userInfo.user_email);
              try {
                phClient.identify(userInfo.user_email, {
                  email: userInfo.user_email,
                  name: userInfo.user_name || null,
                  plan: userInfo.user_plan || 'FREE'
                });
              } catch (e) {
                console.warn('PostHog identification failed:', e);
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
        // Réinitialiser PostHog lors de la déconnexion
        if (phClient && phClient.reset) {
          console.log('📊 PostHog - Réinitialisation (déconnexion)');
          try {
            phClient.reset();
          } catch (e) {
            console.warn('PostHog reset failed:', e);
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

  // ====================================================================
  // POSTHOG BRIDGE - Listener pour les tests depuis la console de la page
  // ====================================================================
  window.addEventListener('message', (event) => {
    // Vérifier que le message vient de la page elle-même
    if (event.source !== window) return;

    // Test d'événement PostHog depuis le bridge
    if (event.data.type === 'POSTHOG_TEST_EVENT') {
      console.log('🧪 PostHog Test Event reçu via bridge:', event.data);

      if (phClient) {
        phClient.capture(event.data.eventName, event.data.properties);
        console.log('✅ Événement PostHog capturé:', event.data.eventName);

        // Envoyer une confirmation à la page
        window.postMessage({
          type: 'POSTHOG_EVENT_SENT',
          eventName: event.data.eventName,
          properties: event.data.properties
        }, '*');
      } else {
        console.error('❌ PostHog client non disponible');
      }
    }

    // Demande de configuration PostHog
    if (event.data.type === 'POSTHOG_GET_CONFIG') {
      console.log('📊 Configuration PostHog demandée via bridge');

      if (phClient) {
        const config = {
          enabled: phClient.enabled,
          apiKey: phClient.apiKey ? phClient.apiKey.substring(0, 15) + '...' : 'NOT SET',
          apiHost: phClient.apiHost,
          distinctId: phClient.distinctId,
          queueLength: phClient.eventQueue ? phClient.eventQueue.length : 0
        };

        console.log('✅ Configuration PostHog:', config);

        // Envoyer la config à la page
        window.postMessage({
          type: 'POSTHOG_CONFIG_RESPONSE',
          config: config
        }, '*');
      } else {
        console.error('❌ PostHog client non disponible');
      }
    }
  });

})();