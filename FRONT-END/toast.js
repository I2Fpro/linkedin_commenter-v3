/**
 * Toast Notification System for LinkedIn AI Commenter
 * Système de notifications visuelles professionnelles et non intrusives
 *
 * Story 7.5: Refactoring Toasts vers BEM
 * - Convention BEM pour les classes CSS
 * - Durées selon spec UX (3s success/info, 5s warning, persist error)
 * - Stacking max 3 toasts visibles
 * - ARIA: role="alert" + aria-live="polite"
 * - Hover pause le timer
 *
 * Types disponibles: 'success', 'error', 'warning', 'info'
 * Usage: showToast(message, type, duration)
 */

(function() {
  'use strict';

  // Container pour les toasts (créé à la première utilisation)
  let toastContainer = null;

  // Configuration des icônes par type (couleurs gérées par CSS via design tokens)
  const TOAST_CONFIG = {
    success: {
      icon: '✅'
    },
    error: {
      icon: '❌'
    },
    warning: {
      icon: '⚠️'
    },
    info: {
      icon: 'ℹ️'
    }
  };

  // Durées par type selon spec UX (Story 7.5)
  const TOAST_DURATIONS = {
    success: 3000,   // 3s auto-dismiss
    info: 3000,      // 3s auto-dismiss
    warning: 5000,   // 5s auto-dismiss
    error: Infinity  // Persist - dismiss manuel requis
  };

  // Limite de toasts visibles (Story 7.5 - AC #2)
  const MAX_VISIBLE_TOASTS = 3;

  /**
   * Initialise le container de toasts (appelé automatiquement)
   */
  function initToastContainer() {
    if (toastContainer) return;

    toastContainer = document.createElement('div');
    toastContainer.className = 'ai-toast-container';
    // ARIA: aria-live pour annoncer les nouveaux toasts aux lecteurs d'écran
    toastContainer.setAttribute('aria-live', 'polite');
    toastContainer.setAttribute('aria-atomic', 'false');
    document.body.appendChild(toastContainer);
  }

  /**
   * Affiche une notification toast
   * @param {string} message - Message à afficher
   * @param {string} type - Type de notification (success, error, warning, info)
   * @param {number|Object} durationOrOptions - Durée d'affichage en ms OU objet d'options
   * @param {Object} durationOrOptions.action - Action optionnelle avec bouton
   * @param {string} durationOrOptions.action.text - Texte du bouton d'action
   * @param {Function} durationOrOptions.action.callback - Fonction appelée au clic sur le bouton
   * @param {number} durationOrOptions.duration - Durée d'affichage en ms (override le défaut par type)
   */
  function showToast(message, type = 'info', durationOrOptions = null) {
    // Initialiser le container si nécessaire
    initToastContainer();

    // Valider le type
    if (!TOAST_CONFIG[type]) {
      console.warn(`Type de toast invalide: ${type}. Utilisation de 'info' par défaut.`);
      type = 'info';
    }

    // Stacking: supprimer le plus ancien si >= MAX_VISIBLE_TOASTS (Story 7.5 - AC #2)
    const existingToasts = toastContainer.querySelectorAll('.ai-toast');
    if (existingToasts.length >= MAX_VISIBLE_TOASTS) {
      removeToast(existingToasts[0]); // Supprime le plus ancien (premier = en haut)
    }

    // Gérer les options (V3 Story 4.1 - support des actions)
    let duration = TOAST_DURATIONS[type]; // Durée par défaut selon le type
    let action = null;
    if (typeof durationOrOptions === 'object' && durationOrOptions !== null) {
      // Si duration explicite fournie, l'utiliser (sinon garder défaut par type)
      if (durationOrOptions.duration !== undefined) {
        duration = durationOrOptions.duration;
      }
      action = durationOrOptions.action || null;
    } else if (typeof durationOrOptions === 'number') {
      // Compatibilité: ancien comportement avec durée en ms directe
      duration = durationOrOptions;
    }

    const config = TOAST_CONFIG[type];

    // Créer l'élément toast avec classes BEM
    const toast = document.createElement('div');
    // Classes BEM: bloc + modifier de type (anciennes classes aussi pour compat)
    toast.className = `ai-toast ai-toast--${type} ai-toast-${type}`;

    // ARIA: role="alert" pour annoncer le toast aux lecteurs d'écran
    toast.setAttribute('role', 'alert');

    // Structure HTML du toast avec classes BEM (avec bouton d'action optionnel)
    let actionHtml = '';
    if (action && action.text) {
      actionHtml = `<button class="ai-button ai-button--primary ai-button--sm ai-toast__action ai-toast-action" aria-label="${escapeHtml(action.text)}">${escapeHtml(action.text)}</button>`;
    }

    toast.innerHTML = `
      <div class="ai-toast__icon ai-toast-icon">
        ${config.icon}
      </div>
      <div class="ai-toast__content ai-toast-content">
        <div class="ai-toast__message ai-toast-message">${escapeHtml(message)}</div>
        ${actionHtml}
      </div>
      <button class="ai-toast__close ai-toast-close" aria-label="Fermer">×</button>
    `;

    // Ajouter au container
    toastContainer.appendChild(toast);

    // Animation d'entrée (classes BEM + compat)
    requestAnimationFrame(() => {
      toast.classList.add('ai-toast--show', 'ai-toast-show');
    });

    // Bouton de fermeture
    const closeButton = toast.querySelector('.ai-toast__close, .ai-toast-close');
    closeButton.addEventListener('click', () => {
      removeToast(toast);
    });

    // Bouton d'action (V3 Story 4.1)
    if (action && action.callback) {
      const actionButton = toast.querySelector('.ai-toast__action, .ai-toast-action');
      if (actionButton) {
        actionButton.addEventListener('click', () => {
          action.callback();
          removeToast(toast);
        });
      }
    }

    // Gestion du timer et du hover (Story 7.5 - AC #2)
    let timeoutId = null;
    let remainingTime = duration;
    let startTime = Date.now();

    // Fonction pour démarrer/reprendre le timer
    function startTimer() {
      // Ne pas démarrer de timer pour les toasts persistants (error)
      if (remainingTime === Infinity) return;

      startTime = Date.now();
      timeoutId = setTimeout(() => {
        removeToast(toast);
      }, remainingTime);
    }

    // Fonction pour pauser le timer
    function pauseTimer() {
      if (timeoutId) {
        clearTimeout(timeoutId);
        timeoutId = null;
        // Calculer le temps restant
        if (remainingTime !== Infinity) {
          remainingTime = remainingTime - (Date.now() - startTime);
          if (remainingTime < 0) remainingTime = 0;
        }
      }
    }

    // Hover: pause le timer (Story 7.5 - AC #2)
    toast.addEventListener('mouseenter', () => {
      pauseTimer();
    });

    // Mouseleave: reprendre le timer avec le temps restant
    toast.addEventListener('mouseleave', () => {
      startTimer();
    });

    // Démarrer le timer initial
    startTimer();

    // Stocker les références pour nettoyage
    toast._toastData = {
      timeoutId: () => timeoutId,
      clearTimeout: () => {
        if (timeoutId) clearTimeout(timeoutId);
      }
    };

    return toast;
  }

  /**
   * Supprime un toast avec animation
   * @param {HTMLElement} toast - Élément toast à supprimer
   */
  function removeToast(toast) {
    if (!toast || !toast.parentElement) return;

    // Nettoyer le timeout si présent
    if (toast._toastData && toast._toastData.clearTimeout) {
      toast._toastData.clearTimeout();
    }

    // Animation de sortie (classes BEM + compat)
    toast.classList.add('ai-toast--hide', 'ai-toast-hide');
    toast.classList.remove('ai-toast--show', 'ai-toast-show');

    // Supprimer après l'animation
    setTimeout(() => {
      if (toast.parentElement) {
        toast.remove();
      }

      // Nettoyer le container si vide
      if (toastContainer && toastContainer.children.length === 0) {
        toastContainer.remove();
        toastContainer = null;
      }
    }, 300); // Durée de l'animation de sortie (var(--ai-transition-normal))
  }

  /**
   * Échappe les caractères HTML pour éviter les injections XSS
   * @param {string} text - Texte à échapper
   * @returns {string} Texte échappé
   */
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Supprime tous les toasts affichés
   */
  function clearAllToasts() {
    if (!toastContainer) return;

    const toasts = toastContainer.querySelectorAll('.ai-toast');
    toasts.forEach(toast => removeToast(toast));
  }

  /**
   * Fonctions de raccourci pour chaque type
   */
  function showSuccess(message, durationOrOptions) {
    return showToast(message, 'success', durationOrOptions);
  }

  function showError(message, durationOrOptions) {
    return showToast(message, 'error', durationOrOptions);
  }

  function showWarning(message, durationOrOptions) {
    return showToast(message, 'warning', durationOrOptions);
  }

  function showInfo(message, durationOrOptions) {
    return showToast(message, 'info', durationOrOptions);
  }

  // Export des fonctions pour utilisation globale
  window.toastNotification = {
    show: showToast,
    success: showSuccess,
    error: showError,
    warning: showWarning,
    info: showInfo,
    clear: clearAllToasts,
    remove: removeToast
  };

  console.log('✅ Toast Notification System chargé (BEM + ARIA)');
})();
