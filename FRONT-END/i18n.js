// Système de traduction pour l'interface du plugin
class I18n {
  constructor() {
    this.currentLang = 'fr'; // Langue par défaut
    this.translations = {
      fr: {
        // Titres et labels principaux
        extensionTitle: 'LinkedIn AI Commenter',
        authRequired: 'Authentification Google requise',
        authMessage: 'Veuillez vous connecter avec Google pour utiliser le plugin',
        signInWithGoogle: 'Se connecter avec Google',
        logout: 'Déconnexion',
        upgrade: 'Mettre à niveau',
        manageSubscription: 'Gérer mon abonnement',

        // Onglets principaux
        tabSettings: 'Paramètres',
        tabSupport: 'Soutien',

        // Sous-onglets
        subTabAccount: '👤 Compte',
        subTabLanguage: '🌐 Langue',
        subTabMore: '⚙️ Plus',

        // Compte
        authenticationStatus: 'Authentification',
        quotaLabel: 'Quota quotidien',

        // Toggles
        toggleOn: 'ON',
        toggleOff: 'OFF',

        // Support
        supportHelp: 'Documentation',
        supportHelpDesc: 'Guide d\'utilisation et FAQ',
        supportFeedback: 'Feedback',
        supportFeedbackDesc: 'Partagez vos suggestions',
        supportBug: 'Signaler un bug',
        supportBugDesc: 'Aidez-nous à améliorer l\'extension',
        supportContact: 'Contact',
        supportContactDesc: 'Contactez le support',

        // Autres
        version: 'Version',
        smartSummaryMode: 'Mode Smart Summary',
        
        // Paramètres de langue
        interfaceLanguage: 'Langue de l\'interface',
        generationSettings: 'Paramètres de génération',
        commentLanguage: 'Langue des commentaires',
        french: '\u{1F1EB}\u{1F1F7} Français',
        english: '\u{1F1EC}\u{1F1E7} Anglais',
        
        // Paramètres de génération
        tone: 'Ton',
        professional: 'Professionnel',
        formal: 'Soutenu',
        friendly: 'Amical',
        expert: 'Expert',
        informative: 'Informatif',
        negative: 'Négatif',
        
        length: 'Longueur',
        words0to10: '0-10 mots',
        words10to20: '10-20 mots',
        words20to40: '20-40 mots',
        
        generationsCount: 'Nombre de Générations',
        generation1: '1 Génération',
        generation2: '2 Générations',
        generation3: '3 Générations',

        // Enrichissement actualité
        newsEnrichment: 'Enrichissement Actualité',
        newsMode: 'Mode d\'enrichissement',
        newsDisabled: '❌ Désactivé',
        newsTitleOnly: '⚡ Rapide (Titres uniquement)',
        newsSmartSummary: '🧠 Intelligent (Résumés enrichis)',
        newsInfoTitleOnly: 'Utilise uniquement les titres des actualités LinkedIn. Rapide et léger.',
        newsInfoTitleOnlyMedium: 'Utilise uniquement les titres des actualités LinkedIn. Passez à PREMIUM pour des résumés enrichis encore plus pertinents.',
        newsInfoSmartSummary: 'Résumés enrichis générés toutes les heures. Commentaires plus pertinents et contextuels.',
        newsInfoDisabled: 'Les commentaires ne tiendront pas compte de l\'actualité LinkedIn.',
        newsInfoDisabledFree: 'Les commentaires ne tiendront pas compte de l\'actualité LinkedIn. Fonctionnalité disponible dans les plans MEDIUM et PREMIUM.',
        newsRequiresMedium: '🔒 Fonctionnalité réservée aux plans MEDIUM et PREMIUM',
        smartRequiresPremium: '🔒 Fonctionnalité réservée au plan PREMIUM',
        autoCloseEmotionsPanel: 'Fermeture auto panneau',

        save: 'Enregistrer',
        
        // Messages content script
        generate: 'Générer',
        withPrompt: 'Avec prompt',
        generating: 'Génération...',
        customInstructions: 'Instructions personnalisées',
        addInstructions: 'Ajoutez vos instructions...',
        cancel: 'Annuler',
        refine: 'Affiner',
        refineComment: 'Affiner le commentaire',
        refineInstructions: 'Instructions pour affiner...',
        comment: 'Commentaire',
        generations: 'génération(s)',
        authRequiredContent: 'Connectez-vous via l\'extension pour utiliser cette fonctionnalité',
        error: 'Erreur',
        impossibleExtract: 'Impossible d\'extraire le contenu',

        // Plan et quotas
        infiniteGenerations: '∞ générations',
        unlimitedGenerations: 'Générations illimitées',
        generationsUnit: 'générations',
        usedToday: 'utilisées aujourd\'hui',
        upgradeToMedium: 'Passer à MEDIUM',
        upgradeToPremium: 'Passez à MEDIUM ou PREMIUM pour débloquer',
        upgradeRequired: 'Veuillez passer à un plan supérieur pour accéder à cette option',

        // V3 — Citation contextuelle
        quoteToggle: 'Citation',
        quoteToggleActive: 'Citation activée',
        quoteToggleInactive: 'Citation désactivée',
        quoteUpgradeRequired: 'La citation contextuelle est réservée aux abonnés Premium',

        // V3 — Tag auteur
        tagAuthor: 'Tag auteur',
        tagAuthorTooltip: 'Ajoute @auteur dans le commentaire — cliquez sur la suggestion LinkedIn',
        tagAuthorActive: 'Tag auteur activé pour',
        tagAuthorUpgradeRequired: 'Le tag auteur est réservé aux abonnés Premium',
        authorNotFound: 'Impossible de trouver le nom de l\'auteur du post',
        clickMentionSuggestion: 'Cliquez sur la suggestion LinkedIn pour valider la mention',
        mentionCompleted: 'Mention ajoutée !',

        // V3 — Contexte commentaires tiers
        contextToggle: 'Contexte',
        contextToggleTooltip: 'Prend en compte les commentaires existants pour se différencier',
        contextToggleActive: 'Contexte activé',
        contextToggleInactive: 'Contexte désactivé',
        contextUpgradeRequired: 'Le contexte des commentaires est réservé aux abonnés Premium',

        // V3 Story 1.4 — Recherche web
        webSearchToggle: 'Recherche web',
        webSearchToggleTooltip: 'Enrichit avec des sources web récentes',
        webSearchToggleActive: 'Recherche web activée',
        webSearchToggleInactive: 'Recherche web désactivée',
        webSearchUpgradeRequired: 'La recherche web est réservée aux abonnés Premium',
        webSearchFallbackMessage: 'Aucune source web trouvée — génération classique utilisée',

        // V3 Story 7.6 — Mode Expanded
        randomGenerate: 'Générer aléatoire',
        tagAuthorSuccess: '{name} sera mentionné dans le commentaire',
        modeAdaptedToSpace: 'Mode adapté à l\'espace',

        // V3 Story 2.1 — Blacklist
        addToBlacklist: 'Blacklister',
        addToBlacklistTooltip: 'Ajoute l\'auteur du post à votre blacklist',
        blacklistTitle: 'Ma blacklist',
        blacklistEmpty: 'Votre blacklist est vide',
        blacklistAddSuccess: '{name} a été ajouté à votre blacklist',
        blacklistAlreadyExists: '{name} est déjà dans votre blacklist',
        blacklistAddError: 'Erreur lors de l\'ajout à la blacklist',
        blacklistLoadError: 'Erreur lors du chargement de la blacklist',
        viewBlacklist: 'Ma liste',
        viewBlacklistTooltip: 'Voir ma blacklist',
        blacklistUpgradeRequired: 'La blacklist est réservée aux abonnés Premium',

        // V3 Story 2.2 — Suppression Blacklist
        removeFromBlacklist: 'Retirer',
        blacklistRemoveConfirm: 'Voulez-vous vraiment retirer {name} de votre blacklist ?',
        blacklistRemoveSuccess: '{name} a été retiré de votre blacklist',
        blacklistRemoveError: 'Erreur lors de la suppression de la blacklist',
        blacklistNotFound: 'Cette personne n\'est plus dans votre blacklist',

        // V3 Story 4.1 — Premium upgrade prompt
        premiumFeatureLockedTitle: 'Fonctionnalité Premium',
        premiumFeatureLockedMessage: 'Cette fonctionnalité est réservée au plan Premium.',
        upgradeNow: 'Passer au Premium',

        // V3 Story 5.1 — Locked comments upgrade
        lockedCommentUpgradeRequired: 'Passez à MEDIUM ou PREMIUM pour débloquer les commentaires supplémentaires.',
        lockedRefineResizeUpgradeRequired: 'Passez à MEDIUM ou PREMIUM pour utiliser Affiner et Redimensionner.',

        // V3 Story 5.4 — News LinkedIn toggle
        newsToggle: 'News LinkedIn',
        newsToggleActive: 'News LinkedIn activées',
        newsToggleInactive: 'News LinkedIn désactivées',
        newsToggleTooltip: 'Enrichit votre commentaire avec les actualités LinkedIn',
        newsUpgradeRequired: 'L\'enrichissement actualités est réservé aux abonnés MEDIUM ou supérieur',

        // V3 Story 5.5 — Afficher la source web
        showSourceBtn: 'Afficher la source',
        showSourceAdded: 'Source ajoutée',
        noSourceAvailable: 'Source non disponible'
        // Note: V3 Story 2.3 translations are in content.js local translations object
      },
      en: {
        // Main titles and labels
        extensionTitle: 'LinkedIn AI Commenter',
        authRequired: 'Google authentication required',
        authMessage: 'Please sign in with Google to use the plugin',
        signInWithGoogle: 'Sign in with Google',
        logout: 'Sign out',
        upgrade: 'Upgrade',
        manageSubscription: 'Manage subscription',

        // Main tabs
        tabSettings: 'Settings',
        tabSupport: 'Support',

        // Sub-tabs
        subTabAccount: '👤 Account',
        subTabLanguage: '🌐 Language',
        subTabMore: '⚙️ More',

        // Account
        authenticationStatus: 'Authentication',
        quotaLabel: 'Daily quota',

        // Toggles
        toggleOn: 'ON',
        toggleOff: 'OFF',

        // Support
        supportHelp: 'Documentation',
        supportHelpDesc: 'User guide and FAQ',
        supportFeedback: 'Feedback',
        supportFeedbackDesc: 'Share your suggestions',
        supportBug: 'Report a bug',
        supportBugDesc: 'Help us improve the extension',
        supportContact: 'Contact',
        supportContactDesc: 'Contact support',

        // Others
        version: 'Version',
        smartSummaryMode: 'Smart Summary Mode',
        
        // Language settings
        interfaceLanguage: 'Interface language',
        generationSettings: 'Generation settings',
        commentLanguage: 'Comments language',
        french: '\u{1F1EB}\u{1F1F7} French',
        english: '\u{1F1EC}\u{1F1E7} English',
        
        // Generation settings
        tone: 'Tone',
        professional: 'Professional',
        formal: 'Formal',
        friendly: 'Friendly',
        expert: 'Expert',
        informative: 'Informative',
        negative: 'Negative',
        
        length: 'Length',
        words0to10: '0-10 words',
        words10to20: '10-20 words',
        words20to40: '20-40 words',
        
        generationsCount: 'Number of Generations',
        generation1: '1 Generation',
        generation2: '2 Generations',
        generation3: '3 Generations',

        // News enrichment
        newsEnrichment: 'News Enrichment',
        newsMode: 'Enrichment mode',
        newsDisabled: '❌ Disabled',
        newsTitleOnly: '⚡ Fast (Titles only)',
        newsSmartSummary: '🧠 Smart (Enriched summaries)',
        newsInfoTitleOnly: 'Uses only LinkedIn news titles. Fast and lightweight.',
        newsInfoTitleOnlyMedium: 'Uses only LinkedIn news titles. Upgrade to PREMIUM for even more relevant enriched summaries.',
        newsInfoSmartSummary: 'Enriched summaries generated hourly. More relevant and contextual comments.',
        newsInfoDisabled: 'Comments will not take LinkedIn news into account.',
        newsInfoDisabledFree: 'Comments will not take LinkedIn news into account. Feature available in MEDIUM and PREMIUM plans.',
        newsRequiresMedium: '🔒 Feature reserved for MEDIUM and PREMIUM plans',
        smartRequiresPremium: '🔒 Feature reserved for PREMIUM plan',
        autoCloseEmotionsPanel: 'Auto-close panel',

        save: 'Save',
        
        // Content script messages
        generate: 'Generate',
        withPrompt: 'With prompt',
        generating: 'Generating...',
        customInstructions: 'Custom instructions',
        addInstructions: 'Add your instructions...',
        cancel: 'Cancel',
        refine: 'Refine',
        refineComment: 'Refine comment',
        refineInstructions: 'Instructions to refine...',
        comment: 'Comment',
        generations: 'generation(s)',
        authRequiredContent: 'Sign in via the extension to use this feature',
        error: 'Error',
        impossibleExtract: 'Unable to extract content',

        // Plan and quotas
        infiniteGenerations: '∞ generations',
        unlimitedGenerations: 'Unlimited generations',
        generationsUnit: 'generations',
        usedToday: 'used today',
        upgradeToMedium: 'Upgrade to MEDIUM',
        upgradeToPremium: 'Upgrade to MEDIUM or PREMIUM to unlock',
        upgradeRequired: 'Please upgrade to a higher plan to access this option',

        // V3 — Contextual quote
        quoteToggle: 'Quote',
        quoteToggleActive: 'Quote enabled',
        quoteToggleInactive: 'Quote disabled',
        quoteUpgradeRequired: 'Contextual quotes are reserved for Premium subscribers',

        // V3 — Tag author
        tagAuthor: 'Tag author',
        tagAuthorTooltip: 'Adds @author in the comment — click the LinkedIn suggestion',
        tagAuthorActive: 'Tag author enabled for',
        tagAuthorUpgradeRequired: 'Tag author is reserved for Premium subscribers',
        authorNotFound: 'Unable to find the post author\'s name',
        clickMentionSuggestion: 'Click the LinkedIn suggestion to validate the mention',
        mentionCompleted: 'Mention added!',

        // V3 — Third-party comments context
        contextToggle: 'Context',
        contextToggleTooltip: 'Considers existing comments to differentiate',
        contextToggleActive: 'Context enabled',
        contextToggleInactive: 'Context disabled',
        contextUpgradeRequired: 'Comments context is reserved for Premium subscribers',

        // V3 Story 1.4 — Web search
        webSearchToggle: 'Web search',
        webSearchToggleTooltip: 'Enriches with recent web sources',
        webSearchToggleActive: 'Web search enabled',
        webSearchToggleInactive: 'Web search disabled',
        webSearchUpgradeRequired: 'Web search is reserved for Premium subscribers',
        webSearchFallbackMessage: 'No web source found — classic generation used',

        // V3 Story 7.6 — Mode Expanded
        randomGenerate: 'Random generate',
        tagAuthorSuccess: '{name} will be mentioned in the comment',
        modeAdaptedToSpace: 'Mode adapted to space',

        // V3 Story 2.1 — Blacklist
        addToBlacklist: 'Blacklist',
        addToBlacklistTooltip: 'Add post author to your blacklist',
        blacklistTitle: 'My blacklist',
        blacklistEmpty: 'Your blacklist is empty',
        blacklistAddSuccess: '{name} has been added to your blacklist',
        blacklistAlreadyExists: '{name} is already in your blacklist',
        blacklistAddError: 'Error adding to blacklist',
        blacklistLoadError: 'Error loading blacklist',
        viewBlacklist: 'My list',
        viewBlacklistTooltip: 'View my blacklist',
        blacklistUpgradeRequired: 'Blacklist is reserved for Premium subscribers',

        // V3 Story 2.2 — Remove Blacklist
        removeFromBlacklist: 'Remove',
        blacklistRemoveConfirm: 'Are you sure you want to remove {name} from your blacklist?',
        blacklistRemoveSuccess: '{name} has been removed from your blacklist',
        blacklistRemoveError: 'Error removing from blacklist',
        blacklistNotFound: 'This person is no longer in your blacklist',

        // V3 Story 4.1 — Premium upgrade prompt
        premiumFeatureLockedTitle: 'Premium Feature',
        premiumFeatureLockedMessage: 'This feature is reserved for Premium plan.',
        upgradeNow: 'Upgrade to Premium',

        // V3 Story 5.1 — Locked comments upgrade
        lockedCommentUpgradeRequired: 'Upgrade to MEDIUM or PREMIUM to unlock additional comments.',
        lockedRefineResizeUpgradeRequired: 'Upgrade to MEDIUM or PREMIUM to use Refine and Resize.',

        // V3 Story 5.4 — News LinkedIn toggle
        newsToggle: 'LinkedIn News',
        newsToggleActive: 'LinkedIn News enabled',
        newsToggleInactive: 'LinkedIn News disabled',
        newsToggleTooltip: 'Enriches your comment with LinkedIn news',
        newsUpgradeRequired: 'News enrichment is reserved for MEDIUM subscribers or higher',

        // V3 Story 5.5 — Show web source
        showSourceBtn: 'Show source',
        showSourceAdded: 'Source added',
        noSourceAvailable: 'Source unavailable'
        // Note: V3 Story 2.3 translations are in content.js local translations object
      }
    };
  }

  // Initialiser avec la langue sauvegardée
  async init() {
    return new Promise((resolve) => {
      chrome.storage.sync.get(['interfaceLanguage'], (data) => {
        this.currentLang = data.interfaceLanguage || 'fr';
        this.updateInterface();
        resolve();
      });
    });
  }

  // Changer la langue courante
  setLanguage(lang) {
    if (this.translations[lang]) {
      this.currentLang = lang;
      chrome.storage.sync.set({ interfaceLanguage: lang });
      this.updateInterface();
    }
  }

  // Obtenir une traduction
  t(key) {
    return this.translations[this.currentLang][key] || this.translations['fr'][key] || key;
  }

  // Mettre à jour tous les éléments avec data-i18n
  updateInterface() {
    document.querySelectorAll('[data-i18n]').forEach(element => {
      const key = element.getAttribute('data-i18n');
      const translation = this.t(key);
      
      if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
        element.placeholder = translation;
      } else if (element.tagName === 'OPTION') {
        // Pour les options, on utilise directement la traduction qui contient déjà les emojis
        element.textContent = translation;
      } else {
        element.textContent = translation;
      }
    });

    // Mettre à jour le titre de la page
    document.title = this.t('extensionTitle');
  }

  // Obtenir la langue actuelle
  getCurrentLanguage() {
    return this.currentLang;
  }
}

// Instance globale
window.i18n = new I18n();