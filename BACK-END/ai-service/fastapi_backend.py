"""
API FastAPI pour LinkedIn AI Commenter (HTTPS via uvicorn) - VERSION MULTILINGUE
- Support Français/Anglais pour les commentaires générés
- CORS minimaliste compatible Chrome Extension
- Auth Google via Bearer token
- Génération via OpenAI (clé en variable d'environnement)
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from openai import OpenAI
import logging
import httpx
import os
import time

from auth_middleware import get_current_user, auth_middleware
from config_py import OPENAI_API_KEY, MODEL_NAME, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_ID_WEB, validate_environment
from dotenv import load_dotenv

# Import du module News
from modules.news.routes import router as news_router
from modules.news.database import news_db

# Import PostHog
from posthog_service import posthog_service

# Import utilitaire d'identification anonyme
from ident import resolve_distinct_id

# Charger les variables d'environnement
load_dotenv()

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Validation env ---
validate_environment()

# Log de l'état de PostHog au démarrage
logger.info(f"PostHog initialized: enabled={posthog_service.enabled}, api_key={'***' if posthog_service.api_key else 'NOT SET'}")

# --- App ---
app = FastAPI(title="LinkedIn AI Commenter Backend", version="4.0.0")

# Inclure les routes du module News
app.include_router(news_router)

# --- Exception Handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log et retourne les erreurs de validation Pydantic"""
    logger.error(f"❌ Validation Error: {exc.errors()}")
    logger.error(f"❌ Body received: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )

# --- CORS (KISS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",                       # autorise les tests locaux et preflight génériques
        "chrome-extension://*",    # extensions Chrome
        "__AI_API_URL__",
        "__SITE_URL__",  # Site web public
    ],
    allow_credentials=False,         # IMPORTANT: extensions Chrome + fetch sans cookies
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],           # Autoriser Origin, Authorization, Content-Type...
    expose_headers=["*"]
)

# --- OpenAI client ---
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Stockage du dernier prompt (pour debug) ---
last_prompt_data = {
    "system_prompt": None,
    "user_prompt": None,
    "parameters": None,
    "timestamp": None,
    "action_type": None
}

# --- Service URLs ---
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8444")
BACKEND_EXTERNAL_URL = os.getenv("BACKEND_EXTERNAL_URL", "__AI_API_URL__")
USER_SERVICE_EXTERNAL_URL = os.getenv("USER_SERVICE_EXTERNAL_URL", "__USERS_API_URL__")

# ---------- Schémas ----------
class NewsItem(BaseModel):
    """Actualité LinkedIn"""
    title: str
    url: str

class GenerateCommentsRequest(BaseModel):
    """Corps de requête: génération de commentaires"""
    post: Optional[str] = None
    postParent: Optional[str] = None
    isComment: bool = False
    includePostParent: bool = False
    tone: str = "professionnel"
    length: int = 40
    optionsCount: int = 2
    commentLanguage: str = "fr"  # Nouvelle option pour la langue des commentaires
    # Nouveaux paramètres contextuels (prioritaires sur tone)
    emotion: Optional[str] = None  # admiration, inspiration, curiosity, gratitude, empathy, skepticism
    intensity: Optional[str] = None  # low, medium, high
    style: Optional[str] = None  # oral, professional, storytelling, poetic, humoristic, impactful, benevolent
    # Contexte des actualités LinkedIn
    newsContext: Optional[List[NewsItem]] = []
    # Mode d'enrichissement des actualités: disabled, title-only, smart-summary
    newsEnrichmentMode: str = "disabled"
    # UserId anonyme (SHA256) envoyé par le frontend pour PostHog (RGPD)
    user_id: Optional[str] = None
    # Plan utilisateur (FREE, MEDIUM, PREMIUM) pour analytics
    plan: Optional[str] = "FREE"
    # Langue de l'interface utilisateur (pour analytics)
    interface_lang: Optional[str] = "fr"

class GenerateCommentsWithPromptRequest(BaseModel):
    """Corps de requête: génération avec prompt utilisateur"""
    post: Optional[str] = None
    postParent: Optional[str] = None
    isComment: bool = False
    includePostParent: bool = False
    userPrompt: str
    tone: str = "professionnel"
    length: int = 40
    optionsCount: int = 2
    commentLanguage: str = "fr"  # Nouvelle option pour la langue des commentaires
    # Nouveaux paramètres contextuels (prioritaires sur tone)
    emotion: Optional[str] = None  # admiration, inspiration, curiosity, gratitude, empathy, skepticism
    intensity: Optional[str] = None  # low, medium, high
    style: Optional[str] = None  # oral, professional, storytelling, poetic, humoristic, impactful, benevolent
    # Contexte des actualités LinkedIn
    newsContext: Optional[List[NewsItem]] = []
    # Mode d'enrichissement des actualités: disabled, title-only, smart-summary
    newsEnrichmentMode: str = "disabled"
    # UserId anonyme (SHA256) envoyé par le frontend pour PostHog (RGPD)
    user_id: Optional[str] = None
    # Plan utilisateur (FREE, MEDIUM, PREMIUM) pour analytics
    plan: Optional[str] = "FREE"
    # Langue de l'interface utilisateur (pour analytics)
    interface_lang: Optional[str] = "fr"

class RefineCommentRequest(BaseModel):
    """Corps de requête: affiner un commentaire"""
    post: str
    originalComment: str
    userPrompt: Optional[str] = None
    refineInstructions: str
    isComment: bool = False
    tone: str = "professionnel"
    length: int = 40
    commentLanguage: str = "fr"  # Nouvelle option pour la langue des commentaires

class ResizeCommentRequest(BaseModel):
    """Corps de requête: agrandir/réduire un commentaire"""
    post: str
    originalComment: str
    resizeDirection: str
    currentWordCount: int
    tone: str = "professionnel"
    commentLanguage: str = "fr"  # Nouvelle option pour la langue des commentaires

class AuthVerifyRequest(BaseModel):
    """Corps de requête: vérification d'authentification"""
    google_token: str
    user_info: Dict[str, Any]

# ---------- Utilitaires ----------
def clean_post_content(post_content: str) -> str:
    """Normalise et tronque le contenu d'un post pour le prompt"""
    if not post_content:
        return ''
    cleaned = post_content.strip()
    return cleaned[:797] + '...' if len(cleaned) > 800 else cleaned

def get_tone_instructions(tone: str, language: str = "fr") -> str:
    """Retourne des instructions adaptées au ton demandé dans la langue spécifiée"""
    tone_map = {
        'fr': {
            'negatif': "Exprimez un désaccord constructif et respectueux",
            'amical': "Utilisez un ton chaleureux et encourageant",
            'expert': "Utilisez un vocabulaire technique et précis",
            'informatif': "Apportez des informations factuelles et neutres",
            'soutenu': "Utilisez un langage formel et élégant",
            'professionnel': "Ajoutez de la valeur avec expertise",
        },
        'en': {
            'negatif': "Express constructive and respectful disagreement",
            'amical': "Use a warm and encouraging tone",
            'expert': "Use technical and precise vocabulary",
            'informatif': "Provide factual and neutral information",
            'soutenu': "Use formal and elegant language",
            'professionnel': "Add value with expertise",
        }
    }
    
    lang_map = tone_map.get(language, tone_map['fr'])
    return lang_map.get(tone, lang_map['professionnel'])

def get_language_instruction(language: str) -> str:
    """Retourne l'instruction de langue pour le prompt"""
    if language == "en":
        return "Write the comment in English."
    else:
        return "Écrivez le commentaire en français."

def get_system_prompt(language: str) -> str:
    """Retourne le prompt système dans la langue appropriée"""
    if language == "en":
        return "You are a LinkedIn coach who writes in a natural, human style. Always respond in English."
    else:
        return "Tu es un coach LinkedIn qui écrit au style naturel, humain. Réponds toujours en français."

def get_emotion_instructions(emotion: str, intensity: str, language: str = "fr") -> str:
    """Convertit une émotion et son intensité en instructions de prompt"""
    emotions_map = {
        'fr': {
            'admiration': {
                'low': "Exprimez une appréciation sincère et respectueuse",
                'medium': "Exprimez une admiration marquée et enthousiaste",
                'high': "Exprimez une admiration profonde et inspirée"
            },
            'inspiration': {
                'low': "Montrez que vous trouvez cela intéressant",
                'medium': "Montrez-vous inspiré et motivé par cette idée",
                'high': "Exprimez une inspiration intense et transformatrice"
            },
            'curiosity': {
                'low': "Posez une question pertinente et réfléchie",
                'medium': "Exprimez une curiosité engagée avec des questions approfondies",
                'high': "Montrez une curiosité intense avec des questions stimulantes"
            },
            'gratitude': {
                'low': "Remerciez poliment pour le partage",
                'medium': "Exprimez une gratitude sincère et chaleureuse",
                'high': "Exprimez une reconnaissance profonde et émue"
            },
            'empathy': {
                'low': "Montrez de la compréhension et du soutien",
                'medium': "Exprimez une empathie marquée et bienveillante",
                'high': "Exprimez une connexion émotionnelle profonde et un soutien fort"
            },
            'skepticism': {
                'low': "Questionnez respectueusement avec ouverture",
                'medium': "Exprimez un questionnement constructif et nuancé",
                'high': "Challengez l'idée avec esprit critique tout en restant bienveillant"
            }
        },
        'en': {
            'admiration': {
                'low': "Express sincere and respectful appreciation",
                'medium': "Express marked and enthusiastic admiration",
                'high': "Express deep and inspired admiration"
            },
            'inspiration': {
                'low': "Show that you find this interesting",
                'medium': "Show yourself inspired and motivated by this idea",
                'high': "Express intense and transformative inspiration"
            },
            'curiosity': {
                'low': "Ask a relevant and thoughtful question",
                'medium': "Express engaged curiosity with in-depth questions",
                'high': "Show intense curiosity with stimulating questions"
            },
            'gratitude': {
                'low': "Thank politely for sharing",
                'medium': "Express sincere and warm gratitude",
                'high': "Express deep and heartfelt appreciation"
            },
            'empathy': {
                'low': "Show understanding and support",
                'medium': "Express marked and caring empathy",
                'high': "Express deep emotional connection and strong support"
            },
            'skepticism': {
                'low': "Question respectfully with openness",
                'medium': "Express constructive and nuanced questioning",
                'high': "Challenge the idea with critical thinking while remaining benevolent"
            }
        }
    }

    lang_map = emotions_map.get(language, emotions_map['fr'])
    emotion_map = lang_map.get(emotion, {})
    return emotion_map.get(intensity, "")

def get_style_instructions(style: str, language: str = "fr") -> str:
    """Convertit un style de langage en instructions de prompt"""
    styles_map = {
        'fr': {
            'oral': "Utilisez un style oral et conversationnel, comme si vous parliez naturellement",
            'professional': "Utilisez un style professionnel et structuré",
            'storytelling': "Racontez une histoire ou utilisez une anecdote pour illustrer votre propos",
            'poetic': "Utilisez un langage poétique, créatif et imagé",
            'humoristic': "Intégrez une touche d'humour subtil et intelligent",
            'impactful': "Créez un message percutant et mémorable avec un fort impact",
            'benevolent': "Adoptez un ton bienveillant, positif et encourageant"
        },
        'en': {
            'oral': "Use an oral and conversational style, as if speaking naturally",
            'professional': "Use a professional and structured style",
            'storytelling': "Tell a story or use an anecdote to illustrate your point",
            'poetic': "Use poetic, creative and imaginative language",
            'humoristic': "Integrate a touch of subtle and intelligent humor",
            'impactful': "Create a powerful and memorable message with strong impact",
            'benevolent': "Adopt a benevolent, positive and encouraging tone"
        }
    }

    lang_map = styles_map.get(language, styles_map['fr'])
    return lang_map.get(style, "")

def build_news_context_prompt(news_items: List[NewsItem], language: str = "fr") -> str:
    """Construit la section du prompt avec le contexte des actualités LinkedIn (mode title-only)"""
    if not news_items or len(news_items) == 0:
        return ""

    news_list = "\n".join([f"- {item.title}" for item in news_items])

    if language == "en":
        return f"""

📰 TODAY'S LINKEDIN NEWS:
{news_list}

If the post relates to one of these news items, you can make a subtle and relevant reference
to make your comment more engaging and timely. Don't force the connection if it's not natural.
"""
    else:
        return f"""

📰 ACTUALITÉS LINKEDIN DU JOUR:
{news_list}

Si le post est lié à l'une de ces actualités, tu peux faire une référence subtile
et pertinente pour rendre ton commentaire plus engageant et actuel. Ne force pas la référence
si ce n'est pas naturel.
"""

async def build_smart_news_context(post_text: str, language: str = "fr", limit: int = 3) -> tuple[str, List[str]]:
    """
    Construit un contexte enrichi via recherche vectorielle (mode smart-summary)

    Args:
        post_text: Le texte du post LinkedIn
        language: Langue de recherche (fr/en)
        limit: Nombre max d'actualités à récupérer

    Returns:
        Tuple (contexte_formaté, liste_des_actualités_utilisées)
    """
    try:
        # Importer ici pour éviter les imports circulaires
        from modules.news.service import news_processor

        # Effectuer la recherche vectorielle
        results = await news_processor.search_similar_news(post_text, language, limit)

        if not results:
            logger.info("🔍 Aucune actualité pertinente trouvée via recherche vectorielle")
            return "", []

        # Filtrer par seuil de similarité (0.7)
        filtered_results = [r for r in results if r.get("similarity", 0) > 0.7]

        if not filtered_results:
            logger.info(f"🔍 Aucune actualité avec similarité > 0.7 (max: {max([r.get('similarity', 0) for r in results]):.2f})")
            return "", []

        # Construire le bloc de contexte ET la liste des actualités
        news_lines = []
        context_used = []

        for result in filtered_results:
            title = result.get("title", "")
            summary = result.get("summary", "")
            url = result.get("url", "")
            similarity = result.get("similarity", 0)

            news_lines.append(f'- "{title}" — Résumé : {summary}')
            news_lines.append(f'  🔗 {url}')

            # Ajouter à la liste des actualités utilisées
            context_used.append(f'{title} — {summary}')

        news_block = "\n".join(news_lines)

        if language == "en":
            context = f"""

🧠 RELEVANT LINKEDIN NEWS:
{news_block}

You can reference these news items if they relate to the post, to make your comment more contextual and timely.
"""
        else:
            context = f"""

🧠 ACTUALITÉS LINKEDIN PERTINENTES :
{news_block}

Tu peux référencer ces actualités si elles sont liées au post, pour rendre ton commentaire plus contextuel et actuel.
"""

        logger.info(f"✅ Contexte enrichi créé avec {len(filtered_results)} actualités (recherche vectorielle)")
        return context, context_used

    except Exception as e:
        # En cas d'erreur, logger mais ne pas bloquer la génération
        logger.error(f"❌ Erreur lors de la recherche vectorielle: {e}")
        return "", []

async def get_news_context(
    enrichment_mode: str,
    post_text: str,
    news_context_items: Optional[List[NewsItem]],
    language: str = "fr"
) -> tuple[str, List[str]]:
    """
    Récupère le contexte des actualités selon le mode d'enrichissement

    Args:
        enrichment_mode: Mode d'enrichissement (disabled, title-only, smart-summary)
        post_text: Texte du post LinkedIn
        news_context_items: Items d'actualités envoyés par le frontend
        language: Langue de génération

    Returns:
        Tuple (bloc_de_contexte, liste_actualités_utilisées)
    """
    if enrichment_mode == "disabled":
        logger.info("📰 Mode d'enrichissement: disabled (aucune actualité)")
        return "", []

    elif enrichment_mode == "title-only":
        logger.info(f"📰 Mode d'enrichissement: title-only ({len(news_context_items) if news_context_items else 0} actualités du frontend)")
        context = build_news_context_prompt(news_context_items or [], language)
        # Construire la liste des titres uniquement
        context_list = [item.title for item in (news_context_items or [])]
        return context, context_list

    elif enrichment_mode == "smart-summary":
        logger.info("📰 Mode d'enrichissement: smart-summary (recherche vectorielle)")
        # Ignorer newsContext du frontend, utiliser uniquement la recherche vectorielle
        return await build_smart_news_context(post_text, language, limit=3)

    else:
        logger.warning(f"⚠️ Mode d'enrichissement inconnu: {enrichment_mode}, fallback sur disabled")
        return "", []

async def check_user_permissions(user_email: str, feature: str) -> Dict[str, Any]:
    """Vérifier les permissions via le User Service"""
    try:
        async with httpx.AsyncClient(verify=False) as client_http:
            response = await client_http.post(
                f"{USER_SERVICE_URL}/api/permissions/validate-action",
                json={"email": user_email, "feature": feature},
                timeout=10.0
            )
            if response.status_code != 200:
                logger.error(f"Permission check failed: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=403, 
                    detail="Permission refusée ou service utilisateur indisponible"
                )
            return response.json()
    except httpx.TimeoutException:
        logger.error("Timeout lors de la vérification des permissions")
        raise HTTPException(status_code=503, detail="Service utilisateur temporairement indisponible")
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des permissions: {e}")
        raise HTTPException(status_code=503, detail="Erreur de service utilisateur")

async def record_user_usage(user_email: str, feature: str, metadata: Dict[str, Any] = None) -> None:
    """Enregistrer l'utilisation d'une fonctionnalité après une génération réussie"""
    try:
        async with httpx.AsyncClient(verify=False) as client_http:
            response = await client_http.post(
                f"{USER_SERVICE_URL}/api/permissions/record-usage",
                json={"email": user_email, "feature": feature, "metadata": metadata},
                timeout=10.0
            )
            if response.status_code != 200:
                logger.error(f"Échec enregistrement usage: {response.status_code} - {response.text}")
                # Ne pas bloquer la réponse si l'enregistrement échoue
            else:
                logger.info(f"Usage enregistré pour {user_email}: {feature}")
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de l'usage: {e}")
        # Ne pas bloquer la réponse si l'enregistrement échoue

def call_openai_api(prompt: str, action_type: str = "generate", options_count: int = 2, language: str = "fr", context: dict = None) -> List[str]:
    """Envoie un prompt à OpenAI et retourne 1..n propositions

    Args:
        prompt: Le prompt utilisateur
        action_type: Type d'action (generate, refine, resize)
        options_count: Nombre de propositions à générer
        language: Langue de génération
        context: Métadonnées contextuelles (tone, emotion, intensity, style, etc.)
    """
    try:
        import datetime
        system_prompt = get_system_prompt(language)
        temperature = 0.9 if action_type == "generate" else 0.7
        n_options = options_count if action_type == "generate" else 1

        # 🔍 STOCKAGE DU DERNIER PROMPT (pour l'endpoint /debug/last-prompt)
        global last_prompt_data
        last_prompt_data = {
            "system_prompt": system_prompt,
            "user_prompt": prompt,
            "parameters": {
                "model": MODEL_NAME,
                "temperature": temperature,
                "n": n_options,
                "max_tokens": 160,
                "language": language
            },
            "context": context or {},  # Ajouter les métadonnées contextuelles
            "timestamp": datetime.datetime.now().isoformat(),
            "action_type": action_type
        }

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=160,
            temperature=temperature,
            n=n_options,
            timeout=30,
        )

        # Fonction pour nettoyer les guillemets autour du texte
        def clean_quotes(text: str) -> str:
            """Retire les guillemets qui entourent le texte (simples ou doubles) uniquement s'ils sont présents au début ET à la fin"""
            text = text.strip()
            # Vérifier si le texte commence ET finit par des guillemets
            if len(text) >= 2:
                if (text[0] == '"' and text[-1] == '"') or \
                   (text[0] == "'" and text[-1] == "'") or \
                   (text[0] == '«' and text[-1] == '»') or \
                   (text[0] == '"' and text[-1] == '"') or \
                   (text[0] == ''' and text[-1] == '''):
                    return text[1:-1].strip()
            return text

        if action_type == "generate":
            return [clean_quotes(c.message.content) for c in response.choices]
        else:
            return [clean_quotes(response.choices[0].message.content)]
    except Exception as e:
        logger.error("Erreur OpenAI: %s", e)
        raise HTTPException(status_code=500, detail=f"Erreur OpenAI: {e}") from e

# ---------- Public ----------
@app.get("/")
async def root():
    """Endpoint racine: info version & HTTPS"""
    return {"message": "LinkedIn AI Commenter Backend", "version": "4.0.0", "https": True, "multilingual": True}

@app.get("/health")
async def health_check():
    """Vérifie l'état du service pour le monitoring"""
    return {"status": "ok", "https_enabled": True, "cors_enabled": True, "multilingual": True}

@app.get("/config")
async def get_config():
    """Endpoint pour le site web - retourne le Client ID web"""
    return {"google_client_id": GOOGLE_CLIENT_ID_WEB or None}

@app.get("/config/google-client-id")
async def get_google_client_id():
    """Expose le GOOGLE_CLIENT_ID pour l'extension Chrome (aucune valeur en dur côté code)"""
    return {"client_id": GOOGLE_CLIENT_ID}

@app.get("/config/complete")
async def get_complete_config():
    """Retourne la configuration utile au frontend (sans secrets)."""
    return {
        "google_client_id": GOOGLE_CLIENT_ID_WEB or None,  # Client ID pour le site web
        "backend_version": "4.0.0",
        "openai_model": MODEL_NAME,
        "https_enabled": True,
        "supported_languages": ["fr", "en"],
        "urls": {
            "backend": BACKEND_EXTERNAL_URL,
            "user_service": USER_SERVICE_EXTERNAL_URL
        },
        "features": {
            "user_registration": os.getenv("ENABLE_USER_REGISTRATION", "true").lower() == "true",
            "google_auth": os.getenv("ENABLE_GOOGLE_AUTH", "true").lower() == "true",
            "quota_enforcement": os.getenv("ENABLE_QUOTA_ENFORCEMENT", "true").lower() == "true",
            "analytics": os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
        },
        "limits": {
            "rate_limit_per_minute": int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
            "rate_limit_burst": int(os.getenv("RATE_LIMIT_BURST", "10"))
        },
        "extension_config": {
            "supported_features": ["google_auth", "comment_generation", "multilingual"],
            "extension_id": "dynamic",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "debug": os.getenv("DEBUG", "false").lower() == "true"
        }
    }

@app.get("/debug/last-prompt")
async def get_last_prompt():
    """
    🔍 ENDPOINT DE DEBUG
    Retourne le dernier prompt envoyé à OpenAI.
    Utile pour déboguer et comprendre ce qui est envoyé à GPT.
    """
    global last_prompt_data

    if last_prompt_data["system_prompt"] is None:
        return {
            "message": "Aucun prompt n'a encore été envoyé",
            "data": None
        }

    return {
        "message": "Dernier prompt envoyé à OpenAI",
        "data": last_prompt_data,
        "full_prompt_preview": {
            "system": last_prompt_data["system_prompt"][:200] + "..." if len(last_prompt_data["system_prompt"]) > 200 else last_prompt_data["system_prompt"],
            "user": last_prompt_data["user_prompt"][:500] + "..." if len(last_prompt_data["user_prompt"]) > 500 else last_prompt_data["user_prompt"]
        },
        "summary": {
            "action": last_prompt_data["action_type"],
            "language": last_prompt_data["parameters"]["language"],
            "model": last_prompt_data["parameters"]["model"],
            "temperature": last_prompt_data["parameters"]["temperature"],
            "options_count": last_prompt_data["parameters"]["n"],
            "context": last_prompt_data.get("context", {}),
            "timestamp": last_prompt_data["timestamp"]
        }
    }

# ---------- Auth ----------
@app.post("/auth/verify")
async def verify_authentication(request: AuthVerifyRequest):
    """Vérifie côté backend que le token Google est valide"""
    user_info = await auth_middleware.verify_google_token(request.google_token)
    return {"success": True, "message": "Authentification réussie", "user_info": user_info}

@app.post("/auth/clear-cache")
async def clear_auth_cache():
    """Point de confort pour vider d'éventuels caches (noop ici)"""
    auth_middleware.clear_all_cache()
    return {"success": True, "message": "Cache vidé"}

# ---------- Protégés ----------
@app.post("/generate-comments")
async def generate_comments(request: GenerateCommentsRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Génère N commentaires pour un post LinkedIn dans la langue spécifiée"""

    # Résoudre le distinct_id pour PostHog dès le début
    distinct_id = resolve_distinct_id(request.dict(), current_user)
    start_time = time.time()

    try:
        # Vérifier les permissions
        user_email = current_user.get("email")
        if not user_email:
            raise HTTPException(status_code=401, detail="Email utilisateur non trouvé")

        permissions = await check_user_permissions(user_email, "generate_comment")

        if not permissions.get("allowed", False):
            raise HTTPException(
                status_code=403,
                detail={
                    "message": permissions.get("message", "Limite atteinte"),
                    "remaining_quota": permissions.get("remaining_quota", 0),
                    "daily_limit": permissions.get("daily_limit", 0),
                    "role": permissions.get("role", "FREE")
                }
            )

        cleaned_post = clean_post_content(request.post) if request.post else ""

        # Logique de priorité : emotion/style surchargent le tone
        # Si emotion et intensity sont définis, on les utilise en priorité
        emotion_instructions = ""
        if request.emotion and request.intensity:
            emotion_instructions = get_emotion_instructions(request.emotion, request.intensity, request.commentLanguage)
            logger.info(f"🎭 Émotion appliquée: {request.emotion} ({request.intensity})")

        # Si style est défini, on l'utilise, sinon on utilise le tone
        if request.style:
            style_instructions = get_style_instructions(request.style, request.commentLanguage)
            logger.info(f"🎨 Style appliqué: {request.style}")
        else:
            # Fallback sur le tone si pas de style spécifique
            style_instructions = get_tone_instructions(request.tone, request.commentLanguage)
            logger.info(f"📝 Tone appliqué (fallback): {request.tone}")

        language_instruction = get_language_instruction(request.commentLanguage)

        # Construire le contexte des actualités selon le mode d'enrichissement
        news_context_prompt, context_used = await get_news_context(
            enrichment_mode=request.newsEnrichmentMode,
            post_text=cleaned_post,
            news_context_items=request.newsContext,
            language=request.commentLanguage
        )

        # Si pas de post fourni, générer un commentaire générique basé sur le ton
        if not cleaned_post:
            if request.commentLanguage == "en":
                prompt = f"""Generate a LinkedIn comment that:
- {style_instructions}
{f"- {emotion_instructions}" if emotion_instructions else ""}
- Is approximately {request.length} words
- {language_instruction}
- Is professional and engaging
{news_context_prompt}

Comment only, no preamble.
"""
            else:
                prompt = f"""Générez un commentaire LinkedIn qui:
- {style_instructions}
{f"- {emotion_instructions}" if emotion_instructions else ""}
- Fait environ {request.length} mots
- {language_instruction}
- Est professionnel et engageant
{news_context_prompt}

Commentaire uniquement, sans préambule.
"""
        elif request.includePostParent and request.isComment and request.postParent:
            cleaned_parent = clean_post_content(request.postParent)
            if request.commentLanguage == "en":
                prompt = f"""Original post: "{cleaned_parent}"
Comment: "{cleaned_post}"

Generate a response that:
- {style_instructions}
{f"- {emotion_instructions}" if emotion_instructions else ""}
- Is approximately {request.length} words
- {language_instruction}
{news_context_prompt}

Response only, no preamble.
"""
            else:
                prompt = f"""Post original: "{cleaned_parent}"
Commentaire: "{cleaned_post}"

Générez une réponse qui:
- {style_instructions}
{f"- {emotion_instructions}" if emotion_instructions else ""}
- Fait environ {request.length} mots
- {language_instruction}
{news_context_prompt}

Réponse uniquement, sans préambule.
"""
        else:
            if request.commentLanguage == "en":
                prompt = f"""LinkedIn post: "{cleaned_post}"

Generate a comment that:
- {style_instructions}
{f"- {emotion_instructions}" if emotion_instructions else ""}
- Is approximately {request.length} words
- {language_instruction}
{news_context_prompt}

Comment only, no preamble.
"""
            else:
                prompt = f"""Post LinkedIn: "{cleaned_post}"

Générez un commentaire qui:
- {style_instructions}
{f"- {emotion_instructions}" if emotion_instructions else ""}
- Fait environ {request.length} mots
- {language_instruction}
{news_context_prompt}

Commentaire uniquement, sans préambule.
"""

        # Préparer le contexte pour le debug
        debug_context = {
            "tone": request.tone,
            "emotion": request.emotion,
            "intensity": request.intensity,
            "style": request.style,
            "length": request.length,
            "is_comment": request.isComment,
            "news_enrichment_mode": request.newsEnrichmentMode,
            "has_news_context": len(request.newsContext) > 0 if request.newsContext else False,
            "news_count": len(request.newsContext) if request.newsContext else 0
        }

        comments = call_openai_api(prompt, "generate", request.optionsCount, request.commentLanguage, context=debug_context)

        processing_time_ms = (time.time() - start_time) * 1000

        # Enregistrer l'utilisation après génération réussie
        await record_user_usage(user_email, "generate_comment", {
            "tone": request.tone,
            "length": request.length,
            "language": request.commentLanguage,
            "options_count": request.optionsCount,
            "is_comment": request.isComment
        })

        # Track avec PostHog (événement standardisé comment_generated)
        posthog_service.track_comment_generated(
            user_id=distinct_id,
            properties={
                "plan": request.plan or "FREE",
                "language": request.commentLanguage,
                "interface_lang": request.interface_lang or "fr",
                "tone": request.tone,
                "emotion": request.emotion,
                "style": request.style,
                "options_count": request.optionsCount,
                "is_comment": request.isComment,
                "duration_ms": processing_time_ms,
                "success": True,
                "status_code": 200,
                "source": "backend"
            }
        )

        return {
            "comments": comments[:request.optionsCount],
            "context_used": context_used
        }

    except Exception as exc:
        processing_time_ms = (time.time() - start_time) * 1000
        logger.error(f"❌ Erreur génération commentaires: {exc}")

        # Track l'erreur avec PostHog
        posthog_service.track_comment_generated(
            user_id=distinct_id,
            properties={
                "plan": request.plan or "FREE",
                "language": request.commentLanguage,
                "interface_lang": request.interface_lang or "fr",
                "tone": request.tone,
                "emotion": request.emotion,
                "style": request.style,
                "options_count": request.optionsCount,
                "is_comment": request.isComment,
                "duration_ms": processing_time_ms,
                "success": False,
                "status_code": 500,
                "error": str(exc),
                "source": "backend"
            }
        )
        raise

@app.post("/generate-comments-with-prompt")
async def generate_comments_with_prompt(request: GenerateCommentsWithPromptRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Génère N commentaires guidés par un prompt utilisateur dans la langue spécifiée"""

    # Résoudre le distinct_id pour PostHog dès le début
    distinct_id = resolve_distinct_id(request.dict(), current_user)
    start_time = time.time()

    try:
        # Debug: Log de la requête reçue
        post_preview = request.post[:50] if request.post else "None"
        logger.info(f"📥 Requête reçue: post={post_preview}..., userPrompt={request.userPrompt}, tone={request.tone}, length={request.length}, optionsCount={request.optionsCount}, commentLanguage={request.commentLanguage}")

        # Vérifier les permissions pour les prompts personnalisés
        user_email = current_user.get("email")
        if not user_email:
            raise HTTPException(status_code=401, detail="Email utilisateur non trouvé")

        # Vérifier d'abord si l'utilisateur peut utiliser des prompts personnalisés
        custom_prompt_permissions = await check_user_permissions(user_email, "custom_prompt")
        if not custom_prompt_permissions.get("allowed", False):
            raise HTTPException(
                status_code=403,
                detail="Les prompts personnalisés ne sont pas disponibles pour votre plan. Veuillez upgrader."
            )

        # Vérifier les permissions de génération
        permissions = await check_user_permissions(user_email, "generate_comment")
        if not permissions.get("allowed", False):
            raise HTTPException(
                status_code=403,
                detail={
                    "message": permissions.get("message", "Limite atteinte"),
                    "remaining_quota": permissions.get("remaining_quota", 0),
                    "daily_limit": permissions.get("daily_limit", 0),
                    "role": permissions.get("role", "FREE")
                }
            )

        cleaned_post = clean_post_content(request.post) if request.post else ""

        # Logique de priorité : emotion/style surchargent le tone
        emotion_instructions = ""
        if request.emotion and request.intensity:
            emotion_instructions = get_emotion_instructions(request.emotion, request.intensity, request.commentLanguage)
            logger.info(f"🎭 Émotion appliquée (avec prompt): {request.emotion} ({request.intensity})")

        # Si style est défini, on l'utilise, sinon on utilise le tone
        if request.style:
            style_instructions = get_style_instructions(request.style, request.commentLanguage)
            logger.info(f"🎨 Style appliqué (avec prompt): {request.style}")
        else:
            style_instructions = get_tone_instructions(request.tone, request.commentLanguage)
            logger.info(f"📝 Tone appliqué (avec prompt - fallback): {request.tone}")

        language_instruction = get_language_instruction(request.commentLanguage)

        # Construire le contexte des actualités selon le mode d'enrichissement
        news_context_prompt, context_used = await get_news_context(
            enrichment_mode=request.newsEnrichmentMode,
            post_text=cleaned_post,
            news_context_items=request.newsContext,
            language=request.commentLanguage
        )

        # Si pas de post fourni, générer du contenu basé uniquement sur le prompt
        if not cleaned_post:
            if request.commentLanguage == "en":
                prompt = f"""User instructions: "{request.userPrompt}"

Generate a LinkedIn comment or post that:
- Follows the user instructions
- {style_instructions}
{f"- {emotion_instructions}" if emotion_instructions else ""}
- Is approximately {request.length} words
- {language_instruction}
{news_context_prompt}

Content only, no preamble.
"""
            else:
                prompt = f"""Instructions utilisateur: "{request.userPrompt}"

Générez un commentaire ou post LinkedIn qui:
- Suit les instructions utilisateur
- {style_instructions}
{f"- {emotion_instructions}" if emotion_instructions else ""}
- Fait environ {request.length} mots
- {language_instruction}
{news_context_prompt}

Contenu uniquement, sans préambule.
"""
        elif request.includePostParent and request.isComment and request.postParent:
            cleaned_parent = clean_post_content(request.postParent)
            if request.commentLanguage == "en":
                prompt = f"""Original post: "{cleaned_parent}"
Comment: "{cleaned_post}"
User instructions: "{request.userPrompt}"

Generate a response that:
- Follows the user instructions
- {style_instructions}
{f"- {emotion_instructions}" if emotion_instructions else ""}
- Is approximately {request.length} words
- {language_instruction}
{news_context_prompt}

Response only.
"""
            else:
                prompt = f"""Post original: "{cleaned_parent}"
Commentaire: "{cleaned_post}"
Instructions utilisateur: "{request.userPrompt}"

Générez une réponse qui:
- Suit les instructions utilisateur
- {style_instructions}
{f"- {emotion_instructions}" if emotion_instructions else ""}
- Fait environ {request.length} mots
- {language_instruction}
{news_context_prompt}

Réponse uniquement.
"""
        else:
            if request.commentLanguage == "en":
                prompt = f"""LinkedIn post: "{cleaned_post}"
User instructions: "{request.userPrompt}"

Generate a comment that:
- Follows the user instructions
- {style_instructions}
{f"- {emotion_instructions}" if emotion_instructions else ""}
- Is approximately {request.length} words
- {language_instruction}
{news_context_prompt}

Comment only.
"""
            else:
                prompt = f"""Post LinkedIn: "{cleaned_post}"
Instructions utilisateur: "{request.userPrompt}"

Générez un commentaire qui:
- Suit les instructions utilisateur
- {style_instructions}
{f"- {emotion_instructions}" if emotion_instructions else ""}
- Fait environ {request.length} mots
- {language_instruction}
{news_context_prompt}

Commentaire uniquement.
"""

        # Préparer le contexte pour le debug
        debug_context = {
            "tone": request.tone,
            "emotion": request.emotion,
            "intensity": request.intensity,
            "style": request.style,
            "length": request.length,
            "is_comment": request.isComment,
            "has_user_prompt": True,
            "user_prompt_length": len(request.userPrompt),
            "news_enrichment_mode": request.newsEnrichmentMode,
            "has_news_context": len(request.newsContext) > 0 if request.newsContext else False,
            "news_count": len(request.newsContext) if request.newsContext else 0
        }

        # Mesurer le temps de génération
        start_time = time.time()

        comments = call_openai_api(prompt, "generate", request.optionsCount, request.commentLanguage, context=debug_context)

        processing_time_ms = (time.time() - start_time) * 1000

        # Enregistrer l'utilisation après génération réussie
        await record_user_usage(user_email, "generate_comment", {
            "tone": request.tone,
            "length": request.length,
            "language": request.commentLanguage,
            "options_count": request.optionsCount,
            "is_comment": request.isComment,
            "custom_prompt": True
        })

        # Résoudre le distinct_id pour PostHog
        distinct_id = resolve_distinct_id(request.dict(), current_user)

        # Track avec PostHog (événement standardisé comment_generated)
        posthog_service.track_comment_generated(
            user_id=distinct_id,
            properties={
                "plan": request.plan or "FREE",
                "language": request.commentLanguage,
                "interface_lang": request.interface_lang or "fr",
                "tone": request.tone,
                "emotion": request.emotion,
                "style": request.style,
                "options_count": request.optionsCount,
                "is_comment": request.isComment,
                "duration_ms": processing_time_ms,
                "success": True,
                "status_code": 200,
                "source": "backend",
                "has_custom_prompt": True
            }
        )

        return {
            "comments": comments[:request.optionsCount],
            "context_used": context_used
        }

    except Exception as exc:
        processing_time_ms = (time.time() - start_time) * 1000
        logger.error(f"❌ Erreur génération commentaires avec prompt: {exc}")

        # Track l'erreur avec PostHog
        posthog_service.track_comment_generated(
            user_id=distinct_id,
            properties={
                "plan": request.plan or "FREE",
                "language": request.commentLanguage,
                "interface_lang": request.interface_lang or "fr",
                "tone": request.tone,
                "emotion": request.emotion,
                "style": request.style,
                "options_count": request.optionsCount,
                "is_comment": request.isComment,
                "duration_ms": processing_time_ms,
                "success": False,
                "status_code": 500,
                "error": str(exc),
                "source": "backend",
                "has_custom_prompt": True
            }
        )
        raise

@app.post("/refine-comment")
async def refine_comment(request: RefineCommentRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Affiner un commentaire existant selon des instructions dans la langue spécifiée"""
    
    # Vérifier les permissions pour le raffinement
    user_email = current_user.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Email utilisateur non trouvé")
    
    # Vérifier si l'utilisateur peut utiliser la fonction de raffinement
    refine_permissions = await check_user_permissions(user_email, "refine_enabled")
    if not refine_permissions.get("allowed", False):
        raise HTTPException(
            status_code=403,
            detail="La fonction de raffinement n'est pas disponible pour votre plan. Veuillez upgrader."
        )
    
    cleaned_post = clean_post_content(request.post)
    tone_instructions = get_tone_instructions(request.tone, request.commentLanguage)
    language_instruction = get_language_instruction(request.commentLanguage)
    
    if request.commentLanguage == "en":
        prompt = f"""Post: "{cleaned_post}"
Original comment: "{request.originalComment}"
Instructions: "{request.refineInstructions}"

Refine the comment by:
- Following the instructions
- {tone_instructions}
- Keeping approximately {request.length} words
- {language_instruction}

Refined comment only.
"""
    else:
        prompt = f"""Post: "{cleaned_post}"
Commentaire original: "{request.originalComment}"
Instructions: "{request.refineInstructions}"

Affinez le commentaire en:
- Suivant les instructions
- {tone_instructions}
- Gardant environ {request.length} mots
- {language_instruction}

Commentaire affiné uniquement.
"""

    # Préparer le contexte pour le debug
    debug_context = {
        "tone": request.tone,
        "length": request.length,
        "is_comment": request.isComment,
        "original_comment_length": len(request.originalComment.split()),
        "refine_instructions_length": len(request.refineInstructions)
    }

    comments = call_openai_api(prompt, "refine", 1, request.commentLanguage, context=debug_context)

    # Enregistrer l'utilisation après affinement réussi
    user_email = current_user.get("email")
    await record_user_usage(user_email, "refine_comment", {
        "tone": request.tone,
        "length": request.length,
        "language": request.commentLanguage,
        "is_comment": request.isComment,
        "original_length": len(request.originalComment.split())
    })

    return {"comment": comments[0]}

@app.post("/resize-comment")
async def resize_comment(request: ResizeCommentRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Réécrit le commentaire pour le raccourcir/allonger dans la langue spécifiée"""
    
    # Vérifier les permissions pour le redimensionnement
    user_email = current_user.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Email utilisateur non trouvé")
    
    # Vérifier si l'utilisateur peut utiliser la fonction de redimensionnement
    resize_permissions = await check_user_permissions(user_email, "resize_enabled")
    if not resize_permissions.get("allowed", False):
        raise HTTPException(
            status_code=403,
            detail="La fonction de redimensionnement n'est pas disponible pour votre plan. Veuillez upgrader."
        )
    
    cleaned_post = clean_post_content(request.post)
    tone_instructions = get_tone_instructions(request.tone, request.commentLanguage)
    language_instruction = get_language_instruction(request.commentLanguage)
    
    if request.resizeDirection == "+":
        new_length = min(request.currentWordCount + 20, 80)
        action = "more detailed" if request.commentLanguage == "en" else "plus détaillé"
    else:
        new_length = max(request.currentWordCount - 15, 15)
        action = "more concise" if request.commentLanguage == "en" else "plus concis"
    
    if request.commentLanguage == "en":
        prompt = f"""Post: "{cleaned_post}"
Comment ({request.currentWordCount} words): "{request.originalComment}"

Rewrite the comment to make it {action}:
- {tone_instructions}
- Approximately {new_length} words
- {language_instruction}

Comment only.
"""
    else:
        prompt = f"""Post: "{cleaned_post}"
Commentaire ({request.currentWordCount} mots): "{request.originalComment}"

Réécrivez le commentaire pour le rendre {action}:
- {tone_instructions}
- Environ {new_length} mots
- {language_instruction}

Commentaire uniquement.
"""

    # Préparer le contexte pour le debug
    debug_context = {
        "tone": request.tone,
        "resize_direction": request.resizeDirection,
        "original_word_count": request.currentWordCount,
        "target_word_count": new_length
    }

    comments = call_openai_api(prompt, "resize", 1, request.commentLanguage, context=debug_context)

    # Enregistrer l'utilisation après redimensionnement réussi
    await record_user_usage(user_email, "resize_comment", {
        "direction": request.resizeDirection,
        "original_word_count": request.currentWordCount,
        "tone": request.tone,
        "language": request.commentLanguage
    })

    return {"comment": comments[0]}

# ---------- Docker status ----------
@app.get("/docker/status")
async def docker_status():
    """Indique un statut simple pour un healthcheck Docker"""
    return {
        "docker_mode": True, 
        "container_healthy": True, 
        "https_port": 8443, 
        "cors_configured": True,
        "multilingual_support": True
    }

# ---------- Events ----------
@app.on_event("startup")
async def startup_event():
    """Log au démarrage de l'application"""
    logger.info("🚀 Backend démarré - HTTPS attendu via uvicorn")
    logger.info("🆔 Extension IDs supportés: chrome-extension://*")
    logger.info("🌐 Support multilingue activé: FR/EN")

    # Initialiser la base de données News
    try:
        await news_db.connect()
        logger.info("📰 Module News initialisé")
    except Exception as e:
        logger.error(f"❌ Erreur initialisation module News: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Nettoyage lors de l'arrêt de l'application"""
    await auth_middleware.close_http_client()

    # Fermer la connexion à la base de données News
    try:
        await news_db.close()
        logger.info("📰 Module News fermé proprement")
    except Exception as e:
        logger.error(f"❌ Erreur fermeture module News: {e}")