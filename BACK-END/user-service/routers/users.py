from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from database import get_db
from models import User, UsageLog
from schemas.user import UserCreate, UserUpdate, UserResponse, PermissionsResponse, GoogleUserInfo, QuotaStatus
from auth import get_current_user, find_user_by_email
from utils.quota_manager import QuotaManager
from utils.feature_flags import FEATURES
from utils.role_manager import RoleManager
from utils.trial_manager import TrialManager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Enregistrer un nouvel utilisateur"""
    existing_user = find_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec cet email existe déjà"
        )

    if user_data.google_id:
        # Pour google_id, on peut utiliser un filtre direct car ce n'est pas chiffré de la même manière
        existing_google_user = db.query(User).filter(User.google_id == user_data.google_id).first()
        if existing_google_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un utilisateur avec ce Google ID existe déjà"
            )

    new_user = User(
        email=user_data.email,
        name=user_data.name,
        google_id=user_data.google_id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Récupérer le profil de l'utilisateur connecté"""
    return current_user

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour le profil de l'utilisateur"""
    update_data = user_update.dict(exclude_unset=True)

    # Gérer le changement de rôle séparément pour l'historique
    if 'role' in update_data:
        new_role = update_data.pop('role')
        try:
            RoleManager.change_user_role(
                db=db,
                user=current_user,
                new_role=new_role,
                changed_by=current_user.email,  # L'utilisateur modifie son propre rôle
                reason="Mise à jour du profil utilisateur"
            )
        except ValueError as e:
            # Le rôle est identique, on ignore
            pass

    # Mettre à jour les autres champs
    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    return current_user

@router.get("/permissions", response_model=PermissionsResponse)
async def get_user_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les permissions de l'utilisateur"""
    quota_manager = QuotaManager(db)
    remaining_quota = quota_manager.get_remaining_quota(current_user.id)
    
    role_features = FEATURES.get(current_user.role.value, FEATURES["FREE"])
    
    return PermissionsResponse(
        role=current_user.role,
        daily_limit=role_features["daily_generations"],
        remaining_quota=remaining_quota,
        features=role_features,
        allowed=remaining_quota > 0 or role_features["daily_generations"] == -1,
        message=f"Quota restant: {remaining_quota}" if remaining_quota > 0 else "Limite quotidienne atteinte"
    )

@router.post("/verify-google", response_model=UserResponse)
async def verify_google_user(
    google_info: GoogleUserInfo,
    db: Session = Depends(get_db)
):
    """Vérifier ou créer un utilisateur via Google OAuth"""
    user = db.query(User).filter(User.google_id == google_info.google_id).first()

    if not user:
        user = find_user_by_email(db, google_info.email)

        if user:
            user.google_id = google_info.google_id
            if not user.name:
                user.name = google_info.name
        else:
            user = User(
                email=google_info.email,
                name=google_info.name,
                google_id=google_info.google_id
            )
            db.add(user)

    db.commit()
    db.refresh(user)

    return user

@router.get("/quota-status", response_model=QuotaStatus)
async def get_quota_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer le statut du quota de l'utilisateur"""
    # Phase 2 — Fallback: verifier l'expiration du trial inline
    try:
        TrialManager.check_user_trial_inline(db, current_user)
        db.refresh(current_user)
    except Exception as e:
        logger.warning(f"Fallback trial check failed for user {current_user.id}: {e}")

    quota_manager = QuotaManager(db)
    
    role_features = FEATURES.get(current_user.role.value, FEATURES["FREE"])
    daily_limit = role_features["daily_generations"]
    used_today = quota_manager.get_daily_usage(current_user.id)
    remaining = quota_manager.get_remaining_quota(current_user.id)
    
    return QuotaStatus(
        user_id=current_user.id,
        role=current_user.role,
        daily_limit=daily_limit,
        used_today=used_today,
        remaining=remaining,
        reset_time=quota_manager.get_next_reset_time()
    )