import os
import uvicorn

os.environ.setdefault("REFLEX_ENV", "prod")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    # Passa a string de importação para o Uvicorn gerir o carregamento sem bloquear a porta
    uvicorn.run("projeto_reflex.projeto_reflex:app", host="0.0.0.0", port=port)