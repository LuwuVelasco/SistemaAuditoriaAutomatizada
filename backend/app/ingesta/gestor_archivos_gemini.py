"""
Gestor de archivos para Google AI Studio (Gemini).
Se encarga de subir los archivos locales (PDFs, DOCX, etc.) a la nube de Google
para que el modelo pueda utilizarlos en su contexto.
"""

from pathlib import Path
from google import genai
from ..config import GEMINI_API_KEY

class GestorArchivosGemini:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.archivos_subidos = []

    def subir_directorio(self, dir_path: Path):
        """Sube todos los archivos de un directorio a Gemini."""
        archivos_locales = list(dir_path.glob("*.*"))
        import unicodedata
        import shutil
        for archivo in archivos_locales:
            # Eliminar acentos y caracteres no-ascii del nombre del archivo
            ascii_name = unicodedata.normalize('NFKD', archivo.name).encode('ascii', 'ignore').decode('ascii')
            # Reemplazar espacios o caracteres raros extra si queremos, pero con ascii es suficiente
            safe_path = archivo.parent / ascii_name
            if archivo != safe_path:
                shutil.move(str(archivo), str(safe_path))
            gemini_file = self.client.files.upload(file=str(safe_path))
            self.archivos_subidos.append(gemini_file)
        return self.archivos_subidos

    def obtener_archivos(self):
        return self.archivos_subidos

    def limpiar_archivos(self):
        """Elimina los archivos subidos de los servidores de Google y limpia la lista."""
        for f in self.archivos_subidos:
            try:
                self.client.files.delete(name=f.name)
            except Exception as e:
                print(f"Error eliminando {f.name}: {e}")
        self.archivos_subidos = []

gestor_archivos = GestorArchivosGemini()
