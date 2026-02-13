from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Text, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
import hashlib
from database import Base
from utils.encrypted_types import EncryptedString

class RoleType(str, enum.Enum):
    FREE = "FREE"
    MEDIUM = "MEDIUM"
    PREMIUM = "PREMIUM"

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Colonnes chiffrées pour la sécurité des données personnelles
    email = Column(EncryptedString(512), unique=True, nullable=False, index=True)
    name = Column(EncryptedString(512))
    google_id = Column(EncryptedString(512), unique=True, index=True)
    role = Column(ENUM(RoleType), default=RoleType.FREE, nullable=False)
    stripe_customer_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_subscription_id = Column(String(255), unique=True, nullable=True, index=True)
    subscription_status = Column(String(50), nullable=True)  # active, canceled, past_due, trialing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Phase 2 — LinkedIn Profile Capture & Trial
    linkedin_profile_id = Column(EncryptedString(512), nullable=True)  # Chiffré (RGPD)
    linkedin_profile_id_hash = Column(String(64), unique=True, nullable=True, index=True)  # SHA256 en clair pour lookup rapide
    linkedin_profile_captured_at = Column(DateTime(timezone=True), nullable=True)
    trial_started_at = Column(DateTime(timezone=True), nullable=True)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True, index=True)
    grace_ends_at = Column(DateTime(timezone=True), nullable=True, index=True)
    trial_reminder_sent_at = Column(DateTime(timezone=True), nullable=True)  # Phase 04 - Garde-fou rappel J-3

    subscriptions = relationship("Subscription", back_populates="user")
    usage_logs = relationship("UsageLog", back_populates="user")

    @staticmethod
    def hash_linkedin_profile_id(profile_id: str) -> str:
        """Hash SHA256 du linkedin_profile_id pour lookup anti-abus."""
        return hashlib.sha256(profile_id.lower().strip().encode()).hexdigest()

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    daily_limit = Column(Integer, default=5)
    features = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan = Column(ENUM(RoleType), nullable=False)
    status = Column(ENUM(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="subscriptions")

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    feature = Column(String(100), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    meta_data = Column('metadata', JSON)  # DB column is 'metadata', Python attr is 'meta_data'

    user = relationship("User", back_populates="usage_logs")

class RoleChangeHistory(Base):
    __tablename__ = "role_change_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    old_role = Column(ENUM(RoleType), nullable=True)  # NULL pour la création initiale
    new_role = Column(ENUM(RoleType), nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    changed_by = Column(String(255))  # Email ou ID de l'admin qui a fait le changement (optionnel)
    reason = Column(Text)  # Raison du changement (optionnel)
    meta_data = Column(JSON)  # Données supplémentaires (optionnel)

class StripeEvent(Base):
    __tablename__ = "stripe_events"

    id = Column(String(255), primary_key=True)  # evt_xxxxx
    type = Column(String(100), nullable=False, index=True)
    processed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    data = Column(JSON, nullable=True)  # Pour stocker les données de l'événement si nécessaire


class BlacklistEntry(Base):
    """
    Entree de blacklist - Story 2.1 Epic 2.
    Permet a un utilisateur Premium de bloquer des personnes sur LinkedIn.
    """
    __tablename__ = "blacklist_entries"
    __table_args__ = (
        UniqueConstraint('user_id', 'blocked_name', name='uq_blacklist_user_blocked_name'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    blocked_name = Column(String(255), nullable=False)
    blocked_profile_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relation vers User
    user = relationship("User", backref="blacklist_entries")

    def __repr__(self):
        return f"<BlacklistEntry {self.blocked_name}>"
