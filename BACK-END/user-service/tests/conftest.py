"""
Configuration pytest pour les tests E2E du user-service.

Phase 04 - Plan 04-05: Tests E2E
Fixtures SQLite in-memory, TestClient FastAPI, factory users.
"""

import os
import pytest
from cryptography.fernet import Fernet

# IMPORTANT: Mocker les env vars AVANT les imports du projet
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-jwt-secret-key-for-testing-only"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode()
os.environ["ENVIRONMENT"] = "test"
os.environ["ADMIN_EMAILS"] = "admin@test.com"
os.environ["ALLOWED_ORIGINS"] = "*"
os.environ["CORS_CREDENTIALS"] = "false"

from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import uuid

from database import Base, get_db
from models import User, RoleType
from auth import create_user_token
from utils.encryption import EncryptionManager

# Engine SQLite in-memory avec StaticPool pour les tests
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Activer les FK sur SQLite
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Event listener pour forcer les dates SQLite à être timezone-aware
@event.listens_for(User, "load")
def receive_load(target, context):
    """Force les dates à être timezone-aware après chargement depuis SQLite."""
    if target.trial_started_at and target.trial_started_at.tzinfo is None:
        target.trial_started_at = target.trial_started_at.replace(tzinfo=timezone.utc)
    if target.trial_ends_at and target.trial_ends_at.tzinfo is None:
        target.trial_ends_at = target.trial_ends_at.replace(tzinfo=timezone.utc)
    if target.grace_ends_at and target.grace_ends_at.tzinfo is None:
        target.grace_ends_at = target.grace_ends_at.replace(tzinfo=timezone.utc)
    if target.linkedin_profile_captured_at and target.linkedin_profile_captured_at.tzinfo is None:
        target.linkedin_profile_captured_at = target.linkedin_profile_captured_at.replace(tzinfo=timezone.utc)
    if target.created_at and target.created_at.tzinfo is None:
        target.created_at = target.created_at.replace(tzinfo=timezone.utc)
    if target.updated_at and target.updated_at.tzinfo is None:
        target.updated_at = target.updated_at.replace(tzinfo=timezone.utc)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db():
    """
    Fixture de session DB pour chaque test.
    Cree les tables, yield la session, puis rollback et drop.
    """
    # Creer les tables
    Base.metadata.create_all(bind=test_engine)

    # Creer une session
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Nettoyer les tables
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db):
    """
    Fixture TestClient FastAPI avec override de get_db.
    """
    from main import app

    # Override de get_db pour utiliser la session de test
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Nettoyer les overrides
    app.dependency_overrides.clear()


@pytest.fixture
def encryption_manager():
    """Fixture EncryptionManager pour les tests."""
    return EncryptionManager()


@pytest.fixture
def create_test_user(db, encryption_manager):
    """
    Factory fixture pour creer des utilisateurs de test.

    Usage:
        user = create_test_user(email="test@example.com", role=RoleType.FREE)
    """
    def _create_user(
        email: str = "test@example.com",
        name: str = "Test User",
        google_id: str = None,
        role: RoleType = RoleType.FREE,
        is_active: bool = True,
        linkedin_profile_id: str = None,
        trial_started_at: datetime = None,
        trial_ends_at: datetime = None,
        grace_ends_at: datetime = None,
        stripe_customer_id: str = None,
        stripe_subscription_id: str = None,
        subscription_status: str = None,
        trial_reminder_sent_at: datetime = None,
    ) -> User:
        """Cree et retourne un utilisateur de test."""
        user = User(
            id=uuid.uuid4(),
            email=email,
            name=name,
            google_id=google_id or f"google_{uuid.uuid4().hex[:8]}",
            role=role,
            is_active=is_active,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            subscription_status=subscription_status,
            trial_reminder_sent_at=trial_reminder_sent_at,
        )

        # LinkedIn profile
        if linkedin_profile_id:
            user.linkedin_profile_id = linkedin_profile_id
            user.linkedin_profile_id_hash = User.hash_linkedin_profile_id(linkedin_profile_id)
            user.linkedin_profile_captured_at = datetime.now(timezone.utc)

        # Trial dates - Forcer timezone-aware avant commit
        if trial_started_at:
            user.trial_started_at = trial_started_at if trial_started_at.tzinfo else trial_started_at.replace(tzinfo=timezone.utc)
        if trial_ends_at:
            user.trial_ends_at = trial_ends_at if trial_ends_at.tzinfo else trial_ends_at.replace(tzinfo=timezone.utc)
        if grace_ends_at:
            user.grace_ends_at = grace_ends_at if grace_ends_at.tzinfo else grace_ends_at.replace(tzinfo=timezone.utc)

        db.add(user)
        db.flush()  # Flush pour avoir l'ID mais pas encore commit

        # Forcer timezone-aware sur l'objet en memoire AVANT le commit
        # pour eviter que SQLite ne perde l'info
        if user.trial_started_at and user.trial_started_at.tzinfo is None:
            user.trial_started_at = user.trial_started_at.replace(tzinfo=timezone.utc)
        if user.trial_ends_at and user.trial_ends_at.tzinfo is None:
            user.trial_ends_at = user.trial_ends_at.replace(tzinfo=timezone.utc)
        if user.grace_ends_at and user.grace_ends_at.tzinfo is None:
            user.grace_ends_at = user.grace_ends_at.replace(tzinfo=timezone.utc)

        db.commit()
        db.refresh(user)

        # Re-forcer apres refresh car SQLite perd la timezone
        if user.trial_started_at and user.trial_started_at.tzinfo is None:
            user.trial_started_at = user.trial_started_at.replace(tzinfo=timezone.utc)
        if user.trial_ends_at and user.trial_ends_at.tzinfo is None:
            user.trial_ends_at = user.trial_ends_at.replace(tzinfo=timezone.utc)
        if user.grace_ends_at and user.grace_ends_at.tzinfo is None:
            user.grace_ends_at = user.grace_ends_at.replace(tzinfo=timezone.utc)
        if user.linkedin_profile_captured_at and user.linkedin_profile_captured_at.tzinfo is None:
            user.linkedin_profile_captured_at = user.linkedin_profile_captured_at.replace(tzinfo=timezone.utc)

        return user

    return _create_user


@pytest.fixture
def auth_headers(create_test_user):
    """
    Fixture pour obtenir des headers d'authentification JWT.

    Usage:
        headers = auth_headers(email="test@example.com", role=RoleType.PREMIUM)
    """
    def _get_headers(email: str = "test@example.com", role: RoleType = RoleType.FREE) -> dict:
        """Cree un user et retourne les headers avec JWT."""
        user = create_test_user(email=email, role=role)
        token = create_user_token(user)
        return {"Authorization": f"Bearer {token}"}

    return _get_headers


@pytest.fixture
def mock_analytics_schema(db):
    """
    Mock du schema analytics.events pour SQLite (ne supporte pas les schemas).
    Cree une table events_mock pour simuler analytics.events.
    """
    # SQLite ne supporte pas les schemas, on skip ce fixture
    # Les tests qui necessitent analytics.* devront mocker les appels SQL
    pass


@pytest.fixture
def mock_track_trial_event(monkeypatch):
    """
    Mock de track_trial_event pour eviter les appels SQL analytics.
    Retourne une liste des events trackes pour verification dans les tests.
    """
    tracked_events = []

    def mock_track(db, user_id, event_type, properties=None):
        tracked_events.append({
            "user_id": user_id,
            "event_type": event_type,
            "properties": properties or {}
        })

    from utils import trial_manager
    monkeypatch.setattr(trial_manager, "track_trial_event", mock_track)

    return tracked_events


@pytest.fixture
def mock_send_trial_email(monkeypatch):
    """
    Mock de send_trial_email pour eviter les appels Resend.
    Retourne une liste des emails envoyes pour verification dans les tests.
    """
    sent_emails = []

    def mock_send(to_email, subject, html_body, from_email=None):
        sent_emails.append({
            "to": to_email,
            "subject": subject,
            "html_body": html_body,
            "from": from_email
        })
        return True

    from notifications import email_sender
    monkeypatch.setattr(email_sender, "send_trial_email", mock_send)

    return sent_emails
