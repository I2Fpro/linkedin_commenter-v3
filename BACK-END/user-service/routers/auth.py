from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import httpx
import os

from database import get_db
from models import User
from auth import create_user_token, AuthManager
from schemas.user import UserResponse
from posthog_service import posthog_service

router = APIRouter()

class GoogleLoginRequest(BaseModel):
    google_token: str
    user_id: Optional[str] = None  # userId anonyme (SHA256) envoyé par le frontend

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

@router.post("/login", response_model=LoginResponse)
async def login_with_google(
    request: GoogleLoginRequest,
    db: Session = Depends(get_db)
):
    """Connexion avec un token Google OAuth"""
    try:
        # Vérifier le token Google en appelant l'API Google
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {request.google_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token Google invalide"
                )
            
            google_user_info = response.json()
        
        # Authentifier ou créer l'utilisateur
        is_new_user = False
        existing_user = None

        # Vérifier si l'utilisateur existe déjà
        try:
            from auth import find_user_by_email
            existing_user = find_user_by_email(db, google_user_info["email"])
            is_new_user = (existing_user is None)
        except:
            pass

        user = AuthManager.authenticate_user(
            email=google_user_info["email"],
            google_id=google_user_info.get("id") or google_user_info.get("sub"),
            name=google_user_info.get("name"),
            db=db
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Impossible de créer ou récupérer l'utilisateur"
            )

        # Mettre à jour le nom si nécessaire
        if not user.name and google_user_info.get("name"):
            user.name = google_user_info["name"]
            db.commit()
            db.refresh(user)

        # Track avec PostHog - Utiliser userId anonyme du frontend si disponible
        # Utiliser le userId anonyme (SHA256) envoyé par le frontend, sinon fallback sur DB user.id
        posthog_user_id = request.user_id if request.user_id else str(user.id)
        user_plan = getattr(user, 'plan', 'FREE') or 'FREE'
        user_role = getattr(user, 'role', None) or user_plan

        if is_new_user:
            posthog_service.track_user_registration(
                user_id=posthog_user_id,
                plan=user_plan,
                registration_method="google_oauth2"
            )
        else:
            posthog_service.track_user_login(
                user_id=posthog_user_id,
                plan=user_plan,
                role=user_role
            )

        # Créer le token JWT
        access_token = create_user_token(user)

        return LoginResponse(
            access_token=access_token,
            user=UserResponse.from_orm(user)
        )
        
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la vérification du token Google"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )

@router.post("/refresh")
async def refresh_access_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Rafraîchir un token d'accès"""
    new_token = AuthManager.refresh_token(refresh_token, db)
    return {"access_token": new_token, "token_type": "bearer"}