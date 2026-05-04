import json
import re
import io
from sqlalchemy.orm import Session
# Asegúrate de importar SessionLocal o tu creador de sesiones de BD
from app.database.database import SessionLocal
from app.database import models
from app.services.gemini_service import GeminiService
from app.services.file_service import S3Service
from gtts import gTTS
import traceback  # IMPORTANTE: Agrega esto arriba en tu archivo

# Importaciones simuladas para tus servicios
# import google.generativeai as genai
# from gtts import gTTS

def limpiar_json_ia(texto_ia: str) -> dict:
    """Limpia los bloques de markdown ```json ``` que suele devolver la IA"""
    texto_limpio = re.sub(r"```json\n?", "", texto_ia)
    texto_limpio = re.sub(r"```\n?", "", texto_limpio)
    return json.loads(texto_limpio.strip())

def generar_y_guardar_oas_con_ia(topic_id: int, topic_name: str, requested_styles: list):
    """
    Genera los 4 estilos VARK, sube los recursos a S3 y guarda en BD.
    """
    print(f"🔄 [BACKGROUND] Iniciando generación IA para: {topic_name}")
    db = SessionLocal()
    gemini_client = GeminiService()
    s3_service = S3Service()

    try:
        # =========================================================
        # 1. ESTILO: LECTURA / ESCRITURA (El nodo base)
        # =========================================================
        print(f"📄 [READ/WRITE] Solicitando contenido base a Gemini API...")
        ia_data = gemini_client.generate_base_read_write_oa(topic=topic_name)

        # --- INICIO BLOQUE DE DEBUGGING ---
        if "error" in ia_data:
            print(f"\n⚠️ [DEBUG] Gemini devolvió un error estructural:")
            print(f"Motivo: {ia_data.get('error')}")
            if "raw_text" in ia_data:
                print(f"Texto Crudo: \n{ia_data.get('raw_text')}\n")
            raise Exception(f"Fallo en la respuesta de Gemini: {ia_data.get('error')}")
        # --- FIN BLOQUE DE DEBUGGING ---

        texto_markdown = ia_data.get("content_markdown", "")

        if not texto_markdown:
            print(f"⚠️ [DEBUG] Respuesta IA completa recibida pero sin markdown: {ia_data}")
            raise Exception("La IA respondió correctamente pero no incluyó la clave 'content_markdown'.")

        # A. Crear registro en BD (hacemos flush para obtener el ID)
        oa_lectura = models.LearningObject(
            idTopic=topic_id,
            title=f"Teoría y Fundamentos de {topic_name}",
            typeName="Documento",
            levelName="Intermedio",
            styleName="lectura/escritura",
            fileName=f"{topic_name.lower().replace(' ', '_')}_teoria.md",
            fileExtension=".md",
            estimatedDuration=15,
            ge_objective=ia_data.get("ge_objective"),
            objectives=ia_data.get("objectives"),
            approach=ia_data.get("approach")
        )
        db.add(oa_lectura)
        db.flush()  # Obtiene el idObject sin hacer un commit definitivo aún

        # B. Subir a S3 en memoria (encode string to bytes)
        file_content_md = texto_markdown.encode('utf-8')
        s3_res_md = s3_service.upload_file(
            file_content=file_content_md,
            original_file_name=oa_lectura.fileName,
            object_id=str(oa_lectura.idObject)
        )

        # C. Actualizar S3 Key en el registro
        oa_lectura.s3_key = s3_res_md['key']
        print(f"✅ [READ/WRITE] Guardado en S3 y BD. (ID: {oa_lectura.idObject})")

        # =========================================================
        # 2. ESTILO: AUDITIVO (Generado a partir del texto base)
        # =========================================================
        print(f"🎧 [AURAL] Generando audio mp3 con gTTS...")

        # A. Generar audio en memoria usando BytesIO
        tts = gTTS(text=texto_markdown, lang='es', slow=False)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)  # Regresar el puntero al inicio del buffer

        # B. Crear registro en BD
        oa_audio = models.LearningObject(
            idTopic=topic_id,
            title=f"Podcast Educativo: {topic_name}",
            typeName="Audio",
            levelName="Intermedio",
            styleName="Auditivo",
            fileName=f"{topic_name.lower().replace(' ', '_')}_audio.mp3",
            fileExtension=".mp3",
            estimatedDuration=10,
            ge_objective=ia_data.get("ge_objective"),
            objectives=ia_data.get("objectives"),
            approach="Auditivo secuencial"
        )
        db.add(oa_audio)
        db.flush()

        # C. Subir el buffer mp3 a S3
        s3_res_mp3 = s3_service.upload_file(
            file_content=mp3_fp.read(),
            original_file_name=oa_audio.fileName,
            object_id=str(oa_audio.idObject)
        )
        oa_audio.s3_key = s3_res_mp3['key']
        print(f"✅ [AURAL] Audio guardado en S3 y BD. (ID: {oa_audio.idObject})")

        # =========================================================
        # 3. ESTILO: VISUAL (YouTube API)
        # =========================================================
        print(f"👁️ [VISUAL] Buscando material en YouTube...")
        # NOTA: Aquí llamarías a tu servicio de YouTube. Asumiremos que obtienes una URL.
        youtube_url = f"https://www.youtube.com/results?search_query=matematicas+{topic_name.replace(' ', '+')}"

        oa_visual = models.LearningObject(
            idTopic=topic_id,
            title=f"Clase Visual: {topic_name}",
            typeName="Video",
            levelName="Intermedio",
            styleName="Visual",
            fileName="youtube_video.url",
            fileExtension=".url",
            estimatedDuration=20,
            s3Url=youtube_url,  # Los videos externos no van a S3, guardamos la URL directa
            s3_key=None
        )
        db.add(oa_visual)
        print(f"✅ [VISUAL] Referencia de video guardada.")

        # =========================================================
        # 4. ESTILO: KINESTÉSICO (Interactivo JSON)
        # =========================================================
        print(f"🖐️ [KINESTHETIC] Solicitando JSON interactivo a Gemini...")

        # A. Pedir JSON de ejercicios interactivos a la IA (Método que agregarás luego)
        # ia_kinestesico = gemini_client.generate_kinesthetic_puzzle(topic=topic_name)
        ia_kinestesico = {"tipo": "arrastrar_y_soltar", "pasos": ["paso 1", "paso 2"]}  # Mock temporal

        oa_kines = models.LearningObject(
            idTopic=topic_id,
            title=f"Simulador Práctico: {topic_name}",
            typeName="Interactivo",
            levelName="Intermedio",
            styleName="Kinestésico",
            fileName=f"{topic_name.lower().replace(' ', '_')}_simulador.json",
            fileExtension=".json",
            estimatedDuration=25
        )
        db.add(oa_kines)
        db.flush()

        # B. Convertir el dict de Python a bytes JSON y subir a S3
        file_content_json = json.dumps(ia_kinestesico, ensure_ascii=False).encode('utf-8')
        s3_res_json = s3_service.upload_file(
            file_content=file_content_json,
            original_file_name=oa_kines.fileName,
            object_id=str(oa_kines.idObject)
        )
        oa_kines.s3_key = s3_res_json['key']
        print(f"✅ [KINESTHETIC] Simulador JSON guardado en S3. (ID: {oa_kines.idObject})")

        # =========================================================
        # COMMIT FINAL: Si todos los estilos se subieron bien a S3, guardamos en la base de datos
        # =========================================================
        db.commit()
        print(f"🎉 [BACKGROUND] Tarea finalizada EXITOSAMENTE para: {topic_name}")

    except Exception as e:
        print(f"\n❌ [BACKGROUND] Error crítico en la orquestación:")
        print(f"Detalle: {str(e)}")
        print("--- TRAZA DEL ERROR ---")
        traceback.print_exc()  # ESTO ES MAGIA: Te dirá la línea exacta donde explotó
        print("-----------------------\n")

        db.rollback()
    finally:
        db.close()
        print(f"🔒 [BACKGROUND] Sesión cerrada.")