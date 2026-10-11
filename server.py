import os
import uvicorn

# Configura o ambiente para evitar recompilação desnecessária no arranque do servidor
os.environ.setdefault("REFLEX_ENV", "prod")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    # Importa o app diretamente após configurar o ambiente
    from projeto_reflex.projeto_reflex import app
    
    uvicorn.run(app, host="0.0.0.0", port=port)