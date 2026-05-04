from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.database import get_db
from app.services.oa_generator import generar_y_guardar_oas_con_ia
from app.database import models
from pydantic import BaseModel
from app.schemas.learning_objects import (
    LearningObjectResponse, TypeResponse, LevelResponse,
    LearningStyleResponse, TopicResponse, LOComponentResponse
)
from app.services.file_service import S3Service

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/learning-objects", tags=["learning-objects"])


class LearningStyleRequest(BaseModel):
    styleName: str
    porcentaje: float


class TopicStyleRequest(BaseModel):
    topicId: str
    topicName: str
    learningStyles: List[LearningStyleRequest]


class ComponentResponse(BaseModel):
    id: int
    componentType: str
    fileName: str
    fileExtension: str
    estimatedDuration: int
    s3Url: str


class LearningObjectResponse(BaseModel):
    idObject: int
    title: str
    author: Optional[str]
    typeName: str
    levelName: str
    styleName: str
    topicName: str
    fileName: str
    fileExtension: str
    estimatedDuration: int
    s3Url: str
    stylePercentage: float
    components: List[ComponentResponse]
    # --- NUEVOS CAMPOS ADITIVOS ---
    ge_objective: Optional[str] = None
    objectives: Optional[dict] = None  # O List[str] si prefieres manejarlo como lista
    approach: Optional[str] = None

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


def create_mock_learning_objects(topic_id: str, topic_name: str,
                                 learning_styles: List[LearningStyleRequest]) -> List[dict]:
    """
    Crea objetos de aprendizaje mock cuando no hay datos reales en la BD
    """
    # Mapeo de estilos a URLs reales
    STYLE_URLS = {
        "Visual": "https://app-tesis-oa.s3.us-east-2.amazonaws.com/learning-objects/01/ECUACIONES+LINEALES+Super+facil+para+principiantes.mp4",
        "Auditivo": "https://app-tesis-oa.s3.us-east-2.amazonaws.com/learning-objects/01/ECUACIONES+LINEALES+Super+facil+para+principiantes.mp3",
        "lectura/escritura": "https://app-tesis-oa.s3.us-east-2.amazonaws.com/learning-objects/01/Ecuaciones+lineales+pdf.pdf"
    }

    # Mapeo de tipos de archivo por estilo
    STYLE_FILE_TYPES = {
        "Visual": {"type": "Video", "extension": "mp4"},
        "Auditivo": {"type": "Audio", "extension": "mp3"},
        "lectura/escritura": {"type": "Documento", "extension": "pdf"}
    }

    # Ordenar estilos por porcentaje descendente
    sorted_styles = sorted(learning_styles, key=lambda x: x.porcentaje, reverse=True)

    mock_objects = []

    # Crear un OA por cada estilo (máximo 3)
    for idx, style in enumerate(sorted_styles[:3], 1):
        print(f"Debug - Estilo recibido: '{style.styleName}' (repr: {repr(style.styleName)})")
        # Obtener URL real o usar mock genérica
        s3_url = STYLE_URLS.get(style.styleName,
                                f"https://mock-bucket.s3.amazonaws.com/learning-objects/mock_{topic_id.lower()}/original/material_{idx}.pdf")

        # Obtener tipo y extensión según el estilo
        file_info = STYLE_FILE_TYPES.get(style.styleName, {"type": "Documento", "extension": "pdf"})

        mock_obj = {
            "idObject": 1000 + idx,
            "title": f"Introducción a {topic_name} - {style.styleName}",
            "author": "Sistema Educativo",
            "typeName": file_info["type"],
            "levelName": "Intermedio",
            "styleName": style.styleName,
            "topicName": topic_name,
            "fileName": f"{topic_id.lower()}_{style.styleName.lower().replace('/', '_')}_{idx}.{file_info['extension']}",
            "fileExtension": file_info["extension"],
            "estimatedDuration": 30 + (idx * 10),
            "s3Url": s3_url,
            "stylePercentage": float(style.porcentaje),
            "components": [
                {
                    "id": 2000 + (idx * 10) + 1,
                    "componentType": "objetivos",
                    "fileName": f"objetivos_{idx}.pdf",
                    "fileExtension": "pdf",
                    "estimatedDuration": 5,
                    "s3Url": f"https://mock-bucket.s3.amazonaws.com/learning-objects/mock_{topic_id.lower()}/components/objetivos_{idx}.pdf"
                },
                {
                    "id": 2000 + (idx * 10) + 2,
                    "componentType": "teoria",
                    "fileName": f"teoria_{idx}.pdf",
                    "fileExtension": "pdf",
                    "estimatedDuration": 15,
                    "s3Url": f"https://mock-bucket.s3.amazonaws.com/learning-objects/mock_{topic_id.lower()}/components/teoria_{idx}.pdf"
                },
                {
                    "id": 2000 + (idx * 10) + 3,
                    "componentType": "ejercicios",
                    "fileName": f"ejercicios_{idx}.pdf",
                    "fileExtension": "pdf",
                    "estimatedDuration": 20,
                    "s3Url": f"https://mock-bucket.s3.amazonaws.com/learning-objects/mock_{topic_id.lower()}/components/ejercicios_{idx}.pdf"
                }
            ]
        }
        mock_objects.append(mock_obj)

    return mock_objects

import logging

logger = logging.getLogger(__name__)

@router.post("/by-topic-and-styles", response_model=TopicLearningObjectsResponse,response_model_exclude_none=True)
async def get_learning_objects_by_topic_and_styles(
    request: TopicStyleRequest,
    db: Session = Depends(get_db)
):
    try:
        logger.info("🔵 Inicio petición /by-topic-and-styles")
        logger.info(
            "📥 Request recibido: topicId=%s | topicName=%s | styles=%s",
            request.topicId,
            request.topicName,
            request.learningStyles
        )

        # -----------------------------------
        # Buscar Topic
        # -----------------------------------
        topic = None

        try:
            topic_id = int(request.topicId.replace("T", ""))
            logger.info("🔍 Buscando topic por ID: %s", topic_id)

            topic = db.query(models.Topic).filter(
                models.Topic.id == topic_id
            ).first()

            if topic:
                logger.info("✅ Topic encontrado por ID: %s", topic.nombre)

        except Exception as ex:
            logger.warning(
                "⚠ No se pudo convertir topicId=%s a entero. Error=%s",
                request.topicId,
                str(ex)
            )

        if not topic:
            logger.info("🔍 Buscando topic por nombre: %s", request.topicName)

            topic = db.query(models.Topic).filter(
                models.Topic.nombre == request.topicName
            ).first()

            if topic:
                logger.info("✅ Topic encontrado por nombre: %s", topic.nombre)

        if not topic:
            logger.error(
                "❌ Topic no encontrado. topicId=%s | topicName=%s",
                request.topicId,
                request.topicName
            )

            raise HTTPException(
                status_code=404,
                detail="Tema no encontrado"
            )

        # -----------------------------------
        # Buscar 1 OA por cada estilo
        # -----------------------------------
        logger.info("📚 Iniciando búsqueda de OAs por estilos")

        results = []

        for style_request in request.learningStyles:
            try:
                style_name = style_request.styleName
                porcentaje = style_request.porcentaje

                logger.info(
                    "🎯 Procesando estilo: %s | porcentaje=%s",
                    style_name,
                    porcentaje
                )

                style = db.query(models.LearningStyle).filter(
                    models.LearningStyle.stype == style_name
                ).first()

                if not style:
                    logger.warning("⚠ Estilo no encontrado: %s", style_name)

                    results.append({
                        "styleName": style_name,
                        "learningObject": None
                    })
                    continue

                lo = db.query(models.LearningObject).filter(
                    models.LearningObject.idTopic == topic.id,
                    models.LearningObject.idStyle == style.id
                ).first()

                if not lo:
                    logger.warning(
                        "⚠ No existe OA para topic=%s style=%s",
                        topic.nombre,
                        style_name
                    )

                    results.append({
                        "styleName": style_name,
                        "learningObject": None
                    })
                    continue

                results.append({
                    "styleName": style_name,
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
                        "url": lo.s3_url,
                        "geObjective": lo.ge_objective,
                        "objectives": lo.objectives,
                        "approach": lo.approach
                    }
                })

            except Exception:
                logger.exception("🔥 Error procesando estilo=%s", style_name)

                results.append({
                    "styleName": style_name,
                    "learningObject": None
                })

        # -----------------------------------
        # Resultado final
        # -----------------------------------
        total = len([
            x for x in results
            if x["learningObject"] is not None
        ])

        logger.info(
            "📦 Resultado final: total encontrados=%s de %s estilos",
            total,
            len(request.learningStyles)
        )

        return {
            "success": True,
            "message": "Objetos de aprendizaje encontrados",
            "topicId": topic.id,
            "topicName": topic.nombre,
            "results": results,
            "totalObjects": total
        }

    except HTTPException as http_error:
        logger.warning(
            "⚠ HTTPException controlada: %s",
            http_error.detail
        )
        raise http_error

    except Exception as e:
        logger.exception("🔥 ERROR GENERAL en endpoint /by-topic-and-styles")

        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

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