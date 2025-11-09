from app.services.huggingface_service import HuggingFaceService
from app.config import settings
import json
from typing import List, Dict


class AIService:
    def __init__(self):
        # Usar Hugging Face como proveedor principal
        self.hf_service = HuggingFaceService()

    def extract_components_from_text(self, text: str) -> Dict:
        """Extrae componentes de aprendizaje usando Hugging Face"""
        return self.hf_service.extract_components_from_text(text)

    def generate_questions_from_topic(self, topic: str, difficulty: str = "intermedio", num_questions: int = 5) -> List[
        Dict]:
        """Genera preguntas usando Hugging Face"""
        return self.hf_service.generate_questions_from_topic(topic, difficulty, num_questions)

    def test_connection(self) -> bool:
        """Prueba la conexión con el servicio de IA"""
        return self.hf_service.test_connection()