from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.database import get_db
from app.database import models
from pydantic import BaseModel
from app.schemas.learning_objects import (
    LearningObjectResponse, TypeResponse, LevelResponse,
    LearningStyleResponse, TopicResponse, LOComponentResponse
)
from app.services.file_service import S3Service
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/learning-objects", tags=["learning-objects"])


# =========================
# HELPERS
# =========================
def build_s3_url(key: str) -> str:
    """URL pública (solo si el bucket lo permite)"""
    return f"https://{settings.S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


def get_s3_service():
    return S3Service()


def resolve_file_url(s3_key: str, s3_service: S3Service) -> str:
    """
    Decide cómo devolver la URL:
    - firmada (recomendado)
    - pública (si decides hacerlo público)
    """
    if settings.S3_USE_PRESIGNED_URL:
        return s3_service.get_presigned_url(s3_key)
    return build_s3_url(s3_key)


# =========================
# REQUEST MODELS
# =========================
class LearningStyleRequest(BaseModel):
    styleName: str
    porcentaje: float


class TopicStyleRequest(BaseModel):
    topicId: str
    topicName: str
    learningStyles: List[LearningStyleRequest]


# =========================
# RESPONSE MODELS
# =========================
class LearningObjectItem(BaseModel):
    idObject: int
    topicId: int
    topicName: str
    styleId: int
    styleName: str
    title: str
    author: Optional[str] = None
    fileName: Optional[str] = None
    fileExtension: Optional[str] = None
    estimatedDuration: Optional[int] = None
    url: Optional[str] = None
    geObjective: Optional[str] = None
    objectives: Optional[list] = None
    approach: Optional[str] = None


class TopicStyleGroupResponse(BaseModel):
    styleName: str
    learningObject: Optional[LearningObjectItem]


class TopicLearningObjectsResponse(BaseModel):
    success: bool
    message: str
    topicId: int
    topicName: str
    results: List[TopicStyleGroupResponse]
    totalObjects: int


# =========================
# ENDPOINT PRINCIPAL
# =========================
@router.post("/by-topic-and-styles", response_model=TopicLearningObjectsResponse)
async def get_learning_objects_by_topic_and_styles(
    request: TopicStyleRequest,
    db: Session = Depends(get_db),
    s3_service: S3Service = Depends(get_s3_service)
):
    try:
        topic = None

        # Buscar por ID
        try:
            topic_id = int(request.topicId.replace("T", ""))
            topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
        except:
            pass

        # Buscar por nombre
        if not topic:
            topic = db.query(models.Topic).filter(
                models.Topic.nombre == request.topicName
            ).first()

        if not topic:
            raise HTTPException(status_code=404, detail="Tema no encontrado")

        results = []

        for style_request in request.learningStyles:
            style = db.query(models.LearningStyle).filter(
                models.LearningStyle.stype == style_request.styleName
            ).first()

            if not style:
                results.append({
                    "styleName": style_request.styleName,
                    "learningObject": None
                })
                continue

            lo = db.query(models.LearningObject).filter(
                models.LearningObject.idTopic == topic.id,
                models.LearningObject.idStyle == style.id
            ).first()

            if not lo:
                results.append({
                    "styleName": style_request.styleName,
                    "learningObject": None
                })
                continue

            # 🔥 AQUÍ ESTÁ EL CAMBIO CLAVE
            file_url = resolve_file_url(lo.s3_key, s3_service)

            results.append({
                "styleName": style_request.styleName,
                "learningObject": {
                    "idObject": lo.idObject,
                    "topicId": topic.id,
                    "topicName": topic.nombre,
                    "styleId": style.id,
                    "styleName": style.stype,
                    "title": lo.title,
                    "author": lo.author,
                    "fileName": lo.file_name,
                    "fileExtension": lo.file_extension,
                    "estimatedDuration": lo.estimated_duration,
                    "url": file_url,  # 🔥 YA NO USA s3_url
                    "geObjective": lo.ge_objective,
                    "objectives": lo.objectives,
                    "approach": lo.approach
                }
            })

        total = len([x for x in results if x["learningObject"]])

        return {
            "success": True,
            "message": "Objetos de aprendizaje encontrados",
            "topicId": topic.id,
            "topicName": topic.nombre,
            "results": results,
            "totalObjects": total
        }

    except Exception:
        logger.exception("Error en endpoint")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# =========================
# DOWNLOAD URL (CORRECTO)
# =========================
@router.get("/{object_id}/download-url")
def get_download_url(
    object_id: int,
    db: Session = Depends(get_db),
    s3_service: S3Service = Depends(get_s3_service)
):
    learning_object = db.query(models.LearningObject).filter(
        models.LearningObject.idObject == object_id
    ).first()

    if not learning_object:
        raise HTTPException(status_code=404, detail="No encontrado")

    return {
        "download_url": s3_service.get_presigned_url(learning_object.s3_key),
        "file_name": learning_object.file_name,
        "expires_in": settings.S3_URL_EXPIRATION
    }