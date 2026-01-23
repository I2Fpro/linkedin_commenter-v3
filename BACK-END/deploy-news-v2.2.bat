@echo off
REM Script de déploiement du module News v2.2 pour Windows
REM Usage: deploy-news-v2.2.bat

setlocal enabledelayedexpansion

echo ========================================
echo Déploiement Module News v2.2
echo ========================================
echo.

REM 1. Vérifier Docker
echo [ETAPE] Vérification de Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Docker n'est pas installé
    exit /b 1
)
echo OK Docker installé
echo.

REM 2. Vérifier Docker Compose
echo [ETAPE] Vérification de Docker Compose...
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Docker Compose n'est pas installé
    exit /b 1
)
echo OK Docker Compose installé
echo.

REM 3. Vérifier .env
echo [ETAPE] Vérification du fichier .env...
if not exist ".env" (
    echo ERREUR: Fichier .env introuvable
    exit /b 1
)

REM Vérifier et ajouter les nouvelles variables si nécessaire
findstr /C:"NEWS_TTL_HOURS" .env >nul
if %errorlevel% neq 0 (
    echo NEWS_TTL_HOURS=48 >> .env
    echo OK Variable NEWS_TTL_HOURS ajoutée
)

findstr /C:"DEBUG_NEWS" .env >nul
if %errorlevel% neq 0 (
    echo DEBUG_NEWS=false >> .env
    echo OK Variable DEBUG_NEWS ajoutée
)

findstr /C:"MAX_NEWS_CONCURRENCY" .env >nul
if %errorlevel% neq 0 (
    echo MAX_NEWS_CONCURRENCY=5 >> .env
    echo OK Variable MAX_NEWS_CONCURRENCY ajoutée
)

findstr /C:"REDIS_URL" .env >nul
if %errorlevel% neq 0 (
    echo REDIS_URL=redis://redis:6379 >> .env
    echo OK Variable REDIS_URL ajoutée
)

echo OK Fichier .env vérifié
echo.

REM 4. Arrêter les conteneurs
echo [ETAPE] Arrêt des conteneurs existants...
docker-compose down
echo OK Conteneurs arrêtés
echo.

REM 5. Rebuild
echo [ETAPE] Reconstruction des images Docker...
docker-compose build --no-cache ai-service
echo OK Images reconstruites
echo.

REM 6. Démarrage
echo [ETAPE] Démarrage des services...
docker-compose up -d
echo OK Services démarrés
echo.

REM Attendre le démarrage
echo Attente du démarrage complet (30s)...
timeout /t 30 /nobreak >nul
echo.

REM 7. Health check
echo [ETAPE] Vérification du health check...
set MAX_RETRIES=5
set RETRY_COUNT=0

:health_check_loop
curl -f http://localhost:8443/news/health >nul 2>&1
if %errorlevel% equ 0 (
    echo OK Health check réussi
    goto health_check_done
)

set /a RETRY_COUNT+=1
if %RETRY_COUNT% geq %MAX_RETRIES% (
    echo ERREUR: Health check échoué après %MAX_RETRIES% tentatives
    exit /b 1
)

echo Tentative %RETRY_COUNT%/%MAX_RETRIES%...
timeout /t 5 /nobreak >nul
goto health_check_loop

:health_check_done
echo.

REM Afficher le résultat
echo Résultat du health check:
curl -s http://localhost:8443/news/health
echo.
echo.

REM 8. Vérifier Redis
echo [ETAPE] Vérification de Redis...
docker exec linkedin_ai_redis redis-cli PING | findstr "PONG" >nul
if %errorlevel% equ 0 (
    echo OK Redis connecté
) else (
    echo ATTENTION: Redis non connecté
)
echo.

REM 9. Vérifier PostgreSQL
echo [ETAPE] Vérification de PostgreSQL...
docker exec linkedin_ai_postgres pg_isready -U linkedin_user | findstr "accepting connections" >nul
if %errorlevel% equ 0 (
    echo OK PostgreSQL connecté
) else (
    echo ATTENTION: PostgreSQL non connecté
)
echo.

REM 10. Test d'une requête
echo [ETAPE] Test d'une requête d'enregistrement...
curl -s -X POST http://localhost:8443/news/register -H "Content-Type: application/json" -d "{\"urls\": [\"https://test-deploy.com/news/123\"], \"lang\": \"fr\"}"
echo.
echo OK Endpoint /news/register fonctionne
echo.

REM 11. Afficher les stats
echo [ETAPE] Récupération des statistiques...
curl -s http://localhost:8443/news/stats
echo.
echo.

REM 12. Résumé final
echo ========================================
echo DEPLOIEMENT TERMINE
echo ========================================
echo.
echo Services disponibles:
echo   - Health check: http://localhost:8443/news/health
echo   - Stats: http://localhost:8443/news/stats
echo   - Register: POST http://localhost:8443/news/register
echo   - Vector Search: POST http://localhost:8443/news/vector-search
echo   - Debug URL: http://localhost:8443/news/debug/{url}
echo   - Debug Logs: http://localhost:8443/news/debug/logs
echo.
echo Logs:
echo   - JSON: docker exec linkedin_ai_service cat /app/logs/news_logs.json
echo   - Debug: docker exec linkedin_ai_service cat /app/logs/news_debug.log
echo.
echo Commandes utiles:
echo   - Logs: docker-compose logs -f ai-service
echo   - Redis: docker exec -it linkedin_ai_redis redis-cli
echo   - PostgreSQL: docker exec -it linkedin_ai_postgres psql -U linkedin_user -d linkedin_ai_db
echo.
echo Module News v2.2 déployé avec succès !
echo.

pause
