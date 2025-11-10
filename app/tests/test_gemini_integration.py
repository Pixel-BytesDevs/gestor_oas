import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from app.services.gemini_service import GeminiService
from app.services.ai_service import AIService


def test_gemini_integration():
    print("🧪 Probando integración con Gemini...")

    # Test 1: Conexión con API Gemini
    gemini_service = GeminiService()
    if gemini_service.test_connection():
        print("✅ Conexión con API Gemini exitosa")
    else:
        print("❌ No se pudo conectar a la API Gemini")
        print("   Asegúrate de que tu API Gemini esté ejecutándose en http://localhost:8000")
        return

    # Test 2: Extracción de componentes
    print("\n📝 Probando extracción de componentes...")
    ai_service = AIService()

    test_text = """
    Las ecuaciones lineales son fundamentales en álgebra. Una ecuación lineal es una igualdad matemática que contiene una o más variables. 
    La forma general es: ax + b = 0, donde 'a' y 'b' son constantes y 'x' es la variable.

    Para resolver una ecuación lineal, debemos despejar la variable x. Por ejemplo, en la ecuación 2x + 3 = 7, 
    restamos 3 de ambos lados: 2x = 4, luego dividimos entre 2: x = 2.

    Las ecuaciones lineales tienen aplicaciones en física, economía y muchas otras áreas. Se utilizan para modelar relaciones lineales entre variables.
    """

    components = ai_service.extract_components_from_text(test_text, "Ecuaciones Lineales")
    print("✅ Componentes extraídos:")
    print(f"   - Objetivos: {len(components.get('objetivos', []))}")
    print(f"   - Teoría: {len(components.get('teoria', ''))} caracteres")
    print(f"   - Ejercicios: {len(components.get('ejercicios', []))}")
    print(f"   - Preguntas sugeridas: {len(components.get('preguntas_sugeridas', []))}")

    # Test 3: Generación de preguntas
    print("\n📝 Probando generación de preguntas...")
    questions = ai_service.generate_questions_from_topic("Ecuaciones Lineales", "básico", 2)
    print(f"✅ Preguntas generadas: {len(questions)}")

    for i, q in enumerate(questions):
        print(f"   {i + 1}. {q['pregunta'][:80]}...")
        print(f"      Alternativas: {len(q['alternativas'])}")

    print("\n🎉 ¡Integración con Gemini completada exitosamente!")


if __name__ == "__main__":
    test_gemini_integration()