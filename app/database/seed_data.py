from app.database.database import SessionLocal
from app.database import models


def create_initial_data():
    db = SessionLocal()

    try:
        # Tipos de materiales
        types = [
            models.Type(type="video"),
            models.Type(type="documento"),
            models.Type(type="presentación"),
            models.Type(type="imagen"),
            models.Type(type="audio")
        ]

        # Niveles de dificultad
        levels = [
            models.Level(level="básico"),
            models.Level(level="intermedio"),
            models.Level(level="avanzado")
        ]

        # Estilos de aprendizaje
        styles = [
            models.LearningStyle(stype="visual"),
            models.LearningStyle(stype="auditivo"),
            models.LearningStyle(stype="kinestésico"),
            models.LearningStyle(stype="lectura/escritura")
        ]

        # Tópicos de ejemplo
        topics = [
            models.Topic(nombre="Numeros naturales"),
            models.Topic(nombre="Ecuaciones lineales"),
        ]

        # Agregar todos a la base de datos
        for item in types + levels + styles + topics:
            db.add(item)

        db.commit()
        print("✅ Datos iniciales creados exitosamente")

    except Exception as e:
        db.rollback()
        print(f"❌ Error creando datos iniciales: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_initial_data()