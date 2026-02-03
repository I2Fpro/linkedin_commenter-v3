/**
 * Toast Notification System for LinkedIn AI Commenter
 * Système de notifications visuelles professionnelles et non intrusives
 *
 * Types disponibles: 'success', 'error', 'warning', 'info'
 * Usage: showToast(message, type, duration)
 */

(function() {
  'use strict';

  // Container pour les toasts (créé à la première utilisation)
  let toastContainer = null;

  // Configuration des icônes et couleurs par type
  const TOAST_CONFIG = {
    success: {
      icon: '✅',
      borderColor: '#2ecc71',
      iconColor: '#2ecc71'
    },
    error: {
      icon: '❌',
      borderColor: '#e74c3c',
      iconColor: '#e74c3c'
    },
    warning: {
      icon: '⚠️',
      borderColor: '#f39c12',
      iconColor: '#f39c12'
    },
    info: {
      icon: 'ℹ️',
      borderColor: '#0077b5',
      iconColor: '#0077b5'
    }
  };

  /**
   * Initialise le container de toasts (appelé automatiquement)
   */
  function initToastContainer() {
    if (toastContainer) return;

    toastContainer = document.createElement('div');
    toastContainer.className = 'ai-toast-container';
    document.body.appendChild(toastContainer);
  }

  /**
   * Affiche une notification toast
   * @param {string} message - Message à afficher
   * @param {string} type - Type de notification (success, error, warning, info)
   * @param {number|Object} durationOrOptions - Durée d'affichage en ms (défaut: 4000ms) OU objet d'options
   * @param {Object} durationOrOptions.action - Action optionnelle avec bouton
   * @param {string} durationOrOptions.action.text - Texte du bouton d'action
   * @param {Function} durationOrOptions.action.callback - Fonction appelée au clic sur le bouton
   * @param {number} durationOrOptions.duration - Durée d'affichage en ms
   */
  function showToast(message, type = 'info', durationOrOptions = 4000) {
    // Initialiser le container si nécessaire
    initToastContainer();

    // Valider le type
    if (!TOAST_CONFIG[type]) {
      console.warn(`Type de toast invalide: ${type}. Utilisation de 'info' par défaut.`);
      type = 'info';
    }

    // Gérer les options (V3 Story 4.1 - support des actions)
    let duration = 4000;
    let action = null;
    if (typeof durationOrOptions === 'object') {
      duration = durationOrOptions.duration || 5000; // Plus long si action présente
      action = durationOrOptions.action || null;
    } else {
      duration = durationOrOptions;
    }

    const config = TOAST_CONFIG[type];

    // Créer l'élément toast
    const toast = document.createElement('div');
    toast.className = `ai-toast ai-toast-${type}`;
    toast.style.borderLeftColor = config.borderColor;

    // Structure HTML du toast (avec bouton d'action optionnel)
    let actionHtml = '';
    if (action && action.text) {
      actionHtml = `<button class="ai-button ai-button--primary ai-button--sm ai-toast-action" aria-label="${escapeHtml(action.text)}">${escapeHtml(action.text)}</button>`;
    }

    toast.innerHTML = `
      <div class="ai-toast-icon" style="color: ${config.iconColor}">
        ${config.icon}
      </div>
      <div class="ai-toast-content">
        <div class="ai-toast-message">${escapeHtml(message)}</div>
        ${actionHtml}
      </div>
      <button class="ai-toast-close" aria-label="Fermer">×</button>
    `;

    // Ajouter au container
    toastContainer.appendChild(toast);

    // Animation d'entrée
    requestAnimationFrame(() => {
      toast.classList.add('ai-toast-show');
    });

    // Bouton de fermeture
    const closeButton = toast.querySelector('.ai-toast-close');
    closeButton.addEventListener('click', () => {
      removeToast(toast);
    });

    // Bouton d'action (V3 Story 4.1)
    if (action && action.callback) {
      const actionButton = toast.querySelector('.ai-toast-action');
      if (actionButton) {
        actionButton.addEventListener('click', () => {
          action.callback();
          removeToast(toast);
        });
      }
    }

    // Auto-fermeture après la durée spécifiée
    const timeoutId = setTimeout(() => {
      removeToast(toast);
    }, duration);

    // Permettre de passer la souris pour garder le toast ouvert
    toast.addEventListener('mouseenter', () => {
      clearTimeout(timeoutId);
    });

    toast.addEventListener('mouseleave', () => {
      setTimeout(() => {
        removeToast(toast);
      }, 1000); // Fermer 1s après avoir quitté le toast
    });

    return toast;
  }

  /**
   * Supprime un toast avec animation
   * @param {HTMLElement} toast - Élément toast à supprimer
   */
  function removeToast(toast) {
    if (!toast || !toast.parentElement) return;

    // Animation de sortie
    toast.classList.add('ai-toast-hide');

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
    }, 300); // Durée de l'animation de sortie
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
  function showSuccess(message, duration) {
    return showToast(message, 'success', duration);
  }

  function showError(message, duration) {
    return showToast(message, 'error', duration);
  }

  function showWarning(message, duration) {
    return showToast(message, 'warning', duration);
  }

  function showInfo(message, duration) {
    return showToast(message, 'info', duration);
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

  console.log('✅ Toast Notification System chargé');
})();
