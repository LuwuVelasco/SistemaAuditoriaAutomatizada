"""
Ruta: GET /audits/{audit_id}/graph
Devuelve el grafo de trazabilidad de cumplimiento normativo como JSON { nodes, edges, stats }.

Estructura del grafo:
  Framework (COBIT / COSO / RGSI)
      └── Norma (APO12.01, C-EV-01, Art.14…)
              └── Hallazgo (H-001, H-002…)
                      ├── Documento/Evidencia (Política_Backups.pdf p.4)
                      └── ── (arista de relación entre hallazgos con normas comunes)

Las aristas de relación finding↔finding se generan cuando dos hallazgos comparten
al menos una referencia normativa (mismo código) o tienen similitud de Jaccard ≥ 0.3
en sus títulos.
"""

from itertools import combinations

from fastapi import APIRouter, Depends

from app.ai.semantic_similarity import jaccard_similarity
from app.api.deps import (
    CurrentUID,
    get_audit_service,
    get_document_service,
    get_finding_service,
)
from app.core.responses import ok
from app.services.audit_service import AuditService
from app.services.document_service import DocumentService
from app.services.finding_service import FindingService

router = APIRouter(prefix="/audits", tags=["graph"])

# Colores fijos por tipo de nodo
FRAMEWORK_HUB_COLOR = {
    "COBIT": "#f59e0b",   # ámbar
    "COSO":  "#8b5cf6",   # violeta
    "RGSI":  "#06b6d4",   # cian
}

RISK_COLORS = {
    "Extremo":     "#ef4444",
    "Alto":        "#f97316",
    "Medio":       "#eab308",
    "Bajo":        "#22c55e",
    "Oportunidad": "#3b82f6",
}

FINDING_RELATION_THRESHOLD = 0.28  # Umbral Jaccard para relacionar hallazgos


@router.get("/{audit_id}/graph")
async def get_compliance_graph(
    audit_id: str,
    uid: CurrentUID,
    audit_svc: AuditService = Depends(get_audit_service),
    finding_svc: FindingService = Depends(get_finding_service),
    doc_svc: DocumentService = Depends(get_document_service),
):
    """
    Construye y retorna el grafo de trazabilidad normativa de la auditoría.
    """
    # Verificar acceso
    await audit_svc.get_by_id(audit_id, uid)

    # Cargar datos
    findings = await finding_svc.list_by_audit(audit_id, uid)
    documents = await doc_svc.list_by_audit(audit_id, uid)

    doc_index = {d.id: d for d in documents}

    nodes: list[dict] = []
    edges: list[dict] = []
    edge_keys: set[tuple] = set()

    seen_norms: dict[str, dict] = {}    # norm_node_id → node
    seen_docs: dict[str, dict] = {}     # doc_node_id → node
    seen_findings: dict[str, dict] = {} # finding_node_id → node

    # ── 1. Nodos hub de los tres frameworks ────────────────────────────────────
    for fw in ["COBIT", "COSO", "RGSI"]:
        nodes.append({
            "id": f"fw-{fw}",
            "label": fw,
            "type": "framework",
            "framework": fw,
            "title": {"COBIT": "Gobierno y Gestión de TI", "COSO": "Control Interno", "RGSI": "Reglamento de Seguridad ASFI"}[fw],
            "color": FRAMEWORK_HUB_COLOR[fw],
            "size": "large",
        })

    def _add_edge(src: str, tgt: str, etype: str, **extra):
        key = (src, tgt)
        if key not in edge_keys:
            edge_keys.add(key)
            edges.append({"source": src, "target": tgt, "type": etype, **extra})

    # ── 2. Procesar cada hallazgo ───────────────────────────────────────────────
    for finding in findings:
        f_id = finding.id
        f_node_id = f"finding-{f_id}"
        risk_val = finding.risk.value if hasattr(finding.risk, "value") else str(finding.risk)
        status_val = finding.status.value if hasattr(finding.status, "value") else str(finding.status)

        if f_node_id not in seen_findings:
            f_node = {
                "id": f_node_id,
                "label": f_id[:6].upper(),
                "type": "finding",
                "title": finding.title,
                "risk": risk_val,
                "status": status_val,
                "color": RISK_COLORS.get(risk_val, "#6b7280"),
                "sourceFramework": getattr(finding, "source_framework", ""),
            }
            seen_findings[f_node_id] = f_node
            nodes.append(f_node)

        # ── 2a. Normas y su conexión fw → norm → finding ────────────────────────
        norm_buckets = [
            ("COBIT", finding.cobit_refs),
            ("COSO",  finding.coso_refs),
            ("RGSI",  finding.rgsi_refs),
        ]

        for fw, refs in norm_buckets:
            for ref in refs:
                norm_node_id = f"norm-{fw}-{ref.code}"

                if norm_node_id not in seen_norms:
                    norm_node = {
                        "id": norm_node_id,
                        "label": ref.code,
                        "type": "norm",
                        "framework": fw,
                        "title": ref.title or ref.code,
                        "domain": ref.domain or ref.component or ref.section or "",
                        "color": FRAMEWORK_HUB_COLOR.get(fw, "#6b7280"),
                    }
                    seen_norms[norm_node_id] = norm_node
                    nodes.append(norm_node)
                    # fw → norm
                    _add_edge(f"fw-{fw}", norm_node_id, "fw-norm")

                # norm → finding
                _add_edge(norm_node_id, f_node_id, "norm-finding")

        # ── 2b. Evidencias/Documentos ───────────────────────────────────────────
        for ev in finding.evidence:
            doc_node_id = f"doc-{ev.doc_id}"

            if doc_node_id not in seen_docs:
                doc_obj = doc_index.get(ev.doc_id)
                doc_name = ev.doc_name or (doc_obj.name if doc_obj else ev.doc_id)
                doc_node = {
                    "id": doc_node_id,
                    "label": (doc_name[:18] + "…") if len(doc_name) > 18 else doc_name,
                    "type": "document",
                    "title": doc_name,
                    "docType": doc_obj.type if doc_obj else "pdf",
                    "page": ev.page,
                    "color": "#22c55e",
                }
                seen_docs[doc_node_id] = doc_node
                nodes.append(doc_node)

            # finding → document
            _add_edge(f_node_id, doc_node_id, "finding-doc")

    # ── 3. Aristas finding ↔ finding (relaciones) ──────────────────────────────
    finding_list = list(seen_findings.values())

    # Índice de códigos normativos por hallazgo: finding_node_id → set(norm_codes)
    finding_norm_codes: dict[str, set] = {}
    for finding in findings:
        f_node_id = f"finding-{finding.id}"
        codes: set[str] = set()
        for ref in finding.cobit_refs:
            codes.add(ref.code)
        for ref in finding.coso_refs:
            codes.add(ref.code)
        for ref in finding.rgsi_refs:
            codes.add(ref.code)
        finding_norm_codes[f_node_id] = codes

    # Índice de títulos por finding_node_id para similitud semántica
    finding_titles: dict[str, str] = {
        f"finding-{f.id}": f.title for f in findings
    }

    for fa_id, fb_id in combinations(seen_findings.keys(), 2):
        codes_a = finding_norm_codes.get(fa_id, set())
        codes_b = finding_norm_codes.get(fb_id, set())

        # Relación por norma compartida
        shared_codes = codes_a & codes_b
        if shared_codes:
            shared_label = ", ".join(list(shared_codes)[:2])
            _add_edge(fa_id, fb_id, "finding-related",
                      reason="shared_norm",
                      sharedCodes=list(shared_codes))
            continue

        # Relación por similitud semántica
        title_a = finding_titles.get(fa_id, "")
        title_b = finding_titles.get(fb_id, "")
        if title_a and title_b:
            sim = jaccard_similarity(title_a, title_b)
            if sim >= FINDING_RELATION_THRESHOLD:
                _add_edge(fa_id, fb_id, "finding-related",
                          reason="semantic",
                          similarity=round(sim, 3))

    # ── 4. Estadísticas ────────────────────────────────────────────────────────
    stats = {
        "total_norms":      len(seen_norms),
        "total_findings":   len(seen_findings),
        "documents_linked": len(seen_docs),
        "related_findings": sum(1 for e in edges if e["type"] == "finding-related"),
        "cobit_norms":      sum(1 for n in seen_norms.values() if n["framework"] == "COBIT"),
        "coso_norms":       sum(1 for n in seen_norms.values() if n["framework"] == "COSO"),
        "rgsi_norms":       sum(1 for n in seen_norms.values() if n["framework"] == "RGSI"),
    }

    return ok({
        "nodes": nodes,
        "edges": edges,
        "stats": stats,
    })
