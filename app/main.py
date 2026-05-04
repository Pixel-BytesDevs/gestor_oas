# app/main.py - Gestor de OAs
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import upload, learning_objects
from app.database.database import engine
from app.database import models
import logging

# Crear las tablas en la base de datos
models.Base.metadata.create_all(bind=engine)



app = FastAPI(
    title="Gestor de Objetos de Aprendizaje",
    description="API para gestionar objetos de aprendizaje y sus componentes",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(upload.router)
app.include_router(learning_objects.router)  # ✅ Nuevo router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)
@app.get("/")
async def root():
    return {
        "message": "Gestor de Objetos de Aprendizaje API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload/learning-object",
            "query_by_topic_and_styles": "/learning-objects/by-topic-and-styles"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)