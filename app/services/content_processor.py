import PyPDF2
import io
from typing import Dict, List
from app.services.ai_service import AIService
from app.services.file_service import S3Service
from app.services.pdf_generator import PDFGenerator


class ContentProcessor:
    def __init__(self):
        self.ai_service = AIService()
        self.s3_service = S3Service()
        self.pdf_generator = PDFGenerator()

    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extrae texto de un archivo PDF"""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""

            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"

            return text
        except Exception as e:
            raise Exception(f"Error extrayendo texto del PDF: {str(e)}")

    def extract_text_from_txt(self, file_content: bytes) -> str:
        """Extrae texto de un archivo TXT"""
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            # Intentar con otra codificación si UTF-8 falla
            return file_content.decode('latin-1')

    def process_learning_object(self, file_content: bytes, file_name: str, metadata: Dict) -> Dict:
        """Procesa un objeto de aprendizaje y extrae sus componentes usando Gemini"""
        # Extraer texto según el tipo de archivo
        file_extension = file_name.lower().split('.')[-1]

        text_content = ""
        if file_extension == 'pdf':
            text_content = self.extract_text_from_pdf(file_content)
        elif file_extension == 'txt':
            text_content = self.extract_text_from_txt(file_content)
        else:
            # Para otros tipos de archivo, usar metadata básica
            text_content = f"Título: {metadata.get('title', '')}\nAutor: {metadata.get('author', '')}\nDescripción: Material educativo sobre {metadata.get('title', 'el tema')}"

        # Validar que se extrajo texto suficiente
        if not text_content or len(text_content.strip()) < 50:
            text_content = f"""
            Título: {metadata.get('title', 'Material Educativo')}
            Autor: {metadata.get('author', 'Desconocido')}
            Tema: {metadata.get('title', 'Contenido educativo')}

            Este material cubre conceptos fundamentales sobre {metadata.get('title', 'el tema')}.
            Incluye explicaciones teóricas, ejemplos prácticos y ejercicios de aplicación.
            """

        # Usar Gemini para extraer componentes (¡Aquí está la mejora principal!)
        components = self.ai_service.extract_components_from_text(
            text_content,
            metadata.get('title', 'Material Educativo')
        )

        return {
            "text_content": text_content,
            "components": components
        }

    def create_component_files(self, components: Dict, object_id: int, base_file_name: str) -> List[Dict]:
        """Crea archivos PDF individuales para cada componente"""
        component_files = []

        # Procesar objetivos como PDF
        if components.get("objetivos"):
            pdf_content = self.pdf_generator.create_objectives_pdf(
                components["objetivos"],
                f"Objetivos - {base_file_name}"
            )
            file_info = self.s3_service.upload_file(
                file_content=pdf_content,
                original_file_name=f"{base_file_name}_objetivos.pdf",
                object_id=str(object_id),
                component_type="objetivos"
            )
            component_files.append({
                **file_info,
                "component_type": "objetivos",
                "estimated_duration": 5
            })

        # Procesar teoría como PDF
        if components.get("teoria"):
            pdf_content = self.pdf_generator.create_theory_pdf(
                components["teoria"],
                f"Teoría - {base_file_name}"
            )
            file_info = self.s3_service.upload_file(
                file_content=pdf_content,
                original_file_name=f"{base_file_name}_teoria.pdf",
                object_id=str(object_id),
                component_type="teoria"
            )
            component_files.append({
                **file_info,
                "component_type": "teoria",
                "estimated_duration": 15
            })

        # Procesar ejercicios como PDF
        if components.get("ejercicios"):
            pdf_content = self.pdf_generator.create_exercises_pdf(
                components["ejercicios"],
                f"Ejercicios - {base_file_name}"
            )
            file_info = self.s3_service.upload_file(
                file_content=pdf_content,
                original_file_name=f"{base_file_name}_ejercicios.pdf",
                object_id=str(object_id),
                component_type="ejercicios"
            )
            component_files.append({
                **file_info,
                "component_type": "ejercicios",
                "estimated_duration": 20
            })

        return component_files