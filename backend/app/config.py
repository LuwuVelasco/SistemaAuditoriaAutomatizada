"""
Configuración global del Sistema de Auditoría Automatizada RAG.
Centraliza rutas, modelos, y parámetros del sistema.
"""

import os
from pathlib import Path

# ============================================================
# RUTAS BASE
# ============================================================

# Directorio raíz del backend
BASE_DIR = Path(__file__).resolve().parent.parent

# Directorio raíz del proyecto (un nivel arriba del backend)
PROJECT_DIR = BASE_DIR.parent

# Directorios de trabajo
UPLOADS_DIR = BASE_DIR / "uploads"
SALIDAS_DIR = BASE_DIR / "salidas"
TEMPLATES_DIR = BASE_DIR / "templates"
PLANTILLAS_ORIGINALES_DIR = PROJECT_DIR / "Plantillas"

# Crear directorios si no existen
for d in [UPLOADS_DIR, SALIDAS_DIR, TEMPLATES_DIR]:
    d.mkdir(parents=True, exist_ok=True)



# ============================================================
# GOOGLE AI STUDIO (GEMINI API) CONFIGURACIÓN
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODELO_GEMINI = os.getenv("MODELO_GEMINI", "gemini-2.5-flash")

# ============================================================
# AUDITORÍA RAG CONFIGURACIÓN
# ============================================================

RAG_TOP_K = 15               # Número de chunks a recuperar por query
MAX_REINTENTOS_VALIDACION = 3  # Reintentos si Pydantic rechaza la respuesta



# ============================================================
# QUERIES DE AUDITORÍA PREDEFINIDAS
# ============================================================

QUERIES_AUDITORIA_COBIT = [
    {
        "id": "planificacion_estrategica",
        "query": "Evaluar la planificación estratégica de TI, existencia de un plan estratégico de TI (PETI), alineación con objetivos institucionales, nivel de madurez de los procesos COBIT, comités de gobierno de TI.",
        "dominios": ["PO1", "PO4", "ME2"],
    },
    {
        "id": "arquitectura_informacion",
        "query": "Evaluar la arquitectura de la información, modelos de datos, clasificación de información, gestión de la integridad de datos.",
        "dominios": ["PO2"],
    },
    {
        "id": "direccion_tecnologica",
        "query": "Evaluar la dirección tecnológica, infraestructura tecnológica, seguridad de la información, SIEM, SOC, MFA, controles de detección y respuesta ante incidentes.",
        "dominios": ["PO3", "ME2"],
    },
    {
        "id": "recursos_humanos",
        "query": "Evaluar la gestión de recursos humanos de TI, plan de desarrollo profesional, evaluaciones de desempeño, capacitaciones, transferencia de conocimiento, código de ética.",
        "dominios": ["PO7", "ME2"],
    },
    {
        "id": "gestion_riesgos",
        "query": "Evaluar la gestión de riesgos tecnológicos, metodología de riesgos, registro de riesgos, seguimiento periódico, tratamiento formal, cobertura de riesgos.",
        "dominios": ["PO1", "PO2", "ME2"],
    },
    {
        "id": "gestion_cambios",
        "query": "Evaluar la gestión de cambios tecnológicos, procedimiento de gestión de cambios, CAB, análisis de impacto sobre controles existentes, cambios regulatorios externos.",
        "dominios": ["PO3", "PO4", "ME2"],
    },
    {
        "id": "monitoreo_desempeno",
        "query": "Evaluar el monitoreo del desempeño de TI, KPIs, indicadores, reportes a instancias de gobierno, dashboards, frecuencia de medición.",
        "dominios": ["PO1", "ME2"],
    },
]

# Lineamientos COSO 2013 para la evaluación
LINEAMIENTOS_COSO = {
    "AMBIENTE DE CONTROL": [
        "1. La Entidad demuestra el compromiso con la integridad (valores) y principios",
        "2. Aplicación de los mecanismos para ejercer una adecuada supervisión del Sistema de Control Interno",
        "3. Establecer la planeación estratégica con responsables, metas, tiempos que faciliten el seguimiento y aplicación de controles que garanticen de forma razonable su cumplimiento.",
        "4. Compromiso con la competencia de todo el personal, por lo que la gestión del talento humano tiene un carácter estratégico con el despliegue de las actividades claves para todo el ciclo de vida del servidor.",
        "5. La entidad establece líneas de reporte dentro de la entidad para evaluar el funcionamiento del Sistema de Control Interno.",
    ],
    "EVALUACIÓN DE RIESGOS": [
        "6. Definición de objetivos con suficiente claridad para identificar y evaluar los riesgos relacionados.",
        "7. Identificación y análisis de riesgos.",
        "8. Evaluación del riesgo de fraude o corrupción.",
        "9. Identificación y análisis de cambios significativos.",
    ],
    "ACTIVIDADES DE CONTROL": [
        "10. Diseño y desarrollo de actividades de control.",
        "11. Seleccionar y Desarrolla controles generales sobre TI para apoyar la consecución de los objetivos.",
        "12. Despliegue de políticas y procedimientos.",
    ],
    "INFORMACIÓN Y COMUNICACIÓN": [
        "13. Utilización de información relevante.",
        "14. Comunicación Interna.",
        "15. Comunicación con el exterior.",
    ],
    "ACTIVIDADES DE MONITOREO": [
        "16. Evaluaciones continuas y/o separadas para determinar si los componentes del Sistema de Control Interno están presentes y funcionando.",
        "17. Evaluación y comunicación de deficiencias oportunamente.",
    ],
}

# ============================================================
# PLANTILLAS - MAPEO DE COLUMNAS EXCEL
# ============================================================

# Columnas del Excel CACTUCITOS-Evaluacion.xlsx (fila de headers = 7)
EVALUACION_HEADER_ROW = 7
EVALUACION_DATA_START_ROW = 8
EVALUACION_COLUMNS = {
    "numero": 1,           # Col A - No.
    "hallazgo": 2,         # Col B - HALLAZGO (merge B-F)
    "criterio": 7,         # Col G - CRITERIO
    "causa_efecto": 8,     # Col H - CAUSA / EFECTO
    "conclusion": 9,       # Col I - CONCLUSIÓN
    "probabilidad": 10,    # Col J - P
    "impacto": 11,         # Col K - I
    "riesgo": 12,          # Col L - RIESGO (fórmula =J*K)
    "nivel_riesgo": 13,    # Col M - NIVEL RIESGO (fórmula IF)
    "recomendacion": 14,   # Col N - RECOMENDACIÓN
}

# Estructura del Excel COSO (fila de inicio de datos = 9)
COSO_HEADER_ROW = 8
COSO_DATA_START_ROW = 9
COSO_COLUMNS = {
    "numero": 2,                      # Col B - No.
    "componente": 3,                  # Col C - COMPONENTE (merge C-E)
    "lineamiento": 6,                 # Col F - LINEAMIENTO
    "cantidad_deficiencias": 7,       # Col G - Cantidad de deficiencias
    "descripcion_observaciones": 8,   # Col H - Descripción de observaciones
}

# ============================================================
# CORS (para desarrollo con React en puerto diferente)
# ============================================================

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
