FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt-get/lists/*

WORKDIR /app

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todos os ficheiros do projeto
COPY . .

# Inicializar o Reflex
RUN reflex init

# Expor a porta padrão do Hugging Face (7860)
EXPOSE 7860

# Comando para iniciar o Reflex mapeando a porta 7860
CMD ["reflex", "run", "--env", "prod", "--frontend-port", "7860", "--backend-port", "8000"]
