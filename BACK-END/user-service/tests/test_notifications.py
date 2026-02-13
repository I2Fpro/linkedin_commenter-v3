"""
Tests E2E des notifications email trial.

Phase 04 - Plan 04-05: Tests E2E notifications
Couvre: templates HTML, email sender Resend.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from notifications.templates import (
    get_trial_expiring_soon_html,
    get_grace_started_html,
    get_grace_expired_html,
    get_conversion_success_html,
)
from notifications.email_sender import send_trial_email


class TestEmailTemplates:
    """Tests des 4 templates HTML d'emails trial."""

    def test_trial_expiring_soon_template(self):
        """Test: template J-3 expiration trial contient les infos attendues."""
        user_name = "Alice"
        days_left = 3
        upgrade_url = "https://linkedinaicommenter.com/upgrade"

        html = get_trial_expiring_soon_html(user_name, days_left, upgrade_url)

        # Assertions
        assert "Alice" in html
        assert "3 jours" in html or "3 jour" in html
        assert upgrade_url in html
        assert "expire" in html.lower()
        assert "Premium" in html or "premium" in html

    def test_grace_started_template(self):
        """Test: template debut grace contient les infos attendues."""
        user_name = "Bob"
        grace_days = 3
        upgrade_url = "https://linkedinaicommenter.com/upgrade"

        html = get_grace_started_html(user_name, grace_days, upgrade_url)

        # Assertions
        assert "Bob" in html
        assert "3 jours" in html or "3 jour" in html
        assert upgrade_url in html
        assert "grâce" in html.lower() or "grace" in html.lower()
        assert "MEDIUM" in html or "Medium" in html

    def test_grace_expired_template(self):
        """Test: template fin grace contient les infos attendues."""
        user_name = "Carol"
        upgrade_url = "https://linkedinaicommenter.com/upgrade"

        html = get_grace_expired_html(user_name, upgrade_url)

        # Assertions
        assert "Carol" in html
        assert upgrade_url in html
        assert "FREE" in html or "free" in html
        assert "expiré" in html.lower() or "expire" in html.lower()

    def test_conversion_success_template(self):
        """Test: template conversion subscription contient les infos attendues."""
        user_name = "David"

        html = get_conversion_success_html(user_name)

        # Assertions
        assert "David" in html
        assert "Premium" in html or "premium" in html
        assert "Félicitations" in html or "félicitations" in html
        assert "illimité" in html.lower() or "illimite" in html.lower()


class TestEmailSender:
    """Tests du service d'envoi email Resend."""

    def test_send_email_without_api_key_returns_false(self, monkeypatch):
        """Test: send_trial_email retourne False si RESEND_API_KEY est absent."""
        # Supprimer la cle API
        monkeypatch.delenv("RESEND_API_KEY", raising=False)

        result = send_trial_email(
            to_email="test@example.com",
            subject="Test",
            html_body="<p>Test</p>"
        )

        # Assertions
        assert result is False

    def test_send_email_with_mock_resend_returns_true(self, monkeypatch):
        """Test: send_trial_email retourne True quand Resend reussit."""
        # Mocker la cle API
        monkeypatch.setenv("RESEND_API_KEY", "re_test_key_123")

        # Mocker resend.Emails.send (avant l'import dans la fonction)
        mock_response = {"id": "email_test_123"}

        with patch("resend.Emails.send", return_value=mock_response):
            result = send_trial_email(
                to_email="test@example.com",
                subject="Test Subject",
                html_body="<p>Test Body</p>"
            )

        # Assertions
        assert result is True

    def test_send_email_resend_failure_returns_false(self, monkeypatch):
        """Test: send_trial_email retourne False quand Resend echoue."""
        # Mocker la cle API
        monkeypatch.setenv("RESEND_API_KEY", "re_test_key_123")

        # Mocker resend.Emails.send pour lever une exception
        with patch("resend.Emails.send", side_effect=Exception("Resend error")):
            result = send_trial_email(
                to_email="test@example.com",
                subject="Test Subject",
                html_body="<p>Test Body</p>"
            )

        # Assertions
        assert result is False

    def test_send_email_uses_correct_params(self, monkeypatch):
        """Test: send_trial_email passe les bons parametres a Resend."""
        # Mocker la cle API
        monkeypatch.setenv("RESEND_API_KEY", "re_test_key_123")

        # Mocker resend.Emails.send et capturer les parametres
        mock_send = MagicMock(return_value={"id": "email_test_123"})

        with patch("resend.Emails.send", mock_send):
            result = send_trial_email(
                to_email="alice@example.com",
                subject="Alice Test",
                html_body="<p>Hello Alice</p>",
                from_email="Custom Sender <custom@example.com>"
            )

        # Assertions
        assert result is True
        mock_send.assert_called_once()

        # Verifier les parametres passes
        call_args = mock_send.call_args[0][0]
        assert call_args["to"] == "alice@example.com"
        assert call_args["subject"] == "Alice Test"
        assert call_args["html"] == "<p>Hello Alice</p>"
        assert call_args["from"] == "Custom Sender <custom@example.com>"
