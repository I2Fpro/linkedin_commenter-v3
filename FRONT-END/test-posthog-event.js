/**
 * Script de test pour envoyer un événement PostHog
 * À exécuter dans la console DevTools de la page LinkedIn
 *
 * MÉTHODE 1: Utiliser le PostHog Bridge (RECOMMANDÉ)
 * MÉTHODE 2: Utiliser la console du content script
 */

// MÉTHODE 1: Via le PostHog Bridge (accessible depuis la console de la page)
console.log('🧪 Test PostHog via Bridge...');

// Vérifier que le bridge est disponible
if (typeof window.__testPostHog === 'undefined') {
  console.error('❌ PostHog Bridge non disponible. Assurez-vous que l\'extension est chargée et rechargez la page.');
  console.log('💡 Alternative: Ouvrez les DevTools > Console > Sélectionnez le contexte "chrome-extension://..." dans le menu déroulant');
} else {
  console.log('✅ PostHog Bridge détecté!');

  // Voir la configuration
  console.log('📊 Récupération de la configuration PostHog...');
  window.__getPostHogConfig();

  // Attendre 1 seconde puis envoyer un événement test
  setTimeout(() => {
    console.log('📤 Envoi d\'un événement test...');
    window.__testPostHog('test_event', {
      test_property: 'test_value',
      timestamp: new Date().toISOString(),
      source: 'bridge_test'
    });

    console.log('✅ Événement test envoyé!');
    console.log('⏳ Vérifiez les logs ci-dessus et PostHog dans quelques secondes...');
  }, 1000);
}

// MÉTHODE 2: Instructions pour la console du content script
console.log('\n📝 ALTERNATIVE: Test depuis la console du content script');
console.log('1. Ouvrez les DevTools (F12)');
console.log('2. Allez dans l\'onglet Console');
console.log('3. Dans le menu déroulant en haut (qui dit "top"), sélectionnez le contexte de l\'extension');
console.log('4. Tapez: posthogClient.capture("test_event", {test: "value"})');
console.log('\n');
