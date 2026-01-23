#!/bin/bash
# Script: check_services.sh
# Description: Vérifie l'état des services backend et notifie Discord en cas de panne.

# Récupération du répertoire du script et chargement des variables d'environnement depuis .env
SCRIPT_DIR="$(dirname "$0")"
if [ -f "$SCRIPT_DIR/.env" ]; then
    # Charge les variables DISCORD_WEBHOOK_URL, AI_SERVICE_URL, USER_SERVICE_URL
    source "$SCRIPT_DIR/.env"
fi

# Liste des URLs de services à surveiller (séparées par des espaces)
SERVICES="$AI_SERVICE_URL $USER_SERVICE_URL"

# Pour chaque service, on effectue une requête HTTP HEAD pour obtenir le code de réponse
for URL in $SERVICES; do
    # Exécute une requête HTTP silencieuse, ne télécharge pas le corps, suit les redirections, retourne le code HTTP
    STATUS_CODE=$(curl -o /dev/null -s -w "%{http_code}" -L "$URL")
    
    # Si le code HTTP n'est pas 200 (OK), on envoie une alerte sur Discord
    if [[ "$STATUS_CODE" -ne 200 ]]; then
        MESSAGE=":red_circle: Le service \`$URL\` est injoignable (code $STATUS_CODE)"
        # Envoie la notification au webhook Discord au format JSON
        curl -H "Content-Type: application/json" -X POST -d "{\"content\":\"$MESSAGE\"}" "$DISCORD_WEBHOOK_URL"
    fi
    # (Si besoin, on pourrait ajouter un else avec un log local indiquant que $URL fonctionne normalement)
done
