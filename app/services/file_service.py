import boto3
from botocore.exceptions import ClientError
from app.config import settings
import uuid
import os
from typing import Optional


class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket = settings.S3_BUCKET

    def upload_file(self, file_content, original_file_name, object_id: Optional[str] = None,
                    component_type: Optional[str] = None, folder: str = "learning-objects") -> dict:
        """Sube un archivo a S3 con estructura organizada"""
        try:
            # Generar nombre de archivo legible
            clean_name = self._clean_filename(original_file_name)
            file_extension = os.path.splitext(clean_name)[1].lower()

            # Definir la estructura de carpetas
            if object_id and component_type:
                # Para componentes de un objeto específico
                s3_key = f"{folder}/{object_id}/components/{component_type}{file_extension}"
                file_name = f"{component_type}{file_extension}"
            elif object_id:
                # Para archivo original de un objeto
                s3_key = f"{folder}/{object_id}/{clean_name}"
                file_name = clean_name
            else:
                # Para archivos temporales o sin estructura
                unique_id = uuid.uuid4().hex[:8]  # ID más corto
                s3_key = f"{folder}/temp/{unique_id}_{clean_name}"
                file_name = clean_name

            # Subir archivo
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=file_content,
                ContentType=self._get_content_type(file_extension),
                Metadata={
                    'original-filename': original_file_name,
                    'object-id': str(object_id) if object_id else 'temp',
                    'component-type': component_type if component_type else 'original'
                }
            )

            return {
                "bucket": self.bucket,
                "key": s3_key,
                "file_name": file_name,
                "original_file_name": original_file_name,
                "file_extension": file_extension,
                "file_size": len(file_content)
            }

        except ClientError as e:
            raise Exception(f"Error uploading file to S3: {str(e)}")

    def _clean_filename(self, filename: str) -> str:
        """Limpia el nombre de archivo para hacerlo más legible"""
        # Remover extensión temporalmente
        name, ext = os.path.splitext(filename)

        # Limpiar caracteres especiales y espacios
        cleaned = "".join(c if c.isalnum() or c in ['-', '_', '.'] else '_' for c in name)

        # Limitar longitud
        cleaned = cleaned[:50]

        return f"{cleaned}{ext}"

    def _get_content_type(self, file_extension):
        """Obtiene el content type basado en la extensión del archivo"""
        content_types = {
            '.pdf': 'application/pdf',
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.txt': 'text/plain',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.md': 'text/markdown',
            '.json': 'application/json',
            '.mp3': 'audio/mpeg'
        }
        return content_types.get(file_extension.lower(), 'application/octet-stream')

    def get_presigned_url(self, s3_key, expiration=3600):
        """Genera una URL firmada para acceder al archivo"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise Exception(f"Error generating presigned URL: {str(e)}")

    def delete_file(self, s3_key):
        """Elimina un archivo de S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError as e:
            raise Exception(f"Error deleting file from S3: {str(e)}")

    def delete_object_folder(self, object_id: str):
        """Elimina toda la carpeta de un objeto"""
        try:
            # Listar todos los objetos en la carpeta del objeto
            objects_to_delete = []
            paginator = self.s3_client.get_paginator('list_objects_v2')

            for page in paginator.paginate(Bucket=self.bucket, Prefix=f"learning-objects/{object_id}/"):
                if 'Contents' in page:
                    objects_to_delete.extend([{'Key': obj['Key']} for obj in page['Contents']])

            # Eliminar todos los objetos
            if objects_to_delete:
                self.s3_client.delete_objects(
                    Bucket=self.bucket,
                    Delete={'Objects': objects_to_delete}
                )

            return True
        except ClientError as e:
            raise Exception(f"Error deleting object folder from S3: {str(e)}")