"""
Fixtures compartidos para los tests del backend SAAM.
Usa mocks para Firebase y Supabase — no requiere conexión real.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.audit import Audit
from app.models.finding import Finding
from app.utils.enums import AuditStatus, FindingStatus, FrameworkType, RiskLevel
from app.utils.timestamps import utcnow_iso


# ── Fixtures de modelos ────────────────────────────────────────────────────────

@pytest.fixture
def sample_audit() -> Audit:
    return Audit(
        id="aud-test-001",
        entity="Banco Prueba S.A.",
        type="Banco",
        city="La Paz",
        period="2025-Q1",
        frameworks=[FrameworkType.COSO, FrameworkType.COBIT],
        ownerId="uid-owner-001",
        status=AuditStatus.PENDIENTE,
        progress=0,
        findingsCount=0,
        pendingFindings=0,
        documentsCount=0,
        createdAt=utcnow_iso(),
    )


@pytest.fixture
def sample_finding() -> Finding:
    return Finding(
        id="HLZ-test-001",
        auditId="aud-test-001",
        title="Falta de segregación de funciones en TI",
        description="Se identificó que el mismo usuario tiene acceso de administrador y de operación.",
        recommendation="Implementar una política de segregación de funciones acorde a COBIT APO01.",
        risk=RiskLevel.ALTO,
        impact=4,
        probability=3,
        status=FindingStatus.PENDIENTE,
        confidence=0.85,
        cobitRef=[],
        cosoRef=[],
        rgsiRef=[],
        evidence=[],
        quote=None,
        detectedBy="COSFI-COBIT",
        createdAt=utcnow_iso(),
        updatedAt=utcnow_iso(),
    )


# ── Mock Firestore ─────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.collection = MagicMock(return_value=db)
    db.document = MagicMock(return_value=db)
    db.get = AsyncMock(return_value=MagicMock(exists=False, id="test-id", to_dict=lambda: {}))
    db.set = AsyncMock()
    db.update = AsyncMock()
    db.delete = AsyncMock()
    return db


# ── Mock Storage ───────────────────────────────────────────────────────────────

@pytest.fixture
def mock_storage():
    storage = MagicMock()
    storage.upload_pdf = AsyncMock(return_value="audits/aud-test-001/test.pdf")
    storage.download_file = AsyncMock(return_value=b"%PDF-1.4 test content")
    storage.upload_report = AsyncMock(return_value="audits/aud-test-001/report.xlsx")
    storage.delete_file = AsyncMock()
    storage.get_public_url = MagicMock(return_value="https://storage.example.com/test.pdf")
    storage.compute_sha256 = MagicMock(return_value="abc123")
    return storage
