from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.database import models
from app.schemas.questions import QuestionResponse, QuestionCreate
from app.services.ai_service import AIService

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("/", response_model=List[QuestionResponse])
def get_questions(
        topic_id: int = None,
        difficulty: str = None,
        db: Session = Depends(get_db)
):
    """Obtiene preguntas con filtros opcionales por tópico y dificultad"""
    query = db.query(models.Question)

    if topic_id:
        query = query.filter(models.Question.id_topic == topic_id)
    if difficulty:
        query = query.filter(models.Question.difficulty_level == difficulty)

    return query.all()


@router.post("/", response_model=QuestionResponse)
def create_question(question: QuestionCreate, db: Session = Depends(get_db)):
    """Crea una nueva pregunta con sus alternativas"""
    # Verificar que el tópico existe
    topic = db.query(models.Topic).filter(models.Topic.id == question.id_topic).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tópico no encontrado"
        )

    # Crear la pregunta
    db_question = models.Question(
        question_text=question.question_text,
        id_topic=question.id_topic,
        difficulty_level=question.difficulty_level
    )

    db.add(db_question)
    db.commit()
    db.refresh(db_question)

    # Crear las alternativas
    for alternative in question.alternatives:
        db_alternative = models.QuestionAlternative(
            question_id=db_question.id,
            alternative_text=alternative.alternative_text,
            is_correct=alternative.is_correct
        )
        db.add(db_alternative)

    db.commit()
    db.refresh(db_question)

    return db_question


@router.post("/generate-from-topic/{topic_id}")
def generate_questions_from_topic(
        topic_id: int,
        difficulty: str = "intermedio",
        num_questions: int = 5,
        db: Session = Depends(get_db)
):
    """Genera preguntas automáticamente para un tópico usando Gemini"""
    # Obtener información del tópico
    topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tópico no encontrado"
        )

    # Generar preguntas usando Gemini
    ai_service = AIService()
    generated_questions = ai_service.generate_questions_from_topic(
        topic.nombre, difficulty, num_questions
    )

    created_questions = []

    # Guardar preguntas generadas en la base de datos
    for gen_question in generated_questions:
        # Crear la pregunta en la base de datos
        db_question = models.Question(
            question_text=gen_question["pregunta"],
            id_topic=topic_id,
            difficulty_level=difficulty
        )

        db.add(db_question)
        db.commit()
        db.refresh(db_question)

        # Guardar alternativas
        for alt in gen_question["alternativas"]:
            db_alternative = models.QuestionAlternative(
                question_id=db_question.id,
                alternative_text=alt["texto"],
                is_correct=alt["correcta"]
            )
            db.add(db_alternative)

        db.commit()
        created_questions.append(db_question)

    return {
        "message": f"Se generaron {len(created_questions)} preguntas para el tópico '{topic.nombre}'",
        "questions_created": len(created_questions),
        "difficulty": difficulty
    }


@router.get("/{question_id}", response_model=QuestionResponse)
def get_question(question_id: int, db: Session = Depends(get_db)):
    """Obtiene una pregunta específica por ID"""
    question = db.query(models.Question).filter(models.Question.id == question_id).first()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pregunta no encontrada"
        )

    return question