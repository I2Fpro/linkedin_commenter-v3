"""
Configuration des fonctionnalités par rôle pour le système LinkedIn AI Commenter
"""

FEATURES = {
    "FREE": {
        "daily_generations": 5,
        "custom_prompt": False,
        "languages": ["fr"],
        "history_days": 0,
        "refine_enabled": False,
        "resize_enabled": False,
        "priority_support": False,
        "advanced_analytics": False,
        "bulk_operations": False,
        "api_access": False,
        "export_formats": ["txt"],
        "max_prompt_length": 200,
        "concurrent_requests": 1,
        "include_quote": False,
        "tag_author": False,
        "web_search_enabled": False
    },
    "MEDIUM": {
        "daily_generations": 50,
        "custom_prompt": True,
        "languages": ["fr", "en"],
        "history_days": 7,
        "refine_enabled": True,
        "resize_enabled": True,
        "priority_support": False,
        "advanced_analytics": True,
        "bulk_operations": False,
        "api_access": False,
        "export_formats": ["txt", "csv"],
        "max_prompt_length": 500,
        "concurrent_requests": 2,
        "include_quote": False,
        "tag_author": False,
        "web_search_enabled": False
    },
    "PREMIUM": {
        "daily_generations": -1,  # Illimité
        "custom_prompt": True,
        "languages": ["fr", "en", "es", "de", "it"],
        "history_days": -1,  # Illimité
        "refine_enabled": True,
        "resize_enabled": True,
        "priority_support": True,
        "advanced_analytics": True,
        "bulk_operations": True,
        "api_access": True,
        "export_formats": ["txt", "csv", "json", "xlsx"],
        "max_prompt_length": 1000,
        "concurrent_requests": 5,
        "include_quote": True,
        "tag_author": True,
        "web_search_enabled": True
    }
}

def get_feature_value(role: str, feature_name: str, default=None):
    """
    Récupérer la valeur d'une fonctionnalité pour un rôle donné
    
    Args:
        role: Le rôle de l'utilisateur (FREE, MEDIUM, PREMIUM)
        feature_name: Le nom de la fonctionnalité
        default: La valeur par défaut si la fonctionnalité n'existe pas
    
    Returns:
        La valeur de la fonctionnalité ou la valeur par défaut
    """
    role_features = FEATURES.get(role, FEATURES["FREE"])
    return role_features.get(feature_name, default)

def is_feature_enabled(role: str, feature_name: str) -> bool:
    """
    Vérifier si une fonctionnalité est activée pour un rôle
    
    Args:
        role: Le rôle de l'utilisateur
        feature_name: Le nom de la fonctionnalité
    
    Returns:
        True si la fonctionnalité est activée, False sinon
    """
    feature_value = get_feature_value(role, feature_name, False)
    
    if isinstance(feature_value, bool):
        return feature_value
    elif isinstance(feature_value, int):
        return feature_value > 0 or feature_value == -1
    elif isinstance(feature_value, list):
        return len(feature_value) > 0
    else:
        return bool(feature_value)

def get_role_limits(role: str) -> dict:
    """
    Récupérer toutes les limites pour un rôle donné
    
    Args:
        role: Le rôle de l'utilisateur
    
    Returns:
        Dictionnaire contenant toutes les limites du rôle
    """
    return FEATURES.get(role, FEATURES["FREE"]).copy()

def compare_roles(current_role: str, target_role: str) -> dict:
    """
    Comparer deux rôles et retourner les différences
    
    Args:
        current_role: Le rôle actuel
        target_role: Le rôle cible
    
    Returns:
        Dictionnaire avec les améliorations et les limitations
    """
    current_features = FEATURES.get(current_role, FEATURES["FREE"])
    target_features = FEATURES.get(target_role, FEATURES["FREE"])
    
    improvements = {}
    limitations = {}
    
    for feature, target_value in target_features.items():
        current_value = current_features.get(feature)
        
        if current_value != target_value:
            if _is_improvement(current_value, target_value):
                improvements[feature] = {
                    "from": current_value,
                    "to": target_value
                }
            else:
                limitations[feature] = {
                    "from": current_value,
                    "to": target_value
                }
    
    return {
        "improvements": improvements,
        "limitations": limitations
    }

def _is_improvement(current_value, target_value) -> bool:
    """
    Déterminer si une valeur cible représente une amélioration
    """
    if isinstance(current_value, bool) and isinstance(target_value, bool):
        return target_value and not current_value
    elif isinstance(current_value, int) and isinstance(target_value, int):
        if current_value == -1:
            return False  # Déjà illimité
        if target_value == -1:
            return True  # Devient illimité
        return target_value > current_value
    elif isinstance(current_value, list) and isinstance(target_value, list):
        return len(target_value) > len(current_value)
    else:
        return str(target_value) > str(current_value)

def get_upgrade_benefits(current_role: str, target_role: str) -> list:
    """
    Obtenir la liste des bénéfices d'une mise à niveau
    
    Args:
        current_role: Le rôle actuel
        target_role: Le rôle cible
    
    Returns:
        Liste des bénéfices textuels
    """
    comparison = compare_roles(current_role, target_role)
    benefits = []
    
    for feature, change in comparison["improvements"].items():
        if feature == "daily_generations":
            if change["to"] == -1:
                benefits.append("Générations illimitées par jour")
            else:
                benefits.append(f"Quota quotidien passant de {change['from']} à {change['to']} générations")
        elif feature == "custom_prompt" and change["to"]:
            benefits.append("Accès aux prompts personnalisés")
        elif feature == "languages":
            new_languages = set(change["to"]) - set(change["from"])
            if new_languages:
                benefits.append(f"Nouvelles langues disponibles: {', '.join(new_languages)}")
        elif feature == "history_days":
            if change["to"] == -1:
                benefits.append("Historique illimité")
            else:
                benefits.append(f"Historique étendu à {change['to']} jours")
        elif feature == "refine_enabled" and change["to"]:
            benefits.append("Fonction de raffinement des commentaires")
        elif feature == "resize_enabled" and change["to"]:
            benefits.append("Fonction de redimensionnement des commentaires")
        elif feature == "priority_support" and change["to"]:
            benefits.append("Support prioritaire")
        elif feature == "advanced_analytics" and change["to"]:
            benefits.append("Analyses avancées d'utilisation")
        elif feature == "bulk_operations" and change["to"]:
            benefits.append("Opérations en lot")
        elif feature == "api_access" and change["to"]:
            benefits.append("Accès API")
    
    return benefits