from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
import io
from typing import List


class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Configura estilos personalizados sin conflictos"""
        # No agregamos estilos a la hoja de estilos, los manejamos por separado
        pass

    def _get_style(self, style_type: str):
        """Obtiene el estilo apropiado según el tipo"""
        if style_type == 'title':
            return ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=16,
                textColor=colors.darkblue,
                spaceAfter=12,
                alignment=TA_CENTER
            )
        elif style_type == 'subtitle':
            return ParagraphStyle(
                name='CustomSubtitle',
                parent=self.styles['Heading2'],
                fontSize=14,
                textColor=colors.darkblue,
                spaceAfter=8
            )
        elif style_type == 'content':
            return ParagraphStyle(
                name='CustomContent',
                parent=self.styles['Normal'],
                fontSize=11,
                textColor=colors.black,
                spaceAfter=6,
                alignment=TA_JUSTIFY
            )
        elif style_type == 'bullet':
            return ParagraphStyle(
                name='CustomBullet',
                parent=self.styles['Normal'],
                fontSize=11,
                textColor=colors.black,
                leftIndent=10,
                spaceAfter=4
            )
        else:
            return self.styles['Normal']

    def clean_text(self, text: str) -> str:
        """Limpia el texto de caracteres problemáticos"""
        if not text:
            return ""

        # Corregir problemas comunes de codificación
        replacements = {
            'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
            'Ã±': 'ñ', 'Ã': 'Á', 'Ã‰': 'É', 'Ã': 'Í', 'Ã“': 'Ó', 'Ãš': 'Ú',
            'Ã‘': 'Ñ', 'Â¿': '¿', 'Â¡': '¡', 'Ã¼': 'ü', 'Ãœ': 'Ü',
            'Ã€': 'À', 'Ãˆ': 'È', 'ÃŒ': 'Ì', 'Ã²': 'ò', 'Ã¹': 'ù'
        }

        cleaned_text = text
        for wrong, correct in replacements.items():
            cleaned_text = cleaned_text.replace(wrong, correct)

        return cleaned_text

    def create_objectives_pdf(self, objectives: List[str], title: str = "Objetivos de Aprendizaje") -> bytes:
        """Crea un PDF para los objetivos de aprendizaje"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        # Título
        story.append(Paragraph(self.clean_text(title), self._get_style('title')))
        story.append(Spacer(1, 20))

        # Objetivos
        for i, objective in enumerate(objectives, 1):
            if objective and objective.strip():
                objective_text = self.clean_text(objective.strip())
                # Usar viñetas para los objetivos
                bullet_text = f"• <b>Objetivo {i}:</b> {objective_text}"
                story.append(Paragraph(bullet_text, self._get_style('bullet')))
                story.append(Spacer(1, 8))

        # Generar PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def create_theory_pdf(self, theory_content: str, title: str = "Contenido Teórico") -> bytes:
        """Crea un PDF para el contenido teórico"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        # Título
        story.append(Paragraph(self.clean_text(title), self._get_style('title')))
        story.append(Spacer(1, 20))

        # Contenido teórico
        if not theory_content or not theory_content.strip():
            theory_content = "El contenido teórico se está generando. Por favor, revise más tarde."

        # Dividir por saltos de línea
        paragraphs = []
        if '\n\n' in theory_content:
            paragraphs = theory_content.split('\n\n')
        else:
            paragraphs = [theory_content]

        for paragraph in paragraphs:
            if paragraph and paragraph.strip():
                clean_paragraph = self.clean_text(paragraph.strip())
                story.append(Paragraph(clean_paragraph, self._get_style('content')))
                story.append(Spacer(1, 12))

        # Generar PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def create_exercises_pdf(self, exercises: List[str], title: str = "Ejercicios Prácticos") -> bytes:
        """Crea un PDF para los ejercicios"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        # Título
        story.append(Paragraph(self.clean_text(title), self._get_style('title')))
        story.append(Spacer(1, 20))

        # Ejercicios
        for i, exercise in enumerate(exercises, 1):
            if exercise and exercise.strip():
                exercise_text = self.clean_text(exercise.strip())
                story.append(Paragraph(f"<b>Ejercicio {i}:</b>", self._get_style('subtitle')))
                story.append(Spacer(1, 4))
                story.append(Paragraph(exercise_text, self._get_style('content')))
                story.append(Spacer(1, 16))

        # Si no hay ejercicios, agregar mensaje
        if not exercises:
            story.append(Paragraph("Los ejercicios se están generando. Por favor, revise más tarde.",
                                   self._get_style('content')))

        # Generar PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()