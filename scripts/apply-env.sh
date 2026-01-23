#!/bin/bash
# apply-env.sh - Remplace les placeholders par les valeurs des variables d'environnement
# Usage: ./apply-env.sh <directory>
# Les variables d'environnement doivent être définies avant l'appel

set -e

DIR="${1:-.}"

echo "Applying environment variables to $DIR..."

# Liste des placeholders à remplacer
declare -A PLACEHOLDERS=(
    ["__AI_API_URL__"]="${AI_API_URL}"
    ["__USERS_API_URL__"]="${USERS_API_URL}"
    ["__SITE_URL__"]="${SITE_URL}"
    ["__GOOGLE_CLIENT_ID__"]="${GOOGLE_CLIENT_ID}"
    ["__GOOGLE_CLIENT_ID_WEB__"]="${GOOGLE_CLIENT_ID_WEB}"
    ["__STRIPE_WEBHOOK_SECRET__"]="${STRIPE_WEBHOOK_SECRET}"
    ["__STRIPE_SUCCESS_URL__"]="${SITE_URL}/success?session_id={CHECKOUT_SESSION_ID}"
    ["__STRIPE_CANCEL_URL__"]="${SITE_URL}/cancel"
    ["__STRIPE_PORTAL_RETURN_URL__"]="${SITE_URL}/account/subscription"
    ["__ALLOWED_ORIGINS__"]="${AI_API_URL},${USERS_API_URL},${SITE_URL},chrome-extension://*"
    ["__CORS_CREDENTIALS__"]="true"
    ["__AI_API_HOST__"]="${AI_API_HOST:-$(echo $AI_API_URL | sed 's|https://||')}"
    ["__USERS_API_HOST__"]="${USERS_API_HOST:-$(echo $USERS_API_URL | sed 's|https://||')}"
    ["__SITE_HOST__"]="${SITE_HOST:-$(echo $SITE_URL | sed 's|https://||')}"
)

# Compteurs
total_files=0
total_replacements=0

# Trouver et remplacer dans tous les fichiers
while IFS= read -r -d '' file; do
    file_modified=false

    for placeholder in "${!PLACEHOLDERS[@]}"; do
        value="${PLACEHOLDERS[$placeholder]}"
        if [ -n "$value" ]; then
            # Compter les occurrences avant remplacement
            count=$(grep -o "$placeholder" "$file" 2>/dev/null | wc -l)
            if [ "$count" -gt 0 ]; then
                sed -i "s|${placeholder}|${value}|g" "$file"
                total_replacements=$((total_replacements + count))
                file_modified=true
            fi
        fi
    done

    if [ "$file_modified" = true ]; then
        total_files=$((total_files + 1))
        echo "  Modified: $file"
    fi
done < <(find "$DIR" -type f \( \
    -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \
    -o -name "*.py" -o -name "*.html" -o -name "*.css" -o -name "*.json" \
    -o -name "*.yml" -o -name "*.yaml" -o -name ".env*" \) \
    -not -path "*/node_modules/*" \
    -not -path "*/.git/*" \
    -not -path "*/venv/*" \
    -not -path "*/__pycache__/*" \
    -print0)

echo ""
echo "Environment applied successfully!"
echo "  Files modified: $total_files"
echo "  Total replacements: $total_replacements"
