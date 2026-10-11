FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema necessárias, incluindo o unzip e curl para o Reflex
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Executa o Reflex em produção utilizando a porta dinâmica do Railway
CMD sh -c "reflex run --env prod --backend-port ${PORT:-8000}"