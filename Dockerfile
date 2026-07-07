# Image de base : Python 3.11 slim (légère mais complète)
FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dossier de travail dans le conteneur
WORKDIR /app

# Installer les dépendances système nécessaires à TensorFlow / Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements.txt en premier (optimisation cache Docker)
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copier le code de l'application
COPY app/ ./app/

# Exposer le port Flask
EXPOSE 8501

# Commande de démarrage : gunicorn sert l'app Flask
CMD ["gunicorn", "--bind", "0.0.0.0:8501", "--workers", "2", "--timeout", "120", "app.ui.main:app"]