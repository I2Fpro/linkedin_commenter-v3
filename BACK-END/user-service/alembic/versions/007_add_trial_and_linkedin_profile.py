"""Add LinkedIn profile and trial columns to users table

Revision ID: 007_add_trial_and_linkedin_profile
Revises: 006_create_analytics_schema
Create Date: 2026-02-12

Phase 02 - Plan 02-01: Migration DB Trial & LinkedIn Profile
"""
from alembic import op
import sqlalchemy as sa

revision = '007_add_trial_and_linkedin_profile'
down_revision = '006_create_analytics_schema'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('linkedin_profile_id', sa.String(512), nullable=True))
    op.add_column('users', sa.Column('linkedin_profile_id_hash', sa.String(64), nullable=True))
    op.create_unique_constraint('uq_users_linkedin_profile_id_hash', 'users', ['linkedin_profile_id_hash'])
    op.create_index('idx_users_linkedin_profile_id_hash', 'users', ['linkedin_profile_id_hash'])
    op.add_column('users', sa.Column('linkedin_profile_captured_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('trial_started_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('idx_users_trial_ends_at', 'users', ['trial_ends_at'])
    op.add_column('users', sa.Column('grace_ends_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('idx_users_grace_ends_at', 'users', ['grace_ends_at'])

def downgrade():
    op.drop_index('idx_users_grace_ends_at', 'users')
    op.drop_column('users', 'grace_ends_at')
    op.drop_index('idx_users_trial_ends_at', 'users')
    op.drop_column('users', 'trial_ends_at')
    op.drop_column('users', 'trial_started_at')
    op.drop_column('users', 'linkedin_profile_captured_at')
    op.drop_index('idx_users_linkedin_profile_id_hash', 'users')
    op.drop_constraint('uq_users_linkedin_profile_id_hash', 'users', type_='unique')
    op.drop_column('users', 'linkedin_profile_id_hash')
    op.drop_column('users', 'linkedin_profile_id')
