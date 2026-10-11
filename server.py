import os
import uvicorn

# Configura o ambiente de produção do Reflex
os.environ.setdefault("REFLEX_ENV", "prod")

# Importa o app diretamente do pacote absoluto da aplicação
from projeto_reflex.projeto_reflex import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    # Executa o objeto app diretamente, evitando qualquer erro de importação por string
    uvicorn.run(app, host="0.0.0.0", port=port)
