"""Add blacklist_entries table

Revision ID: 005_add_blacklist_entries_table
Revises: 004_add_stripe_subscription_fields
Create Date: 2026-01-31

Story 2.1 - Epic 2 : Controle des Interactions V3
Permet aux utilisateurs Premium de gerer une blacklist de personnes avec lesquelles
ils ne souhaitent pas interagir sur LinkedIn.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '005_add_blacklist_entries_table'
down_revision = '004_add_stripe_subscription_fields'
branch_labels = None
depends_on = None


def upgrade():
    """
    Cree la table blacklist_entries pour stocker les personnes blacklistees par utilisateur.

    Colonnes:
    - id: Identifiant unique (UUID v4)
    - user_id: Reference a l'utilisateur proprietaire de l'entree
    - blocked_name: Nom de la personne blacklistee (obligatoire)
    - blocked_profile_url: URL du profil LinkedIn (optionnel)
    - created_at: Date et heure de l'ajout a la blacklist
    """
    op.create_table(
        'blacklist_entries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('blocked_name', sa.String(255), nullable=False),
        sa.Column('blocked_profile_url', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )

    # Index pour le chargement rapide de la liste par utilisateur (NFR4 < 200ms)
    op.create_index('ix_blacklist_entries_user_id', 'blacklist_entries', ['user_id'])

    # Contrainte UNIQUE pour eviter les doublons (user_id, blocked_name)
    # Securise contre les race conditions entre SELECT et INSERT
    op.create_unique_constraint(
        'uq_blacklist_user_blocked_name',
        'blacklist_entries',
        ['user_id', 'blocked_name']
    )


def downgrade():
    """
    Supprime la table blacklist_entries et ses index.

    ATTENTION: Cette operation supprime definitivement toutes les entrees de blacklist.
    """
    op.drop_constraint('uq_blacklist_user_blocked_name', 'blacklist_entries', type_='unique')
    op.drop_index('ix_blacklist_entries_user_id', table_name='blacklist_entries')
    op.drop_table('blacklist_entries')
