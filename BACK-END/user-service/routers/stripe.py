from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
import stripe
import os
import logging
from datetime import datetime

from database import get_db
from models import User, StripeEvent, RoleType
from auth import get_current_user

# Configuration du logging
logger = logging.getLogger(__name__)

# Configuration de Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter()

# Mapping des plans vers les price IDs
STRIPE_PRICE_IDS = {
    "medium": os.getenv("STRIPE_PRICE_MEDIUM_MONTHLY"),
    "premium": os.getenv("STRIPE_PRICE_PREMIUM_MONTHLY")
}

class CheckoutSessionRequest(BaseModel):
    plan: str  # "medium" ou "premium"

class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str

class CustomerPortalResponse(BaseModel):
    portal_url: str

class InvoiceItem(BaseModel):
    amount: int
    currency: str
    created: int
    status: str
    invoice_pdf: str

class InvoicesResponse(BaseModel):
    invoices: list[InvoiceItem]

@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Créer une session de paiement Stripe pour un abonnement Medium ou Premium

    - **plan**: Type d'abonnement ("medium" ou "premium")
    - Retourne l'URL de paiement Stripe et l'ID de session
    """
    try:
        # Validation du plan demandé
        plan_lower = request.plan.lower()
        if plan_lower not in STRIPE_PRICE_IDS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan invalide. Valeurs acceptées: 'medium', 'premium'. Reçu: '{request.plan}'"
            )

        price_id = STRIPE_PRICE_IDS[plan_lower]

        # Vérification que le price_id est configuré
        if not price_id or price_id.startswith("price_") is False:
            logger.error(f"Price ID manquant ou invalide pour le plan {plan_lower}: {price_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Configuration Stripe incomplète. Veuillez contacter l'administrateur."
            )

        # URLs de succès et d'annulation
        success_url = os.getenv("STRIPE_SUCCESS_URL", "__STRIPE_SUCCESS_URL__")
        cancel_url = os.getenv("STRIPE_CANCEL_URL", "__STRIPE_CANCEL_URL__")

        # Paramètres de la session Stripe
        session_params = {
            "mode": "subscription",
            "line_items": [{
                "price": price_id,
                "quantity": 1,
            }],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": {
                "user_id": str(current_user.id),
                "email": current_user.email,
                "plan": plan_lower
            }
        }

        # Si l'utilisateur a déjà un customer_id Stripe, on l'utilise
        if hasattr(current_user, 'stripe_customer_id') and current_user.stripe_customer_id:
            session_params["customer"] = current_user.stripe_customer_id
            logger.info(f"Utilisation du customer Stripe existant: {current_user.stripe_customer_id}")
        else:
            # Sinon, on crée un nouveau customer avec l'email de l'utilisateur
            session_params["customer_email"] = current_user.email
            logger.info(f"Création d'un nouveau customer Stripe pour: {current_user.email}")

        # Création de la session Stripe
        checkout_session = stripe.checkout.Session.create(**session_params)

        logger.info(f"Session Stripe créée avec succès: {checkout_session.id} pour l'utilisateur {current_user.id} (plan: {plan_lower})")
        logger.info(f"URL de la session Stripe: {checkout_session.url}")

        return CheckoutSessionResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id
        )

    except stripe.StripeError as e:
        logger.error(f"Erreur Stripe lors de la création de la session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la communication avec Stripe: {str(e)}"
        )
    except HTTPException:
        # Re-lever les HTTPException sans les wrapper
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la création de la session Stripe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur inattendue s'est produite. Veuillez réessayer."
        )


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook Stripe pour gérer les événements de paiement

    Cet endpoint reçoit les événements Stripe et met à jour la base de données en conséquence.

    Événements gérés :
    - checkout.session.completed : Paiement d'abonnement réussi
    - invoice.paid : Paiement de facture récurrent
    - invoice.payment_failed : Échec de paiement
    - customer.subscription.updated : Mise à jour d'abonnement
    - customer.subscription.deleted : Annulation d'abonnement
    """

    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    if not webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET n'est pas configuré")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuration webhook Stripe manquante"
        )

    try:
        # Vérification de la signature Stripe
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )

        logger.info(f"Événement Stripe reçu: {event['type']} (ID: {event['id']})")

        # Vérifier si l'événement a déjà été traité (déduplication)
        existing_event = db.query(StripeEvent).filter(StripeEvent.id == event['id']).first()
        if existing_event:
            logger.info(f"Événement {event['id']} déjà traité, ignoré")
            return {"status": "success", "message": "Event already processed"}

        # Enregistrer l'événement comme traité
        stripe_event = StripeEvent(
            id=event['id'],
            type=event['type'],
            processed_at=datetime.utcnow(),
            data=event['data']
        )
        db.add(stripe_event)
        db.commit()

        # Traiter l'événement selon son type
        if event['type'] == 'checkout.session.completed':
            await handle_checkout_completed(event, db)
        elif event['type'] == 'invoice.paid':
            await handle_invoice_paid(event, db)
        elif event['type'] == 'invoice.payment_failed':
            await handle_payment_failed(event, db)
        elif event['type'] == 'customer.subscription.updated':
            await handle_subscription_updated(event, db)
        elif event['type'] == 'customer.subscription.deleted':
            await handle_subscription_deleted(event, db)
        else:
            logger.info(f"Événement {event['type']} non géré, ignoré")

        return {"status": "success"}

    except stripe.SignatureVerificationError as e:
        logger.error(f"Erreur de vérification de signature webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signature webhook invalide"
        )
    except Exception as e:
        logger.error(f"Erreur lors du traitement du webhook Stripe: {str(e)}")
        # Ne pas lever d'exception pour éviter que Stripe ne réessaye indéfiniment
        # On retourne un 200 même en cas d'erreur interne
        return {"status": "error", "message": str(e)}


async def handle_checkout_completed(event: dict, db: Session):
    """
    Gérer l'événement checkout.session.completed

    Cet événement est déclenché quand un utilisateur termine avec succès un paiement.
    """
    session = event['data']['object']

    try:
        # Récupérer les informations de la session
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        metadata = session.get('metadata', {})

        user_id = metadata.get('user_id')
        plan = metadata.get('plan')

        if not user_id:
            logger.error(f"user_id manquant dans les métadonnées de la session {session['id']}")
            return

        # Récupérer l'utilisateur
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"Utilisateur {user_id} non trouvé pour la session {session['id']}")
            return

        # Mettre à jour l'utilisateur avec les informations Stripe
        user.stripe_customer_id = customer_id
        user.stripe_subscription_id = subscription_id
        user.subscription_status = 'active'

        # Mettre à jour le rôle selon le plan
        if plan == 'medium':
            user.role = RoleType.MEDIUM
        elif plan == 'premium':
            user.role = RoleType.PREMIUM

        db.commit()

        logger.info(f"Utilisateur {user_id} mis à jour avec succès: plan={plan}, customer={customer_id}, subscription={subscription_id}")

    except Exception as e:
        logger.error(f"Erreur lors du traitement de checkout.session.completed: {str(e)}")
        db.rollback()
        raise


async def handle_invoice_paid(event: dict, db: Session):
    """
    Gérer l'événement invoice.paid

    Cet événement est déclenché quand une facture récurrente est payée avec succès.
    """
    invoice = event['data']['object']

    try:
        customer_id = invoice.get('customer')
        subscription_id = invoice.get('subscription')

        # Récupérer l'utilisateur par customer_id
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            logger.warning(f"Utilisateur non trouvé pour customer_id {customer_id}")
            return

        # Mettre à jour le statut de l'abonnement
        user.subscription_status = 'active'
        db.commit()

        logger.info(f"Facture payée pour l'utilisateur {user.id}, abonnement {subscription_id} actif")

    except Exception as e:
        logger.error(f"Erreur lors du traitement de invoice.paid: {str(e)}")
        db.rollback()
        raise


async def handle_payment_failed(event: dict, db: Session):
    """
    Gérer l'événement invoice.payment_failed

    Cet événement est déclenché quand un paiement récurrent échoue.
    """
    invoice = event['data']['object']

    try:
        customer_id = invoice.get('customer')

        # Récupérer l'utilisateur par customer_id
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            logger.warning(f"Utilisateur non trouvé pour customer_id {customer_id}")
            return

        # Mettre à jour le statut de l'abonnement
        user.subscription_status = 'past_due'
        db.commit()

        logger.warning(f"Paiement échoué pour l'utilisateur {user.id}, statut: past_due")

    except Exception as e:
        logger.error(f"Erreur lors du traitement de invoice.payment_failed: {str(e)}")
        db.rollback()
        raise


async def handle_subscription_updated(event: dict, db: Session):
    """
    Gérer l'événement customer.subscription.updated

    Cet événement est déclenché quand un abonnement est modifié.
    """
    subscription = event['data']['object']

    try:
        customer_id = subscription.get('customer')
        subscription_id = subscription.get('id')
        status = subscription.get('status')

        # Récupérer l'utilisateur par customer_id
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            logger.warning(f"Utilisateur non trouvé pour customer_id {customer_id}")
            return

        # Mettre à jour le statut de l'abonnement
        user.subscription_status = status

        # Si l'abonnement est annulé ou expiré, rétrograder l'utilisateur
        if status in ['canceled', 'unpaid', 'incomplete_expired']:
            user.role = RoleType.FREE
            logger.info(f"Utilisateur {user.id} rétrogradé vers FREE suite à statut: {status}")

        db.commit()

        logger.info(f"Abonnement {subscription_id} mis à jour pour l'utilisateur {user.id}, statut: {status}")

    except Exception as e:
        logger.error(f"Erreur lors du traitement de customer.subscription.updated: {str(e)}")
        db.rollback()
        raise


async def handle_subscription_deleted(event: dict, db: Session):
    """
    Gérer l'événement customer.subscription.deleted

    Cet événement est déclenché quand un abonnement est annulé.
    """
    subscription = event['data']['object']

    try:
        customer_id = subscription.get('customer')
        subscription_id = subscription.get('id')

        # Récupérer l'utilisateur par customer_id
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            logger.warning(f"Utilisateur non trouvé pour customer_id {customer_id}")
            return

        # Rétrograder l'utilisateur vers FREE
        user.role = RoleType.FREE
        user.subscription_status = 'canceled'
        user.stripe_subscription_id = None

        db.commit()

        logger.info(f"Abonnement {subscription_id} supprimé pour l'utilisateur {user.id}, rétrogradé vers FREE")

    except Exception as e:
        logger.error(f"Erreur lors du traitement de customer.subscription.deleted: {str(e)}")
        db.rollback()
        raise


@router.post("/create-customer-portal-session", response_model=CustomerPortalResponse)
async def create_customer_portal_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Créer une session Customer Portal Stripe pour gérer l'abonnement

    Permet à l'utilisateur de :
    - Mettre à jour son moyen de paiement
    - Changer de formule (medium ↔ premium)
    - Annuler son abonnement

    Retourne l'URL du portail Stripe
    """
    try:
        # Vérifier que l'utilisateur a un customer_id Stripe
        if not hasattr(current_user, 'stripe_customer_id') or not current_user.stripe_customer_id:
            logger.warning(f"Tentative d'accès au portail client sans stripe_customer_id pour l'utilisateur {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucun abonnement Stripe actif. Veuillez d'abord souscrire à un plan."
            )

        # URL de retour après utilisation du portail
        return_url = os.getenv("STRIPE_PORTAL_RETURN_URL", "__STRIPE_PORTAL_RETURN_URL__")

        # Créer la session du portail client
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=return_url,
        )

        logger.info(f"Session portail Stripe créée avec succès pour l'utilisateur {current_user.id} (customer: {current_user.stripe_customer_id})")

        return CustomerPortalResponse(
            portal_url=portal_session.url
        )

    except stripe.StripeError as e:
        logger.error(f"Erreur Stripe lors de la création de la session portail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la communication avec Stripe: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la création de la session portail Stripe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur inattendue s'est produite. Veuillez réessayer."
        )


@router.get("/invoices", response_model=InvoicesResponse)
async def get_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer l'historique des factures Stripe de l'utilisateur connecté

    Retourne les 12 dernières factures avec :
    - Montant et devise
    - Date de création
    - Statut (traduit en français)
    - Lien de téléchargement PDF

    Nécessite une authentification JWT et un stripe_customer_id valide
    """
    try:
        # Vérifier que l'utilisateur a un customer_id Stripe
        if not hasattr(current_user, 'stripe_customer_id') or not current_user.stripe_customer_id:
            logger.warning(f"Tentative d'accès aux factures sans stripe_customer_id pour l'utilisateur {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucun abonnement Stripe actif. Vous devez d'abord souscrire à un plan."
            )

        # Vérifier que l'utilisateur n'est pas FREE
        if current_user.role == RoleType.FREE:
            logger.warning(f"Utilisateur FREE {current_user.id} tentant d'accéder aux factures")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cette fonctionnalité est réservée aux abonnés Medium et Premium."
            )

        # Récupérer les 12 dernières factures depuis Stripe
        invoices_list = stripe.Invoice.list(
            customer=current_user.stripe_customer_id,
            limit=12
        )

        # Mapping des statuts Stripe vers français
        status_translation = {
            "paid": "Payée",
            "open": "En attente",
            "draft": "Brouillon",
            "uncollectible": "Irrécouvrable",
            "void": "Annulée"
        }

        # Formater les factures
        formatted_invoices = []
        for invoice in invoices_list.data:
            # Ne pas inclure les factures sans PDF
            if not invoice.invoice_pdf:
                continue

            formatted_invoices.append(InvoiceItem(
                amount=invoice.total,
                currency=invoice.currency,
                created=invoice.created,
                status=status_translation.get(invoice.status, invoice.status),
                invoice_pdf=invoice.invoice_pdf
            ))

        logger.info(f"Récupération de {len(formatted_invoices)} factures pour l'utilisateur {current_user.id}")

        return InvoicesResponse(invoices=formatted_invoices)

    except stripe.StripeError as e:
        logger.error(f"Erreur Stripe lors de la récupération des factures: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la communication avec Stripe: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération des factures: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur inattendue s'est produite. Veuillez réessayer."
        )
