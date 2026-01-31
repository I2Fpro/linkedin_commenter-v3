"""
Router blacklist - Story 2.1/2.2 Epic 2.
CRUD pour la gestion de la blacklist utilisateur Premium.
"""
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from models import User, BlacklistEntry
from schemas.blacklist import (
    BlacklistEntryCreate,
    BlacklistEntryResponse,
    BlacklistListResponse,
    BlacklistCheckResponse
)
from utils.feature_flags import is_feature_enabled

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=BlacklistEntryResponse, status_code=status.HTTP_201_CREATED)
async def add_to_blacklist(
    entry: BlacklistEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ajoute une personne a la blacklist de l'utilisateur.
    Requiert le plan Premium.
    """
    # Verifier le plan Premium
    if not is_feature_enabled(current_user.role.value, "blacklist"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La blacklist est reservee au plan Premium"
        )

    # Verifier si l'entree existe deja (meme nom)
    existing = db.query(BlacklistEntry).filter(
        BlacklistEntry.user_id == current_user.id,
        BlacklistEntry.blocked_name == entry.blocked_name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ALREADY_EXISTS", "message": "Cette personne est deja dans votre blacklist"}
        )

    # Creer l'entree
    new_entry = BlacklistEntry(
        user_id=current_user.id,
        blocked_name=entry.blocked_name,
        blocked_profile_url=entry.blocked_profile_url
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    logger.info(f"Blacklist: utilisateur {current_user.id} a ajoute {entry.blocked_name}")
    return new_entry


@router.get("/", response_model=BlacklistListResponse)
async def get_blacklist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Recupere la liste complete de la blacklist de l'utilisateur.
    Requiert le plan Premium.
    """
    # Verifier le plan Premium
    if not is_feature_enabled(current_user.role.value, "blacklist"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La blacklist est reservee au plan Premium"
        )

    entries = db.query(BlacklistEntry).filter(
        BlacklistEntry.user_id == current_user.id
    ).order_by(BlacklistEntry.created_at.desc()).all()

    return BlacklistListResponse(entries=entries, count=len(entries))


@router.get("/check/{blocked_name}", response_model=BlacklistCheckResponse)
async def check_blacklist(
    blocked_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verifie si une personne est dans la blacklist.
    Utilise pour le warning pre-generation (Story 2.3).
    Pour les utilisateurs non-Premium, retourne toujours False.
    """
    if not is_feature_enabled(current_user.role.value, "blacklist"):
        return BlacklistCheckResponse(is_blacklisted=False, blocked_name=blocked_name)

    exists = db.query(BlacklistEntry).filter(
        BlacklistEntry.user_id == current_user.id,
        BlacklistEntry.blocked_name == blocked_name
    ).first() is not None

    return BlacklistCheckResponse(is_blacklisted=exists, blocked_name=blocked_name)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_blacklist(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprime une personne de la blacklist de l'utilisateur.
    Requiert le plan Premium.
    Story 2.2 - Suppression blacklist.
    """
    # Verifier le plan Premium
    if not is_feature_enabled(current_user.role.value, "blacklist"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La blacklist est reservee au plan Premium"
        )

    # Trouver l'entree avec DOUBLE condition (entry_id + user_id) pour isolation donnees
    entry = db.query(BlacklistEntry).filter(
        BlacklistEntry.id == entry_id,
        BlacklistEntry.user_id == current_user.id
    ).first()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entree non trouvee dans votre blacklist"
        )

    blocked_name = entry.blocked_name
    db.delete(entry)
    db.commit()

    logger.info(f"Blacklist: utilisateur {current_user.id} a retire {blocked_name}")
    return None  # 204 No Content
