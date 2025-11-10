from app.services.gemini_service import GeminiService
from app.config import settings
import json
from typing import List, Dict


class AIService:
    def __init__(self):
        # Usar Hugging Face como proveedor principal
        self.gemini_service = GeminiService()

    def extract_components_from_text(self, text: str, topic: str) -> Dict:
        """Extrae componentes de aprendizaje usando Gemini"""
        return self.gemini_service.extract_components_from_text(text, topic)

    def generate_questions_from_topic(self, topic: str, difficulty: str = "intermedio", num_questions: int = 5) -> List[
        Dict]:
        """Genera preguntas usando Gemini"""
        return self.gemini_service.generate_questions_from_topic(topic, difficulty, num_questions)

    def test_connection(self) -> bool:
        """Prueba la conexión con el servicio de IA"""
        return self.gemini_service.test_connection()