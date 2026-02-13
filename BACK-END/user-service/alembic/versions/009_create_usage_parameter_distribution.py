"""Create usage_parameter_distribution materialized view

Phase 6, Plan 06-01: Vue materialisee pour distributions d'usage par parametre.
"""
from alembic import op

revision = '009_create_usage_parameter_distribution'
down_revision = '008_create_admin_materialized_views'
branch_labels = None
depends_on = None


def upgrade():
    # Create materialized view for parameter usage distributions
    op.execute("""
        CREATE MATERIALIZED VIEW analytics.usage_parameter_distribution AS

        -- Dimension 1: tone
        SELECT
            'tone'::TEXT AS dimension,
            properties->>'tone' AS value,
            COUNT(*)::BIGINT AS usage_count,
            ROUND(
                COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (PARTITION BY 'tone'::TEXT), 0),
                2
            )::NUMERIC AS percentage
        FROM analytics.events
        WHERE event_type = 'comment_generated'
            AND properties->>'tone' IS NOT NULL
        GROUP BY properties->>'tone'

        UNION ALL

        -- Dimension 2: emotion
        SELECT
            'emotion'::TEXT AS dimension,
            properties->>'emotion' AS value,
            COUNT(*)::BIGINT AS usage_count,
            ROUND(
                COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (PARTITION BY 'emotion'::TEXT), 0),
                2
            )::NUMERIC AS percentage
        FROM analytics.events
        WHERE event_type = 'comment_generated'
            AND properties->>'emotion' IS NOT NULL
        GROUP BY properties->>'emotion'

        UNION ALL

        -- Dimension 3: style
        SELECT
            'style'::TEXT AS dimension,
            properties->>'style' AS value,
            COUNT(*)::BIGINT AS usage_count,
            ROUND(
                COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (PARTITION BY 'style'::TEXT), 0),
                2
            )::NUMERIC AS percentage
        FROM analytics.events
        WHERE event_type = 'comment_generated'
            AND properties->>'style' IS NOT NULL
        GROUP BY properties->>'style'

        UNION ALL

        -- Dimension 4: language
        SELECT
            'language'::TEXT AS dimension,
            properties->>'language' AS value,
            COUNT(*)::BIGINT AS usage_count,
            ROUND(
                COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (PARTITION BY 'language'::TEXT), 0),
                2
            )::NUMERIC AS percentage
        FROM analytics.events
        WHERE event_type = 'comment_generated'
            AND properties->>'language' IS NOT NULL
        GROUP BY properties->>'language'

        UNION ALL

        -- Dimension 5: news_enrichment_mode (avec COALESCE pour events historiques)
        SELECT
            'news_enrichment_mode'::TEXT AS dimension,
            COALESCE(properties->>'news_enrichment_mode', 'disabled') AS value,
            COUNT(*)::BIGINT AS usage_count,
            ROUND(
                COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (PARTITION BY 'news_enrichment_mode'::TEXT), 0),
                2
            )::NUMERIC AS percentage
        FROM analytics.events
        WHERE event_type = 'comment_generated'
        GROUP BY COALESCE(properties->>'news_enrichment_mode', 'disabled')
    """)

    # Create UNIQUE index (required for REFRESH CONCURRENTLY)
    op.execute("""
        CREATE UNIQUE INDEX idx_usage_param_dist_unique
            ON analytics.usage_parameter_distribution (dimension, value)
    """)

    # Create index for fast dimension filtering
    op.execute("""
        CREATE INDEX idx_usage_param_dist_dimension
            ON analytics.usage_parameter_distribution (dimension)
    """)


def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS analytics.usage_parameter_distribution")
