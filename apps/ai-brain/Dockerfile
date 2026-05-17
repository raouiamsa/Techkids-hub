# Utiliser une image Python officielle basée sur Debian
FROM python:3.12-slim

# Installer ngspice et les librairies partagées nécessaires pour PySpice
RUN apt-get update && apt-get install -y \
    ngspice \
    libngspice0 \
    libngspice0-dev \
    && rm -rf /var/lib/apt/lists/*

# Définir le dossier de travail
WORKDIR /app

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code de l'ai-brain
COPY . .

# Exposer le port 8000 pour FastAPI
EXPOSE 8000

# Lancer le serveur (sans --reload en production, mais vous pouvez l'ajouter pour le dev)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
