"""Add stripe_customer_id to users table

Revision ID: 003_add_stripe_customer_id
Revises: 002_add_encryption
Create Date: 2025-01-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_stripe_customer_id'
down_revision = '002_add_encryption'
branch_labels = None
depends_on = None


def upgrade():
    """
    Ajoute la colonne stripe_customer_id à la table users.

    Cette colonne stocke l'identifiant du customer Stripe associé à l'utilisateur.
    Elle permet de lier les paiements Stripe aux utilisateurs de l'application.
    """
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(length=255), nullable=True))

    # Créer un index unique pour améliorer les performances de recherche
    op.create_index(
        op.f('ix_users_stripe_customer_id'),
        'users',
        ['stripe_customer_id'],
        unique=True
    )


def downgrade():
    """
    Supprime la colonne stripe_customer_id de la table users.

    ATTENTION: Cette opération supprimera toutes les données de la colonne stripe_customer_id.
    """
    op.drop_index(op.f('ix_users_stripe_customer_id'), table_name='users')
    op.drop_column('users', 'stripe_customer_id')
