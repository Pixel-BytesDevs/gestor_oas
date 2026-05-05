from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database import models
from app.services.file_service import S3Service
from app.services.content_processor import ContentProcessor
from app.schemas.learning_objects import LearningObjectResponse
import json

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/learning-object", response_model=LearningObjectResponse)
async def upload_learning_object(
        file: UploadFile = File(...),
        title: str = Form(...),
        author: str = Form(None),
        idType: int = Form(...),
        idLevel: int = Form(...),
        idStyle: int = Form(...),
        idTopic: int = Form(...),
        db: Session = Depends(get_db)
):
    """Endpoint para subir un nuevo objeto de aprendizaje"""

    # Validar tipo de archivo
    allowed_extensions = {'pdf', 'mp4', 'avi', 'mov', 'doc', 'docx', 'ppt', 'pptx', 'txt','m4a'}
    file_extension = file.filename.split('.')[-1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(allowed_extensions)}"
        )

    try:
        # Leer contenido del archivo

        file_content = await file.read()
        file_size = len(file_content)

        # PRIMERO: Crear el objeto de aprendizaje en la base de datos para obtener el ID
        db_learning_object = models.LearningObject(
            title=title,
            author=author,
            idType=idType,
            idLevel=idLevel,
            idStyle=idStyle,
            idTopic=idTopic,
            # Estos campos se actualizarán después de subir a S3
            s3_bucket="",
            s3_key="",
            s3_url="",  # ✅ Inicializar URL vacía
            file_name=file.filename,
            file_size=file_size,
            file_extension=file_extension,
            estimated_duration=30
        )

        db.add(db_learning_object)
        db.commit()
        db.refresh(db_learning_object)

        # AHORA tenemos el ID del objeto para usar en la estructura de S3
        object_id = db_learning_object.idObject
        topic_id = db_learning_object.idTopic

        # Subir archivo principal a S3 con la nueva estructura
        s3_service = S3Service()
        file_info = s3_service.upload_file(
            file_content=file_content,
            original_file_name=file.filename,
            object_id=str(topic_id)
        )

        # ✅ Generar URL presignada (válida por 7 días por defecto)
        s3_url = s3_service.get_presigned_url(file_info["key"], expiration=604800)  # 7 días

        # Actualizar el objeto con la información de S3 y la URL
        db_learning_object.s3_bucket = file_info["bucket"]
        db_learning_object.s3_key = file_info["key"]
        db_learning_object.s3_url = s3_url  # ✅ Guardar URL
        db_learning_object.file_name = file_info["file_name"]
        db.commit()

        # # Procesar contenido para extraer componentes
        # content_processor = ContentProcessor()
        # metadata = {
        #     "title": title,
        #     "author": author
        # }
        #
        # processing_result = content_processor.process_learning_object(
        #     file_content, file.filename, metadata
        # )
        #
        # # Crear componentes del objeto de aprendizaje
        # component_files = content_processor.create_component_files(
        #     processing_result["components"],
        #     object_id,
        #     f"lo_{object_id}"
        # )
        #
        # for component_info in component_files:
        #     # ✅ Generar URL para cada componente
        #     component_url = s3_service.get_presigned_url(component_info["key"], expiration=604800)
        #
        #     db_component = models.LOComponent(
        #         idObject=object_id,
        #         idType=idType,
        #         component_type=component_info["component_type"],
        #         s3_bucket=component_info["bucket"],
        #         s3_key=component_info["key"],
        #         s3_url=component_url,  # ✅ Guardar URL del componente
        #         file_name=component_info["file_name"],
        #         file_size=component_info["file_size"],
        #         file_extension=component_info["file_extension"],
        #         estimated_duration=component_info["estimated_duration"]
        #     )
        #     db.add(db_component)
        #
        # db.commit()
        # db.refresh(db_learning_object)

        return db_learning_object

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando el archivo: {str(e)}"
        )