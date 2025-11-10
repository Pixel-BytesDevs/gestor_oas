from fastapi import FastAPI
from app.routers import upload, learning_objects, questions
from app.database.database import engine
from app.database import models

# Crear tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Gestión de Objetos de Aprendizaje",
    description="API para gestionar objetos de aprendizaje, materiales educativos y preguntas de evaluación",
    version="1.0.0"
)

# Incluir routers
app.include_router(upload.router)
app.include_router(learning_objects.router)
app.include_router(questions.router)

@app.get("/")
def read_root():
    return {"message": "Sistema de Gestión de Objetos de Aprendizaje"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)