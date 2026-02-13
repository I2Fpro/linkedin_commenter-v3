"""
Templates HTML pour les emails transactionnels trial.

Phase 04 - Plan 04-03: Notifications email Resend
4 templates HTML brandés LinkedIn AI Commenter.
"""


def get_trial_expiring_soon_html(user_name: str, days_left: int, upgrade_url: str) -> str:
    """
    Email de rappel J-3 avant expiration trial Premium.

    Args:
        user_name: Prénom de l'utilisateur
        days_left: Nombre de jours restants
        upgrade_url: URL vers la page de souscription

    Returns:
        HTML string
    """
    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Votre essai expire bientôt</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f5f5f5; padding: 20px 0;">
        <tr>
            <td align="center">
                <table role="presentation" style="max-width: 600px; width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; background-color: #0a66c2; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 600;">LinkedIn AI Commenter</h1>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px; color: #333333;">
                            <p style="margin: 0 0 16px; font-size: 16px; line-height: 24px;">Bonjour {user_name},</p>

                            <p style="margin: 0 0 16px; font-size: 16px; line-height: 24px;">
                                Votre essai Premium expire dans <strong>{days_left} jours</strong>.
                            </p>

                            <p style="margin: 0 0 24px; font-size: 16px; line-height: 24px;">
                                Pour continuer à bénéficier de commentaires IA illimités et de toutes les fonctionnalités Premium,
                                passez dès maintenant à un abonnement payant.
                            </p>

                            <!-- CTA Button -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{upgrade_url}" style="display: inline-block; padding: 14px 32px; background-color: #0a66c2; color: #ffffff; text-decoration: none; border-radius: 24px; font-size: 16px; font-weight: 600;">
                                            Passer à Premium
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin: 24px 0 0; font-size: 14px; line-height: 20px; color: #666666;">
                                Après expiration, vous bénéficierez de 3 jours de grâce avec accès MEDIUM (5 commentaires/jour),
                                puis retour automatique au plan FREE.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; text-align: center; border-top: 1px solid #e5e5e5; background-color: #f9f9f9; border-radius: 0 0 8px 8px;">
                            <p style="margin: 0; font-size: 12px; color: #999999;">
                                © 2026 LinkedIn AI Commenter. Tous droits réservés.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def get_grace_started_html(user_name: str, grace_days: int, upgrade_url: str) -> str:
    """
    Email d'information début période de grâce MEDIUM.

    Args:
        user_name: Prénom de l'utilisateur
        grace_days: Nombre de jours de grâce
        upgrade_url: URL vers la page de souscription

    Returns:
        HTML string
    """
    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Période de grâce activée</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f5f5f5; padding: 20px 0;">
        <tr>
            <td align="center">
                <table role="presentation" style="max-width: 600px; width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; background-color: #0a66c2; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 600;">LinkedIn AI Commenter</h1>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px; color: #333333;">
                            <p style="margin: 0 0 16px; font-size: 16px; line-height: 24px;">Bonjour {user_name},</p>

                            <p style="margin: 0 0 16px; font-size: 16px; line-height: 24px;">
                                Votre essai Premium a expiré. Vous bénéficiez maintenant d'une <strong>période de grâce de {grace_days} jours</strong>
                                avec accès au plan MEDIUM (5 commentaires par jour).
                            </p>

                            <p style="margin: 0 0 24px; font-size: 16px; line-height: 24px;">
                                Ne perdez pas vos avantages ! Souscrivez maintenant pour retrouver l'accès Premium illimité.
                            </p>

                            <!-- CTA Button -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{upgrade_url}" style="display: inline-block; padding: 14px 32px; background-color: #0a66c2; color: #ffffff; text-decoration: none; border-radius: 24px; font-size: 16px; font-weight: 600;">
                                            Reprendre Premium
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin: 24px 0 0; font-size: 14px; line-height: 20px; color: #666666;">
                                Sans action de votre part, vous serez automatiquement basculé vers le plan FREE
                                à la fin de cette période de grâce.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; text-align: center; border-top: 1px solid #e5e5e5; background-color: #f9f9f9; border-radius: 0 0 8px 8px;">
                            <p style="margin: 0; font-size: 12px; color: #999999;">
                                © 2026 LinkedIn AI Commenter. Tous droits réservés.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def get_grace_expired_html(user_name: str, upgrade_url: str) -> str:
    """
    Email d'information fin période de grâce, retour FREE.

    Args:
        user_name: Prénom de l'utilisateur
        upgrade_url: URL vers la page de souscription

    Returns:
        HTML string
    """
    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Retour au plan FREE</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f5f5f5; padding: 20px 0;">
        <tr>
            <td align="center">
                <table role="presentation" style="max-width: 600px; width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; background-color: #0a66c2; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 600;">LinkedIn AI Commenter</h1>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px; color: #333333;">
                            <p style="margin: 0 0 16px; font-size: 16px; line-height: 24px;">Bonjour {user_name},</p>

                            <p style="margin: 0 0 16px; font-size: 16px; line-height: 24px;">
                                Votre période de grâce a expiré. Votre compte a été basculé vers le <strong>plan FREE</strong>
                                (2 commentaires par jour).
                            </p>

                            <p style="margin: 0 0 24px; font-size: 16px; line-height: 24px;">
                                Vous pouvez à tout moment reprendre un abonnement Premium pour profiter de nouveau
                                des commentaires illimités et de toutes les fonctionnalités avancées.
                            </p>

                            <!-- CTA Button -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{upgrade_url}" style="display: inline-block; padding: 14px 32px; background-color: #0a66c2; color: #ffffff; text-decoration: none; border-radius: 24px; font-size: 16px; font-weight: 600;">
                                            Passer à Premium
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin: 24px 0 0; font-size: 14px; line-height: 20px; color: #666666;">
                                Merci d'avoir essayé LinkedIn AI Commenter. Nous espérons vous revoir bientôt !
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; text-align: center; border-top: 1px solid #e5e5e5; background-color: #f9f9f9; border-radius: 0 0 8px 8px;">
                            <p style="margin: 0; font-size: 12px; color: #999999;">
                                © 2026 LinkedIn AI Commenter. Tous droits réservés.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def get_conversion_success_html(user_name: str) -> str:
    """
    Email de confirmation conversion trial → subscription payante.

    Args:
        user_name: Prénom de l'utilisateur

    Returns:
        HTML string
    """
    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bienvenue chez les Premium !</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f5f5f5; padding: 20px 0;">
        <tr>
            <td align="center">
                <table role="presentation" style="max-width: 600px; width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; background-color: #0a66c2; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 600;">LinkedIn AI Commenter</h1>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px; color: #333333;">
                            <p style="margin: 0 0 16px; font-size: 16px; line-height: 24px;">Bonjour {user_name},</p>

                            <p style="margin: 0 0 16px; font-size: 16px; line-height: 24px;">
                                <strong>Félicitations !</strong> Votre abonnement Premium a été activé avec succès.
                            </p>

                            <p style="margin: 0 0 24px; font-size: 16px; line-height: 24px;">
                                Vous bénéficiez maintenant de :
                            </p>

                            <ul style="margin: 0 0 24px; padding-left: 20px; font-size: 16px; line-height: 24px; color: #333333;">
                                <li style="margin-bottom: 8px;">Commentaires IA illimités</li>
                                <li style="margin-bottom: 8px;">Personnalisation avancée du ton</li>
                                <li style="margin-bottom: 8px;">Liste noire (blocage de profils)</li>
                                <li style="margin-bottom: 8px;">Support prioritaire</li>
                            </ul>

                            <p style="margin: 0 0 16px; font-size: 16px; line-height: 24px;">
                                Merci de nous faire confiance pour booster votre présence sur LinkedIn !
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; text-align: center; border-top: 1px solid #e5e5e5; background-color: #f9f9f9; border-radius: 0 0 8px 8px;">
                            <p style="margin: 0; font-size: 12px; color: #999999;">
                                © 2026 LinkedIn AI Commenter. Tous droits réservés.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
