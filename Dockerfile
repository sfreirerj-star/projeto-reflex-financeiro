FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema necessárias para compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar os requisitos e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código do projeto para o container
COPY . .

# Expor a porta e iniciar o Reflex
EXPOSE 8000
CMD reflex run --env prod --backend-port ${PORT:-8000}