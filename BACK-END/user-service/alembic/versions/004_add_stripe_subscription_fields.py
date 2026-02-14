"""Add stripe subscription fields and events table

Revision ID: 004_add_stripe_subscription_fields
Revises: 003_role_history
Create Date: 2025-01-19 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_stripe_subscription_fields'
down_revision = '003_role_history'
branch_labels = None
depends_on = None


def upgrade():
    """
    Ajoute les colonnes stripe_subscription_id et subscription_status à la table users.
    Crée également la table stripe_events pour la déduplication des webhooks.
    """
    # Ajouter les colonnes d'abonnement Stripe
    op.add_column('users', sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('subscription_status', sa.String(length=50), nullable=True))

    # Créer un index pour améliorer les performances de recherche
    op.create_index(
        op.f('ix_users_stripe_subscription_id'),
        'users',
        ['stripe_subscription_id'],
        unique=True
    )

    # Créer la table stripe_events pour la déduplication des webhooks
    op.create_table(
        'stripe_events',
        sa.Column('id', sa.String(length=255), nullable=False),  # evt_xxxxx
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),  # Pour stocker les données de l'événement si nécessaire
        sa.PrimaryKeyConstraint('id')
    )

    # Créer un index sur le type d'événement pour les requêtes
    op.create_index(
        op.f('ix_stripe_events_type'),
        'stripe_events',
        ['type'],
        unique=False
    )

    # Créer un index sur la date de traitement
    op.create_index(
        op.f('ix_stripe_events_processed_at'),
        'stripe_events',
        ['processed_at'],
        unique=False
    )


def downgrade():
    """
    Supprime les colonnes d'abonnement Stripe et la table stripe_events.

    ATTENTION: Cette opération supprimera toutes les données des colonnes et de la table.
    """
    # Supprimer la table stripe_events
    op.drop_index(op.f('ix_stripe_events_processed_at'), table_name='stripe_events')
    op.drop_index(op.f('ix_stripe_events_type'), table_name='stripe_events')
    op.drop_table('stripe_events')

    # Supprimer les colonnes d'abonnement
    op.drop_index(op.f('ix_users_stripe_subscription_id'), table_name='users')
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'stripe_subscription_id')
