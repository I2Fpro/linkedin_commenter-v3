/**
 * Bridge pour exposer PostHog dans le contexte de la page web
 * Ce script est injecté dans la page pour permettre les tests depuis la console
 */

// Créer un pont de communication entre le content script et la page
(function() {
  'use strict';

  // Exposer une fonction de test globale accessible depuis la console
  window.__testPostHog = function(eventName, properties = {}) {
    console.log('🧪 Test PostHog via Bridge...');

    // Envoyer un message au content script
    window.postMessage({
      type: 'POSTHOG_TEST_EVENT',
      eventName: eventName || 'test_event',
      properties: {
        ...properties,
        source: 'page_bridge',
        timestamp: new Date().toISOString()
      }
    }, '*');

    console.log('✅ Message envoyé au content script');
  };

  // Exposer une fonction pour voir la config PostHog
  window.__getPostHogConfig = function() {
    window.postMessage({
      type: 'POSTHOG_GET_CONFIG'
    }, '*');
  };

  // Écouter les réponses du content script
  window.addEventListener('message', (event) => {
    if (event.source !== window) return;

    if (event.data.type === 'POSTHOG_CONFIG_RESPONSE') {
      console.log('📊 PostHog Configuration:', event.data.config);
    } else if (event.data.type === 'POSTHOG_EVENT_SENT') {
      console.log('✅ PostHog Event Captured:', event.data);
    }
  });

  console.log('✅ PostHog Bridge chargé!');
  console.log('📝 Utiliser: __testPostHog("mon_event", {prop: "value"})');
  console.log('📝 Utiliser: __getPostHogConfig()');
})();
