"""Add role change history table

Revision ID: 003_role_history
Revises: 003_add_stripe_customer_id
Create Date: 2025-11-16 15:30:00.000000

Cette migration crée une table d'audit pour suivre l'historique des changements de rôle des utilisateurs.
Elle permet de tracer quand un utilisateur passe d'un rôle à un autre (FREE -> MEDIUM, MEDIUM -> PREMIUM, etc.)

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM


# revision identifiers, used by Alembic.
revision = '003_role_history'
down_revision = '003_add_stripe_customer_id'
branch_labels = None
depends_on = None


def upgrade():
    """
    Crée la table role_change_history pour tracer les changements de rôle.

    Colonnes:
    - id: Identifiant unique
    - user_id: Référence à l'utilisateur
    - old_role: Ancien rôle (NULL si c'est la création initiale)
    - new_role: Nouveau rôle
    - changed_at: Date et heure du changement
    - changed_by: Email ou ID de l'admin qui a fait le changement (optionnel)
    - reason: Raison du changement (optionnel)
    - meta_data: Données supplémentaires en JSON (optionnel)
    """
    # Créer l'enum RoleType s'il n'existe pas déjà
    role_type_enum = ENUM('FREE', 'MEDIUM', 'PREMIUM', name='roletype', create_type=False)

    # Créer la table role_change_history
    op.create_table(
        'role_change_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('old_role', role_type_enum, nullable=True),
        sa.Column('new_role', role_type_enum, nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('changed_by', sa.String(255), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('meta_data', sa.JSON(), nullable=True)
    )

    # Créer des index pour améliorer les performances des requêtes
    op.create_index('ix_role_change_history_user_id', 'role_change_history', ['user_id'])
    op.create_index('ix_role_change_history_changed_at', 'role_change_history', ['changed_at'])

    # Créer un index composite pour les requêtes fréquentes
    op.create_index('ix_role_change_history_user_changed_at', 'role_change_history', ['user_id', 'changed_at'])


def downgrade():
    """
    Supprime la table role_change_history et ses index.

    ATTENTION: Cette opération supprime définitivement tout l'historique des changements de rôle.
    """
    # Supprimer les index
    op.drop_index('ix_role_change_history_user_changed_at', table_name='role_change_history')
    op.drop_index('ix_role_change_history_changed_at', table_name='role_change_history')
    op.drop_index('ix_role_change_history_user_id', table_name='role_change_history')

    # Supprimer la table
    op.drop_table('role_change_history')
