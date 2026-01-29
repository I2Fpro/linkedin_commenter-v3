#!/bin/bash
# =============================================================================
# rebuild-backend.sh - Rebuild les services backend avec version timestampee
# =============================================================================
#
# Usage:
#   bash GIT/scripts/rebuild-backend.sh              # Rebuild tous les services
#   bash GIT/scripts/rebuild-backend.sh ai-service   # Rebuild seulement ai-service
#   bash GIT/scripts/rebuild-backend.sh user-service # Rebuild seulement user-service
#
# La version est generee automatiquement: X.Y.Z.HHMM (timestamp)
# Exemple: 10.3.0.1842 = version 10.3.0, build a 18h42
#
# Ce script synchronise automatiquement:
#   - manifest.json (frontend)
#   - ai-service (backend)
#   - user-service (backend)
#
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_DIR="$SCRIPT_DIR/.."
BACKEND_DIR="$GIT_DIR/BACK-END"
VERSION_FILE="$GIT_DIR/VERSION"
MANIFEST_FILE="$GIT_DIR/FRONT-END/manifest.json"
ENV_FILE="$BACKEND_DIR/.env.local"
COMPOSE_FILE="$BACKEND_DIR/docker-compose.dev.yml"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Lire la version de base
read_base_version() {
    if [ -f "$VERSION_FILE" ]; then
        cat "$VERSION_FILE" | tr -d '\n\r'
    else
        echo "0.0.0"
    fi
}

# Generer la version dev avec timestamp
generate_dev_version() {
    local base_version=$(read_base_version)
    local timestamp=$(date +%H%M)
    echo "${base_version}.${timestamp}"
}

# Mettre a jour manifest.json avec la version dev
update_manifest() {
    local version="$1"
    if [ -f "$MANIFEST_FILE" ]; then
        if command -v jq &> /dev/null; then
            jq --arg v "$version" '.version = $v' "$MANIFEST_FILE" > "$MANIFEST_FILE.tmp"
            mv "$MANIFEST_FILE.tmp" "$MANIFEST_FILE"
        else
            sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$version\"/" "$MANIFEST_FILE"
        fi
        echo -e "${GREEN}manifest.json${NC}: $version"
    fi
}

# Verifier les prerequis
check_prerequisites() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo -e "${RED}Erreur${NC}: $COMPOSE_FILE non trouve"
        exit 1
    fi
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}Erreur${NC}: $ENV_FILE non trouve"
        exit 1
    fi
}

# Main
SERVICE="${1:-all}"
DEV_VERSION=$(generate_dev_version)

echo -e "${CYAN}=== Rebuild Backend ===${NC}"
echo -e "Version: ${GREEN}$DEV_VERSION${NC}"
echo ""

check_prerequisites

# Synchroniser manifest.json avec la meme version
update_manifest "$DEV_VERSION"
echo ""

cd "$BACKEND_DIR"

case "$SERVICE" in
    ai-service|ai)
        echo -e "${YELLOW}Building ai-service...${NC}"
        docker compose -f docker-compose.dev.yml --env-file .env.local build \
            --build-arg APP_VERSION="$DEV_VERSION" \
            ai-service
        echo -e "${YELLOW}Starting ai-service...${NC}"
        docker compose -f docker-compose.dev.yml --env-file .env.local up -d ai-service
        ;;
    user-service|user)
        echo -e "${YELLOW}Building user-service...${NC}"
        docker compose -f docker-compose.dev.yml --env-file .env.local build \
            --build-arg APP_VERSION="$DEV_VERSION" \
            user-service
        echo -e "${YELLOW}Starting user-service...${NC}"
        docker compose -f docker-compose.dev.yml --env-file .env.local up -d user-service
        ;;
    all|"")
        echo -e "${YELLOW}Building all services...${NC}"
        docker compose -f docker-compose.dev.yml --env-file .env.local build \
            --build-arg APP_VERSION="$DEV_VERSION" \
            ai-service user-service
        echo -e "${YELLOW}Starting all services...${NC}"
        docker compose -f docker-compose.dev.yml --env-file .env.local up -d
        ;;
    *)
        echo -e "${RED}Erreur${NC}: Service inconnu '$SERVICE'"
        echo "Usage: $0 [ai-service|user-service|all]"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Done!${NC} Version deployee: ${GREEN}$DEV_VERSION${NC}"
echo ""
echo "Tous les composants sont synchronises:"
echo "  - Frontend (manifest.json): $DEV_VERSION"
echo "  - AI Service: $DEV_VERSION"
echo "  - User Service: $DEV_VERSION"
echo ""
echo "Verifier avec:"
echo "  curl https://ai.local.dev/health | jq .version"
echo "  docker logs linkedin_ai_service | grep 'Backend'"
