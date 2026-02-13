"""Create usage_trends_weekly materialized view and refresh function

Phase 6, Plan 06-03: Vue materialisee pour tendances temporelles hebdomadaires
et fonction SQL de refresh automatique des 4 vues d'usage.
"""
from alembic import op

revision = '011_create_usage_trends_weekly_and_refresh'
down_revision = '010_create_usage_feature_adoption_and_by_role'
branch_labels = None
depends_on = None


def upgrade():
    # === Vue: usage_trends_weekly ===
    op.execute("""
        CREATE MATERIALIZED VIEW analytics.usage_trends_weekly AS
        WITH date_range AS (
            SELECT
                DATE_TRUNC('week', MIN(timestamp))::DATE AS min_week,
                DATE_TRUNC('week', NOW())::DATE AS max_week
            FROM analytics.events
            WHERE event_type = 'comment_generated'
        ),
        all_weeks AS (
            SELECT generate_series(
                (SELECT min_week FROM date_range),
                (SELECT max_week FROM date_range),
                '1 week'::INTERVAL
            )::DATE AS week_start_date
        ),

        -- Parametres: toutes les valeurs distinctes par dimension
        param_dimension_values AS (
            SELECT DISTINCT 'tone'::TEXT AS dimension, properties->>'tone' AS value
            FROM analytics.events
            WHERE event_type = 'comment_generated' AND properties->>'tone' IS NOT NULL
            UNION ALL
            SELECT DISTINCT 'emotion'::TEXT, properties->>'emotion'
            FROM analytics.events
            WHERE event_type = 'comment_generated' AND properties->>'emotion' IS NOT NULL
            UNION ALL
            SELECT DISTINCT 'style'::TEXT, properties->>'style'
            FROM analytics.events
            WHERE event_type = 'comment_generated' AND properties->>'style' IS NOT NULL
            UNION ALL
            SELECT DISTINCT 'language'::TEXT, properties->>'language'
            FROM analytics.events
            WHERE event_type = 'comment_generated' AND properties->>'language' IS NOT NULL
            UNION ALL
            SELECT DISTINCT 'news_enrichment_mode'::TEXT, COALESCE(properties->>'news_enrichment_mode', 'disabled')
            FROM analytics.events
            WHERE event_type = 'comment_generated'
        ),

        -- Counts hebdo pour parametres (tous events)
        param_weekly_counts AS (
            SELECT DATE_TRUNC('week', timestamp)::DATE AS week_start_date,
                'tone'::TEXT AS dimension, properties->>'tone' AS value, COUNT(*) AS usage_count
            FROM analytics.events
            WHERE event_type = 'comment_generated' AND properties->>'tone' IS NOT NULL
            GROUP BY 1, properties->>'tone'
            UNION ALL
            SELECT DATE_TRUNC('week', timestamp)::DATE, 'emotion'::TEXT, properties->>'emotion', COUNT(*)
            FROM analytics.events
            WHERE event_type = 'comment_generated' AND properties->>'emotion' IS NOT NULL
            GROUP BY 1, properties->>'emotion'
            UNION ALL
            SELECT DATE_TRUNC('week', timestamp)::DATE, 'style'::TEXT, properties->>'style', COUNT(*)
            FROM analytics.events
            WHERE event_type = 'comment_generated' AND properties->>'style' IS NOT NULL
            GROUP BY 1, properties->>'style'
            UNION ALL
            SELECT DATE_TRUNC('week', timestamp)::DATE, 'language'::TEXT, properties->>'language', COUNT(*)
            FROM analytics.events
            WHERE event_type = 'comment_generated' AND properties->>'language' IS NOT NULL
            GROUP BY 1, properties->>'language'
            UNION ALL
            SELECT DATE_TRUNC('week', timestamp)::DATE, 'news_enrichment_mode'::TEXT,
                COALESCE(properties->>'news_enrichment_mode', 'disabled'), COUNT(*)
            FROM analytics.events
            WHERE event_type = 'comment_generated'
            GROUP BY 1, COALESCE(properties->>'news_enrichment_mode', 'disabled')
        ),

        -- Features: valeurs fixes (adopted)
        feature_dimension_values AS (
            SELECT dimension, value FROM (VALUES
                ('feature_web_search'::TEXT, 'adopted'::TEXT),
                ('feature_include_quote'::TEXT, 'adopted'::TEXT),
                ('feature_custom_prompt'::TEXT, 'adopted'::TEXT),
                ('feature_news_enrichment'::TEXT, 'adopted'::TEXT)
            ) AS t(dimension, value)
        ),

        -- Counts hebdo pour features (generations primaires uniquement)
        feature_weekly_counts AS (
            SELECT DATE_TRUNC('week', timestamp)::DATE AS week_start_date,
                'feature_web_search'::TEXT AS dimension, 'adopted'::TEXT AS value,
                COUNT(*) FILTER (WHERE COALESCE(properties->>'web_search_enabled', 'false') = 'true') AS usage_count
            FROM analytics.events
            WHERE event_type = 'comment_generated' AND properties->>'mode' IN ('generate', 'custom_prompt')
            GROUP BY 1
            UNION ALL
            SELECT DATE_TRUNC('week', timestamp)::DATE,
                'feature_include_quote'::TEXT, 'adopted'::TEXT,
                COUNT(*) FILTER (WHERE COALESCE(properties->>'include_quote_enabled', 'false') = 'true')
            FROM analytics.events
            WHERE event_type = 'comment_generated' AND properties->>'mode' IN ('generate', 'custom_prompt')
            GROUP BY 1
            UNION ALL
            SELECT DATE_TRUNC('week', timestamp)::DATE,
                'feature_custom_prompt'::TEXT, 'adopted'::TEXT,
                COUNT(*) FILTER (WHERE COALESCE(properties->>'custom_prompt_used', 'false') = 'true')
            FROM analytics.events
            WHERE event_type = 'comment_generated' AND properties->>'mode' IN ('generate', 'custom_prompt')
            GROUP BY 1
            UNION ALL
            SELECT DATE_TRUNC('week', timestamp)::DATE,
                'feature_news_enrichment'::TEXT, 'adopted'::TEXT,
                COUNT(*) FILTER (WHERE COALESCE(properties->>'news_enrichment_mode', 'disabled') != 'disabled')
            FROM analytics.events
            WHERE event_type = 'comment_generated' AND properties->>'mode' IN ('generate', 'custom_prompt')
            GROUP BY 1
        ),

        -- Combiner dimensions et counts
        all_dimension_values AS (
            SELECT * FROM param_dimension_values
            UNION ALL
            SELECT * FROM feature_dimension_values
        ),
        all_weekly_counts AS (
            SELECT * FROM param_weekly_counts
            UNION ALL
            SELECT * FROM feature_weekly_counts
        ),

        -- CROSS JOIN pour combler les semaines vides
        complete_weeks AS (
            SELECT
                aw.week_start_date,
                dv.dimension,
                dv.value,
                COALESCE(wc.usage_count, 0)::BIGINT AS usage_count
            FROM all_weeks aw
            CROSS JOIN all_dimension_values dv
            LEFT JOIN all_weekly_counts wc
                ON aw.week_start_date = wc.week_start_date
                AND dv.dimension = wc.dimension
                AND dv.value = wc.value
        )

        -- Resultat final avec growth_rate via LAG()
        SELECT
            week_start_date,
            dimension,
            value,
            usage_count,
            ROUND(
                (usage_count - LAG(usage_count, 1) OVER (PARTITION BY dimension, value ORDER BY week_start_date)) * 100.0
                / NULLIF(LAG(usage_count, 1) OVER (PARTITION BY dimension, value ORDER BY week_start_date), 0),
                2
            )::NUMERIC AS growth_rate
        FROM complete_weeks
    """)

    # Index UNIQUE for REFRESH CONCURRENTLY
    op.execute("""
        CREATE UNIQUE INDEX idx_usage_trends_weekly_unique
            ON analytics.usage_trends_weekly (week_start_date, dimension, value)
    """)

    # Index for dimension and date filtering
    op.execute("""
        CREATE INDEX idx_usage_trends_weekly_dimension
            ON analytics.usage_trends_weekly (dimension, week_start_date DESC)
    """)

    # === Fonction SQL de refresh pour les 4 vues d'usage ===
    op.execute("""
        CREATE OR REPLACE FUNCTION analytics.refresh_usage_views()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.usage_parameter_distribution;
            REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.usage_feature_adoption;
            REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.usage_by_role;
            REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.usage_trends_weekly;
            RAISE NOTICE 'All usage views refreshed at %', NOW();
        END;
        $$ LANGUAGE plpgsql
    """)

    # === Setup pg_cron (tentative, avec gestion d'erreur) ===
    op.execute("""
        DO $$
        BEGIN
            CREATE EXTENSION IF NOT EXISTS pg_cron;

            PERFORM cron.schedule(
                'refresh-usage-views',
                '0 2 * * *',
                'SELECT analytics.refresh_usage_views()'
            );

            RAISE NOTICE 'pg_cron configured: daily refresh at 2am UTC';
        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'pg_cron not available (%). Use external cron: psql -c "SELECT analytics.refresh_usage_views()"', SQLERRM;
        END;
        $$
    """)


def downgrade():
    # Tenter de desactiver le job pg_cron
    op.execute("""
        DO $$
        BEGIN
            PERFORM cron.unschedule('refresh-usage-views');
        EXCEPTION
            WHEN OTHERS THEN NULL;
        END;
        $$
    """)

    # Supprimer la fonction de refresh
    op.execute("DROP FUNCTION IF EXISTS analytics.refresh_usage_views()")

    # Supprimer la vue materialisee
    op.execute("DROP MATERIALIZED VIEW IF EXISTS analytics.usage_trends_weekly")
