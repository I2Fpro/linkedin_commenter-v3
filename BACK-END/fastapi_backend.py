"""
API FastAPI pour LinkedIn AI Commenter (HTTPS via uvicorn) - VERSION MULTILINGUE
- Support Français/Anglais pour les commentaires générés
- CORS minimaliste compatible Chrome Extension
- Auth Google via Bearer token
- Génération via OpenAI (clé en variable d'environnement)
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from openai import OpenAI
import logging
import httpx
import os

from auth_middleware import get_current_user, auth_middleware
from config_py import OPENAI_API_KEY, MODEL_NAME, GOOGLE_CLIENT_ID, validate_environment
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Validation env ---
validate_environment()

# --- App ---
app = FastAPI(title="LinkedIn AI Commenter Backend", version="4.0.0")

# --- CORS (KISS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",                       # autorise les tests locaux et preflight génériques
        "chrome-extension://*",    # extensions Chrome
        "__AI_API_URL__",
    ],
    allow_credentials=False,         # IMPORTANT: extensions Chrome + fetch sans cookies
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],           # Autoriser Origin, Authorization, Content-Type...
    expose_headers=["*"]
)

# --- OpenAI client ---
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Service URLs ---
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8444")
BACKEND_EXTERNAL_URL = os.getenv("BACKEND_EXTERNAL_URL", "__AI_API_URL__")
USER_SERVICE_EXTERNAL_URL = os.getenv("USER_SERVICE_EXTERNAL_URL", "__USERS_API_URL__")

# ---------- Schémas ----------
class GenerateCommentsRequest(BaseModel):
    """Corps de requête: génération de commentaires"""
    post: str
    postParent: Optional[str] = None
    isComment: bool = False
    includePostParent: bool = False
    tone: str = "professionnel"
    length: int = 40
    optionsCount: int = 2
    commentLanguage: str = "fr"  # Nouvelle option pour la langue des commentaires

class GenerateCommentsWithPromptRequest(BaseModel):
    """Corps de requête: génération avec prompt utilisateur"""
    post: str
    postParent: Optional[str] = None
    isComment: bool = False
    includePostParent: bool = False
    userPrompt: str
    tone: str = "professionnel"
    length: int = 40
    optionsCount: int = 2
    commentLanguage: str = "fr"  # Nouvelle option pour la langue des commentaires

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

def call_openai_api(prompt: str, action_type: str = "generate", options_count: int = 2, language: str = "fr") -> List[str]:
    """Envoie un prompt à OpenAI et retourne 1..n propositions"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": get_system_prompt(language)},
                {"role": "user", "content": prompt},
            ],
            max_tokens=160,
            temperature=0.9 if action_type == "generate" else 0.7,
            n=options_count if action_type == "generate" else 1,
            timeout=30,
        )
        if action_type == "generate":
            return [c.message.content.strip() for c in response.choices]
        return [response.choices[0].message.content.strip()]
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

@app.get("/config/google-client-id")
async def get_google_client_id():
    """Expose le GOOGLE_CLIENT_ID (aucune valeur en dur côté code)"""
    return {"client_id": GOOGLE_CLIENT_ID}

@app.get("/config/complete")
async def get_complete_config():
    """Retourne la configuration utile au frontend (sans secrets)."""
    return {
        "google_client_id": GOOGLE_CLIENT_ID or None,
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
    
    cleaned_post = clean_post_content(request.post)
    tone_instructions = get_tone_instructions(request.tone, request.commentLanguage)
    language_instruction = get_language_instruction(request.commentLanguage)
    
    if request.includePostParent and request.isComment and request.postParent:
        cleaned_parent = clean_post_content(request.postParent)
        if request.commentLanguage == "en":
            prompt = f"""Original post: "{cleaned_parent}"
Comment: "{cleaned_post}"

Generate a response that:
- {tone_instructions}
- Is approximately {request.length} words
- {language_instruction}

Response only, no preamble.
"""
        else:
            prompt = f"""Post original: "{cleaned_parent}"
Commentaire: "{cleaned_post}"

Générez une réponse qui:
- {tone_instructions}
- Fait environ {request.length} mots
- {language_instruction}

Réponse uniquement, sans préambule.
"""
    else:
        if request.commentLanguage == "en":
            prompt = f"""LinkedIn post: "{cleaned_post}"

Generate a comment that:
- {tone_instructions}
- Is approximately {request.length} words
- {language_instruction}

Comment only, no preamble.
"""
        else:
            prompt = f"""Post LinkedIn: "{cleaned_post}"

Générez un commentaire qui:
- {tone_instructions}
- Fait environ {request.length} mots
- {language_instruction}

Commentaire uniquement, sans préambule.
"""
    
    comments = call_openai_api(prompt, "generate", request.optionsCount, request.commentLanguage)
    
    # Enregistrer l'utilisation après génération réussie
    await record_user_usage(user_email, "generate_comment", {
        "tone": request.tone,
        "length": request.length,
        "language": request.commentLanguage,
        "options_count": request.optionsCount,
        "is_comment": request.isComment
    })
    
    return {"comments": comments[:request.optionsCount]}

@app.post("/generate-comments-with-prompt")
async def generate_comments_with_prompt(request: GenerateCommentsWithPromptRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Génère N commentaires guidés par un prompt utilisateur dans la langue spécifiée"""
    
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
    
    cleaned_post = clean_post_content(request.post)
    tone_instructions = get_tone_instructions(request.tone, request.commentLanguage)
    language_instruction = get_language_instruction(request.commentLanguage)
    
    if request.includePostParent and request.isComment and request.postParent:
        cleaned_parent = clean_post_content(request.postParent)
        if request.commentLanguage == "en":
            prompt = f"""Original post: "{cleaned_parent}"
Comment: "{cleaned_post}"
User instructions: "{request.userPrompt}"

Generate a response that:
- Follows the user instructions
- {tone_instructions}
- Is approximately {request.length} words
- {language_instruction}

Response only.
"""
        else:
            prompt = f"""Post original: "{cleaned_parent}"
Commentaire: "{cleaned_post}"
Instructions utilisateur: "{request.userPrompt}"

Générez une réponse qui:
- Suit les instructions utilisateur
- {tone_instructions}
- Fait environ {request.length} mots
- {language_instruction}

Réponse uniquement.
"""
    else:
        if request.commentLanguage == "en":
            prompt = f"""LinkedIn post: "{cleaned_post}"
User instructions: "{request.userPrompt}"

Generate a comment that:
- Follows the user instructions
- {tone_instructions}
- Is approximately {request.length} words
- {language_instruction}

Comment only.
"""
        else:
            prompt = f"""Post LinkedIn: "{cleaned_post}"
Instructions utilisateur: "{request.userPrompt}"

Générez un commentaire qui:
- Suit les instructions utilisateur
- {tone_instructions}
- Fait environ {request.length} mots
- {language_instruction}

Commentaire uniquement.
"""
    
    comments = call_openai_api(prompt, "generate", request.optionsCount, request.commentLanguage)
    
    # Enregistrer l'utilisation après génération réussie
    await record_user_usage(user_email, "generate_comment", {
        "tone": request.tone,
        "length": request.length,
        "language": request.commentLanguage,
        "options_count": request.optionsCount,
        "is_comment": request.isComment,
        "custom_prompt": True
    })
    
    return {"comments": comments[:request.optionsCount]}

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
    
    comments = call_openai_api(prompt, "refine", 1, request.commentLanguage)
    
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
    
    comments = call_openai_api(prompt, "resize", 1, request.commentLanguage)
    
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

@app.on_event("shutdown")
async def shutdown_event():
    """Nettoyage lors de l'arrêt de l'application"""
    await auth_middleware.close_http_client()