"""
Modelos Pydantic para validación estricta del Sistema de Auditoría.
Incluye modelos de dominio (Hallazgo, Evidencia, COSO) y modelos de API.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


# ============================================================
# ENUMS
# ============================================================

class NivelRiesgo(str, Enum):
    MUY_BAJO = "Muy Bajo"
    BAJO = "Bajo"
    MEDIO = "Medio"
    ALTO = "Alto"
    EXTREMO = "Extremo"

    @classmethod
    def calcular(cls, probabilidad: int, impacto: int) -> "NivelRiesgo":
        """Calcula el nivel de riesgo a partir de P x I."""
        riesgo = probabilidad * impacto
        if riesgo <= 2:
            return cls.MUY_BAJO
        elif riesgo <= 4:
            return cls.BAJO
        elif riesgo <= 9:
            return cls.MEDIO
        elif riesgo < 20:
            return cls.ALTO
        else:
            return cls.EXTREMO


class EstadoAuditoria(str, Enum):
    IDLE = "idle"
    PROCESANDO_DOCUMENTOS = "procesando_documentos"
    EXTRAYENDO_CONTEXTO = "extrayendo_contexto"
    VECTORIZANDO = "vectorizando"
    EJECUTANDO_AUDITORIA = "ejecutando_auditoria"
    VALIDANDO = "validando"
    GENERANDO_DOCUMENTOS = "generando_documentos"
    COMPLETADO = "completado"
    ERROR = "error"


# ============================================================
# MODELOS DE DOMINIO
# ============================================================

class CitaBibliografica(BaseModel):
    """Cita bibliográfica obligatoria por cada hallazgo."""
    documento: str = Field(
        ...,
        description="Nombre del documento fuente, ej: 'PESI 2025-2027'",
        min_length=3
    )
    seccion: str = Field(
        ...,
        description="Sección del documento, ej: 'Sección 4.1'",
        min_length=2
    )
    pagina: Optional[str] = Field(
        None,
        description="Número de página si está disponible"
    )
    descripcion: str = Field(
        ...,
        description="Texto relevante citado del documento",
        min_length=10
    )


class Evidencia(BaseModel):
    """Evidencia documental que respalda un hallazgo."""
    numero: int = Field(..., ge=1)
    referencia: str = Field(
        ...,
        description="Referencia completa, ej: 'PETI 2025-2027, Sección 2.3 — Nivel de Madurez COBIT'",
        min_length=5
    )
    descripcion: str = Field(
        ...,
        description="Descripción detallada de la evidencia encontrada",
        min_length=20
    )


class Hallazgo(BaseModel):
    """
    Hallazgo de auditoría con validación estricta.
    REGLA INQUEBRANTABLE: citas_bibliograficas NO puede estar vacío.
    """
    codigo: str = Field(
        ...,
        description="Código del hallazgo, ej: 'H1'",
        pattern=r"^H\d+$"
    )
    dominio: str = Field(
        ...,
        description="Dominio COBIT, ej: 'Dominio PO – Planear y Organizar'"
    )
    procesos: list[str] = Field(
        ...,
        description="Lista de procesos COBIT, ej: ['PO1', 'PO4', 'ME2']",
        min_length=1
    )
    objetivo_control: str = Field(
        ...,
        description="Objetivo de control evaluado",
        min_length=20
    )
    riesgos_asociados: list[str] = Field(
        ...,
        description="Lista de riesgos, ej: ['R1', 'R2']",
        min_length=1
    )
    descripcion: str = Field(
        ...,
        description="Descripción detallada del hallazgo",
        min_length=50
    )
    recomendacion: str = Field(
        ...,
        description="Recomendación para mitigar el hallazgo",
        min_length=30
    )
    causa: str = Field(
        ...,
        description="Causa raíz del hallazgo"
    )
    efecto: str = Field(
        ...,
        description="Efecto o impacto del hallazgo"
    )
    probabilidad: int = Field(
        ...,
        ge=1, le=5,
        description="Probabilidad del riesgo (1-5)"
    )
    impacto: int = Field(
        ...,
        ge=1, le=5,
        description="Impacto del riesgo (1-5)"
    )
    nivel_riesgo: Optional[str] = Field(
        None,
        description="Se calcula automáticamente a partir de P x I"
    )
    conclusion: str = Field(
        ...,
        description="Conclusión técnica del hallazgo",
        min_length=30
    )
    criterio: str = Field(
        ...,
        description="Criterio de evaluación (marco normativo, COBIT, COSO)"
    )
    citas_bibliograficas: list[CitaBibliografica] = Field(
        ...,
        description="OBLIGATORIO: Al menos una cita bibliográfica",
        min_length=1
    )
    evidencias: list[Evidencia] = Field(
        default_factory=list,
        description="Evidencias documentales del hallazgo"
    )

    @model_validator(mode="after")
    def calcular_nivel_riesgo(self) -> "Hallazgo":
        """Calcula automáticamente el nivel de riesgo si no se proporcionó."""
        self.nivel_riesgo = NivelRiesgo.calcular(
            self.probabilidad, self.impacto
        ).value
        return self

    @field_validator("citas_bibliograficas")
    @classmethod
    def validar_citas_no_vacias(cls, v: list[CitaBibliografica]) -> list[CitaBibliografica]:
        """REGLA INQUEBRANTABLE: Debe haber al menos una cita."""
        if not v or len(v) == 0:
            raise ValueError(
                "REGLA INQUEBRANTABLE VIOLADA: Cada hallazgo DEBE tener al menos "
                "una cita bibliográfica con documento, sección y descripción. "
                "Vuelve a generar incluyendo las citas."
            )
        return v


class ContextoEntidad(BaseModel):
    """Datos dinámicos extraídos de los documentos de la entidad."""
    nombre_entidad: str = Field(
        ...,
        description="Nombre de la entidad auditada",
        min_length=3
    )
    periodo_evaluado: str = Field(
        ...,
        description="Periodo evaluado, ej: 'Semestre I-2026'"
    )
    fecha_auditoria: str = Field(
        ...,
        description="Fecha de la auditoría"
    )
    grupo_auditor: Optional[str] = Field(
        None,
        description="Nombre del grupo auditor"
    )
    integrantes: Optional[list[str]] = Field(
        None,
        description="Lista de integrantes del grupo"
    )
    alcance: Optional[str] = Field(
        None,
        description="Alcance de la auditoría"
    )


class LineamientoCOSO(BaseModel):
    """Lineamiento individual dentro de un componente COSO."""
    numero: int = Field(..., ge=1, le=17)
    descripcion: str
    cantidad_deficiencias: int = Field(..., ge=0)
    observaciones: str = Field(
        ...,
        description="Descripción de observaciones y deficiencias"
    )


class ComponenteCOSO(BaseModel):
    """Componente COSO con sus lineamientos evaluados."""
    numero: int = Field(..., ge=1, le=5)
    nombre: str = Field(
        ...,
        description="Nombre del componente: AMBIENTE DE CONTROL, EVALUACIÓN DE RIESGOS, etc."
    )
    lineamientos: list[LineamientoCOSO]


# ============================================================
# MODELOS DE API (Request/Response)
# ============================================================

class ProgresoAuditoria(BaseModel):
    """Mensaje de progreso enviado via WebSocket."""
    paso: int
    total: int = 6
    mensaje: str
    porcentaje: float = Field(..., ge=0, le=100)
    estado: EstadoAuditoria


class DocumentoInfo(BaseModel):
    """Información de un documento subido."""
    nombre: str
    tamano: int
    tipo: str  # "pdf", "docx"
    ruta: str


class ResultadoAuditoria(BaseModel):
    """Resultado completo de la auditoría."""
    contexto: ContextoEntidad
    hallazgos: list[Hallazgo]
    componentes_coso: list[ComponenteCOSO]
    archivos_generados: list[str]
    total_hallazgos: int = 0
    resumen_riesgos: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def calcular_resumen(self) -> "ResultadoAuditoria":
        """Calcula el resumen de riesgos por nivel."""
        self.total_hallazgos = len(self.hallazgos)
        conteo: dict[str, int] = {}
        for h in self.hallazgos:
            nivel = h.nivel_riesgo or "Sin clasificar"
            conteo[nivel] = conteo.get(nivel, 0) + 1
        self.resumen_riesgos = conteo
        return self


class IniciarAuditoriaRequest(BaseModel):
    """Request para iniciar auditoría."""
    nombre_grupo: Optional[str] = None
    integrantes: Optional[list[str]] = None
    alcance: Optional[str] = None
