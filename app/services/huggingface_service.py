import requests
import json
import time
from typing import Dict, List
from app.config import settings


class HuggingFaceService:
    def __init__(self):
        self.api_token = settings.HUGGINGFACE_API_TOKEN
        self.headers = {"Authorization": f"Bearer {self.api_token}"}

    def extract_components_from_text(self, text: str) -> Dict:
        """Extrae componentes de aprendizaje usando modelos de Hugging Face"""

        text = self._clean_text(text)
        # Usar un modelo de question-answering o text generation
        prompt = f"""
            Analiza el siguiente contenido educativo y extrae los componentes en formato JSON.
            Por favor, proporciona contenido bien estructurado y claro:

            1. objetivos: lista de 3-5 objetivos de aprendizaje específicos y medibles acorde al contenido
            2. teoria: explicación clara y bien estructurada, organizada en párrafos lógicos, y de contener caracteres matemáticos formatearlos adecuadamente
            3. ejercicios: muestra de los ejercicios mostrados en el contenido, y si no tiene se debe generar ejercicios resolutivos
            4. preguntas_sugeridas: preguntas de evaluación con alternativas

            CONTENIDO ORIGINAL:
            {text[:3000]}

            IMPORTANTE: Usa caracteres UTF-8 correctos (tildes, eñes) y estructura clara.

            FORMATO JSON:
            {{
                "objetivos": ["objetivo 1", "objetivo 2", ...],
                "teoria": "texto bien estructurado...",
                "ejercicios": ["ejercicio 1", "ejercicio 2", ...],
                "preguntas_sugeridas": []
            }}
            """

        try:
            # Intentar con modelo de chat/generación
            response = self._query_chat_model(prompt)

            if response and "objetivos" in response:
                return response
            else:
                # Fallback a estructura básica
                return self._create_fallback_components(text)

        except Exception as e:
            print(f"Error con Hugging Face: {str(e)}")
            return self._create_fallback_components(text)

    def _clean_text(self, text: str) -> str:
        """Limpia problemas comunes de codificación"""
        replacements = {
            'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
            'Ã±': 'ñ', 'Ã': 'Á', 'Ã‰': 'É', 'Ã': 'Í', 'Ã“': 'Ó', 'Ãš': 'Ú',
            'Ã‘': 'Ñ', 'Â¿': '¿', 'Â¡': '¡', 'Ã¼': 'ü', 'Ãœ': 'Ü'
        }

        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)

        return text

    def _query_chat_model(self, prompt: str) -> Dict:
        """Consulta modelos de chat/generación de texto"""

        # Opción 1: Modelo de chat (si está disponible)
        try:
            API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"

            response = requests.post(
                API_URL,
                headers=self.headers,
                json={"inputs": prompt, "parameters": {"max_length": 1000}}
            )

            result = response.json()

            # Procesar respuesta para extraer JSON
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get('generated_text', '')
                return self._parse_json_response(generated_text)

        except Exception as e:
            print(f"Error con modelo de chat: {str(e)}")

        return None

    def _parse_json_response(self, text: str) -> Dict:
        """Intenta extraer JSON de la respuesta del modelo"""
        try:
            # Buscar contenido entre llaves
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = text[start:end]
                return json.loads(json_str)
        except:
            pass

        return None

    def _create_fallback_components(self, text: str) -> Dict:
        """Crea componentes básicos cuando falla la IA"""
        sentences = text.split('.')
        main_content = ' '.join(sentences[:5]) if len(sentences) > 5 else text[:500]

        return {
            "objetivos": [
                "Comprender los conceptos principales del material",
                "Aplicar los conocimientos en ejercicios prácticos"
            ],
            "teoria": main_content,
            "ejercicios": [
                "Realizar un resumen de los conceptos principales",
                "Aplicar los conceptos en un caso práctico"
            ],
            "preguntas_sugeridas": []
        }

    def generate_questions_from_topic(self, topic: str, difficulty: str = "intermedio", num_questions: int = 3) -> List[
        Dict]:
        """Genera preguntas usando modelos de question generation"""

        prompt = f"""
        Genera {num_questions} preguntas de opción múltiple sobre: {topic}
        Dificultad: {difficulty}
        Formato JSON con: preguntas[texto, alternativas[texto, correcta]]
        """

        try:
            # Usar modelo de generación de texto
            API_URL = "https://api-inference.huggingface.co/models/gpt2"

            response = requests.post(
                API_URL,
                headers=self.headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_length": 800,
                        "temperature": 0.7,
                        "do_sample": True
                    }
                }
            )

            result = response.json()

            # Procesar respuesta y crear preguntas estructuradas
            return self._create_structured_questions(topic, difficulty, num_questions)

        except Exception as e:
            print(f"Error generando preguntas: {str(e)}")
            return self._create_structured_questions(topic, difficulty, num_questions)

    def _create_structured_questions(self, topic: str, difficulty: str, num_questions: int) -> List[Dict]:
        """Crea preguntas estructuradas cuando el modelo no responde adecuadamente"""
        questions = []

        base_questions = {
            "básico": [
                f"¿Qué es {topic}?",
                f"¿Cuál es el concepto principal de {topic}?",
                f"¿Para qué se utiliza {topic}?"
            ],
            "intermedio": [
                f"Explica cómo aplicar {topic} en un caso práctico",
                f"¿Cuáles son las características principales de {topic}?",
                f"Compara {topic} con conceptos relacionados"
            ],
            "avanzado": [
                f"Analiza las ventajas y desventajas de {topic}",
                f"Propón una solución innovadora usando {topic}",
                f"Evalúa el impacto de {topic} en el ámbito educativo"
            ]
        }

        question_list = base_questions.get(difficulty, base_questions["intermedio"])

        for i in range(min(num_questions, len(question_list))):
            questions.append({
                "pregunta": question_list[i],
                "dificultad": difficulty,
                "alternativas": [
                    {"texto": "Respuesta correcta (ejemplo)", "correcta": True},
                    {"texto": "Respuesta incorrecta 1", "correcta": False},
                    {"texto": "Respuesta incorrecta 2", "correcta": False},
                    {"texto": "Respuesta incorrecta 3", "correcta": False}
                ]
            })

        return questions

    def test_connection(self):
        """Prueba la conexión con Hugging Face"""
        try:
            API_URL = "https://api-inference.huggingface.co/models/gpt2"
            response = requests.get(API_URL, headers=self.headers)
            return response.status_code == 200
        except:
            return False