from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.database import get_db
from app.database import models
from app.schemas.learning_objects import (
    LearningObjectResponse, TypeResponse, LevelResponse,
    LearningStyleResponse, TopicResponse, LOComponentResponse
)
from app.services.file_service import S3Service

router = APIRouter(prefix="/learning-objects", tags=["learning-objects"])


@router.get("/", response_model=List[LearningObjectResponse])
def get_learning_objects(
        skip: int = 0,
        limit: int = 100,
        topic_id: Optional[int] = None,
        level_id: Optional[int] = None,
        db: Session = Depends(get_db)
):
    """Obtiene todos los objetos de aprendizaje con filtros opcionales"""
    query = db.query(models.LearningObject)

    if topic_id:
        query = query.filter(models.LearningObject.idTopic == topic_id)
    if level_id:
        query = query.filter(models.LearningObject.idLevel == level_id)

    return query.offset(skip).limit(limit).all()


@router.get("/{object_id}", response_model=LearningObjectResponse)
def get_learning_object(object_id: int, db: Session = Depends(get_db)):
    """Obtiene un objeto de aprendizaje específico por ID"""
    learning_object = db.query(models.LearningObject).filter(
        models.LearningObject.idObject == object_id
    ).first()

    if not learning_object:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objeto de aprendizaje no encontrado"
        )

    return learning_object


@router.get("/{object_id}/download-url")
def get_download_url(object_id: int, db: Session = Depends(get_db)):
    """Genera una URL firmada para descargar el archivo del objeto de aprendizaje"""
    learning_object = db.query(models.LearningObject).filter(
        models.LearningObject.idObject == object_id
    ).first()

    if not learning_object:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objeto de aprendizaje no encontrado"
        )

    s3_service = S3Service()
    download_url = s3_service.get_presigned_url(learning_object.s3_key)

    return {
        "download_url": download_url,
        "file_name": learning_object.file_name,
        "expires_in": "1 hora"
    }


@router.get("/{object_id}/components", response_model=List[LOComponentResponse])
def get_learning_object_components(object_id: int, db: Session = Depends(get_db)):
    """Obtiene los componentes de un objeto de aprendizaje"""
    components = db.query(models.LOComponent).filter(
        models.LOComponent.idObject == object_id
    ).all()

    return components


# Endpoints para tipos, niveles, estilos y tópicos
@router.get("/types/", response_model=List[TypeResponse])
def get_types(db: Session = Depends(get_db)):
    return db.query(models.Type).all()


@router.get("/levels/", response_model=List[LevelResponse])
def get_levels(db: Session = Depends(get_db)):
    return db.query(models.Level).all()


@router.get("/learning-styles/", response_model=List[LearningStyleResponse])
def get_learning_styles(db: Session = Depends(get_db)):
    return db.query(models.LearningStyle).all()


@router.get("/topics/", response_model=List[TopicResponse])
def get_topics(db: Session = Depends(get_db)):
    return db.query(models.Topic).all()