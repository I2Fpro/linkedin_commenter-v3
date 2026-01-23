# Dockerfile pour AI Service - LinkedIn AI Commenter
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers requirements depuis user-service (mêmes dépendances de base)
COPY user-service/requirements.txt ./requirements-user.txt

# Créer un fichier requirements.txt spécifique à l'AI service
RUN echo "fastapi>=0.104.1" > requirements.txt && \
    echo "uvicorn[standard]>=0.24.0" >> requirements.txt && \
    echo "openai>=1.0.0" >> requirements.txt && \
    echo "httpx>=0.25.0" >> requirements.txt && \
    echo "python-dotenv>=1.0.0" >> requirements.txt && \
    echo "python-jose[cryptography]>=3.3.0" >> requirements.txt && \
    echo "pydantic>=2.0.0" >> requirements.txt && \
    echo "google-auth>=2.0.0" >> requirements.txt && \
    echo "google-auth-oauthlib>=0.7.0" >> requirements.txt && \
    echo "google-auth-httplib2>=0.1.0" >> requirements.txt

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY *.py .

# Créer un utilisateur non-root pour la sécurité
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

# Exposer le port
EXPOSE 8443

# Définir les variables d'environnement
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Commande de démarrage
CMD ["uvicorn", "fastapi_backend:app", "--host", "0.0.0.0", "--port", "8443"]