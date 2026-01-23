"""Add encryption to user fields

Revision ID: 002_add_encryption
Revises: 001_initial_user_system
Create Date: 2025-10-15 12:00:00.000000

IMPORTANT: Cette migration augmente la taille des colonnes pour accueillir les données chiffrées.
Les colonnes email, name et google_id seront chiffrées automatiquement par le modèle SQLAlchemy.

ATTENTION: Si vous avez déjà des données en production:
1. Faites une sauvegarde complète de votre base de données AVANT d'appliquer cette migration
2. Cette migration va modifier le type des colonnes sans chiffrer les données existantes
3. Vous devrez chiffrer manuellement les données existantes après la migration
4. Un script de migration des données est fourni dans /scripts/encrypt_existing_data.py

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_encryption'
down_revision = '001_initial_user_system'
branch_labels = None
depends_on = None


def upgrade():
    """
    Modifie les colonnes sensibles de la table users pour supporter le chiffrement.

    Les données chiffrées avec Fernet sont plus longues que les données originales.
    On passe à VARCHAR(512) pour avoir suffisamment d'espace.
    """
    # Augmenter la taille des colonnes pour accueillir les données chiffrées
    op.alter_column('users', 'email',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=512),
                    existing_nullable=False)

    op.alter_column('users', 'name',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=512),
                    existing_nullable=True)

    op.alter_column('users', 'google_id',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=512),
                    existing_nullable=True)


def downgrade():
    """
    Revient aux tailles de colonnes originales.

    ATTENTION: Cette opération peut échouer si les données chiffrées sont trop longues
    pour tenir dans VARCHAR(255).
    """
    op.alter_column('users', 'google_id',
                    existing_type=sa.String(length=512),
                    type_=sa.String(length=255),
                    existing_nullable=True)

    op.alter_column('users', 'name',
                    existing_type=sa.String(length=512),
                    type_=sa.String(length=255),
                    existing_nullable=True)

    op.alter_column('users', 'email',
                    existing_type=sa.String(length=512),
                    type_=sa.String(length=255),
                    existing_nullable=False)
