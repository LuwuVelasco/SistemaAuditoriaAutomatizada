"""
Gestor de conexiones WebSocket para envío de progreso en tiempo real.
"""

from __future__ import annotations
import json
import asyncio
from typing import Any
from fastapi import WebSocket


class WebSocketManager:
    """Gestiona conexiones WebSocket activas y envía progreso."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Acepta y registra una nueva conexión."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        """Elimina una conexión desconectada."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def send_progress(
        self,
        paso: int,
        total: int,
        mensaje: str,
        porcentaje: float,
        estado: str,
        extra: dict[str, Any] | None = None,
    ):
        """Envía mensaje de progreso a todos los clientes conectados."""
        data = {
            "tipo": "progreso",
            "paso": paso,
            "total": total,
            "mensaje": mensaje,
            "porcentaje": porcentaje,
            "estado": estado,
        }
        if extra:
            data.update(extra)

        message = json.dumps(data, ensure_ascii=False)
        disconnected: list[WebSocket] = []

        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception:
                    disconnected.append(connection)

            for conn in disconnected:
                self.active_connections.remove(conn)

    async def send_error(self, mensaje: str, detalle: str = ""):
        """Envía un mensaje de error a todos los clientes."""
        data = {
            "tipo": "error",
            "mensaje": mensaje,
            "detalle": detalle,
            "estado": "error",
        }
        message = json.dumps(data, ensure_ascii=False)
        disconnected: list[WebSocket] = []

        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception:
                    disconnected.append(connection)

            for conn in disconnected:
                self.active_connections.remove(conn)

    async def send_completed(self, resultado: dict[str, Any]):
        """Envía notificación de auditoría completada."""
        data = {
            "tipo": "completado",
            "estado": "completado",
            "resultado": resultado,
        }
        message = json.dumps(data, ensure_ascii=False, default=str)
        disconnected: list[WebSocket] = []

        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception:
                    disconnected.append(connection)

            for conn in disconnected:
                self.active_connections.remove(conn)


# Instancia global
ws_manager = WebSocketManager()
