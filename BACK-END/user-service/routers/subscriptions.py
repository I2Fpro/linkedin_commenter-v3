from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from models import User, Subscription, UsageLog, RoleType
from schemas.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse, UpgradeRequest, UsageLogResponse
from schemas.user import RoleEnum
from auth import get_current_user
from utils.feature_flags import FEATURES

router = APIRouter()

@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer l'abonnement actuel de l'utilisateur"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "ACTIVE"
    ).first()
    
    if not subscription:
        subscription = Subscription(
            user_id=current_user.id,
            plan=current_user.role,
            status="ACTIVE"
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
    
    return subscription

@router.post("/upgrade", response_model=SubscriptionResponse)
async def upgrade_subscription(
    upgrade_request: UpgradeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à niveau l'abonnement de l'utilisateur"""
    role_hierarchy = {
        RoleEnum.FREE: 0,
        RoleEnum.MEDIUM: 1,
        RoleEnum.PREMIUM: 2
    }
    
    current_level = role_hierarchy.get(current_user.role, 0)
    target_level = role_hierarchy.get(upgrade_request.target_plan, 0)
    
    if target_level <= current_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de rétrograder ou de rester au même niveau"
        )
    
    current_subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "ACTIVE"
    ).first()
    
    if current_subscription:
        current_subscription.status = "CANCELLED"
    
    new_subscription = Subscription(
        user_id=current_user.id,
        plan=upgrade_request.target_plan,
        status="ACTIVE"
    )
    
    current_user.role = upgrade_request.target_plan
    
    db.add(new_subscription)
    db.commit()
    db.refresh(new_subscription)
    
    return new_subscription

@router.post("/downgrade", response_model=SubscriptionResponse)
async def downgrade_subscription(
    target_plan: RoleEnum,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rétrograder l'abonnement de l'utilisateur"""
    role_hierarchy = {
        RoleEnum.FREE: 0,
        RoleEnum.MEDIUM: 1,
        RoleEnum.PREMIUM: 2
    }
    
    current_level = role_hierarchy.get(current_user.role, 0)
    target_level = role_hierarchy.get(target_plan, 0)
    
    if target_level >= current_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de mettre à niveau ou de rester au même niveau"
        )
    
    current_subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "ACTIVE"
    ).first()
    
    if current_subscription:
        current_subscription.status = "CANCELLED"
    
    new_subscription = Subscription(
        user_id=current_user.id,
        plan=target_plan,
        status="ACTIVE"
    )
    
    current_user.role = target_plan
    
    db.add(new_subscription)
    db.commit()
    db.refresh(new_subscription)
    
    return new_subscription

@router.get("/features")
async def get_subscription_features(
    current_user: User = Depends(get_current_user)
):
    """Récupérer les fonctionnalités disponibles pour l'abonnement actuel"""
    role_features = FEATURES.get(current_user.role.value, FEATURES["FREE"])
    
    return {
        "role": current_user.role,
        "features": role_features,
        "available_upgrades": [
            role for role in ["MEDIUM", "PREMIUM"] 
            if role != current_user.role.value
        ]
    }

@router.get("/usage", response_model=List[UsageLogResponse])
async def get_usage_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer l'historique d'utilisation de l'utilisateur"""
    usage_logs = db.query(UsageLog).filter(
        UsageLog.user_id == current_user.id
    ).order_by(UsageLog.timestamp.desc()).limit(limit).all()
    
    return usage_logs

@router.get("/all", response_model=List[SubscriptionResponse])
async def get_all_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer tout l'historique des abonnements de l'utilisateur"""
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).order_by(Subscription.created_at.desc()).all()
    
    return subscriptions