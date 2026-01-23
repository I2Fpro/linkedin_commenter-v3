"""
Système de logging structuré pour le module News
- Logs JSON pour traçabilité
- Mode debug avec détails complets
- Fichiers séparés (logs normaux + debug)
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class NewsLogger:
    """Gestionnaire de logs structurés pour les actualités"""

    def __init__(self):
        self.debug_mode = os.getenv("DEBUG_NEWS", "false").lower() == "true"

        # Créer le répertoire de logs s'il n'existe pas
        self.logs_dir = Path("/app/logs") if os.path.exists("/app") else Path("./logs")
        self.logs_dir.mkdir(exist_ok=True)

        # Fichiers de logs
        self.logs_file = self.logs_dir / "news_logs.json"
        self.debug_file = self.logs_dir / "news_debug.log"

        logger.info(f"📝 NewsLogger initialisé (DEBUG_NEWS={self.debug_mode})")

    def _append_json_log(self, log_entry: Dict[str, Any]) -> None:
        """Ajoute une entrée au fichier JSON de logs"""
        try:
            # Charger les logs existants
            if self.logs_file.exists():
                with open(self.logs_file, "r", encoding="utf-8") as f:
                    try:
                        logs = json.load(f)
                        if not isinstance(logs, list):
                            logs = []
                    except json.JSONDecodeError:
                        logs = []
            else:
                logs = []

            # Ajouter la nouvelle entrée
            logs.append(log_entry)

            # Limiter à 1000 entrées (garder les plus récentes)
            if len(logs) > 1000:
                logs = logs[-1000:]

            # Sauvegarder
            with open(self.logs_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"❌ Erreur écriture JSON log: {e}")

    def _append_debug_log(self, message: str) -> None:
        """Ajoute une ligne au fichier de debug"""
        if not self.debug_mode:
            return

        try:
            with open(self.debug_file, "a", encoding="utf-8") as f:
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            logger.error(f"❌ Erreur écriture debug log: {e}")

    def log_processing(
        self,
        url: str,
        status: str,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Enregistre le traitement d'une actualité

        Args:
            url: L'URL traitée
            status: "success", "cached", "error", "pending_retry"
            duration_ms: Durée du traitement en millisecondes
            error: Message d'erreur (si status="error")
            metadata: Métadonnées additionnelles (title, lang, etc.)
        """
        # Créer l'entrée de log
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "url": url,
            "status": status,
            "duration_ms": duration_ms,
            "error": error,
            **(metadata or {})
        }

        # Log JSON
        self._append_json_log(log_entry)

        # Log console avec emoji
        emoji_map = {
            "success": "✅",
            "cached": "⚠️",
            "error": "❌",
            "pending_retry": "🔄"
        }
        emoji = emoji_map.get(status, "ℹ️")

        if status == "success":
            msg = f"{emoji} Processed: {url} ({duration_ms}ms)"
        elif status == "cached":
            msg = f"{emoji} Skipped (cached): {url}"
        elif status == "error":
            msg = f"{emoji} Error: {url} - {error}"
        elif status == "pending_retry":
            msg = f"{emoji} Pending retry: {url}"
        else:
            msg = f"{emoji} {status}: {url}"

        logger.info(msg)

        # Log debug si activé
        if self.debug_mode:
            self._append_debug_log(json.dumps(log_entry, ensure_ascii=False))

    def log_scraping_debug(
        self,
        url: str,
        content: str,
        content_length: int
    ) -> None:
        """Log le contenu brut scraped (mode debug uniquement)"""
        if not self.debug_mode:
            return

        debug_msg = f"""
=== SCRAPING DEBUG ===
URL: {url}
Content Length: {content_length} chars
Content Preview (500 chars):
{content[:500]}
...
=====================
"""
        self._append_debug_log(debug_msg)

    def log_summary_debug(
        self,
        url: str,
        system_prompt: str,
        user_prompt: str,
        summary: str
    ) -> None:
        """Log le prompt GPT complet et le résumé (mode debug uniquement)"""
        if not self.debug_mode:
            return

        debug_msg = f"""
=== SUMMARY DEBUG ===
URL: {url}

System Prompt:
{system_prompt}

User Prompt:
{user_prompt}

Generated Summary:
{summary}
====================
"""
        self._append_debug_log(debug_msg)

    def log_embedding_debug(
        self,
        url: str,
        text: str,
        embedding_size: int
    ) -> None:
        """Log l'embedding (sans le vecteur complet, trop volumineux)"""
        if not self.debug_mode:
            return

        debug_msg = f"""
=== EMBEDDING DEBUG ===
URL: {url}
Text Length: {len(text)} chars
Embedding Dimensions: {embedding_size}
Text Preview:
{text[:200]}...
=======================
"""
        self._append_debug_log(debug_msg)

    def get_recent_logs(self, limit: int = 50) -> list:
        """
        Récupère les logs récents depuis le fichier JSON

        Args:
            limit: Nombre maximum de logs à retourner

        Returns:
            Liste des logs récents (plus récents en premier)
        """
        try:
            if not self.logs_file.exists():
                return []

            with open(self.logs_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
                if isinstance(logs, list):
                    # Retourner les plus récents
                    return logs[-limit:][::-1]
                return []
        except Exception as e:
            logger.error(f"❌ Erreur lecture logs: {e}")
            return []

    def get_error_logs(self, limit: int = 20) -> list:
        """Récupère uniquement les logs d'erreur"""
        try:
            all_logs = self.get_recent_logs(limit=1000)
            error_logs = [log for log in all_logs if log.get("status") == "error"]
            return error_logs[-limit:][::-1]
        except Exception as e:
            logger.error(f"❌ Erreur récupération error logs: {e}")
            return []

    def clear_old_logs(self, days: int = 7) -> None:
        """
        Supprime les logs plus anciens que X jours

        Args:
            days: Nombre de jours à conserver
        """
        try:
            if not self.logs_file.exists():
                return

            with open(self.logs_file, "r", encoding="utf-8") as f:
                logs = json.load(f)

            if not isinstance(logs, list):
                return

            # Filtrer les logs récents
            cutoff_date = datetime.utcnow().timestamp() - (days * 86400)
            filtered_logs = []

            for log in logs:
                try:
                    log_time = datetime.fromisoformat(log["timestamp"]).timestamp()
                    if log_time >= cutoff_date:
                        filtered_logs.append(log)
                except:
                    # Garder les logs sans timestamp valide
                    filtered_logs.append(log)

            # Sauvegarder
            with open(self.logs_file, "w", encoding="utf-8") as f:
                json.dump(filtered_logs, f, indent=2, ensure_ascii=False)

            logger.info(f"🗑️ Logs nettoyés: {len(logs) - len(filtered_logs)} supprimés")

        except Exception as e:
            logger.error(f"❌ Erreur nettoyage logs: {e}")


# Instance globale
news_logger = NewsLogger()
