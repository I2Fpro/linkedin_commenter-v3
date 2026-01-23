
"""
Middleware d'authentification Google (via token Bearer)
- Vérifie le token côté Google (endpoint userinfo)
- Expose un Depends get_current_user pour les routes protégées
"""

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from typing import Optional, Dict, Any
import logging
from config_py import GOOGLE_CLIENT_ID

logger = logging.getLogger(__name__)

GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
security = HTTPBearer(auto_error=False)

class GoogleAuthMiddleware:
    """
    Wrapper simplifié pour vérifier un token Google et obtenir les infos utilisateur.
    """
    def __init__(self):
        self.client_id = GOOGLE_CLIENT_ID
        self._http_client = None

    async def _get_http_client(self):
        """
        Retourne un client HTTP réutilisable (httpx.AsyncClient).
        """
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=10.0)
        return self._http_client

    async def verify_google_token(self, token: str) -> Dict[str, Any]:
        """
        Vérifie un token Google OU un token JWT de notre User Service.
        Lève HTTPException en cas d'échec/expiration.
        """
        # D'abord, essayer avec notre User Service (tokens JWT internes)
        try:
            from jose import jwt
            import os
            
            # Essayer de décoder comme token JWT interne
            JWT_SECRET = os.getenv("JWT_SECRET", "linkedin_ai_jwt_secret_key_very_secure_2024_minimum_32_chars")
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            
            if payload.get("sub"):  # Token JWT interne valide
                logger.info("Utilisateur authentifié via JWT interne: %s", payload.get("sub"))
                return {
                    "email": payload.get("sub"),
                    "name": payload.get("name"),
                    "id": payload.get("user_id"),
                    "role": payload.get("role"),
                    "auth_type": "jwt_internal"
                }
        except Exception as jwt_error:
            logger.debug("Token JWT interne invalide, essai avec Google: %s", jwt_error)
            
        # Si JWT interne échoue, essayer avec Google
        try:
            client = await self._get_http_client()
            response = await client.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {token}"})
            if response.status_code == 200:
                user_info = response.json()
                # Optionnel: vérifier la présence d'un email vérifié
                if not user_info.get("email"):
                    raise HTTPException(status_code=401, detail="Email absent dans le token Google")
                logger.info("Utilisateur authentifié via Google: %s", user_info.get("email"))
                user_info["auth_type"] = "google_oauth"
                return user_info
            elif response.status_code == 401:
                raise HTTPException(status_code=401, detail="Token expiré")
            else:
                raise HTTPException(status_code=401, detail="Token invalide")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Timeout Google API")
        except Exception as e:
            logger.error("Erreur vérification token: %s", e)
            raise HTTPException(status_code=401, detail="Erreur authentification") from e

    def get_client_id(self) -> str:
        """
        Retourne le Client ID Google (issu de l'environnement).
        """
        return self.client_id

    def clear_all_cache(self):
        """
        Méthode de compatibilité (aucun cache interne ici).
        """
        logger.info("Cache auth: noop (aucun cache interne)")

    async def close_http_client(self):
        """
        Ferme le client HTTP httpx si ouvert.
        """
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

# Instance globale utilisée par Depends
auth_middleware = GoogleAuthMiddleware()

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """
    Depends FastAPI: extrait le Bearer token et renvoie le user_info vérifié.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Token manquant")
    return await auth_middleware.verify_google_token(credentials.credentials)
