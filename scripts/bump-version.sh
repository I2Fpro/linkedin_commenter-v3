#!/bin/bash
# =============================================================================
# bump-version.sh - Gestion unifiee des versions pour LinkedIn AI Commenter
# =============================================================================
#
# Usage:
#   bash GIT/scripts/bump-version.sh status     # Affiche version actuelle
#   bash GIT/scripts/bump-version.sh patch      # X.Y.Z -> X.Y.Z+1
#   bash GIT/scripts/bump-version.sh minor      # X.Y.Z -> X.Y+1.0
#   bash GIT/scripts/bump-version.sh major      # X.Y.Z -> X+1.0.0
#   bash GIT/scripts/bump-version.sh set 1.2.3  # Definir version specifique
#   bash GIT/scripts/bump-version.sh dev        # X.Y.Z.HHMM (manifest only, pour dev local)
#
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_DIR="$SCRIPT_DIR/.."
VERSION_FILE="$GIT_DIR/VERSION"
MANIFEST_FILE="$GIT_DIR/FRONT-END/manifest.json"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Lire la version actuelle
read_version() {
    if [ -f "$VERSION_FILE" ]; then
        cat "$VERSION_FILE" | tr -d '\n\r'
    else
        echo "0.0.0"
    fi
}

# Ecrire la version dans tous les fichiers
write_version() {
    local version="$1"

    # Ecrire dans VERSION
    echo "$version" > "$VERSION_FILE"
    echo -e "${GREEN}VERSION${NC}: $version"

    # Mettre a jour manifest.json
    if [ -f "$MANIFEST_FILE" ]; then
        if command -v jq &> /dev/null; then
            jq --arg v "$version" '.version = $v' "$MANIFEST_FILE" > "$MANIFEST_FILE.tmp"
            mv "$MANIFEST_FILE.tmp" "$MANIFEST_FILE"
        else
            # Fallback: sed
            sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$version\"/" "$MANIFEST_FILE"
        fi
        echo -e "${GREEN}manifest.json${NC}: $version"
    fi
}

# Parser les composants de la version
parse_version() {
    local version="$1"
    IFS='.' read -ra PARTS <<< "$version"
    MAJOR="${PARTS[0]:-0}"
    MINOR="${PARTS[1]:-0}"
    PATCH="${PARTS[2]:-0}"
}

# Ecrire la version DEV uniquement dans manifest.json (pas dans VERSION)
write_dev_version() {
    local version="$1"

    # Mettre a jour manifest.json SEULEMENT
    if [ -f "$MANIFEST_FILE" ]; then
        if command -v jq &> /dev/null; then
            jq --arg v "$version" '.version = $v' "$MANIFEST_FILE" > "$MANIFEST_FILE.tmp"
            mv "$MANIFEST_FILE.tmp" "$MANIFEST_FILE"
        else
            # Fallback: sed
            sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$version\"/" "$MANIFEST_FILE"
        fi
        echo -e "${GREEN}manifest.json${NC}: $version"
        echo -e "${YELLOW}Note${NC}: VERSION file inchange ($CURRENT)"
    fi
}

# Afficher l'usage
usage() {
    echo "Usage: $0 {status|patch|minor|major|set VERSION|dev}"
    echo ""
    echo "Commands:"
    echo "  status    Affiche la version actuelle"
    echo "  patch     Incremente patch: X.Y.Z -> X.Y.Z+1"
    echo "  minor     Incremente minor: X.Y.Z -> X.Y+1.0"
    echo "  major     Incremente major: X.Y.Z -> X+1.0.0"
    echo "  set VER   Definit une version specifique"
    echo "  dev       Version dev avec timestamp: X.Y.Z.HHMM (manifest only)"
    exit 1
}

# Main
ACTION="${1:-status}"
CURRENT=$(read_version)
parse_version "$CURRENT"

case "$ACTION" in
    status)
        echo -e "${YELLOW}Version actuelle${NC}: $CURRENT"
        echo "  Major: $MAJOR"
        echo "  Minor: $MINOR"
        echo "  Patch: $PATCH"
        ;;
    patch)
        NEW_VERSION="$MAJOR.$MINOR.$((PATCH + 1))"
        echo -e "Bump patch: $CURRENT -> ${GREEN}$NEW_VERSION${NC}"
        write_version "$NEW_VERSION"
        ;;
    minor)
        NEW_VERSION="$MAJOR.$((MINOR + 1)).0"
        echo -e "Bump minor: $CURRENT -> ${GREEN}$NEW_VERSION${NC}"
        write_version "$NEW_VERSION"
        ;;
    major)
        NEW_VERSION="$((MAJOR + 1)).0.0"
        echo -e "Bump major: $CURRENT -> ${GREEN}$NEW_VERSION${NC}"
        write_version "$NEW_VERSION"
        ;;
    set)
        if [ -z "${2:-}" ]; then
            echo -e "${RED}Erreur${NC}: Version requise. Usage: $0 set X.Y.Z"
            exit 1
        fi
        NEW_VERSION="$2"
        echo -e "Set version: $CURRENT -> ${GREEN}$NEW_VERSION${NC}"
        write_version "$NEW_VERSION"
        ;;
    dev)
        TIMESTAMP=$(date +%H%M)
        DEV_VERSION="${CURRENT}.${TIMESTAMP}"
        echo -e "Dev version: ${GREEN}$DEV_VERSION${NC}"
        write_dev_version "$DEV_VERSION"
        ;;
    *)
        usage
        ;;
esac
