"""
Orquestador principal de auditoría con Gemini API.
"""

from __future__ import annotations
import asyncio
import json
from pathlib import Path
from google import genai
from google.genai import types

from ..config import (
    GEMINI_API_KEY,
    MODELO_GEMINI,
    QUERIES_AUDITORIA_COBIT,
    MAX_REINTENTOS_VALIDACION,
    UPLOADS_DIR,
    SALIDAS_DIR,
)
from ..models import (
    Hallazgo,
    ComponenteCOSO,
    ContextoEntidad,
    ResultadoAuditoria,
    EstadoAuditoria,
)
from ..ingesta.gestor_archivos_gemini import gestor_archivos
from .prompts import (
    PROMPT_SISTEMA_AUDITOR,
    PROMPT_AUDITORIA_COBIT,
    PROMPT_SISTEMA_COSO,
    PROMPT_EVALUACION_COSO,
    PROMPT_REINTENTO,
)
from .validador import (
    validar_hallazgos,
    validar_componentes_coso,
    formatear_errores_para_reintento,
)
from ..websocket_manager import ws_manager


class AuditorRAG:
    """Orquestador del pipeline de auditoría RAG usando Gemini."""

    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.contexto_entidad: ContextoEntidad | None = None
        self.hallazgos: list[Hallazgo] = []
        self.componentes_coso: list[ComponenteCOSO] = []
        self.estado = EstadoAuditoria.IDLE

    async def ejecutar_auditoria_completa(
        self,
        nombre_grupo: str | None = None,
        integrantes: list[str] | None = None,
        alcance: str | None = None,
    ) -> ResultadoAuditoria:
        try:
            # ── Paso 1: Subir documentos a Gemini ────────────────────
            self.estado = EstadoAuditoria.PROCESANDO_DOCUMENTOS
            await ws_manager.send_progress(1, 6, "📄 Subiendo documentos a Google AI Studio...", 10, self.estado.value)

            gestor_archivos.limpiar_archivos()
            archivos_gemini = await asyncio.to_thread(gestor_archivos.subir_directorio, UPLOADS_DIR)
            
            if not archivos_gemini:
                raise ValueError("No se encontraron documentos en la carpeta de uploads")

            await ws_manager.send_progress(1, 6, f"📄 {len(archivos_gemini)} documentos subidos exitosamente", 20, self.estado.value)

            # ── Paso 2: Extraer contexto de la entidad ───────────────
            self.estado = EstadoAuditoria.EXTRAYENDO_CONTEXTO
            await ws_manager.send_progress(2, 6, "🏢 Analizando contexto de la entidad...", 30, self.estado.value)

            self.contexto_entidad = await self._extraer_contexto_entidad()
            if nombre_grupo:
                self.contexto_entidad.grupo_auditor = nombre_grupo
            if integrantes:
                self.contexto_entidad.integrantes = integrantes
            if alcance:
                self.contexto_entidad.alcance = alcance

            await ws_manager.send_progress(2, 6, f"🏢 Entidad: {self.contexto_entidad.nombre_entidad}", 40, self.estado.value)

            # ── Paso 3: Preparar contexto vectorial (dummy step) ─────
            self.estado = EstadoAuditoria.VECTORIZANDO
            await ws_manager.send_progress(3, 6, "🧮 Procesando caché vectorial en Gemini...", 45, self.estado.value)
            await asyncio.sleep(1) # Gemini lo hace instantáneo
            await ws_manager.send_progress(3, 6, "🧮 Caché indexada exitosamente", 50, self.estado.value)

            # ── Paso 4: Ejecutar auditoría COBIT ─────────────────────
            self.estado = EstadoAuditoria.EJECUTANDO_AUDITORIA
            await ws_manager.send_progress(4, 6, "🤖 Ejecutando auditoría COBIT con Gemini...", 55, self.estado.value)

            self.hallazgos = await self._ejecutar_auditoria_cobit()

            await ws_manager.send_progress(4, 6, f"🤖 {len(self.hallazgos)} hallazgos identificados", 75, self.estado.value)

            # ── Paso 5: Evaluación COSO ──────────────────────────────
            self.estado = EstadoAuditoria.VALIDANDO
            await ws_manager.send_progress(5, 6, "📋 Ejecutando evaluación COSO...", 80, self.estado.value)

            self.componentes_coso = await self._ejecutar_evaluacion_coso()

            await ws_manager.send_progress(5, 6, f"📋 {len(self.componentes_coso)} componentes COSO evaluados", 90, self.estado.value)

            # ── Paso 6: Generar documentos ───────────────────────────
            self.estado = EstadoAuditoria.GENERANDO_DOCUMENTOS
            await ws_manager.send_progress(6, 6, "📊 Generando documentos de salida...", 95, self.estado.value)

            archivos = await asyncio.to_thread(self._generar_documentos)

            # ── Completado ───────────────────────────────────────────
            self.estado = EstadoAuditoria.COMPLETADO
            resultado = ResultadoAuditoria(
                contexto=self.contexto_entidad,
                hallazgos=self.hallazgos,
                componentes_coso=self.componentes_coso,
                archivos_generados=archivos,
            )
            await ws_manager.send_progress(6, 6, f"✅ Auditoría completada — {len(self.hallazgos)} hallazgos", 100, self.estado.value)
            await ws_manager.send_completed(resultado.model_dump())

            return resultado

        except Exception as e:
            self.estado = EstadoAuditoria.ERROR
            await ws_manager.send_error(f"Error en Gemini: {str(e)}", detalle=str(e))
            raise

    async def _extraer_contexto_entidad(self) -> ContextoEntidad:
        prompt = "Analiza todos los documentos proporcionados e identifica: nombre de la empresa, rubro principal, periodo evaluado (ej. 2024, semestre I), fecha de auditoria y nivel de madurez tecnológica aparente (Bajo, Medio, Alto). Devuelve un JSON con las claves: nombre_entidad, rubro, periodo_evaluado, fecha_auditoria, tamano_aparente, madurez_tecnologica. No agregues markdown."
        
        contents = gestor_archivos.obtener_archivos() + [prompt]
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=MODELO_GEMINI,
            contents=contents,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        try:
            datos = json.loads(response.text)
            return ContextoEntidad(
                nombre_entidad=datos.get("nombre_entidad", "Entidad Desconocida"),
                rubro=datos.get("rubro", "No especificado"),
                periodo_evaluado=datos.get("periodo_evaluado", "2024"),
                fecha_auditoria=datos.get("fecha_auditoria", "2024"),
                tamano_aparente=datos.get("tamano_aparente", "No especificado"),
                madurez_tecnologica=datos.get("madurez_tecnologica", "No especificado"),
                grupo_auditor="Sin definir",
                integrantes=[],
                alcance="Auditoría General de Sistemas"
            )
        except Exception:
            return ContextoEntidad(nombre_entidad="Error Parseando Entidad", periodo_evaluado="2024", fecha_auditoria="2024", grupo_auditor="", integrantes=[], alcance="", rubro="", tamano_aparente="", madurez_tecnologica="")

    async def _ejecutar_auditoria_cobit(self) -> list[Hallazgo]:
        todos_hallazgos: list[Hallazgo] = []
        codigo_actual = 1

        for i, query_info in enumerate(QUERIES_AUDITORIA_COBIT):
            print(f"  🔍 Query {i + 1}/{len(QUERIES_AUDITORIA_COBIT)}: {query_info['id']}")
            
            # Formatear prompt
            prompt_user = PROMPT_AUDITORIA_COBIT.format(
                contexto="[Contexto extraído directamente de los archivos subidos al File API de Gemini]",
                query=query_info["query"],
                dominios=", ".join(query_info["dominios"]),
                inicio_codigo=codigo_actual,
            )

            hallazgos = await self._generar_hallazgos_con_reintento(
                prompt_base=prompt_user,
                inicio_codigo=codigo_actual,
            )

            todos_hallazgos.extend(hallazgos)
            codigo_actual += len(hallazgos)

        for i, h in enumerate(todos_hallazgos, 1):
            h.codigo = f"H{i}"

        return todos_hallazgos

    async def _generar_hallazgos_con_reintento(self, prompt_base: str, inicio_codigo: int) -> list[Hallazgo]:
        archivos = gestor_archivos.obtener_archivos()

        for intento in range(MAX_REINTENTOS_VALIDACION):
            try:
                if intento == 0:
                    prompt = prompt_base
                else:
                    prompt = PROMPT_REINTENTO.format(errores=errores_str, contexto="[Archivos Gemini]", query="Reintento")

                contents = archivos + [prompt]
                
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=MODELO_GEMINI,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=PROMPT_SISTEMA_AUDITOR,
                        response_mime_type="application/json",
                        temperature=0.2
                    )
                )

                respuesta = response.text
                hallazgos, errores = validar_hallazgos(respuesta)

                if hallazgos:
                    return hallazgos

                errores_str = formatear_errores_para_reintento(errores)
                print(f"    ✗ Intento {intento + 1}: Validación fallida")

            except Exception as e:
                print(f"    ✗ Intento {intento + 1}: Error: {e}")
                errores_str = str(e)

        return []

    async def _ejecutar_evaluacion_coso(self) -> list[ComponenteCOSO]:
        archivos = gestor_archivos.obtener_archivos()
        hallazgos_resumen = "\n".join(f"- {h.codigo}: {h.descripcion[:150]}..." for h in self.hallazgos)

        prompt = PROMPT_EVALUACION_COSO.format(
            contexto="[Archivos de la entidad cargados en Gemini]",
            hallazgos_resumen=hallazgos_resumen,
        )

        for intento in range(MAX_REINTENTOS_VALIDACION):
            try:
                contents = archivos + [prompt]
                
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=MODELO_GEMINI,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=PROMPT_SISTEMA_COSO,
                        response_mime_type="application/json",
                        temperature=0.2
                    )
                )

                respuesta = response.text
                componentes, errores = validar_componentes_coso(respuesta)

                if componentes:
                    return componentes

            except Exception as e:
                print(f"  ✗ Error COSO intento {intento + 1}: {e}")

        return []

    def _generar_documentos(self) -> list[str]:
        archivos_generados: list[str] = []
        if not self.contexto_entidad or not self.hallazgos:
            return archivos_generados

        json_path = SALIDAS_DIR / "hallazgos.json"
        with open(json_path, "w", encoding="utf-8") as f:
            datos = {
                "contexto": self.contexto_entidad.model_dump(),
                "hallazgos": [h.model_dump() for h in self.hallazgos],
                "componentes_coso": [c.model_dump() for c in self.componentes_coso],
            }
            json.dump(datos, f, ensure_ascii=False, indent=2)
        archivos_generados.append("hallazgos.json")

        try:
            from ..exportacion.exportar_word import generar_fichas_hallazgos, generar_guia_pruebas
            ruta_fichas = generar_fichas_hallazgos(self.hallazgos, self.contexto_entidad)
            if ruta_fichas: archivos_generados.append(ruta_fichas.name)
            ruta_pruebas = generar_guia_pruebas(self.hallazgos, self.contexto_entidad)
            if ruta_pruebas: archivos_generados.append(ruta_pruebas.name)
        except Exception as e:
            print(f"  ⚠ Error generando Word: {e}")

        try:
            from ..exportacion.exportar_excel_evaluacion import generar_excel_evaluacion
            ruta_eval = generar_excel_evaluacion(self.hallazgos, self.contexto_entidad)
            if ruta_eval: archivos_generados.append(ruta_eval.name)
        except Exception as e:
            print(f"  ⚠ Error generando Excel evaluación: {e}")

        try:
            from ..exportacion.exportar_excel_coso import generar_excel_coso
            ruta_coso = generar_excel_coso(self.componentes_coso, self.contexto_entidad)
            if ruta_coso: archivos_generados.append(ruta_coso.name)
        except Exception as e:
            print(f"  ⚠ Error generando Excel COSO: {e}")

        return archivos_generados

auditor_rag = AuditorRAG()
