from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel

from database import get_db
from models import User, UsageLog
from schemas.user import PermissionsResponse, FeatureAccess, QuotaStatus
from auth import get_current_user, find_user_by_email
from utils.quota_manager import QuotaManager
from utils.feature_flags import FEATURES

router = APIRouter()

class PermissionCheckRequest(BaseModel):
    email: str
    feature: str

class ActionValidationRequest(BaseModel):
    email: str
    feature: str
    metadata: Dict[str, Any] = None

@router.get("/check", response_model=PermissionsResponse)
async def check_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vérifier les permissions générales de l'utilisateur"""
    quota_manager = QuotaManager(db)
    remaining_quota = quota_manager.get_remaining_quota(current_user.id)
    
    role_features = FEATURES.get(current_user.role.value, FEATURES["FREE"])
    daily_limit = role_features["daily_generations"]
    
    allowed = remaining_quota > 0 or daily_limit == -1
    
    return PermissionsResponse(
        role=current_user.role,
        daily_limit=daily_limit,
        remaining_quota=remaining_quota,
        features=role_features,
        allowed=allowed,
        message="Accès autorisé" if allowed else "Limite quotidienne atteinte"
    )

@router.post("/validate-action", response_model=PermissionsResponse)
async def validate_action(
    request: ActionValidationRequest,
    db: Session = Depends(get_db)
):
    """Valider une action spécifique pour un utilisateur donné"""
    user = find_user_by_email(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    quota_manager = QuotaManager(db)
    role_features = FEATURES.get(user.role.value, FEATURES["FREE"])
    
    if request.feature == "generate_comment":
        daily_limit = role_features["daily_generations"]
        remaining_quota = quota_manager.get_remaining_quota(user.id)
        
        if daily_limit != -1 and remaining_quota <= 0:
            return PermissionsResponse(
                role=user.role,
                daily_limit=daily_limit,
                remaining_quota=0,
                features=role_features,
                allowed=False,
                message="Limite quotidienne de génération atteinte"
            )
        
        # Ne pas incrémenter automatiquement l'usage ici
        # L'usage sera incrémenté via l'endpoint /record-usage après une génération réussie
        remaining_quota = quota_manager.get_remaining_quota(user.id)
        
        return PermissionsResponse(
            role=user.role,
            daily_limit=daily_limit,
            remaining_quota=remaining_quota,
            features=role_features,
            allowed=True,
            message="Action autorisée"
        )
    
    elif request.feature in ["custom_prompt", "refine_enabled", "resize_enabled", "include_quote"]:
        feature_enabled = role_features.get(request.feature, False)
        
        return PermissionsResponse(
            role=user.role,
            daily_limit=role_features["daily_generations"],
            remaining_quota=quota_manager.get_remaining_quota(user.id),
            features=role_features,
            allowed=feature_enabled,
            message=f"Fonctionnalité {'disponible' if feature_enabled else 'non disponible'} pour votre plan"
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fonctionnalité inconnue: {request.feature}"
        )

@router.get("/quota-status", response_model=QuotaStatus)
async def get_quota_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer le statut détaillé du quota"""
    quota_manager = QuotaManager(db)
    
    role_features = FEATURES.get(current_user.role.value, FEATURES["FREE"])
    daily_limit = role_features["daily_generations"]
    used_today = quota_manager.get_daily_usage(current_user.id)
    remaining = quota_manager.get_remaining_quota(current_user.id)
    
    return QuotaStatus(
        daily_limit=daily_limit,
        used_today=used_today,
        remaining=remaining,
        reset_time=quota_manager.get_next_reset_time()
    )

class RecordUsageRequest(BaseModel):
    email: str
    feature: str
    metadata: Dict[str, Any] = None

@router.post("/record-usage")
async def record_usage(
    request: RecordUsageRequest,
    db: Session = Depends(get_db)
):
    """Enregistrer l'utilisation d'une fonctionnalité après une action réussie"""
    user = find_user_by_email(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    quota_manager = QuotaManager(db)
    success = quota_manager.increment_usage(user.id, request.feature, request.metadata)
    
    if success:
        remaining_quota = quota_manager.get_remaining_quota(user.id)
        role_features = FEATURES.get(user.role.value, FEATURES["FREE"])
        
        return {
            "success": True,
            "remaining_quota": remaining_quota,
            "daily_limit": role_features["daily_generations"],
            "message": "Usage enregistré avec succès"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible d'enregistrer l'usage - limite atteinte"
        )

@router.get("/feature-access/{feature_name}", response_model=FeatureAccess)
async def check_feature_access(
    feature_name: str,
    current_user: User = Depends(get_current_user)
):
    """Vérifier l'accès à une fonctionnalité spécifique"""
    role_features = FEATURES.get(current_user.role.value, FEATURES["FREE"])
    
    if feature_name in role_features:
        feature_value = role_features[feature_name]
        
        if isinstance(feature_value, bool):
            return FeatureAccess(
                feature_name=feature_name,
                allowed=feature_value,
                reason=f"Fonctionnalité {'incluse' if feature_value else 'non incluse'} dans le plan {current_user.role.value}"
            )
        elif isinstance(feature_value, list):
            return FeatureAccess(
                feature_name=feature_name,
                allowed=len(feature_value) > 0,
                reason=f"Options disponibles: {', '.join(feature_value)}"
            )
        elif isinstance(feature_value, int):
            if feature_value == -1:
                return FeatureAccess(
                    feature_name=feature_name,
                    allowed=True,
                    reason="Accès illimité"
                )
            else:
                return FeatureAccess(
                    feature_name=feature_name,
                    allowed=feature_value > 0,
                    reason=f"Limite: {feature_value}"
                )
    
    return FeatureAccess(
        feature_name=feature_name,
        allowed=False,
        reason="Fonctionnalité non reconnue"
    )