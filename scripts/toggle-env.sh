#!/bin/bash
# =============================================================================
# toggle-env.sh - Bascule le FRONT-END entre mode PLACEHOLDER et mode DEV
# =============================================================================
#
# Usage (depuis Git Bash, a la racine du repo) :
#
#   bash GIT/scripts/toggle-env.sh dev          # Injecte les URLs locales
#   bash GIT/scripts/toggle-env.sh placeholder  # Restaure les __PLACEHOLDERS__
#   bash GIT/scripts/toggle-env.sh status       # Affiche le mode actuel
#
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/../FRONT-END"

# ---------------------------------------------------------------------------
# Mapping : PLACEHOLDER -> valeur DEV locale
# ---------------------------------------------------------------------------
# Ordre : du plus long au plus court (evite les remplacements partiels)
# NOTE: On utilise localhost directement (pas Traefik) pour eviter les problemes
#       CORS avec les extensions Chrome. Traefik ne gere pas bien les wildcards
#       chrome-extension://* dans Access-Control-Allow-Origin.
PLACEHOLDERS=(
  "__GOOGLE_CLIENT_ID__"
  "__USERS_API_URL__"
  "__AI_API_URL__"
  "__SITE_URL__"
)

DEV_VALUES=(
  "192205751398-29e500ilsol48ccvmp8dnoberc6kf1en.apps.googleusercontent.com"
  "http://localhost:8444"
  "http://localhost:8443"
  "http://localhost:8080"
)

# ---------------------------------------------------------------------------
# Fichiers front-end concernes
# ---------------------------------------------------------------------------
SITE_DIR="$SCRIPT_DIR/../SITE-INTERNET"

FILES=(
  "$FRONTEND_DIR/api-config.js"
  "$FRONTEND_DIR/manifest.json"
  "$FRONTEND_DIR/config.js"
  "$FRONTEND_DIR/shared_env.js"
  "$FRONTEND_DIR/auth.js"
  "$FRONTEND_DIR/background.js"
  "$FRONTEND_DIR/popup.js"
  "$FRONTEND_DIR/test-connection.html"
  "$SITE_DIR/admin/admin.js"
  "$SITE_DIR/account/login.html"
  "$SITE_DIR/account/subscription.html"
  "$SITE_DIR/checkout-intent.html"
  "$SITE_DIR/index.html"
)

# ---------------------------------------------------------------------------
# Detection du mode actuel
# ---------------------------------------------------------------------------
detect_mode() {
  if grep -q "__AI_API_URL__" "$FRONTEND_DIR/api-config.js" 2>/dev/null; then
    echo "placeholder"
  elif grep -q "localhost:8443" "$FRONTEND_DIR/api-config.js" 2>/dev/null; then
    echo "dev"
  else
    echo "unknown"
  fi
}

# ---------------------------------------------------------------------------
# PLACEHOLDER -> DEV
# ---------------------------------------------------------------------------
to_dev() {
  local total=0
  for file in "${FILES[@]}"; do
    [ -f "$file" ] || continue
    for i in "${!PLACEHOLDERS[@]}"; do
      local ph="${PLACEHOLDERS[$i]}"
      local val="${DEV_VALUES[$i]}"
      local hits
      hits=$(grep -c "$ph" "$file" 2>/dev/null || true)
      if [ "$hits" -gt 0 ]; then
        sed -i "s|${ph}|${val}|g" "$file"
        total=$((total + hits))
      fi
    done
  done
  echo "Mode DEV active ($total remplacements dans ${#FILES[@]} fichiers)"
}

# ---------------------------------------------------------------------------
# DEV -> PLACEHOLDER
# ---------------------------------------------------------------------------
to_placeholder() {
  local total=0
  for file in "${FILES[@]}"; do
    [ -f "$file" ] || continue
    for i in "${!PLACEHOLDERS[@]}"; do
      local ph="${PLACEHOLDERS[$i]}"
      local val="${DEV_VALUES[$i]}"
      local hits
      hits=$(grep -c "$val" "$file" 2>/dev/null || true)
      if [ "$hits" -gt 0 ]; then
        sed -i "s|${val}|${ph}|g" "$file"
        total=$((total + hits))
      fi
    done
  done
  echo "Mode PLACEHOLDER restaure ($total remplacements dans ${#FILES[@]} fichiers)"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
MODE="${1:-status}"
CURRENT=$(detect_mode)

case "$MODE" in
  dev)
    if [ "$CURRENT" = "dev" ]; then
      echo "Deja en mode DEV - rien a faire"
      exit 0
    fi
    to_dev
    echo "Extension prete pour le dev local."
    ;;
  placeholder)
    if [ "$CURRENT" = "placeholder" ]; then
      echo "Deja en mode PLACEHOLDER - rien a faire"
      exit 0
    fi
    to_placeholder
    echo "Extension prete pour le commit / CI."
    ;;
  status)
    echo "Mode actuel : $(echo "$CURRENT" | tr '[:lower:]' '[:upper:]')"
    ;;
  *)
    echo "Usage: $0 {dev|placeholder|status}"
    echo ""
    echo "  dev          Injecte les URLs locales (http://localhost:PORT)"
    echo "  placeholder  Restaure les __PLACEHOLDERS__ (pour commit)"
    echo "  status       Affiche le mode actuel"
    exit 1
    ;;
esac
