/**
 * Utilitaires pour la génération d'identifiants utilisateur anonymes
 */

(function() {
  'use strict';

  class UserIdUtils {
    /**
     * Génère un identifiant utilisateur anonyme à partir de l'email
     * @param {string} email - Adresse email de l'utilisateur
     * @returns {Promise<string>} - Hash SHA256 de l'email normalisé
     */
    async generateUserId(email) {
      if (!email) {
        throw new Error('Email requis pour générer userId');
      }

      // Normaliser l'email (minuscules + trim)
      const normalizedEmail = email.toLowerCase().trim();

      // Générer le hash SHA256
      const hashBuffer = await this.sha256(normalizedEmail);

      // Convertir en string hexadécimal
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

      return hashHex;
    }

    /**
     * Calcule le hash SHA256 d'une chaîne
     * @param {string} message - Message à hasher
     * @returns {Promise<ArrayBuffer>} - Hash SHA256
     */
    async sha256(message) {
      // Encoder le message en UTF-8
      const msgBuffer = new TextEncoder().encode(message);

      // Calculer le hash
      const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);

      return hashBuffer;
    }

    /**
     * Récupère ou génère le userId depuis le storage
     * @param {string} email - Email de l'utilisateur
     * @returns {Promise<string>} - UserId (récupéré ou généré)
     */
    async getOrGenerateUserId(email) {
      if (!email) {
        throw new Error('Email requis');
      }

      try {
        // Vérifier si user_id existe déjà dans le storage (clé officielle)
        const stored = await chrome.storage.local.get(['user_id', 'userId', 'userIdEmail']);

        // Si on a un user_id et qu'il correspond au même email, le retourner
        if (stored.user_id && stored.userIdEmail === email) {
          console.log('📊 UserId existant récupéré depuis storage (user_id)');
          return stored.user_id;
        }

        // Fallback sur userId (compatibilité)
        if (stored.userId && stored.userIdEmail === email) {
          console.log('📊 UserId existant récupéré depuis storage (userId - compat)');
          return stored.userId;
        }

        // Sinon, générer un nouveau userId
        console.log('📊 Génération nouveau userId pour:', email);
        const userId = await this.generateUserId(email);

        // Sauvegarder dans le storage local avec les deux clés (migration)
        await chrome.storage.local.set({
          user_id: userId,    // Clé officielle (snake_case)
          userId: userId,     // Compatibilité (camelCase) - à supprimer après migration
          userIdEmail: email  
        });

        console.log('✅ UserId généré et sauvegardé (user_id + userId)');
        return userId;
      } catch (error) {
        console.error('❌ Erreur getOrGenerateUserId:', error);
        throw error;
      }
    }

    /**
     * Nettoie le userId du storage (lors de la déconnexion)
     */
    async clearUserId() {
      try {
        await chrome.storage.local.remove(['user_id', 'userId', 'userIdEmail']);
        console.log('🧹 UserId nettoyé du storage');
      } catch (error) {
        console.error('❌ Erreur clearUserId:', error);
      }
    }

    /**
     * Récupère le userId actuel (sans le générer)
     * @returns {Promise<string|null>} - UserId ou null si absent
     */
    async getUserId() {
      try {
        const stored = await chrome.storage.local.get(['user_id', 'userId']);
        // Lire user_id en priorité, fallback sur userId
        return stored.user_id || stored.userId || null;
      } catch (error) {
        console.error('❌ Erreur getUserId:', error);
        return null;
      }
    }
  }

  // Créer une instance globale unique
  window.userIdUtils = window.userIdUtils || new UserIdUtils();

  console.log('✅ UserIdUtils chargé');
})();
