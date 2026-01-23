"""Initial user system tables

Revision ID: 001_initial_user_system
Revises: 
Create Date: 2025-08-18 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_user_system'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create ENUM types with checkfirst to avoid duplicate errors
    role_type = postgresql.ENUM('FREE', 'MEDIUM', 'PREMIUM', name='role_type')
    role_type.create(op.get_bind(), checkfirst=True)

    subscription_status = postgresql.ENUM('ACTIVE', 'EXPIRED', 'CANCELLED', name='subscription_status')
    subscription_status.create(op.get_bind(), checkfirst=True)
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('google_id', sa.String(length=255), nullable=True),
        sa.Column('role', role_type, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=True)
    
    # Create roles table
    op.create_table('roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('daily_limit', sa.Integer(), nullable=True),
        sa.Column('features', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create subscriptions table
    op.create_table('subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan', role_type, nullable=False),
        sa.Column('status', subscription_status, nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create usage_logs table
    op.create_table('usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feature', sa.String(length=100), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usage_logs_timestamp'), 'usage_logs', ['timestamp'], unique=False)
    op.create_index('idx_usage_logs_user_timestamp', 'usage_logs', ['user_id', 'timestamp'], unique=False)
    
    # Set default values
    op.execute("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'FREE'")
    op.execute("ALTER TABLE users ALTER COLUMN is_active SET DEFAULT true")
    op.execute("ALTER TABLE subscriptions ALTER COLUMN status SET DEFAULT 'ACTIVE'")


def downgrade():
    # Drop tables in reverse order
    op.drop_index('idx_usage_logs_user_timestamp', table_name='usage_logs')
    op.drop_index(op.f('ix_usage_logs_timestamp'), table_name='usage_logs')
    op.drop_table('usage_logs')
    op.drop_table('subscriptions')
    op.drop_table('roles')
    op.drop_index(op.f('ix_users_google_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop ENUM types
    subscription_status = postgresql.ENUM('ACTIVE', 'EXPIRED', 'CANCELLED', name='subscription_status')
    subscription_status.drop(op.get_bind())
    
    role_type = postgresql.ENUM('FREE', 'MEDIUM', 'PREMIUM', name='role_type')
    role_type.drop(op.get_bind())