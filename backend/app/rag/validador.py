"""
Validador de respuestas del LLM con Pydantic.
Implementa reintentos automáticos cuando la respuesta no cumple los requisitos.
"""

from __future__ import annotations
import json
from typing import Any

from pydantic import ValidationError

from ..models import Hallazgo, ComponenteCOSO


def validar_hallazgos(respuesta_json: str) -> tuple[list[Hallazgo], list[str]]:
    """
    Valida la respuesta JSON del LLM contra el modelo Hallazgo.

    Args:
        respuesta_json: String JSON con la lista de hallazgos.

    Returns:
        Tupla de (hallazgos_validos, errores).
    """
    errores: list[str] = []

    # Parsear JSON
    try:
        datos = _parsear_json(respuesta_json)
    except Exception as e:
        return [], [f"Error parseando JSON: {e}"]

    if not isinstance(datos, list):
        datos = [datos]

    # Validar cada hallazgo
    hallazgos_validos: list[Hallazgo] = []

    for i, dato in enumerate(datos):
        try:
            hallazgo = Hallazgo(**dato)
            hallazgos_validos.append(hallazgo)
        except ValidationError as e:
            errores_hallazgo = []
            for error in e.errors():
                campo = " → ".join(str(loc) for loc in error["loc"])
                msg = error["msg"]
                errores_hallazgo.append(f"  Hallazgo {i + 1}, campo '{campo}': {msg}")
            errores.extend(errores_hallazgo)
        except Exception as e:
            errores.append(f"  Hallazgo {i + 1}: Error inesperado: {e}")

    return hallazgos_validos, errores


def validar_componentes_coso(
    respuesta_json: str,
) -> tuple[list[ComponenteCOSO], list[str]]:
    """
    Valida la respuesta JSON del LLM contra el modelo ComponenteCOSO.

    Args:
        respuesta_json: String JSON con la lista de componentes COSO.

    Returns:
        Tupla de (componentes_validos, errores).
    """
    errores: list[str] = []

    try:
        datos = _parsear_json(respuesta_json)
    except Exception as e:
        return [], [f"Error parseando JSON COSO: {e}"]

    if not isinstance(datos, list):
        datos = [datos]

    componentes_validos: list[ComponenteCOSO] = []

    for i, dato in enumerate(datos):
        try:
            componente = ComponenteCOSO(**dato)
            componentes_validos.append(componente)
        except ValidationError as e:
            for error in e.errors():
                campo = " → ".join(str(loc) for loc in error["loc"])
                msg = error["msg"]
                errores.append(
                    f"  Componente {i + 1}, campo '{campo}': {msg}"
                )
        except Exception as e:
            errores.append(f"  Componente {i + 1}: Error inesperado: {e}")

    return componentes_validos, errores


def formatear_errores_para_reintento(errores: list[str]) -> str:
    """Formatea los errores para incluirlos en el prompt de reintento."""
    return "\n".join(errores)


def _parsear_json(texto: str) -> Any:
    """
    Parsea JSON de la respuesta del LLM, manejando formatos comunes.
    """
    texto = texto.strip()

    # Remover bloques markdown
    if texto.startswith("```json"):
        texto = texto[7:]
    elif texto.startswith("```"):
        texto = texto[3:]
    if texto.endswith("```"):
        texto = texto[:-3]
    texto = texto.strip()

    # Intentar parsear directamente
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass

    # Buscar el array JSON dentro del texto
    inicio_array = texto.find("[")
    fin_array = texto.rfind("]")
    if inicio_array != -1 and fin_array != -1:
        try:
            return json.loads(texto[inicio_array : fin_array + 1])
        except json.JSONDecodeError:
            pass

    # Buscar un objeto JSON
    inicio_obj = texto.find("{")
    fin_obj = texto.rfind("}")
    if inicio_obj != -1 and fin_obj != -1:
        try:
            return json.loads(texto[inicio_obj : fin_obj + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"No se pudo parsear JSON de la respuesta. "
        f"Primeros 200 chars: {texto[:200]}"
    )
