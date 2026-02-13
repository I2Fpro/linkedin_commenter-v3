"""
Service d'envoi d'emails via Resend.

Phase 04 - Plan 04-03: Notifications email Resend
Envoi non-bloquant, ne lève jamais d'exception, utilise structlog.
"""

import os
import structlog

logger = structlog.get_logger(__name__)


def send_trial_email(
    to_email: str,
    subject: str,
    html_body: str,
    from_email: str = "LinkedIn AI Commenter <noreply@linkedinaicommenter.com>"
) -> bool:
    """
    Envoie un email transactionnel via Resend.

    Cette fonction ne lève JAMAIS d'exception. En cas d'erreur,
    elle log un warning/error et retourne False.

    Args:
        to_email: Adresse email du destinataire (déchiffrée)
        subject: Sujet de l'email
        html_body: Corps HTML de l'email
        from_email: Adresse email expéditeur

    Returns:
        True si succès, False si échec ou clé API manquante
    """
    # Lazy import pour ne pas casser le service si resend n'est pas installé
    try:
        import resend
    except ImportError:
        logger.warning("resend_library_not_installed", action="email_not_sent")
        return False

    # Vérifier que la clé API est présente
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.warning("resend_api_key_missing", action="email_not_sent", to_email=to_email)
        return False

    # Configuration Resend
    resend.api_key = api_key

    try:
        # Envoi de l'email
        response = resend.Emails.send({
            "from": from_email,
            "to": to_email,
            "subject": subject,
            "html": html_body
        })

        # Succès
        logger.info(
            "email_sent_success",
            to_email=to_email,
            subject=subject,
            resend_id=response.get("id")
        )
        return True

    except Exception as e:
        # Échec (ne jamais lever l'exception)
        logger.error(
            "email_send_failed",
            to_email=to_email,
            subject=subject,
            error=str(e),
            error_type=type(e).__name__
        )
        return False
