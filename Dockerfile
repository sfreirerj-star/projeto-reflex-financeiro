FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Inicializa o projeto Reflex e compila o frontend para produção dentro do container
RUN reflex init || true

EXPOSE 8000

# Executa o Reflex em produção utilizando a porta dinâmica do Railway
CMD sh -c "reflex run --env prod --backend-port ${PORT:-8000}"