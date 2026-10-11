import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    # Executa o servidor apontando diretamente para o ASGI gerado na build do Reflex
    uvicorn.run(
        "web._static.server:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
