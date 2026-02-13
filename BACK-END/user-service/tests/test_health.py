"""
Tests E2E des health checks analytics.

Phase 04 - Plan 04-05: Tests E2E health checks
Couvre: check_events_volume, check_future_partitions, endpoint /health/analytics.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from health.analytics_checks import check_events_volume, check_future_partitions


class TestEventsVolumeCheck:
    """Tests du check de volume d'events (24h)."""

    def test_healthy_when_events_exist(self, db):
        """Test: check_events_volume retourne healthy si events > 0."""
        # Mocker le resultat SQL pour simuler 100 events
        with patch.object(db, "execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar.return_value = 100
            mock_execute.return_value = mock_result

            result = check_events_volume(db)

        # Assertions
        assert result["status"] == "healthy"
        assert result["count"] == 100
        assert result["threshold"] == "> 0"

    def test_unhealthy_when_no_events(self, db):
        """Test: check_events_volume retourne unhealthy si events = 0."""
        # Mocker le resultat SQL pour simuler 0 events
        with patch.object(db, "execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar.return_value = 0
            mock_execute.return_value = mock_result

            result = check_events_volume(db)

        # Assertions
        assert result["status"] == "unhealthy"
        assert result["count"] == 0
        assert "No events in last 24h" in result["message"]

    def test_unhealthy_on_database_error(self, db):
        """Test: check_events_volume retourne unhealthy en cas d'erreur DB."""
        # Mocker une exception SQL
        with patch.object(db, "execute", side_effect=Exception("DB connection error")):
            result = check_events_volume(db)

        # Assertions
        assert result["status"] == "unhealthy"
        assert result["count"] == -1
        assert "Check failed" in result["message"]


class TestFuturePartitionsCheck:
    """Tests du check de partitions futures (>= 2 mois)."""

    def test_healthy_when_enough_future_partitions(self, db):
        """Test: check_future_partitions retourne healthy si >= 2 partitions futures."""
        # Mocker le resultat SQL pour simuler 3 partitions futures
        now = datetime.now(timezone.utc)
        current_ym = now.strftime("%Y_%m")

        # Generer des noms de partitions: 1 passee, 1 actuelle, 3 futures
        partitions = [
            (f"events_{(now - timedelta(days=60)).strftime('%Y_%m')}",),
            (f"events_{current_ym}",),
            (f"events_{(now + timedelta(days=30)).strftime('%Y_%m')}",),
            (f"events_{(now + timedelta(days=60)).strftime('%Y_%m')}",),
            (f"events_{(now + timedelta(days=90)).strftime('%Y_%m')}",),
        ]

        with patch.object(db, "execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.fetchall.return_value = partitions
            mock_execute.return_value = mock_result

            result = check_future_partitions(db)

        # Assertions
        assert result["status"] == "healthy"
        assert result["future_partitions"] >= 2
        assert result["total_partitions"] == len(partitions)
        assert result["threshold"] == ">= 2 future months"

    def test_degraded_when_few_future_partitions(self, db):
        """Test: check_future_partitions retourne degraded si < 2 partitions futures."""
        # Mocker le resultat SQL pour simuler 1 seule partition future
        now = datetime.now(timezone.utc)
        current_ym = now.strftime("%Y_%m")

        partitions = [
            (f"events_{current_ym}",),
            (f"events_{(now + timedelta(days=30)).strftime('%Y_%m')}",),
        ]

        with patch.object(db, "execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.fetchall.return_value = partitions
            mock_execute.return_value = mock_result

            result = check_future_partitions(db)

        # Assertions
        assert result["status"] == "degraded"
        assert result["future_partitions"] < 2
        assert "Only" in result["message"]

    def test_unhealthy_on_database_error(self, db):
        """Test: check_future_partitions retourne unhealthy en cas d'erreur DB."""
        # Mocker une exception SQL
        with patch.object(db, "execute", side_effect=Exception("DB error")):
            result = check_future_partitions(db)

        # Assertions
        assert result["status"] == "unhealthy"
        assert result["future_partitions"] == -1
        assert "Check failed" in result["message"]


class TestHealthEndpoint:
    """Tests du endpoint GET /health/analytics."""

    def test_health_endpoint_accessible_without_auth(self, client):
        """Test: endpoint /health/analytics accessible sans auth."""
        # Mocker les checks pour ne pas interroger analytics.* sur SQLite
        with patch("main.check_events_volume") as mock_events, \
             patch("main.check_future_partitions") as mock_partitions:

            mock_events.return_value = {
                "status": "healthy",
                "count": 50,
                "threshold": "> 0",
                "message": "Events flowing normally"
            }
            mock_partitions.return_value = {
                "status": "healthy",
                "future_partitions": 3,
                "total_partitions": 5,
                "threshold": ">= 2 future months",
                "message": "3 future partitions ready"
            }

            response = client.get("/health/analytics")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "events_last_24h" in data["checks"]
        assert "future_partitions" in data["checks"]

    def test_health_endpoint_returns_unhealthy_when_check_fails(self, client):
        """Test: endpoint retourne 503 si un check est unhealthy."""
        # Mocker un check unhealthy
        with patch("main.check_events_volume") as mock_events, \
             patch("main.check_future_partitions") as mock_partitions:

            mock_events.return_value = {
                "status": "unhealthy",
                "count": 0,
                "threshold": "> 0",
                "message": "No events in last 24h"
            }
            mock_partitions.return_value = {
                "status": "healthy",
                "future_partitions": 3,
                "total_partitions": 5,
                "threshold": ">= 2 future months",
                "message": "3 future partitions ready"
            }

            response = client.get("/health/analytics")

        # Assertions
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"

    def test_health_endpoint_returns_degraded_status(self, client):
        """Test: endpoint retourne 503 avec status degraded si un check est degraded."""
        # Mocker un check degraded
        with patch("main.check_events_volume") as mock_events, \
             patch("main.check_future_partitions") as mock_partitions:

            mock_events.return_value = {
                "status": "healthy",
                "count": 50,
                "threshold": "> 0",
                "message": "Events flowing normally"
            }
            mock_partitions.return_value = {
                "status": "degraded",
                "future_partitions": 1,
                "total_partitions": 3,
                "threshold": ">= 2 future months",
                "message": "Only 1 future partition"
            }

            response = client.get("/health/analytics")

        # Assertions
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
