@echo off
REM Script de verification du module News
REM Verifie que tout est correctement installe et fonctionnel

echo ========================================
echo   VERIFICATION MODULE NEWS
echo ========================================
echo.

echo [1/6] Verification de l'etat des conteneurs...
docker-compose ps
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Docker n'est pas demarre
    pause
    exit /b 1
)

echo.
echo [2/6] Verification de l'extension pgvector...
docker exec linkedin_ai_postgres psql -U linkedin_user -d linkedin_ai_db -c "SELECT extname, extversion FROM pg_extension WHERE extname='vector';"
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Extension pgvector non trouvee
    pause
    exit /b 1
)

echo.
echo [3/6] Verification de la table news...
docker exec linkedin_ai_postgres psql -U linkedin_user -d linkedin_ai_db -c "\d news"
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Table news non trouvee
    pause
    exit /b 1
)

echo.
echo [4/6] Verification des index vectoriels...
docker exec linkedin_ai_postgres psql -U linkedin_user -d linkedin_ai_db -c "SELECT indexname FROM pg_indexes WHERE tablename='news';"

echo.
echo [5/6] Verification des fonctions SQL...
docker exec linkedin_ai_postgres psql -U linkedin_user -d linkedin_ai_db -c "SELECT proname, pronargs FROM pg_proc WHERE proname IN ('search_similar_news', 'cleanup_old_news');"

echo.
echo [6/6] Test des endpoints News...
echo.

echo Test GET /news/health...
curl -s http://localhost:8443/news/health
echo.
echo.

echo Test GET /news/debug/all...
curl -s http://localhost:8443/news/debug/all
echo.
echo.

echo ========================================
echo   VERIFICATION COMPLETE
echo ========================================
echo.
echo Le module News est pret a etre utilise !
echo.
echo Endpoints disponibles :
echo   - GET  /news/health         : Health check
echo   - GET  /news/debug/all      : Liste toutes les news
echo   - POST /news/register       : Enregistrer de nouvelles URLs
echo   - POST /news/vector-search  : Recherche semantique
echo.
echo Pour tester l'enregistrement d'une news :
echo   curl -X POST http://localhost:8443/news/register \
echo     -H "Content-Type: application/json" \
echo     -H "Authorization: Bearer YOUR_TOKEN" \
echo     -d "{\"urls\": [\"https://linkedin.com/news/story/123\"], \"lang\": \"fr\"}"
echo.

pause
