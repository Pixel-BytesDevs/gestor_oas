import os
import sys
import json

# Agregar el directorio raíz al path para importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


def test_huggingface_basic():
    """Prueba básica sin depender de las clases del proyecto"""

    print("🧪 Probando configuración básica...")

    # Verificar que el token existe
    token = os.getenv('HUGGINGFACE_API_TOKEN')
    if not token:
        print("❌ HUGGINGFACE_API_TOKEN no encontrado en .env")
        print("   Asegúrate de que tu archivo .env tenga:")
        print("   HUGGINGFACE_API_TOKEN=hf_tu_token_aqui")
        return

    print(f"✅ Token encontrado: {token[:10]}...")

    # Prueba simple de requests
    try:
        import requests
        print("✅ Requests instalado correctamente")
    except ImportError as e:
        print("❌ Error importando requests:", e)
        return

    # Prueba de conexión básica a Hugging Face
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # Probamos con un modelo simple
        API_URL = "https://api-inference.huggingface.co/models/gpt2"
        response = requests.get(API_URL, headers=headers)

        if response.status_code == 200:
            print("✅ Conexión exitosa con Hugging Face API")
        else:
            print(f"⚠️  Respuesta HTTP {response.status_code}")
            print(f"   Mensaje: {response.text[:100]}...")

    except Exception as e:
        print(f"❌ Error en la conexión: {e}")


def test_ai_service():
    """Prueba el servicio de IA completo"""
    print("\n🧪 Probando servicio de IA completo...")

    try:
        from app.services.huggingface_service import HuggingFaceService
        from app.services.ai_service import AIService

        ai_service = AIService()

        # Test de componentes
        test_text = "El álgebra estudia ecuaciones lineales como 2x + 3 = 7. El objetivo es resolver para x."

        print("📝 Extrayendo componentes...")
        components = ai_service.extract_components_from_text(test_text)

        print("✅ Componentes extraídos:")
        print(f"   - Objetivos: {components.get('objetivos', [])}")
        print(f"   - Teoría: {components.get('teoria', '')[:50]}...")
        print(f"   - Ejercicios: {components.get('ejercicios', [])}")

        # Test de preguntas
        print("\n📝 Generando preguntas...")
        questions = ai_service.generate_questions_from_topic("ecuaciones lineales", "básico", 2)
        print(f"✅ Preguntas generadas: {len(questions)}")

        for i, q in enumerate(questions):
            print(f"   {i + 1}. {q['pregunta']}")

    except Exception as e:
        print(f"❌ Error en servicio de IA: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_huggingface_basic()
    test_ai_service()