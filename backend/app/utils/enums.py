"""Enumeraciones del dominio SAAM."""

from enum import Enum


class AuditStatus(str, Enum):
    PENDIENTE = "Pendiente"
    PROCESANDO = "Procesando"
    EN_REVISION = "En revisión"
    FINALIZADA = "Finalizada"


class DocumentStatus(str, Enum):
    QUEUED = "queued"
    INDEXING = "indexing"
    READY = "ready"


class FindingStatus(str, Enum):
    PENDIENTE = "Pendiente"
    APROBADO = "Aprobado"
    RECHAZADO = "Rechazado"


class RiskLevel(str, Enum):
    BAJO = "Bajo"
    MEDIO = "Medio"
    ALTO = "Alto"
    EXTREMO = "Extremo"
    OPORTUNIDAD = "Oportunidad"


class FrameworkType(str, Enum):
    COBIT = "COBIT"
    COSO = "COSO"
    RGSI = "RGSI"


class ReportKind(str, Enum):
    MATRIZ_HALLAZGOS = "matriz-hallazgos"
    FICHAS_HALLAZGO = "fichas-hallazgo"
    FICHAS_PRUEBAS = "fichas-pruebas"
    MATRIZ_COSO = "matriz-coso"
    INFORME_MADUREZ = "informe-madurez"


class ReportFormat(str, Enum):
    XLSX = "xlsx"
    DOCX = "docx"
    PDF = "pdf"
