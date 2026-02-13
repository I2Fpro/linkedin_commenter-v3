"""Create admin analytics materialized views

Revision ID: 008_create_admin_materialized_views
Revises: 007_add_trial_and_linkedin_profile
Create Date: 2026-02-13

Phase 03 - Plan 03-01: Infrastructure backend métriques admin
"""
from alembic import op

revision = '008_create_admin_materialized_views'
down_revision = '007_add_trial_and_linkedin_profile'
branch_labels = None
depends_on = None

def upgrade():
    # Create materialized view analytics.daily_summary
    op.execute("""
        CREATE MATERIALIZED VIEW analytics.daily_summary AS
        SELECT
            DATE_TRUNC('day', timestamp)::DATE AS date,
            event_type,
            COUNT(*) AS event_count,
            COUNT(DISTINCT user_id) AS unique_users
        FROM analytics.events
        WHERE timestamp >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY DATE_TRUNC('day', timestamp)::DATE, event_type
        ORDER BY date DESC, event_type
    """)

    # Create UNIQUE index for REFRESH CONCURRENTLY
    op.execute("""
        CREATE UNIQUE INDEX idx_daily_summary_date_type ON analytics.daily_summary (date, event_type)
    """)

    # Create materialized view analytics.user_consumption
    op.execute("""
        CREATE MATERIALIZED VIEW analytics.user_consumption AS
        SELECT
            u.id AS user_id,
            u.email,
            u.role,
            COALESCE(COUNT(e.id) FILTER (WHERE e.event_type = 'comment_generated'), 0) AS generation_count,
            COALESCE(SUM((e.properties->>'tokens_input')::INTEGER) FILTER (WHERE e.event_type = 'comment_generated'), 0) AS total_tokens_input,
            COALESCE(SUM((e.properties->>'tokens_output')::INTEGER) FILTER (WHERE e.event_type = 'comment_generated'), 0) AS total_tokens_output,
            MAX(e.timestamp) FILTER (WHERE e.event_type = 'comment_generated') AS last_generation
        FROM public.users u
        LEFT JOIN analytics.events e ON u.id = e.user_id
            AND e.timestamp >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY u.id, u.email, u.role
    """)

    # Create indexes on user_consumption
    op.execute("""
        CREATE UNIQUE INDEX idx_user_consumption_user_id ON analytics.user_consumption (user_id)
    """)
    op.execute("""
        CREATE INDEX idx_user_consumption_role ON analytics.user_consumption (role)
    """)
    op.execute("""
        CREATE INDEX idx_user_consumption_last_gen ON analytics.user_consumption (last_generation DESC NULLS LAST)
    """)

def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS analytics.user_consumption")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS analytics.daily_summary")
