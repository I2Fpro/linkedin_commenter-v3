from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
import httpx
import os
import uuid
import json
from datetime import datetime, timezone

from database import get_db
from models import User
from auth import create_user_token, AuthManager
from schemas.user import UserResponse
from utils.trial_manager import TrialManager

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

        # Phase 2 — Fallback: verifier l'expiration du trial au login
        try:
            TrialManager.check_user_trial_inline(db, user)
            db.refresh(user)
        except Exception:
            pass  # Non-blocking: le login continue normalement

        # Mettre à jour le nom si nécessaire
        if not user.name and google_user_info.get("name"):
            user.name = google_user_info["name"]
            db.commit()
            db.refresh(user)

        # Créer le token JWT
        access_token = create_user_token(user)

        # Track login event
        try:
            db.execute(
                text("""
                    INSERT INTO analytics.events (id, user_id, event_type, properties, timestamp)
                    VALUES (:id, :user_id, :event_type, CAST(:properties AS jsonb), :timestamp)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "user_id": str(user.id),
                    "event_type": "login",
                    "properties": json.dumps({"method": "google", "role": str(user.role.value) if hasattr(user.role, 'value') else str(user.role)}),
                    "timestamp": datetime.now(timezone.utc),
                }
            )
            db.commit()
        except Exception as e:
            # Non-blocking analytics tracking
            db.rollback()
            pass

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