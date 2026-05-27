"""Servicio de lógica de negocio para hallazgos."""

from typing import List, Optional

from loguru import logger

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.finding import Finding, NormativeRef, Evidence
from app.repositories.audit_repository import AuditRepository
from app.repositories.finding_repository import FindingRepository
from app.schemas.finding import FindingCreate, FindingUpdate
from app.services.history_service import HistoryService
from app.utils.enums import FindingStatus, RiskLevel
from app.utils.helpers import generate_id
from app.utils.risk_matrix import calculate_risk
from app.utils.timestamps import utcnow_iso


class FindingService:
    def __init__(
        self,
        finding_repo: FindingRepository,
        audit_repo: AuditRepository,
        history: HistoryService,
    ):
        self._findings = finding_repo
        self._audits = audit_repo
        self._history = history

    async def _assert_owner(self, audit_id: str, owner_id: str) -> None:
        if not await self._audits.verify_owner(audit_id, owner_id):
            raise ForbiddenError("No tienes acceso a esta auditoría.")

    def _build_finding_from_schema(self, audit_id: str, data: FindingCreate) -> Finding:
        finding_id = generate_id("HLZ-")
        risk = calculate_risk(data.impact, data.probability)
        now = utcnow_iso()

        def _parse_refs(raw_list, ref_class=NormativeRef):
            return [ref_class(**r.model_dump(by_alias=True)) for r in raw_list]

        return Finding(
            id=finding_id,
            auditId=audit_id,
            title=data.title,
            description_finding=data.description_finding,
            criteria_description=data.criteria_description,
            cause=data.cause,
            effect=data.effect,
            conclusion=data.conclusion,
            description=data.description,
            recommendation=data.recommendation,
            risk=risk,
            risk_level=risk.value,
            impact=data.impact,
            probability=data.probability,
            status=FindingStatus.PENDIENTE,
            confidence=data.confidence,
            cobitRef=_parse_refs(data.cobit_refs),
            cosoRef=_parse_refs(data.coso_refs),
            rgsiRef=_parse_refs(data.rgsi_refs),
            evidence=[Evidence(**e.model_dump(by_alias=True)) for e in data.evidence],
            quote=data.quote,
            detectedBy=data.detected_by,
            createdAt=now,
            updatedAt=now,
        )

    async def create(self, audit_id: str, data: FindingCreate, owner_id: str) -> Finding:
        await self._assert_owner(audit_id, owner_id)
        finding = self._build_finding_from_schema(audit_id, data)
        result = await self._findings.create(finding)

        await self._audits.increment_counter(audit_id, "findingsCount", 1)
        await self._audits.increment_counter(audit_id, "pendingFindings", 1)

        logger.info(f"Hallazgo creado: {result.id} en auditoría {audit_id}")
        return result

    async def create_batch_internal(self, audit_id: str, findings: List[Finding]) -> List[Finding]:
        """Inserción masiva desde el pipeline IA (sin verificar owner)."""
        result = await self._findings.create_batch(findings)
        count = len(result)
        await self._audits.increment_counter(audit_id, "findingsCount", count)
        await self._audits.increment_counter(audit_id, "pendingFindings", count)
        logger.info(f"{count} hallazgos creados en auditoría {audit_id}")
        return result

    async def get_by_id(self, audit_id: str, finding_id: str, owner_id: str) -> Finding:
        await self._assert_owner(audit_id, owner_id)
        finding = await self._findings.get_by_id(audit_id, finding_id)
        if finding is None:
            raise NotFoundError("Hallazgo", finding_id)
        return finding

    async def list_by_audit(self, audit_id: str, owner_id: str) -> List[Finding]:
        await self._assert_owner(audit_id, owner_id)
        return await self._findings.list_by_audit(audit_id)

    async def update(self, audit_id: str, finding_id: str, data: FindingUpdate, owner_id: str) -> Finding:
        old = await self.get_by_id(audit_id, finding_id, owner_id)
        old_dict = old.to_firestore()

        update_fields: dict = {"updatedAt": utcnow_iso()}

        if data.title is not None:
            update_fields["title"] = data.title
        if data.description is not None:
            update_fields["description"] = data.description
        if data.recommendation is not None:
            update_fields["recommendation"] = data.recommendation
        if data.impact is not None:
            update_fields["impact"] = data.impact
        if data.probability is not None:
            update_fields["probability"] = data.probability

        # Recalcular riesgo si cambiaron impacto o probabilidad
        new_impact = data.impact if data.impact is not None else old.impact
        new_prob = data.probability if data.probability is not None else old.probability
        if data.impact is not None or data.probability is not None:
            update_fields["risk"] = calculate_risk(new_impact, new_prob).value

        if data.status is not None:
            update_fields["status"] = data.status.value
            # Ajustar contador pendingFindings
            if old.status == FindingStatus.PENDIENTE and data.status != FindingStatus.PENDIENTE:
                await self._audits.increment_counter(audit_id, "pendingFindings", -1)
            elif old.status != FindingStatus.PENDIENTE and data.status == FindingStatus.PENDIENTE:
                await self._audits.increment_counter(audit_id, "pendingFindings", 1)

        updated = await self._findings.update(audit_id, finding_id, update_fields)

        # Registrar en history los campos modificados
        await self._history.record_update(
            audit_id, finding_id, old_dict, update_fields, owner_id
        )

        return updated

    async def delete(self, audit_id: str, finding_id: str, owner_id: str) -> None:
        finding = await self.get_by_id(audit_id, finding_id, owner_id)
        await self._findings.delete(audit_id, finding_id)

        await self._audits.increment_counter(audit_id, "findingsCount", -1)
        if finding.status == FindingStatus.PENDIENTE:
            await self._audits.increment_counter(audit_id, "pendingFindings", -1)

        logger.info(f"Hallazgo eliminado: {finding_id}")
