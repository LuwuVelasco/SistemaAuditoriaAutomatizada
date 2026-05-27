"""
Constructor de prompts para los motores IA.

Principios del lenguaje auditorial:
- Formal y profesional
- Neutral y objetivo
- Orientado a mejora continua
- No acusatorio ni agresivo
- En español boliviano estándar
"""

import json
from typing import List


TONE_INSTRUCTIONS = """
Usa lenguaje formal, profesional y neutral. Las observaciones deben estar
orientadas a la mejora continua, sin señalar responsables individuales
ni usar términos acusatorios. Evita palabras como "negligencia", "incumplimiento grave",
"falla crítica" o similares. Prefiere frases como "se identificó una oportunidad de mejora",
"se observa la ausencia de", "se recomienda fortalecer".
"""


DEPTH_INSTRUCTIONS = """
Realiza un análisis EXHAUSTIVO Y PROFUNDO. Debes extraer la mayor cantidad posible de hallazgos relevantes (intenta encontrar entre 3 y 5 hallazgos detallados y distintos, o más si el texto lo amerita). No te limites a un solo hallazgo general; desglosa los problemas en debilidades específicas, vulnerabilidades, incumplimientos normativos o riesgos latentes que identifiques en el texto.
"""


def build_coso_prompt(document_text: str, prior_findings: List[dict] = None) -> str:
    prior_section = ""
    if prior_findings:
        prior_section = f"""
Hallazgos previos ya identificados por otros motores (NO duplicar):
{json.dumps(prior_findings, ensure_ascii=False, indent=2)}

Solo identifica hallazgos NUEVOS que no estén cubiertos por los anteriores.
"""

    return f"""Eres un auditor experto en COSO 2013 (Marco Integrado de Control Interno).

{TONE_INSTRUCTIONS}
{DEPTH_INSTRUCTIONS}

Tu tarea es analizar el siguiente texto de documentos organizacionales de una entidad
del sistema financiero boliviano e identificar debilidades de control interno conforme
a los 5 componentes de COSO 2013:
1. Entorno de Control
2. Evaluación de Riesgos
3. Actividades de Control
4. Información y Comunicación
5. Actividades de Monitoreo
{prior_section}
Para cada debilidad identificada, devuelve un JSON array con exactamente este formato:
[
  {{
    "title": "Título conciso del hallazgo (máx. 80 caracteres)",
    "description_finding": "Registro de la deficiencia, falta de control, amenaza o vulnerabilidad identificada.",
    "criteria_description": "Reglamento, ley o política que establece el requisito de cumplimiento.",
    "cause": "Qué causa que ocurra el problema.",
    "effect": "Consecuencia resultante.",
    "conclusion": "Conclusión resumida considerando causa, efecto y criterio.",
    "recommendation": "Recomendación específica, accionable y orientada a la mejora.",
    "confidence": 0.85,
    "risk_level": "Alto",
    "coso_refs": [
      {{"code": "CC6.1", "title": "Control de Acceso Lógico", "component": "Actividades de Control"}}
    ],
    "cobit_refs": [],
    "rgsi_refs": [],
    "evidence": [],
    "quote": "Fragmento textual del documento que sustenta el hallazgo (si aplica)"
  }}
]

Si no se identifican hallazgos COSO claros en el texto, devuelve [].
Responde ÚNICAMENTE con el JSON array, sin explicaciones adicionales.

TEXTO A ANALIZAR:
{document_text[:6000]}
"""


def build_cobit_prompt(document_text: str, prior_findings: List[dict] = None) -> str:
    prior_section = ""
    if prior_findings:
        prior_section = f"""
Hallazgos previos identificados (NO duplicar):
{json.dumps(prior_findings, ensure_ascii=False, indent=2)}

Solo identifica hallazgos de COBIT 2019 que complementen los anteriores.
"""

    return f"""Eres un auditor experto en COBIT 2019 (Gobierno y Gestión de TI Empresarial).

{TONE_INSTRUCTIONS}
{DEPTH_INSTRUCTIONS}

Tu tarea es analizar el siguiente texto de documentos organizacionales e identificar
observaciones de auditoría TI conforme a los dominios de COBIT 2019:
- EDM: Evaluar, Orientar y Supervisar
- APO: Alinear, Planificar y Organizar
- BAI: Construir, Adquirir e Implementar
- DSS: Entregar, dar Servicio y Soporte
- MEA: Monitorear, Evaluar y Valorar
{prior_section}
Para cada observación identificada, devuelve un JSON array:
[
  {{
    "title": "Título conciso (máx. 80 caracteres)",
    "description_finding": "Registro de la deficiencia, falta de control, amenaza o vulnerabilidad identificada.",
    "criteria_description": "Reglamento, ley o política que establece el requisito de cumplimiento.",
    "cause": "Qué causa que ocurra el problema.",
    "effect": "Consecuencia resultante.",
    "conclusion": "Conclusión resumida considerando causa, efecto y criterio.",
    "recommendation": "Recomendación específica y accionable.",
    "confidence": 0.85,
    "risk_level": "Alto",
    "cobit_refs": [
      {{"code": "APO13.01", "title": "Establecer y mantener el SGSI", "domain": "APO"}}
    ],
    "coso_refs": [],
    "rgsi_refs": [],
    "evidence": [],
    "quote": "Cita textual que sustenta el hallazgo (si aplica)"
  }}
]

Si no se identifican hallazgos COBIT claros, devuelve [].
Responde ÚNICAMENTE con el JSON array.

TEXTO A ANALIZAR:
{document_text[:6000]}
"""


def build_rgsi_prompt(document_text: str, prior_findings: List[dict] = None) -> str:
    prior_section = ""
    if prior_findings:
        prior_section = f"""
Hallazgos previos identificados (NO duplicar):
{json.dumps(prior_findings, ensure_ascii=False, indent=2)}

Solo identifica hallazgos del RGSI-ASFI que complementen los anteriores.
"""

    return f"""Eres un auditor experto en el Reglamento de Gestión de Seguridad de la Información
(RGSI) emitido por la ASFI (Autoridad de Supervisión del Sistema Financiero) de Bolivia.

{TONE_INSTRUCTIONS}
{DEPTH_INSTRUCTIONS}

Tu tarea es analizar el siguiente texto de documentos de una entidad de intermediación
financiera boliviana e identificar observaciones de cumplimiento normativo con el RGSI-ASFI.
Los capítulos principales del RGSI son:
- Cap. I: Disposiciones Generales
- Cap. II: Organización de la Seguridad
- Cap. III: Gestión de Activos e Información
- Cap. IV: Control de Accesos
- Cap. V: Criptografía y Seguridad Física
- Cap. VI: Continuidad Operativa
- Cap. VII: Gestión de Incidentes
{prior_section}
Para cada observación identificada, devuelve un JSON array:
[
  {{
    "title": "Título conciso (máx. 80 caracteres)",
    "description_finding": "Registro de la deficiencia, falta de control, amenaza o vulnerabilidad identificada.",
    "criteria_description": "Reglamento, ley o política que establece el requisito de cumplimiento.",
    "cause": "Qué causa que ocurra el problema.",
    "effect": "Consecuencia resultante.",
    "conclusion": "Conclusión resumida considerando causa, efecto y criterio.",
    "recommendation": "Recomendación específica para alcanzar conformidad con el RGSI.",
    "confidence": 0.85,
    "risk_level": "Alto",
    "rgsi_refs": [
      {{"code": "Art. 12", "title": "Gestión de Accesos y Autenticación", "section": "Cap. IV"}}
    ],
    "cobit_refs": [],
    "coso_refs": [],
    "evidence": [],
    "quote": "Cita textual que sustenta la observación (si aplica)"
  }}
]

Si no se identifican observaciones RGSI claras, devuelve [].
Responde ÚNICAMENTE con el JSON array.

TEXTO A ANALIZAR:
{document_text[:6000]}
"""
