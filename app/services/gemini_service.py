import requests
import json
from typing import Dict, List
from app.config import settings


class GeminiService:
    def __init__(self):
        self.base_url = "http://localhost:8000"  # URL de tu API Gemini
        self.timeout = 30  # Timeout en segundos

    def extract_components_from_text(self, text: str, topic: str, educational_level: str = "secundaria") -> Dict:
        """
        Extrae componentes de aprendizaje usando la API Gemini
        """
        try:
            payload = {
                "text_content": text,
                "course_topic": topic,
                "educational_level": educational_level
            }

            response = requests.post(
                f"{self.base_url}/prompt/oa/extract-components",
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()

                # Adaptar la respuesta al formato esperado por el sistema actual
                return self._adapt_components_response(result)
            else:
                print(f"Error en Gemini API: {response.status_code} - {response.text}")
                return self._create_fallback_components(text, topic)

        except requests.exceptions.RequestException as e:
            print(f"Error de conexión con Gemini API: {str(e)}")
            return self._create_fallback_components(text, topic)
        except Exception as e:
            print(f"Error inesperado en Gemini service: {str(e)}")
            return self._create_fallback_components(text, topic)

    def generate_questions_from_topic(self, topic: str, difficulty: str = "intermedio",
                                      num_questions: int = 5, context_text: str = None) -> List[Dict]:
        """
        Genera preguntas de evaluación usando la API Gemini
        """
        try:
            payload = {
                "topic": topic,
                "difficulty": difficulty,
                "num_questions": num_questions,
                "context_text": context_text
            }

            response = requests.post(
                f"{self.base_url}/prompt/oa/generate-questions",
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return self._adapt_questions_response(result)
            else:
                print(f"Error en Gemini API: {response.status_code} - {response.text}")
                return self._create_fallback_questions(topic, difficulty, num_questions)

        except requests.exceptions.RequestException as e:
            print(f"Error de conexión con Gemini API: {str(e)}")
            return self._create_fallback_questions(topic, difficulty, num_questions)
        except Exception as e:
            print(f"Error inesperado en Gemini service: {str(e)}")
            return self._create_fallback_questions(topic, difficulty, num_questions)

    def _adapt_components_response(self, gemini_response: Dict) -> Dict:
        """
        Adapta la respuesta de Gemini al formato esperado por el sistema actual
        """
        return {
            "objetivos": gemini_response.get("objetivos_aprendizaje", []),
            "teoria": gemini_response.get("contenido_teorico", ""),
            "ejercicios": gemini_response.get("ejercicios_practicos", []),
            "preguntas_sugeridas": gemini_response.get("preguntas_evaluacion", [])
        }

    def _adapt_questions_response(self, gemini_response: Dict) -> List[Dict]:
        """
        Adapta las preguntas de Gemini al formato esperado por el sistema actual
        """
        questions = []
        for gemini_question in gemini_response.get("preguntas", []):
            question = {
                "pregunta": gemini_question.get("pregunta", ""),
                "dificultad": gemini_question.get("dificultad", "intermedio"),
                "alternativas": gemini_question.get("alternativas", [])
            }
            questions.append(question)
        return questions

    def _create_fallback_components(self, text: str, topic: str) -> Dict:
        """
        Crea componentes básicos como fallback cuando Gemini falla
        """
        # Tomar las primeras líneas del texto como teoría
        theory_lines = text.split('\n')
        theory = ' '.join([line.strip() for line in theory_lines[:3] if line.strip()])

        return {
            "objetivos": [
                f"Comprender los conceptos principales de {topic}",
                f"Aplicar los conocimientos de {topic} en ejercicios prácticos",
                f"Analizar situaciones relacionadas con {topic}"
            ],
            "teoria": theory[:500] + "..." if len(theory) > 500 else theory,
            "ejercicios": [
                f"Realizar un resumen de los conceptos principales de {topic}",
                f"Aplicar los conceptos de {topic} en un caso práctico"
            ],
            "preguntas_sugeridas": []
        }

    def _create_fallback_questions(self, topic: str, difficulty: str, num_questions: int) -> List[Dict]:
        """
        Crea preguntas básicas como fallback cuando Gemini falla
        """
        questions = []
        base_questions = {
            "básico": [
                f"¿Qué es {topic}?",
                f"¿Cuál es el concepto principal de {topic}?",
                f"¿Para qué se utiliza {topic} en la vida real?"
            ],
            "intermedio": [
                f"Explica cómo aplicar {topic} en un problema práctico",
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


    #nuevo
    def generate_base_read_write_oa(self, topic: str, educational_level: str = "secundaria") -> Dict:
        """
        Genera el OA de Lectura/Escritura y la metadata pedagógica del nodo.
        """
        try:
            payload = {
                "course_topic": topic,
                "educational_level": educational_level
            }

            # Asumimos que crearás este nuevo endpoint en tu API de IA local
            response = requests.post(
                f"{self.base_url}/prompt/oa/generate-base",
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return self._adapt_base_oa_response(result)
            else:
                print(f"Error en Gemini API: {response.status_code} - {response.text}")
                return self._create_fallback_base_oa(topic)

        except requests.exceptions.RequestException as e:
            print(f"Error de conexión con Gemini API: {str(e)}")
            return self._create_fallback_base_oa(topic)
        except Exception as e:
            print(f"Error inesperado en Gemini service: {str(e)}")
            return self._create_fallback_base_oa(topic)

    def _adapt_base_oa_response(self, gemini_response: Dict) -> Dict:
        """Adapta la respuesta al esquema de nuestra base de datos"""
        return {
            "ge_objective": gemini_response.get("ge_objective", ""),
            "objectives": gemini_response.get("objectives", {}),
            "approach": gemini_response.get("approach", ""),
            "content_markdown": gemini_response.get("content_markdown", "")
        }

    def _create_fallback_base_oa(self, topic: str) -> Dict:
        """Fallback en caso de que la IA no responda"""
        return {
            "ge_objective": f"Comprender los fundamentos de {topic}",
            "objectives": {"1": "Identificar el concepto", "2": "Aplicar la teoría"},
            "approach": "Enfoque teórico estándar",
            "content_markdown": f"# {topic}\n\nActualmente el contenido detallado para este tema se encuentra en proceso de generación. Por favor, revisa el material de apoyo brindado por el docente."
        }

    def test_connection(self) -> bool:
        """
        Prueba la conexión con la API Gemini
        """
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            return response.status_code == 200
        except:
            return False