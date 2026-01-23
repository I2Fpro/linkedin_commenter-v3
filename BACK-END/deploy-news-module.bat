@echo off
REM Script de déploiement du module News pour LinkedIn AI Commenter
REM Ce script reconstruit la stack Docker avec les migrations News

echo ========================================
echo   DEPLOIEMENT MODULE NEWS
echo ========================================
echo.

echo [1/3] Arret des conteneurs existants...
docker-compose down --volumes
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Docker n'est pas demarré ou docker-compose a echoue
    echo Veuillez demarrer Docker Desktop et reessayer
    pause
    exit /b 1
)

echo.
echo [2/3] Reconstruction des images Docker...
docker-compose build --no-cache
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Echec de la construction des images
    pause
    exit /b 1
)

echo.
echo [3/3] Demarrage des services...
docker-compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Echec du demarrage des services
    pause
    exit /b 1
)

echo.
echo ========================================
echo   DEPLOIEMENT REUSSI !
echo ========================================
echo.
echo Services demarres :
docker-compose ps

echo.
echo Verification de la migration...
timeout /t 5 /nobreak >nul
docker exec linkedin_ai_postgres psql -U linkedin_user -d linkedin_ai_db -c "\dt"

echo.
echo Verification de l'extension pgvector...
docker exec linkedin_ai_postgres psql -U linkedin_user -d linkedin_ai_db -c "SELECT * FROM pg_extension WHERE extname='vector';"

echo.
echo ========================================
echo   TEST DES ENDPOINTS
echo ========================================
echo.

echo Test du health check AI Service...
timeout /t 3 /nobreak >nul
curl -s http://localhost:8443/health

echo.
echo.
echo Test du health check User Service...
curl -s http://localhost:8444/health

echo.
echo.
echo ========================================
echo   DEPLOIEMENT TERMINE
echo ========================================
echo.
echo Pour tester le module News :
echo   GET  http://localhost:8443/news/health
echo   POST http://localhost:8443/news/register
echo   POST http://localhost:8443/news/vector-search
echo.
echo Pour voir les logs :
echo   docker-compose logs -f ai-service
echo.

pause
