from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import uuid

from models import User, UsageLog
from utils.feature_flags import FEATURES

class QuotaManager:
    def __init__(self, db: Session):
        self.db = db
    
    def check_daily_limit(self, user_id: uuid.UUID, feature: str = "generate_comment") -> bool:
        """Vérifier si l'utilisateur a atteint sa limite quotidienne"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        role_features = FEATURES.get(user.role.value, FEATURES["FREE"])
        daily_limit = role_features.get("daily_generations", 5)
        
        if daily_limit == -1:
            return True
        
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        usage_count = self.db.query(func.count(UsageLog.id)).filter(
            and_(
                UsageLog.user_id == user_id,
                UsageLog.feature == feature,
                UsageLog.timestamp >= today_start,
                UsageLog.timestamp < today_end
            )
        ).scalar()
        
        return usage_count < daily_limit
    
    def increment_usage(self, user_id: uuid.UUID, feature: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Incrémenter l'utilisation d'une fonctionnalité"""
        if not self.check_daily_limit(user_id, feature):
            return False
        
        usage_log = UsageLog(
            user_id=user_id,
            feature=feature,
            metadata=metadata
        )
        
        self.db.add(usage_log)
        self.db.commit()
        
        return True
    
    def get_daily_usage(self, user_id: uuid.UUID, feature: str = "generate_comment") -> int:
        """Récupérer l'utilisation quotidienne actuelle"""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        usage_count = self.db.query(func.count(UsageLog.id)).filter(
            and_(
                UsageLog.user_id == user_id,
                UsageLog.feature == feature,
                UsageLog.timestamp >= today_start,
                UsageLog.timestamp < today_end
            )
        ).scalar()
        
        return usage_count
    
    def get_remaining_quota(self, user_id: uuid.UUID, feature: str = "generate_comment") -> int:
        """Récupérer le quota restant pour aujourd'hui"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return 0
        
        role_features = FEATURES.get(user.role.value, FEATURES["FREE"])
        daily_limit = role_features.get("daily_generations", 5)
        
        if daily_limit == -1:
            return 999999  # Représente l'illimité
        
        used_today = self.get_daily_usage(user_id, feature)
        remaining = max(0, daily_limit - used_today)
        
        return remaining
    
    def reset_daily_quotas(self) -> int:
        """Réinitialiser les quotas quotidiens (généralement appelé par un cron job)"""
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        
        deleted_count = self.db.query(UsageLog).filter(
            UsageLog.timestamp < yesterday
        ).count()
        
        self.db.query(UsageLog).filter(
            UsageLog.timestamp < yesterday
        ).delete(synchronize_session=False)
        
        self.db.commit()
        
        return deleted_count
    
    def get_next_reset_time(self) -> datetime:
        """Récupérer l'heure de la prochaine réinitialisation"""
        now = datetime.now(timezone.utc)
        next_reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return next_reset
    
    def get_user_statistics(self, user_id: uuid.UUID, days: int = 30) -> Dict[str, Any]:
        """Récupérer les statistiques d'utilisation d'un utilisateur"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        total_usage = self.db.query(func.count(UsageLog.id)).filter(
            and_(
                UsageLog.user_id == user_id,
                UsageLog.timestamp >= start_date
            )
        ).scalar()
        
        daily_usage = self.db.query(
            func.date(UsageLog.timestamp).label('date'),
            func.count(UsageLog.id).label('count')
        ).filter(
            and_(
                UsageLog.user_id == user_id,
                UsageLog.timestamp >= start_date
            )
        ).group_by(func.date(UsageLog.timestamp)).all()
        
        feature_usage = self.db.query(
            UsageLog.feature,
            func.count(UsageLog.id).label('count')
        ).filter(
            and_(
                UsageLog.user_id == user_id,
                UsageLog.timestamp >= start_date
            )
        ).group_by(UsageLog.feature).all()
        
        return {
            "total_usage": total_usage,
            "daily_breakdown": [{"date": str(day.date), "count": day.count} for day in daily_usage],
            "feature_breakdown": [{"feature": feature.feature, "count": feature.count} for feature in feature_usage],
            "period_days": days
        }