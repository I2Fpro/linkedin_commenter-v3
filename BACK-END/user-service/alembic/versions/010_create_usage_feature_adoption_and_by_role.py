"""Create usage_feature_adoption and usage_by_role materialized views

Phase 6, Plan 06-02: Vues materialisees pour taux d'adoption features et segmentation par role.
"""
from alembic import op

revision = '010_create_usage_feature_adoption_and_by_role'
down_revision = '009_create_usage_parameter_distribution'
branch_labels = None
depends_on = None


def upgrade():
    # === Vue 1: usage_feature_adoption ===
    op.execute("""
        CREATE MATERIALIZED VIEW analytics.usage_feature_adoption AS
        WITH generation_events AS (
            SELECT
                COALESCE((properties->>'web_search_enabled'), 'false') AS web_search_enabled,
                COALESCE((properties->>'web_search_success'), 'false') AS web_search_success,
                COALESCE((properties->>'include_quote_enabled'), 'false') AS include_quote_enabled,
                COALESCE((properties->>'custom_prompt_used'), 'false') AS custom_prompt_used,
                COALESCE(properties->>'news_enrichment_mode', 'disabled') AS news_enrichment_mode
            FROM analytics.events
            WHERE event_type = 'comment_generated'
                AND properties->>'mode' IN ('generate', 'custom_prompt')
        ),
        totals AS (
            SELECT COUNT(*) AS total_generations FROM generation_events
        )
        SELECT
            'web_search_enabled'::TEXT AS feature_name,
            COUNT(*) FILTER (WHERE web_search_enabled = 'true')::BIGINT AS generations_with_feature,
            (SELECT total_generations FROM totals)::BIGINT AS total_generations,
            COALESCE(
                ROUND(COUNT(*) FILTER (WHERE web_search_enabled = 'true') * 100.0
                    / NULLIF((SELECT total_generations FROM totals), 0), 2),
                0
            )::NUMERIC AS adoption_rate,
            COALESCE(
                ROUND(COUNT(*) FILTER (WHERE web_search_enabled = 'true' AND web_search_success = 'true') * 100.0
                    / NULLIF(COUNT(*) FILTER (WHERE web_search_enabled = 'true'), 0), 2),
                0
            )::NUMERIC AS success_rate
        FROM generation_events

        UNION ALL

        SELECT
            'include_quote_enabled'::TEXT AS feature_name,
            COUNT(*) FILTER (WHERE include_quote_enabled = 'true')::BIGINT,
            (SELECT total_generations FROM totals)::BIGINT,
            COALESCE(
                ROUND(COUNT(*) FILTER (WHERE include_quote_enabled = 'true') * 100.0
                    / NULLIF((SELECT total_generations FROM totals), 0), 2),
                0
            )::NUMERIC,
            NULL::NUMERIC AS success_rate
        FROM generation_events

        UNION ALL

        SELECT
            'custom_prompt_used'::TEXT AS feature_name,
            COUNT(*) FILTER (WHERE custom_prompt_used = 'true')::BIGINT,
            (SELECT total_generations FROM totals)::BIGINT,
            COALESCE(
                ROUND(COUNT(*) FILTER (WHERE custom_prompt_used = 'true') * 100.0
                    / NULLIF((SELECT total_generations FROM totals), 0), 2),
                0
            )::NUMERIC,
            NULL::NUMERIC AS success_rate
        FROM generation_events

        UNION ALL

        SELECT
            'news_enrichment_enabled'::TEXT AS feature_name,
            COUNT(*) FILTER (WHERE news_enrichment_mode != 'disabled')::BIGINT,
            (SELECT total_generations FROM totals)::BIGINT,
            COALESCE(
                ROUND(COUNT(*) FILTER (WHERE news_enrichment_mode != 'disabled') * 100.0
                    / NULLIF((SELECT total_generations FROM totals), 0), 2),
                0
            )::NUMERIC,
            NULL::NUMERIC AS success_rate
        FROM generation_events

        UNION ALL

        SELECT
            'news_mode_title_only'::TEXT AS feature_name,
            COUNT(*) FILTER (WHERE news_enrichment_mode = 'title-only')::BIGINT,
            (SELECT total_generations FROM totals)::BIGINT,
            COALESCE(
                ROUND(COUNT(*) FILTER (WHERE news_enrichment_mode = 'title-only') * 100.0
                    / NULLIF((SELECT total_generations FROM totals), 0), 2),
                0
            )::NUMERIC,
            NULL::NUMERIC AS success_rate
        FROM generation_events

        UNION ALL

        SELECT
            'news_mode_smart_summary'::TEXT AS feature_name,
            COUNT(*) FILTER (WHERE news_enrichment_mode = 'smart-summary')::BIGINT,
            (SELECT total_generations FROM totals)::BIGINT,
            COALESCE(
                ROUND(COUNT(*) FILTER (WHERE news_enrichment_mode = 'smart-summary') * 100.0
                    / NULLIF((SELECT total_generations FROM totals), 0), 2),
                0
            )::NUMERIC,
            NULL::NUMERIC AS success_rate
        FROM generation_events
    """)

    # Index UNIQUE for REFRESH CONCURRENTLY
    op.execute("""
        CREATE UNIQUE INDEX idx_usage_feature_adoption_unique
            ON analytics.usage_feature_adoption (feature_name)
    """)

    # === Vue 2: usage_by_role ===
    op.execute("""
        CREATE MATERIALIZED VIEW analytics.usage_by_role AS
        -- Volume total par role
        SELECT
            COALESCE(properties->>'role', 'FREE') AS role,
            'total_generations'::TEXT AS metric_type,
            'all'::TEXT AS dimension,
            'all'::TEXT AS value,
            COUNT(*)::BIGINT AS count
        FROM analytics.events
        WHERE event_type = 'comment_generated'
        GROUP BY COALESCE(properties->>'role', 'FREE')

        UNION ALL

        -- Distribution tone par role
        SELECT
            COALESCE(properties->>'role', 'FREE') AS role,
            'parameter'::TEXT AS metric_type,
            'tone'::TEXT AS dimension,
            properties->>'tone' AS value,
            COUNT(*)::BIGINT AS count
        FROM analytics.events
        WHERE event_type = 'comment_generated'
            AND properties->>'tone' IS NOT NULL
        GROUP BY COALESCE(properties->>'role', 'FREE'), properties->>'tone'

        UNION ALL

        -- Distribution emotion par role
        SELECT
            COALESCE(properties->>'role', 'FREE') AS role,
            'parameter'::TEXT AS metric_type,
            'emotion'::TEXT AS dimension,
            properties->>'emotion' AS value,
            COUNT(*)::BIGINT AS count
        FROM analytics.events
        WHERE event_type = 'comment_generated'
            AND properties->>'emotion' IS NOT NULL
        GROUP BY COALESCE(properties->>'role', 'FREE'), properties->>'emotion'

        UNION ALL

        -- Distribution style par role
        SELECT
            COALESCE(properties->>'role', 'FREE') AS role,
            'parameter'::TEXT AS metric_type,
            'style'::TEXT AS dimension,
            properties->>'style' AS value,
            COUNT(*)::BIGINT AS count
        FROM analytics.events
        WHERE event_type = 'comment_generated'
            AND properties->>'style' IS NOT NULL
        GROUP BY COALESCE(properties->>'role', 'FREE'), properties->>'style'

        UNION ALL

        -- Distribution language par role
        SELECT
            COALESCE(properties->>'role', 'FREE') AS role,
            'parameter'::TEXT AS metric_type,
            'language'::TEXT AS dimension,
            properties->>'language' AS value,
            COUNT(*)::BIGINT AS count
        FROM analytics.events
        WHERE event_type = 'comment_generated'
            AND properties->>'language' IS NOT NULL
        GROUP BY COALESCE(properties->>'role', 'FREE'), properties->>'language'

        UNION ALL

        -- Distribution news_enrichment_mode par role
        SELECT
            COALESCE(properties->>'role', 'FREE') AS role,
            'parameter'::TEXT AS metric_type,
            'news_enrichment_mode'::TEXT AS dimension,
            COALESCE(properties->>'news_enrichment_mode', 'disabled') AS value,
            COUNT(*)::BIGINT AS count
        FROM analytics.events
        WHERE event_type = 'comment_generated'
        GROUP BY COALESCE(properties->>'role', 'FREE'), COALESCE(properties->>'news_enrichment_mode', 'disabled')

        UNION ALL

        -- Feature: web_search_enabled par role
        SELECT
            COALESCE(properties->>'role', 'FREE') AS role,
            'feature'::TEXT AS metric_type,
            'web_search_enabled'::TEXT AS dimension,
            'adopted'::TEXT AS value,
            COUNT(*) FILTER (WHERE COALESCE(properties->>'web_search_enabled', 'false') = 'true')::BIGINT AS count
        FROM analytics.events
        WHERE event_type = 'comment_generated'
            AND properties->>'mode' IN ('generate', 'custom_prompt')
        GROUP BY COALESCE(properties->>'role', 'FREE')

        UNION ALL

        -- Feature: include_quote_enabled par role
        SELECT
            COALESCE(properties->>'role', 'FREE') AS role,
            'feature'::TEXT AS metric_type,
            'include_quote_enabled'::TEXT AS dimension,
            'adopted'::TEXT AS value,
            COUNT(*) FILTER (WHERE COALESCE(properties->>'include_quote_enabled', 'false') = 'true')::BIGINT AS count
        FROM analytics.events
        WHERE event_type = 'comment_generated'
            AND properties->>'mode' IN ('generate', 'custom_prompt')
        GROUP BY COALESCE(properties->>'role', 'FREE')

        UNION ALL

        -- Feature: custom_prompt_used par role
        SELECT
            COALESCE(properties->>'role', 'FREE') AS role,
            'feature'::TEXT AS metric_type,
            'custom_prompt_used'::TEXT AS dimension,
            'adopted'::TEXT AS value,
            COUNT(*) FILTER (WHERE COALESCE(properties->>'custom_prompt_used', 'false') = 'true')::BIGINT AS count
        FROM analytics.events
        WHERE event_type = 'comment_generated'
            AND properties->>'mode' IN ('generate', 'custom_prompt')
        GROUP BY COALESCE(properties->>'role', 'FREE')

        UNION ALL

        -- Feature: news_enrichment_enabled par role
        SELECT
            COALESCE(properties->>'role', 'FREE') AS role,
            'feature'::TEXT AS metric_type,
            'news_enrichment_enabled'::TEXT AS dimension,
            'adopted'::TEXT AS value,
            COUNT(*) FILTER (WHERE COALESCE(properties->>'news_enrichment_mode', 'disabled') != 'disabled')::BIGINT AS count
        FROM analytics.events
        WHERE event_type = 'comment_generated'
            AND properties->>'mode' IN ('generate', 'custom_prompt')
        GROUP BY COALESCE(properties->>'role', 'FREE')
    """)

    # Index UNIQUE for REFRESH CONCURRENTLY
    op.execute("""
        CREATE UNIQUE INDEX idx_usage_by_role_unique
            ON analytics.usage_by_role (role, metric_type, dimension, value)
    """)

    # Index for role filtering
    op.execute("""
        CREATE INDEX idx_usage_by_role_role
            ON analytics.usage_by_role (role)
    """)


def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS analytics.usage_by_role")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS analytics.usage_feature_adoption")
