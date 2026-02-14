FROM python:3.11-slim

# Version de l'application (passee via --build-arg)
ARG APP_VERSION="0.0.0"
ENV APP_VERSION=$APP_VERSION

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier le fichier requirements.txt
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Rendre l'entrypoint executable
RUN chmod +x entrypoint.sh

# Créer un utilisateur non-root pour la sécurité
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

# Exposer le port
EXPOSE 8444

# Définir les variables d'environnement
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Entrypoint: migrations Alembic puis uvicorn
ENTRYPOINT ["./entrypoint.sh"]