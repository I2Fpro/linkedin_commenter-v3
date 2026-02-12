"""Create analytics schema with partitioned events table

Revision ID: 006_create_analytics_schema
Revises: 005_add_blacklist_entries_table
Create Date: 2026-02-12

Phase 01 - Task 01-01: PostgreSQL Analytics Schema
Cree le schema analytics avec une table events partitionnee par mois,
indexes optimises pour les requetes temporelles, et fonctions SQL pour
la gestion automatique des partitions futures et la purge des anciennes.

Manual migration - partitioned tables not supported by Alembic autogenerate
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_create_analytics_schema'
down_revision = '005_add_blacklist_entries_table'
branch_labels = None
depends_on = None


def upgrade():
    """
    Cree le schema analytics avec table partitionnee et fonctions de gestion.

    Structure:
    - Schema analytics
    - Table events partitionnee par timestamp (RANGE mensuel)
    - Indexes: timestamp, event_type, user_id, properties (GIN)
    - Partitions initiales: 2026_02, 2026_03, default
    - Fonctions: create_future_partitions(), purge_old_partitions()
    """

    # 1. Create analytics schema
    op.execute("CREATE SCHEMA IF NOT EXISTS analytics")

    # 2. Create partitioned parent table
    # Note: PRIMARY KEY must include timestamp (partition key requirement)
    op.execute("""
        CREATE TABLE analytics.events (
            id UUID DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            event_type VARCHAR(100) NOT NULL,
            properties JSONB DEFAULT '{}',
            timestamp TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            PRIMARY KEY (id, timestamp)
        ) PARTITION BY RANGE (timestamp)
    """)

    # 3. Create indexes on parent table
    op.execute("CREATE INDEX idx_events_timestamp ON analytics.events (timestamp)")
    op.execute("CREATE INDEX idx_events_event_type ON analytics.events (event_type)")
    op.execute("CREATE INDEX idx_events_user_id ON analytics.events (user_id)")
    op.execute("CREATE INDEX idx_events_properties ON analytics.events USING GIN (properties)")

    # 4. Create DEFAULT partition
    op.execute("""
        CREATE TABLE analytics.events_default PARTITION OF analytics.events DEFAULT
    """)

    # 5. Create initial monthly partitions (2026_02 and 2026_03)
    op.execute("""
        CREATE TABLE analytics.events_2026_02 PARTITION OF analytics.events
            FOR VALUES FROM ('2026-02-01') TO ('2026-03-01')
    """)

    op.execute("""
        CREATE TABLE analytics.events_2026_03 PARTITION OF analytics.events
            FOR VALUES FROM ('2026-03-01') TO ('2026-04-01')
    """)

    # 6. Create function to automatically create future partitions
    op.execute("""
        CREATE OR REPLACE FUNCTION analytics.create_future_partitions()
        RETURNS void AS $$
        DECLARE
            current_month DATE;
            next_month DATE;
            next_next_month DATE;
            partition_name TEXT;
            start_date TEXT;
            end_date TEXT;
        BEGIN
            -- Get current date and calculate next 2 months
            current_month := DATE_TRUNC('month', CURRENT_DATE);
            next_month := current_month + INTERVAL '1 month';
            next_next_month := current_month + INTERVAL '2 months';

            -- Create partition for next month if it doesn't exist
            partition_name := 'events_' || TO_CHAR(next_month, 'YYYY_MM');
            IF NOT EXISTS (
                SELECT 1 FROM pg_tables
                WHERE schemaname = 'analytics'
                AND tablename = partition_name
            ) THEN
                start_date := TO_CHAR(next_month, 'YYYY-MM-DD');
                end_date := TO_CHAR(next_next_month, 'YYYY-MM-DD');

                EXECUTE format(
                    'CREATE TABLE analytics.%I PARTITION OF analytics.events FOR VALUES FROM (%L) TO (%L)',
                    partition_name,
                    start_date,
                    end_date
                );

                RAISE NOTICE 'Created partition: %', partition_name;
            END IF;

            -- Create partition for month after next if it doesn't exist
            partition_name := 'events_' || TO_CHAR(next_next_month, 'YYYY_MM');
            IF NOT EXISTS (
                SELECT 1 FROM pg_tables
                WHERE schemaname = 'analytics'
                AND tablename = partition_name
            ) THEN
                start_date := TO_CHAR(next_next_month, 'YYYY-MM-DD');
                end_date := TO_CHAR(next_next_month + INTERVAL '1 month', 'YYYY-MM-DD');

                EXECUTE format(
                    'CREATE TABLE analytics.%I PARTITION OF analytics.events FOR VALUES FROM (%L) TO (%L)',
                    partition_name,
                    start_date,
                    end_date
                );

                RAISE NOTICE 'Created partition: %', partition_name;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 7. Create function to purge old partitions
    op.execute("""
        CREATE OR REPLACE FUNCTION analytics.purge_old_partitions(retention_days INTEGER DEFAULT 90)
        RETURNS void AS $$
        DECLARE
            partition_record RECORD;
            partition_month DATE;
            cutoff_date DATE;
            year_part TEXT;
            month_part TEXT;
        BEGIN
            -- Calculate cutoff date
            cutoff_date := CURRENT_DATE - (retention_days || ' days')::INTERVAL;

            -- Loop through all event partitions
            FOR partition_record IN
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'analytics'
                AND tablename LIKE 'events_____\___'
                AND tablename != 'events_default'
            LOOP
                -- Parse YYYY_MM from tablename (format: events_2026_02)
                year_part := SUBSTRING(partition_record.tablename FROM 8 FOR 4);
                month_part := SUBSTRING(partition_record.tablename FROM 13 FOR 2);

                -- Convert to date (first day of the month)
                partition_month := TO_DATE(year_part || '-' || month_part || '-01', 'YYYY-MM-DD');

                -- Drop partition if older than retention period
                IF partition_month < DATE_TRUNC('month', cutoff_date) THEN
                    EXECUTE format('DROP TABLE analytics.%I', partition_record.tablename);
                    RAISE NOTICE 'Dropped old partition: % (month: %)',
                        partition_record.tablename,
                        TO_CHAR(partition_month, 'YYYY-MM');
                END IF;
            END LOOP;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade():
    """
    Supprime le schema analytics et toutes ses tables/fonctions.

    ATTENTION: Cette operation supprime definitivement toutes les donnees analytics.
    """
    op.execute("DROP SCHEMA IF EXISTS analytics CASCADE")
