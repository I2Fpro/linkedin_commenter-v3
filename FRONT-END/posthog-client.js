/**
 * PostHog Client pour Chrome Extension
 * Utilise la bibliothèque officielle posthog-js
 *
 * Événements capturés :
 * - Connexions/Déconnexions
 * - Profil utilisateur (FREE, MEDIUM, PREMIUM)
 * - Générations de commentaires
 * - Choix d'émotion et de ton
 */

(function() {
  'use strict';

  /**
   * Classe wrapper pour PostHog utilisant la bibliothèque officielle
   * Expose l'objet posthog global après initialisation
   */
  class PostHogClient {
    constructor() {
      this.initialized = false;
      this.isIdentified = false;
      this.queue = [];
      this._resolveReady = null;
      this.readyPromise = new Promise((res) => (this._resolveReady = res));
      this.apiKey = API_CONFIG.posthog.apiKey;
      this.apiHost = API_CONFIG.posthog.apiHost;
    }

    /**
     * Initialiser PostHog avec les credentials
     * Utilise l'API officielle posthog.init()
     */
    async init() {
      if (this.initialized || !API_CONFIG?.posthog?.enabled) {
        return;
      }

      try {
        // Vérifier si posthog est chargé
        if (typeof posthog === 'undefined') {
          console.error('❌ PostHog library not loaded');
          return;
        }

        // Initialiser PostHog avec la configuration
        posthog.init(this.apiKey, {
          api_host: this.apiHost,
          autocapture: false,
          disable_session_recording: true,
          disable_external_dependency_loading: true, // évite CSP externe
          advanced_disable_decide: true, // évite decide -> deps externes
          loaded: (ph) => {
            console.log('📊 PostHog initialisé avec succès', {
              distinctId: ph.get_distinct_id(),
              apiHost: this.apiHost
            });
            this.initialized = true;
            this._resolveReady?.();
            this.flush();
          }
        });

      } catch (error) {
        console.error('❌ Erreur initialisation PostHog:', error);
      }
    }

    /**
     * Retourne une Promise qui se résout quand PostHog est prêt
     */
    async ready() {
      return this.readyPromise;
    }

    /**
     * Vide la queue d'événements en attente
     */
    flush() {
      if (!this.initialized || typeof posthog === 'undefined' || !this.isIdentified) return;
      while (this.queue.length) {
        const it = this.queue.shift();
        if (it.event) {
          try { posthog.capture(it.event, it.properties || {}); } catch {}
        }
      }
    }

    /**
     * Envoyer un événement à PostHog
     * @param {string} event - Nom de l'événement
     * @param {object} properties - Propriétés de l'événement
     */
    capture(event, properties = {}) {
      if (!this.initialized || typeof posthog === 'undefined') {
        this.queue.push({ event, properties });
        return;
      }

      // Buffer events until identify is called
      if (!this.isIdentified) {
        this.queue.push({ event, properties });
        return;
      }

      try {
        console.log('📊 PostHog event:', event, properties);
        posthog.capture(event, properties);
      } catch (error) {
        console.error('❌ Erreur envoi événement PostHog:', error);
      }
    }

    /**
     * Identifier un utilisateur
     * @param {string} userId - Email ou ID de l'utilisateur
     * @param {object} properties - Propriétés de l'utilisateur
     */
    identify(userId, properties = {}) {
      if (!this.initialized || typeof posthog === 'undefined') {
        console.warn('⚠️ PostHog non initialisé, identify ignoré');
        return;
      }

      try {
        console.log('👤 PostHog identify:', userId, properties);
        posthog.identify(userId, properties);

        // Mark as identified and flush queued events
        this.isIdentified = true;
        this.flush();
      } catch (error) {
        console.error('❌ Erreur identification PostHog:', error);
      }
    }

    /**
     * Définir des propriétés utilisateur
     * @param {object} properties - Propriétés à définir
     */
    setPersonProperties(properties = {}) {
      if (!this.initialized || typeof posthog === 'undefined') {
        console.warn('⚠️ PostHog non initialisé, setPersonProperties ignoré');
        return;
      }

      try {
        console.log('👤 PostHog setPersonProperties:', properties);
        posthog.setPersonProperties(properties);
      } catch (error) {
        console.error('❌ Erreur setPersonProperties PostHog:', error);
      }
    }

    /**
     * Réinitialiser PostHog (déconnexion)
     */
    reset() {
      if (typeof posthog !== 'undefined') {
        try {
          console.log('🔄 PostHog reset');
          posthog.reset();
          // Reset identification state
          this.isIdentified = false;
          this.queue = [];
        } catch (error) {
          console.error('❌ Erreur reset PostHog:', error);
        }
      }
    }

    // ==================== ÉVÉNEMENTS : CONNEXION / DÉCONNEXION ====================

    /**
     * Capturer une connexion utilisateur
     * @param {string} userId - Identifiant anonyme de l'utilisateur (SHA256)
     * @param {object} userProfile - Profil utilisateur (plan, role, interface_lang, etc.)
     */
    trackUserLogin(userId, userProfile = {}) {
      // Identifier l'utilisateur avec toutes les propriétés (SANS email)
      this.identify(userId, {
        plan: userProfile.plan || 'FREE',
        role: userProfile.role || userProfile.plan || 'FREE',
        interface_lang: userProfile.interface_lang || null,
        auth_method: 'google_oauth2'
      });

      // Capturer l'événement de connexion (SANS email)
      this.capture('user_login', {
        user_id: userId,
        plan: userProfile.plan || 'FREE',
        auth_method: 'google_oauth2',
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer une déconnexion utilisateur
     */
    trackUserLogout() {
      this.capture('user_logout', {
        timestamp: new Date().toISOString()
      });

      // Réinitialiser PostHog après la déconnexion
      this.reset();
    }

    // ==================== ÉVÉNEMENTS : PROFIL UTILISATEUR ====================

    /**
     * Capturer un changement de plan utilisateur
     * @param {string} newPlan - Nouveau plan (FREE, MEDIUM, PREMIUM)
     * @param {string} oldPlan - Ancien plan
     */
    trackPlanChange(newPlan, oldPlan) {
      this.capture('plan_changed', {
        new_plan: newPlan,
        old_plan: oldPlan,
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Mettre à jour les propriétés utilisateur (plan, quota, role, interface_lang, etc.)
     * @param {object} userProfile - Profil utilisateur
     */
    updateUserProfile(userProfile) {
      if (!this.initialized || typeof posthog === 'undefined') {
        return;
      }

      try {
        // Utiliser setPersonProperties avec toutes les propriétés (SANS email)
        const properties = {
          plan: userProfile.plan || 'FREE',
          role: userProfile.role || userProfile.plan || 'FREE',
          daily_limit: userProfile.daily_limit || 5,
          remaining_quota: userProfile.remaining || 0
        };

        // Ajouter interface_lang si présent
        if (userProfile.interface_lang) {
          properties.interface_lang = userProfile.interface_lang;
        }

        posthog.setPersonProperties(properties);
        console.log('📊 PostHog - Person properties updated:', userProfile.plan);
      } catch (error) {
        console.error('❌ Erreur mise à jour profil:', error);
      }
    }

    // ==================== ÉVÉNEMENTS : GÉNÉRATIONS ====================

    /**
     * Capturer une génération de commentaire
     * @param {object} options - Options de génération
     */
    trackCommentGeneration(options) {
      this.capture('comment_generated', {
        generation_type: options.generationType || 'automatic',
        has_custom_prompt: options.hasCustomPrompt || false,
        tone: options.tone || null,
        language: options.language || 'fr',
        length: options.length || 15,
        options_count: options.optionsCount || 2,
        is_reply: options.isComment || false,
        user_plan: options.userPlan || 'FREE',
        success: options.success !== false,
        duration_ms: options.durationMs || 0,
        error: options.error || null,
        emotion: options.emotion || null,
        intensity: options.intensity || null,
        style: options.style || null,
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer le début d'une génération
     * @param {object} options - Options de génération
     */
    trackGenerationStarted(options) {
      this.capture('generation_started', {
        generation_type: options.generationType || 'automatic',
        has_custom_prompt: options.hasCustomPrompt || false,
        tone: options.tone || null,
        language: options.language || 'fr',
        emotion: options.emotion || null,
        intensity: options.intensity || null,
        style: options.style || null,
        timestamp: new Date().toISOString()
      });
    }

    // ==================== ÉVÉNEMENTS : ÉMOTION ET TON ====================

    /**
     * Capturer une sélection d'émotion
     * @param {string} emotion - Émotion sélectionnée
     * @param {string} intensity - Intensité (low, medium, high)
     */
    trackEmotionSelected(emotion, intensity) {
      this.capture('emotion_selected', {
        emotion: emotion,
        intensity: intensity,
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer une sélection de style
     * @param {string} style - Style sélectionné
     */
    trackStyleSelected(style) {
      this.capture('style_selected', {
        style: style,
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer un changement de ton
     * @param {string} newTone - Nouveau ton
     * @param {string} oldTone - Ancien ton
     */
    trackToneChanged(newTone, oldTone) {
      this.capture('tone_changed', {
        new_tone: newTone,
        old_tone: oldTone,
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer un changement de longueur
     * @param {number} newLength - Nouvelle longueur
     * @param {number} oldLength - Ancienne longueur
     */
    trackLengthChanged(newLength, oldLength) {
      this.capture('length_changed', {
        new_length: newLength,
        old_length: oldLength,
        timestamp: new Date().toISOString()
      });
    }

    // ==================== ÉVÉNEMENTS : PARAMÈTRES ====================

    /**
     * Capturer un changement de langue d'interface
     * @param {string} newLanguage - Nouvelle langue
     * @param {string} oldLanguage - Ancienne langue
     */
    trackInterfaceLanguageChanged(newLanguage, oldLanguage) {
      this.capture('interface_language_changed', {
        new_language: newLanguage,
        old_language: oldLanguage,
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer la définition de la langue d'interface (nouveau événement selon plan v3)
     * @param {string} langCode - Code de langue (fr, en, etc.)
     */
    trackInterfaceLanguageSet(langCode) {
      if (!this.initialized || typeof posthog === 'undefined') {
        console.warn('⚠️ PostHog non initialisé, trackInterfaceLanguageSet ignoré');
        return;
      }

      try {
        // Mettre à jour la propriété utilisateur directement avec posthog
        posthog.setPersonProperties({ interface_lang: langCode });

        // Capturer l'événement directement avec posthog
        posthog.capture('interface_language_set', { interface_lang: langCode });

        console.log('📊 PostHog - interface_language_set:', langCode);
      } catch (error) {
        console.error('❌ Erreur trackInterfaceLanguageSet:', error);
      }
    }

    /**
     * Capturer un changement de langue de commentaire
     * @param {string} newLanguage - Nouvelle langue
     * @param {string} oldLanguage - Ancienne langue
     */
    trackCommentLanguageChanged(newLanguage, oldLanguage) {
      this.capture('comment_language_changed', {
        new_language: newLanguage,
        old_language: oldLanguage,
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer un changement du nombre d'options
     * @param {number} newCount - Nouveau nombre
     * @param {number} oldCount - Ancien nombre
     */
    trackOptionsCountChanged(newCount, oldCount) {
      this.capture('options_count_changed', {
        new_count: newCount,
        old_count: oldCount,
        timestamp: new Date().toISOString()
      });
    }

    // ==================== ÉVÉNEMENTS : FONCTIONNALITÉS ====================

    /**
     * Capturer une utilisation de fonctionnalité
     * @param {string} featureName - Nom de la fonctionnalité
     * @param {object} properties - Propriétés additionnelles
     */
    trackFeatureUsed(featureName, properties = {}) {
      this.capture('feature_used', {
        feature_name: featureName,
        ...properties,
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer l'ouverture des paramètres
     */
    trackSettingsOpened() {
      this.capture('settings_opened', {
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer un clic sur le bouton d'upgrade
     * @param {string} currentPlan - Plan actuel
     * @param {string} targetPlan - Plan cible
     */
    trackUpgradeButtonClicked(currentPlan, targetPlan) {
      this.capture('upgrade_button_clicked', {
        current_plan: currentPlan,
        target_plan: targetPlan,
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer un changement du mode d'enrichissement des actualités
     * @param {string} newMode - Nouveau mode
     * @param {string} oldMode - Ancien mode
     * @param {string} userPlan - Plan utilisateur
     */
    trackNewsEnrichmentChanged(newMode, oldMode, userPlan) {
      this.capture('news_enrichment_changed', {
        new_mode: newMode,
        old_mode: oldMode,
        user_plan: userPlan,
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer l'activation/désactivation du smart summary
     * @param {boolean} enabled - Activé ou non
     * @param {string} userPlan - Plan utilisateur
     */
    trackSmartSummaryToggled(enabled, userPlan) {
      this.capture('smart_summary_toggled', {
        enabled: enabled,
        user_plan: userPlan,
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer l'insertion d'un commentaire
     * @param {object} options - Options
     */
    trackCommentInserted(options) {
      this.capture('comment_inserted', {
        comment_index: options.commentIndex || 0,
        comment_length: options.commentLength || 0,
        has_custom_prompt: options.hasCustomPrompt || false,
        language: options.language || 'fr',
        emotion: options.emotion || null,
        intensity: options.intensity || null,
        style: options.style || null,
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer une vérification de quota
     * @param {object} quotaData - Données du quota
     */
    trackQuotaChecked(quotaData) {
      this.capture('quota_checked', {
        plan: quotaData.plan || 'FREE',
        quota_remaining: quotaData.remaining || 0,
        quota_limit: quotaData.limit || 0,
        quota_percentage: quotaData.limit > 0 ? (quotaData.remaining / quotaData.limit * 100) : 0,
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer une erreur de l'extension
     * @param {object} error - Erreur
     * @param {object} context - Contexte
     */
    trackExtensionError(error, context = {}) {
      this.capture('extension_error', {
        error_type: error.type || 'unknown',
        error_message: error.message || String(error),
        endpoint: context.endpoint || null,
        ...context,
        timestamp: new Date().toISOString()
      });
    }

    // ==================== NOUVEAUX ÉVÉNEMENTS (PLAN POSTHOG) ====================

    /**
     * Capturer l'utilisation d'un prompt
     * @param {object} details - Détails du prompt (custom, length)
     */
    trackPromptUsed(details = {}) {
      this.capture('prompt_used', {
        custom: !!details.custom,
        length: details.length || null,
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer un redimensionnement de l'interface
     * @param {object} details - Détails du resize (target, width, height, deltaW, deltaH)
     */
    trackUIResized(details = {}) {
      this.capture('ui_resized', {
        target: details.target || 'unknown',
        width: details.width || null,
        height: details.height || null,
        delta_w: details.deltaW || null,
        delta_h: details.deltaH || null,
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer le début d'une session d'utilisation
     */
    trackUsageSessionStart() {
      this.capture('usage_session_start', {
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer la fin d'une session d'utilisation
     * @param {number} durationMs - Durée de la session en millisecondes
     */
    trackUsageSessionEnd(durationMs) {
      this.capture('usage_session_end', {
        duration_ms: durationMs,
        timestamp: new Date().toISOString()
      });
    }

    /**
     * Capturer un heartbeat d'utilisation (optionnel)
     * @param {number} activeMs - Temps actif en millisecondes
     */
    trackUsageHeartbeat(activeMs) {
      this.capture('usage_heartbeat', {
        active_ms: activeMs,
        timestamp: new Date().toISOString()
      });
    }

    // ==================== ALIASES POUR COMPATIBILITÉ ====================

    trackUserAuthenticated(userId, userProfile = {}) {
      this.trackUserLogin(userId, userProfile);
    }

    trackCommentGenerationStarted(options) {
      this.trackGenerationStarted(options);
    }

    trackCommentGenerated(options) {
      this.trackCommentGeneration(options);
    }

    trackUserPlanUpdated(newPlan, oldPlan) {
      this.trackPlanChange(newPlan, oldPlan);
    }
  }

  // Créer une instance globale unique
  window.posthogClient = window.posthogClient || new PostHogClient();

  console.log('✅ PostHog Client chargé (bibliothèque officielle posthog-js)');
})();
