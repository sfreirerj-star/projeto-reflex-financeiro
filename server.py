import os
import uvicorn
from projeto_reflex.projeto_reflex import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("projeto_reflex.projeto_reflex:app", host="0.0.0.0", port=port)